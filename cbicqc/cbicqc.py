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
import tempfile
import numpy as np
import nibabel as nb

from .timeseries import temporal_mean_sd, extract_timeseries, detrend_timeseries
from .graphics import plot_roi_timeseries, orthoslice_montage
from .rois import roi_labels
from .report import ReportPDF


class CBICQC:

    def __init__(self, qc_mcf):

        self._qc_mcf = qc_mcf

        # Derive moco pars filename from mcf image filename
        self._qc_mopars_fname = qc_mcf.replace('.nii.gz', '.par')

        self._work_dir = tempfile.mkdtemp()
        self._report_fname = os.path.join(self._work_dir, 'report.pdf')

        print('Report PDF : {}'.format(self._report_fname))

    def run(self):

        print('Starting QC analysis')

        # Load 4D motion corrected QC phantom image
        print('  Loading motion corrected QC timeseries image')
        qc_moco_nii = nb.load(self._qc_mcf)

        print('  Loading motion parameter timeseries')
        qc_mopars = np.genfromtxt(self._qc_mopars_fname)

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

        # Plot ROI time series graphs
        roi_ts_fname = os.path.join(self._work_dir, 'roi_timeseries.png')
        plot_roi_timeseries(s_mean_t, s_detrend_t, roi_ts_fname)

        # Create mean image orthoslices
        tmean_montage_fname = os.path.join(self._work_dir, 'tmean_montage.png')
        orthoslice_montage(tmean_nii, tmean_montage_fname)

        # Create sd image orthoslices
        tsd_montage_fname = os.path.join(self._work_dir, 'tsd_montage.png')
        orthoslice_montage(tsd_nii, tsd_montage_fname)

        # Save all intermediate images
        print('  Saving temporal mean image')
        tmean_fname = os.path.join(self._work_dir, 'tmean.nii.gz')
        nb.save(tmean_nii, tmean_fname)

        print('  Saving temporal sd image')
        tsd_fname = os.path.join(self._work_dir, 'tsd.nii.gz')
        nb.save(tsd_nii, tsd_fname)

        print('  Saving ROI labels')
        roi_labels_fname = os.path.join(self._work_dir, 'roi_labels.nii.gz')
        nb.save(rois_nii, roi_labels_fname)

        # Construct filename dictionary to pass to PDF generator
        fnames = dict(TempDir=self._work_dir,
                      ReportPDF=self._report_fname,
                      ROITimeseries=roi_ts_fname,
                      TMeanMontage=tmean_montage_fname,
                      TSDMontage=tsd_montage_fname,
                      TMean=tmean_fname,
                      TSD=tsd_fname,
                      ROILabels = roi_labels_fname)

        # Generate and save PDF report
        ReportPDF(fnames)

        return fnames
