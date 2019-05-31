#!/usr/bin/env python3
"""
CBICQC quality control analysis and reporting class

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
import numpy as np
import nibabel as nb
from cbicqc.timeseries import temporal_mean
from cbicqc.rois import roi_labels
from cbicqc.report import PDFReport


class CBICQC:

    def __init__(self, qc_mcf, work_dir):

        self._qc_mcf = qc_mcf
        self._work_dir = work_dir

    def run(self):

        print('')
        print('Starting QC analysis')

        results = dict()

        # Load 4D motion corrected QC phantom image
        print('  Loading motion corrected QC timeseries image')
        qc_moco = nb.load(self._qc_mcf)

        # Temporal mean and sd images
        print('  Calculating temporal mean image')
        tmean = temporal_mean(qc_moco)

        # Create ROI labels
        print('  Constructing ROI labels')
        rois = roi_labels(tmean)

        # Save all intermediate images
        print('  Saving ROI labels')
        rois_fname = 'roi_labels.nii.gz'
        nb.save(rois, rois_fname)

        # Generate PDF report
        pdf_report = PDFReport(self._work_dir)


        results['ROILabels'] = rois_fname
        results['ReportPDF'] = pdf_report.filename

        return results



