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
import shutil
import numpy as np
import nibabel as nb
import datetime as dt
import pandas as pd

import bids

from .timeseries import temporal_mean_sd, extract_timeseries, detrend_timeseries
from .graphics import (plot_roi_timeseries, plot_roi_powerspec,
                       plot_mopar_timeseries, plot_mopar_powerspec,
                       orthoslices,
                       roi_demeaned_ts)
from .rois import register_template, make_rois
from .metrics import qc_metrics
from .moco import moco_phantom, moco_live
from .report import ReportPDF
from .summary import Summarize


class CBICQC:

    def __init__(self, bids_dir, subject='', session='', mode='phantom', past_months=12):

        # Copy arguments into object
        self._bids_dir = bids_dir
        self._subject = subject
        self._session = session
        self._mode = mode
        self._past_months = past_months

        # Phantom or in vivo suffix ('T2star' or 'bold')
        self._suffix = 'T2star' if 'phantom' in mode else 'bold'

        # Batch subject/session ids
        self._this_subject = ''
        self._this_session = ''

        # BIDS layout
        self._layout = None

        # Create work and report directories
        self._work_dir = tempfile.mkdtemp()
        self._report_dir = os.path.join(self._bids_dir, 'derivatives', 'cbicqc')
        os.makedirs(self._report_dir, exist_ok=True)

        # Intermediate filenames
        self._report_pdf = ''
        self._report_json = ''
        self._tmean_fname = os.path.join(self._work_dir, 'tmean.nii.gz')
        self._tsd_fname = os.path.join(self._work_dir, 'tsd.nii.gz')
        self._roi_labels_fname = os.path.join(self._work_dir, 'roi_labels.nii.gz')
        self._roi_ts_png = os.path.join(self._work_dir, 'roi_timeseries.png')
        self._roi_ps_png = os.path.join(self._work_dir, 'roi_powerspec.png')
        self._mopar_ts_png = os.path.join(self._work_dir, 'mopar_timeseries.png')
        self._mopar_pspec_png = os.path.join(self._work_dir, 'mopar_powerspec.png')
        self._tmean_montage_png = os.path.join(self._work_dir, 'tmean_montage.png')
        self._tsd_montage_png = os.path.join(self._work_dir, 'tsd_montage.png')
        self._rois_montage_png = os.path.join(self._work_dir, 'rois_montage.png')
        self._rois_demeaned_png = os.path.join(self._work_dir, 'rois_demeaned.png')

        # Flags
        self._save_intermediates = False

        # Metrics of interest to summarize
        self._metrics_df = pd.DataFrame()
        self._metrics_of_interest = []

    def run(self):

        print('')
        print('Starting CBIC QC analysis')
        print('')

        # Index BIDS directory
        print('  Indexing BIDS layout')

        bids.config.set_option('extension_initial_dot', True)
        self._layout = bids.BIDSLayout(self._bids_dir,
                                  absolute_paths=True,
                                  ignore=['sourcedata', 'work', 'derivatives', 'exclude'])

        print('    Indexing complete')
        print('')

        # Get complete subject list from BIDS layout
        if self._subject:
            subject_list = [self._subject]
        else:
            subject_list = self._layout.get_subjects()

        # Loop over all QC subjects
        for self._this_subject in subject_list:

            print('  Subject {}'.format(self._this_subject))

            # Get the session list either from class data or BIDS layout (fallback)
            if self._session:
                session_list = [self._session]
            else:
                session_list = self._layout.get_sessions(subject=self._this_subject)

            # Init list of session metrics for this subject
            metric_list = []

            for self._this_session in session_list:

                print('')
                print('    Session {}'.format(self._this_session))

                # Report PDF and JSON filenames - used in both report and summarize modes
                self._report_pdf = os.path.join(self._report_dir,
                                                '{}_{}_qc.pdf'.format(self._this_subject, self._this_session))
                self._report_json = self._report_pdf.replace('.pdf', '.json')

                if os.path.isfile(self._report_pdf) and os.path.isfile(self._report_json):

                    # QC analysis and reporting already run
                    print('      Report and metadata detected for this session')

                else:

                    # QC analysis and report generation
                    self._analyze_and_report()

                # Add metrics for this subject/session to cumulative list
                metric_list.append(self._get_metrics())

            # Convert metric list to dataframe and save to file
            self._metrics_df = pd.DataFrame(metric_list)

            # Generate summary report for this subject
            Summarize(self._report_dir, self._metrics_df, self._past_months)

            # Cleanup temporary QC directory
            self.cleanup()

    def _analyze_and_report(self):

        # Get first QC image for this subject/session
        img_list = self._layout.get(return_type='file',
                                    extension=['nii', 'nii.gz'],
                                    subject=self._this_subject,
                                    session=self._this_session,
                                    suffix=self._suffix)
        if not img_list:
            print('    * No QC images found for subject {} session {} - exiting'.
                  format(self._this_subject, self._this_session))
            sys.exit(1)

        qc_img_fname = img_list[0]
        qc_meta_fname = qc_img_fname.replace('.nii.gz', '.json')

        # Load 4D QC phantom image
        print('      Loading QC timeseries image')
        qc_nii = nb.load(qc_img_fname)

        # Load metadata if available
        print('      Loading QC metadata')
        try:
            with open(qc_meta_fname, 'r') as fd:
                meta = json.load(fd)
        except IOError:
            print('      * Could not open image metadata {}'.format(qc_meta_fname))
            print('      * Using default imaging parameters')
            meta = self.default_metadata()

        # Check for missing fields (typically non-Siemens scanners)
        if 'SequenceName' not in meta:
            meta['SequenceName'] = 'Unknown Sequence'

        if 'ReceiveCoilName' not in meta:
            meta['ReceiveCoilName'] = 'Unknown Coil'

        if 'BandwidthPerPixelPhaseEncode' not in meta:
            meta['BandwidthPerPixelPhaseEncode'] = '-'

        # Integrate additional meta data from Nifti header and filename
        meta['Subject'] = self._this_subject
        meta['Session'] = self._this_session
        meta['VoxelSize'] = ' x '.join(str(x) for x in qc_nii.header.get('pixdim')[1:4])
        meta['MatrixSize'] = ' x '.join(str(x) for x in qc_nii.shape)

        # Perform rigid body motion correction on QC series
        print('      Starting {} motion correction'.format(self._mode))
        t0 = dt.datetime.now()

        qc_moco_nii, qc_moco_pars = self._moco(qc_nii, skip=True)

        t1 = dt.datetime.now()
        print('      Completed motion correction in {} seconds'.format((t1 - t0).seconds))

        # Temporal mean and sd images
        print('      Calculating temporal mean image')
        tmean_nii, tsd_nii, tsfnr_nii = temporal_mean_sd(qc_moco_nii)

        # Register labels to temporal mean via template image
        print('      Register labels to temporal mean image')
        labels_nii = register_template(tmean_nii, self._work_dir, mode=self._mode)

        # Generate ROIs from labels
        # Construct Nyquist Ghost and airspace ROIs from labels
        rois_nii = make_rois(labels_nii)

        # Extract ROI time series
        print('      Extracting ROI time series')
        s_mean_t = extract_timeseries(qc_moco_nii, rois_nii)

        # Detrend time series
        print('      Detrending time series')
        fit_results, s_detrend_t = detrend_timeseries(s_mean_t)

        # Calculate QC metrics
        metrics = qc_metrics(fit_results, tsfnr_nii, rois_nii)

        # Merge meta data into metrics dictionary for report JSON sidecar
        metrics.update(meta)

        # Time vector (seconds)
        t = np.arange(0, s_mean_t.shape[1]) * meta['RepetitionTime']

        print('      Generating Report')

        # Create report images
        plot_roi_timeseries(t, s_mean_t, s_detrend_t, self._roi_ts_png)
        plot_roi_powerspec(t, s_detrend_t, self._roi_ps_png)
        plot_mopar_timeseries(t, qc_moco_pars, self._mopar_ts_png)
        plot_mopar_powerspec(t, qc_moco_pars, self._mopar_pspec_png)
        roi_demeaned_ts(qc_moco_nii, rois_nii, self._rois_demeaned_png)
        orthoslices(tmean_nii, self._tmean_montage_png, cmap='gray', irng='robust')
        orthoslices(tsd_nii, self._tsd_montage_png, cmap='viridis', irng='robust')
        orthoslices(rois_nii, self._rois_montage_png, cmap='tab20', irng='noscale')

        # OPTIONAL: Save intermediate images
        if self._save_intermediates:
            nb.save(tmean_nii, self._tmean_fname)
            nb.save(tsd_nii, self._tsd_fname)
            nb.save(rois_nii, self._roi_labels_fname)

        # Construct filename dictionary to pass to PDF generator
        fnames = dict(WorkDir=self._work_dir,
                      ReportPDF=self._report_pdf,
                      ReportJSON=self._report_json,
                      ROITimeseries=self._roi_ts_png,
                      ROIPowerspec=self._roi_ps_png,
                      MoparTimeseries=self._mopar_ts_png,
                      MoparPowerspec=self._mopar_pspec_png,
                      TMeanMontage=self._tmean_montage_png,
                      TSDMontage=self._tsd_montage_png,
                      ROIsMontage=self._rois_montage_png,
                      ROIDemeanedTS=self._rois_demeaned_png,
                      TMean=self._tmean_fname,
                      TSD=self._tsd_fname,
                      ROILabels=self._roi_labels_fname)

        # Build PDF report
        ReportPDF(fnames, meta, metrics)

    def cleanup(self, skip=False):

        if skip:
            print('')
            print('Retaining {}'.format(self._work_dir))
        else:
            print('')
            print('Deleting work directory')
            shutil.rmtree(self._work_dir)

    def _moco(self, img_nii, skip=False):
        """
        Motion correction wrapper

        :param img_nii: Nifti, image object
        :param skip: bool, skip motion correction
        :return moco_nii: Nifti, motion corrected image object
        :return moco_pars: array, motion parameter timeseries
        """

        if skip:

            moco_nii = img_nii
            moco_pars = np.zeros([img_nii.shape[3], 6])

        else:

            if 'phantom' in self._mode:

                moco_nii, moco_pars = moco_phantom(img_nii)

            elif 'live' in self._mode:

                moco_nii, moco_pars = moco_live(img_nii, self._work_dir)

            else:

                print('      * Unknown QC mode ({})'.format(self._mode))
                sys.exit(1)

        return moco_nii, moco_pars

    def _get_metrics(self):

        with open(self._report_json, 'r') as fd:
            metrics = json.load(fd)

        return metrics

    @staticmethod
    def default_metadata():

        meta = dict(Manufacturer='Unkown',
                    Scanner='Unknown',
                    RepetitionTime=3.0,
                    EchoTime=0.030)

        return meta

    @staticmethod
    def parse_filename(fname):

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

    @staticmethod
    def save_report(src_pdf, dest_pdf):

        if os.path.isfile(dest_pdf):
            os.remove(dest_pdf)
        elif os.path.isdir(dest_pdf):
            shutil.rmtree(dest_pdf)

        print('Saving QC report to {}'.format(dest_pdf))
        shutil.copyfile(src_pdf, dest_pdf)
