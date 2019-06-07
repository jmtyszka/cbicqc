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
import subprocess
import json
import tempfile
import shutil
import numpy as np
import nibabel as nb
import datetime as dt

from nipype.interfaces.fsl import MCFLIRT

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

        # Create work and report directories
        self._work_dir = tempfile.mkdtemp()
        self._report_dir = os.path.join(self._bids_dir, 'derivatives', 'cbicqc')
        os.makedirs(self._report_dir, exist_ok=True)

        # Intermediate filenames
        self._report_fname = os.path.join(self._work_dir, 'report.pdf')
        self._tmean_fname = os.path.join(self._work_dir, 'tmean.nii.gz')
        self._tsd_fname = os.path.join(self._work_dir, 'tsd.nii.gz')
        self._roi_labels_fname = os.path.join(self._work_dir, 'roi_labels.nii.gz')
        self._roi_ts_png = os.path.join(self._work_dir, 'roi_timeseries.png')
        self._mopar_ts_png = os.path.join(self._work_dir, 'mopar_timeseries.png')
        self._tmean_montage_png = os.path.join(self._work_dir, 'tmean_montage.png')
        self._tsd_montage_png = os.path.join(self._work_dir, 'tsd_montage.png')

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
        print('  Starting motion correction')
        t0 = dt.datetime.now()
        qc_moco_nii, qc_moco_pars = self._moco(qc_nii)
        t1 = dt.datetime.now()
        print('  Completed motion correction in {} seconds'.format((t1-t0).seconds))

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
        # Create report images
        #
        plot_roi_timeseries(s_mean_t, s_detrend_t, self._roi_ts_png)
        plot_mopar_timeseries(qc_moco_pars, self._mopar_ts_png)
        orthoslice_montage(tmean_nii, self._tmean_montage_png)
        orthoslice_montage(tsd_nii, self._tsd_montage_png)

        # OPTIONAL: Save intermediate images
        if self._save_intermediates:

            print('  Saving intermediate images')
            nb.save(tmean_nii, self._tmean_fname)
            nb.save(tsd_nii, self._tsd_fname)
            nb.save(rois_nii, self._roi_labels_fname)

        # Construct filename dictionary to pass to PDF generator
        fnames = dict(TempDir=self._work_dir,
                      ReportPDF=self._report_fname,
                      ROITimeseries=self._roi_ts_png,
                      MoparTimeseries=self._mopar_ts_png,
                      TMeanMontage=self._tmean_montage_png,
                      TSDMontage=self._tsd_montage_png,
                      TMean=self._tmean_fname,
                      TSD=self._tsd_fname,
                      ROILabels = self._roi_labels_fname)

        # Generate PDF report
        ReportPDF(fnames, meta, metrics)

        # Copy final report to derivatives
        self._save_report(fnames)

        # Cleanup temporary QC directory
        self.cleanup()

    def cleanup(self):

        shutil.rmtree(self._work_dir)

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
        metrics['PhantomMean'] = phantom_mean
        metrics['SFNR'] = phantom_mean / noise_mean
        metrics['SigArtRatio'] = phantom_mean / nyquist_mean
        metrics['NoiseFloor'] = noise_mean
        metrics['Drift'] = phantom_drift / phantom_mean * 100
        metrics['WarmupAmp'] = phantom_a_warm / phantom_mean * 100
        metrics['WarmupTime'] = phantom_t_warm

        return metrics

    def _moco(self, img_nii):
        """
        Light wrapper for MCFLIRT (no need to use nipype)

        :param img_nii:
        :return:
        """

        in_fname = os.path.join(self._work_dir, 'qc.nii.gz')
        out_stub = os.path.join(self._work_dir, 'qc_mcf')

        nb.save(img_nii, in_fname)

        mcflirt_cmd = os.path.join(os.environ['FSLDIR'], 'bin', 'mcflirt')

        subprocess.run([mcflirt_cmd, '-in', in_fname, '-out', out_stub, '-meanvol', '-plots'])

        moco_nii = nb.load(out_stub + '.nii.gz')
        moco_pars = np.genfromtxt(out_stub + '.par')

        return moco_nii, moco_pars

    def _save_report(self, fnames):

        # Save report to derivatives directory
        report_pdf = os.path.join(self._report_dir, '{}_{}_qc.pdf'.format(self._subject, self._session))

        if os.path.isfile(report_pdf):
            os.remove(report_pdf)
        elif os.path.isdir(report_pdf):
            shutil.rmtree(report_pdf)

        print('Saving QC report to {}'.format(report_pdf))
        shutil.copyfile(fnames['ReportPDF'], report_pdf)



