#!/usr/bin/env python3
"""
CBICQC quality control analysis and reporting class
The main analysis and reporting workflow is handled from here

AUTHORS
----
Mike Tyszka, Ph.D., Caltech Brain Imaging Center

DATES
----
2019-05-30 JMT Split out from workflow into single class for easy testing

MIT License

Copyright (c) 2019 Mike Tyszka

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import json
import tempfile
import numpy as np
import nibabel as nb
import SimpleITK as sitk

from bids import BIDSLayout

from .timeseries import temporal_mean_sd, extract_timeseries, detrend_timeseries
from .graphics import (plot_roi_timeseries,
                       plot_mopar_timeseries,
                       orthoslice_montage)
from .rois import roi_labels
from .report import ReportPDF


class CBICQC:

    def __init__(self, bids_dir, subject, session):

        self._bids_dir = bids_dir
        self._subject = subject
        self._session = session

        # Create safe temporary directory
        self._work_dir = tempfile.mkdtemp()
        self._report_fname = os.path.join(self._work_dir, 'report.pdf')

        # Intermediate filenames
        self._tmean_fname = os.path.join(self._work_dir, 'tmean.nii.gz')
        self._tsd_fname = os.path.join(self._work_dir, 'tsd.nii.gz')
        self._roi_labels_fname = os.path.join(self._work_dir, 'roi_labels.nii.gz')

        # Flags
        self._save_intermediates = False

    def run(self):

        print('Starting CBIC QC analysis')

        # Get BIDS layout
        # Index BIDS directory
        layout = BIDSLayout(self._bids_dir,
                            absolute_paths=True,
                            ignore=['work', 'derivatives', 'exclude'])

        # Get first QC image for this subject/session
        img_list = layout.get(subject=self._subject,
                              session=self._session,
                              suffix='T2star',
                              extensions=['nii', 'nii.gz'],
                              return_type='file')
        if not img_list:
            print('* No QC images found for subject {} session {} - exiting'.
                  format(self._subject, self._session))
            sys.exit(1)

        qc_img_fname = img_list[0]
        qc_meta_fname = qc_img_fname.replace('.nii.gz', '.json')

        # Load 4D QC phantom image
        print('  Loading QC timeseries image')
        qc_nii = nb.load(qc_img_fname)

        # Load metadata if available
        print('  Loading QC metadata')
        try:
            with open(qc_meta_fname, 'r') as fd:
                meta = json.load(fd)
        except IOError:
            print('* Could not open image metadata {}'.format(qc_meta_fname))
            print('* Using default imaging parameters')
            meta = self._default_metadata()

        # Integrate additional meta data from Nifti header and filename
        meta['Subject'] = self._subject
        meta['Session'] = self._session
        meta['VoxelSize'] = ' x '.join(str(x) for x in qc_nii.header.get('pixdim')[1:4])
        meta['MatrixSize'] = ' x '.join(str(x) for x in qc_nii.shape)

        # Perform rigid body motion correction on QC series
        qc_moco_nii, qc_moco_pars = self._moco(qc_nii)

        # Temporal mean and sd images
        print('  Calculating temporal mean image')
        tmean_nii, tsd_nii = temporal_mean_sd(qc_moco_nii)

        # Create ROI labels
        print('  Constructing ROI labels')
        rois_nii = roi_labels(tmean_nii)

        # Extract ROI time series
        print('  Extracting ROI time series')
        s_mean_t = extract_timeseries(qc_moco_nii, rois_nii)

        # Detrend time series
        print('  Detrending time series')
        fit_results, s_detrend_t = detrend_timeseries(s_mean_t)

        # Calculate QC metrics
        metrics = self._qc_metrics(fit_results)

        #
        # Plot graphs
        #

        roi_ts_fname = os.path.join(self._work_dir, 'roi_timeseries.png')
        plot_roi_timeseries(s_mean_t, s_detrend_t, roi_ts_fname)

        mopar_ts_fname = os.path.join(self._work_dir, 'mopar_timeseries.png')
        plot_mopar_timeseries(qc_moco_pars, mopar_ts_fname)

        #
        # Create orthoslice images
        #

        tmean_montage_fname = os.path.join(self._work_dir, 'tmean_montage.png')
        orthoslice_montage(tmean_nii, tmean_montage_fname)

        tsd_montage_fname = os.path.join(self._work_dir, 'tsd_montage.png')
        orthoslice_montage(tsd_nii, tsd_montage_fname)

        # OPTIONAL: Save intermediate images
        if self._save_intermediates:

            print('  Saving intermediate images')
            nb.save(tmean_nii, self._tmean_fname)
            nb.save(tsd_nii, self._tsd_fname)
            nb.save(rois_nii, self._roi_labels_fname)

        # Construct filename dictionary to pass to PDF generator
        fnames = dict(TempDir=self._work_dir,
                      ReportPDF=self._report_fname,
                      ROITimeseries=roi_ts_fname,
                      MoparTimeseries=mopar_ts_fname,
                      TMeanMontage=tmean_montage_fname,
                      TSDMontage=tsd_montage_fname,
                      TMean=self._tmean_fname,
                      TSD=self._tsd_fname,
                      ROILabels = self._roi_labels_fname)

        # Generate and save PDF report
        ReportPDF(fnames, meta, metrics)

        return fnames

    def _default_metadata(self):

        meta = dict(Manufacturer='Unkown',
                    Scanner='Unknown',
                    RepetitionTime=3.0,
                    EchoTime=0.030)

        return meta

    def _parse_filename(self, fname):

        bname = os.path.basename(fname)

        # Split at underscores
        keyvals = bname.split('_')

        subject, session = 'Unknown', 'Unknown'

        for kv in keyvals:

            if '-' in kv and len(kv) >= 3:

                k, v = kv.split('-')

                if 'sub' in k:
                    subject = v
                if 'ses' in k:
                    session = v

        return subject, session

    def _qc_metrics(self, fit_results):

        phantom_res = fit_results[0]
        nyquist_res = fit_results[1]
        air_res = fit_results[2]

        phantom_a_warm = phantom_res.x[0]
        phantom_t_warm = phantom_res.x[1]
        phantom_drift = phantom_res.x[2]
        phantom_mean = phantom_res.x[3]
        nyquist_mean = nyquist_res.x[3]
        noise_mean = air_res.x[3]

        metrics = dict()
        metrics['SFNR'] = phantom_mean / noise_mean
        metrics['PhantomMean'] = phantom_mean
        metrics['SigArtRatio'] = phantom_mean / nyquist_mean
        metrics['NoiseFloor'] = noise_mean
        metrics['Drift'] = phantom_drift / phantom_mean * 100
        metrics['WarmupAmp'] = phantom_a_warm / phantom_mean * 100
        metrics['WarmupTime'] = phantom_t_warm

        return metrics

    def _moco(self, img_nii):

        img = img_nii.get_data()
        moco = np.zeros_like(img)

        # Reference image
        img_0 = img[:, :, :, 0]

        # Loop over remaining images
        for tc in range(1, img.shape[3]):

            img_t = img[:, :, :, tc]

            img_t_0, tx_pars = self._rigid_register(img_t, img_0)

            moco[:, :, :, tc] = img_t_0

        moco_nii = nb.Nifti1Image(moco, img_nii.affine)

        moco_pars = np.zeros([img.shape[3], 6])

        return moco_nii, moco_pars

    def _rigid_register(self, img, ref):

        fixed_image = sitk.GetImageFromArray(ref)
        moving_image = sitk.GetImageFromArray(img)

        initial_transform = sitk.CenteredTransformInitializer(fixed_image,
                                                              moving_image,
                                                              sitk.Euler3DTransform(),
                                                              sitk.CenteredTransformInitializerFilter.GEOMETRY)

        # Setup image registration
        registration_method = sitk.ImageRegistrationMethod()

        # Similarity metric settings.
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.01)

        registration_method.SetInterpolator(sitk.sitkLinear)

        # Optimizer settings.
        registration_method.SetOptimizerAsGradientDescent(learningRate=1.0,
                                                          numberOfIterations=100,
                                                          convergenceMinimumValue=1e-6,
                                                          convergenceWindowSize=10)

        registration_method.SetOptimizerScalesFromPhysicalShift()

        # Setup for the multi-resolution framework.
        registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

        # Don't optimize in-place, we would possibly like to run this cell multiple times.
        registration_method.SetInitialTransform(initial_transform, inPlace=False)

        # Run registration
        final_transform = registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
                                                      sitk.Cast(moving_image, sitk.sitkFloat32))

        moving_resampled = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0,
                                         moving_image.GetPixelID())

        return moving_resampled, final_transform

