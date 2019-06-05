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
import json
import tempfile
import numpy as np
import nibabel as nb

from .timeseries import temporal_mean_sd, extract_timeseries, detrend_timeseries
from .graphics import (plot_roi_timeseries,
                       plot_mopar_timeseries,
                       orthoslice_montage)
from .rois import roi_labels
from .report import ReportPDF


class CBICQC:

    def __init__(self, mcf_fname, mopars_fname, report_fname=None):

        self._mcf_fname = mcf_fname
        self._subject, self._session = self._parse_filename(mcf_fname)
        self._meta_fname = mcf_fname.replace('_mcf.nii.gz', '.json')
        self._mopars_fname = mopars_fname

        # Derive moco pars filename from mcf image filename
        self._qc_mopars_fname = mcf_fname.replace('.nii.gz', '.par')

        self._work_dir = tempfile.mkdtemp()

        if report_fname:
            self._report_fname = report_fname
        else:
            self._report_fname = os.path.join(self._work_dir, 'report.pdf')

        # Intermediate filenames
        self._tmean_fname = os.path.join(self._work_dir, 'tmean.nii.gz')
        self._tsd_fname = os.path.join(self._work_dir, 'tsd.nii.gz')
        self._roi_labels_fname = os.path.join(self._work_dir, 'roi_labels.nii.gz')

        # Flags
        self._save_intermediates = False

    def run(self):

        print('Starting QC analysis')

        # Load 4D motion corrected QC phantom image
        print('  Loading motion corrected QC timeseries image')
        mcf_nii = nb.load(self._mcf_fname)

        # Load JSON sidecar if available
        print('  Loading QC metadata')
        try:
            with open(self._meta_fname, 'r') as fd:
                meta = json.load(fd)
        except IOError:
            print('* Could not open image metadata {}'.format(self._meta_fname))
            print('* Using default imaging parameters')
            meta = self._default_metadata()

        # Integrate addition meta data from Nifti header and filename
        meta['Subject'] = self._subject
        meta['Session'] = self._session
        meta['VoxelSize'] = ' x '.join(str(x) for x in mcf_nii.header.get('pixdim')[1:4])
        meta['MatrixSize'] = ' x '.join(str(x) for x in mcf_nii.shape)

        print('  Loading motion parameter timeseries')
        mopars = np.genfromtxt(self._mopars_fname)

        # Temporal mean and sd images
        print('  Calculating temporal mean image')
        tmean_nii, tsd_nii = temporal_mean_sd(mcf_nii)

        # Create ROI labels
        print('  Constructing ROI labels')
        rois_nii = roi_labels(tmean_nii)

        # Extract ROI time series
        print('  Extracting ROI time series')
        s_mean_t = extract_timeseries(mcf_nii, rois_nii)

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
        plot_mopar_timeseries(mopars, mopar_ts_fname)

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

