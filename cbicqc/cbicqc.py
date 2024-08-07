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
from glob import glob
from pathlib import Path

import bids

from .timeseries import temporal_mean_sd, extract_timeseries, detrend_timeseries
from .graphics import (plot_roi_timeseries, plot_roi_powerspec,
                       plot_mopar_timeseries, plot_mopar_powerspec,
                       orthoslices,
                       roi_demeaned_ts)
from .rois import register_template, make_rois
from .metrics import signal_metrics, moco_metrics
from .moco import moco_phantom, moco_live, moco_postprocess
from .report import ReportPDF
from .summary import Summarize


class CBICQC:

    def __init__(self, bids_dir, subject='', session='', mode='phantom', past_months=12, no_sessions=False):

        # Copy arguments into object
        self._bids_dir = Path(bids_dir)
        self._subject = subject
        self._session = session
        self._mode = mode
        self._past_months = past_months
        self._no_sessions = no_sessions

        # Phantom or in vivo suffix ('T2star' or 'bold')
        self._suffix = 'T2star' if 'phantom' in mode else 'bold'

        # Batch subject/session ids
        self._this_subject = ''
        self._this_session = ''
        self._this_epits_fpath = ''
        self._this_epits_stub = ''

        # BIDS layout
        self._layout = None

        # Create work and report directories
        # Individual subject/session folders created during runtime
        self._work_dir = self._bids_dir / 'work' / 'cbicqc'
        self._report_dir = self._bids_dir / 'derivatives' / 'cbicqc'

        # Declare subject/session specific work and report directories
        self._epits_work_dir = None
        self._epits_report_dir = None

        # Report filenames in derivatives
        self._report_pdf = ''
        self._report_json = ''

        # Working directory intermediate filenames
        self._tmean_fname = 'tmean.nii.gz'
        self._tsd_fname = 'tsd.nii.gz'
        self._tsfnr_fname = 'tsfnr.nii.gz'
        self._roi_labels_fname = 'roi_labels.nii.gz'

        # Working directory report images
        self._roi_ts_png = 'roi_timeseries.png'
        self._roi_ps_png = 'roi_powerspec.png'
        self._mopar_ts_png = 'mopar_timeseries.png'
        self._mopar_pspec_png = 'mopar_powerspec.png'
        self._tmean_montage_png = 'tmean_montage.png'
        self._tsd_montage_png = 'tsd_montage.png'
        self._rois_montage_png = 'rois_montage.png'
        self._rois_demeaned_png = 'rois_demeaned.png'

        # Flags
        self._save_intermediates = True

        # Metrics of interest to summarize
        self._metrics_df = pd.DataFrame()
        self._metrics_of_interest = []

    def run(self):

        print('')
        print('Starting CBIC EPI Timeseries QC analysis')
        print('')

        # Get complete list of EPI time series for this subject
        # Use _bold.nii.gz suffix to identify time series for now
        # TODO: Broaden search for non-BOLD series
        epits_list = self._get_epits_list()

        if len(epits_list) < 1:
            print(f'*** No EPI timeseries found in {self._bids_dir}')

        # Init list of session metrics for this subject
        metric_list = []

        # Loop over all EPI timeseries images
        for epits_fpath in epits_list:

            self._this_epits_fpath = epits_fpath

            # Parse image filename for BIDS keys
            bids_dict = bids.layout.parse_file_entities(epits_fpath)
            self._this_subject = bids_dict['subject']

            if 'session' in bids_dict:
                self._this_session = bids_dict['session']
            else:
                self._this_session = 'None'

            # Extract EPI series prefix (basename without extensions)
            epits_prefix = os.path.basename(epits_fpath).replace('.nii.gz', '').replace('.nii', '')

            # Create work and report folders for this EPI timeseries
            self._epits_work_dir = self._work_dir / epits_prefix
            os.makedirs(self._epits_work_dir, exist_ok=True)
            self._epits_report_dir = self._report_dir / epits_prefix
            os.makedirs(self._epits_report_dir, exist_ok=True)

            print('')
            print('    EPI timeseries {}'.format(epits_prefix))

            # Report PDF and JSON filenames - used in both report and summarize modes
            self._report_pdf = self._epits_report_dir / f'{epits_prefix}_qc.pdf'
            self._report_json = self._epits_report_dir / f'{epits_prefix}_qc.json'

            if os.path.isfile(self._report_pdf) and os.path.isfile(self._report_json):

                # QC analysis and reporting already run
                print('      Report and metadata detected for this session - skipping')

            else:

                # QC analysis and report generation
                self._analyze_and_report()

            # Add metrics for this subject/session to cumulative list
            metric_list.append(self._get_metrics())

        # Convert metric list to dataframe and save to file
        self._metrics_df = pd.DataFrame(metric_list)

        # Generate summary report for phantom QC only
        if 'phantom' in self._mode:

            # Check for deidentified BIDS data
            # dcm2niix with anonymization on by default generates AcquisitionTime but not AcquisitionDateTime
            # Use "bidskit --no-anon" to skip deidentification and generate AcquisitionDataTime in the JSON sidecars
            if 'AcquisitionDateTime' in self._metrics_df:
                Summarize(self._report_dir, self._metrics_df, self._past_months)
            else:
                print('')
                print('* AcquisitionDateTime is missing from the BIDS metadata')
                print('* The most likely cause of this is deidentification of the data by dcm2niix or bidskit')
                print('* A QC trend summary cannot be generated from deidentified data')


        # Cleanup work directory
        self.cleanup(retain=True)

    def _analyze_and_report(self):

        img_fname = self._this_epits_fpath
        json_fname = img_fname.replace('.nii.gz', '.json')

        # Load EPI timeseries image
        print('      Loading EPI timeseries image')
        epits_nii = nb.load(img_fname)

        # Load metadata if available
        print('      Loading QC metadata')
        try:
            with open(json_fname, 'r') as fd:
                meta = json.load(fd)
        except IOError:
            print('      * Could not open image metadata {}'.format(json_fname))
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
        meta['VoxelSize'] = ' x '.join(str(x) for x in epits_nii.header.get('pixdim')[1:4])
        meta['MatrixSize'] = ' x '.join(str(x) for x in epits_nii.shape)

        # Perform rigid body motion correction on EPI timeseries

        # Hardwired moco flag for debugging
        skip_moco = False

        print(f"      Starting {self._mode} motion correction of {epits_nii.shape[3]} volumes")
        t0 = dt.datetime.now()
        epits_moco_nii, epits_moco_df = self._moco(epits_nii, meta, skip=skip_moco)
        t1 = dt.datetime.now()
        print('      Completed motion correction in {} seconds'.format((t1 - t0).seconds))

        # Temporal mean and sd images
        print('      Calculating temporal mean image')
        tmean_nii, tsd_nii, tsfnr_nii = temporal_mean_sd(epits_moco_nii)

        # Register labels to temporal mean via template image
        print('      Register labels to temporal mean image')
        labels_nii = register_template(tmean_nii, self._epits_work_dir, mode=self._mode)

        # Generate ROIs from labels
        # Construct Nyquist Ghost and airspace ROIs from labels
        rois_nii = make_rois(labels_nii)

        # Extract ROI time series
        print('      Extracting ROI time series')
        s_mean_t = extract_timeseries(epits_moco_nii, rois_nii)

        # Detrend time series
        print('      Detrending time series')
        fit_results, s_detrend_t, s_fit_t = detrend_timeseries(s_mean_t)

        # Calculate signal metrics
        metrics = signal_metrics(fit_results, tsfnr_nii, rois_nii)

        # Add motion metrics dictionary
        metrics.update(moco_metrics(epits_moco_df))

        # Add image meta data into metrics dictionary
        metrics.update(meta)

        # Time vector (seconds)
        t = np.arange(0, s_mean_t.shape[1]) * meta['RepetitionTime']

        print('      Generating Report')

        # Create report images
        plot_roi_timeseries(t, s_mean_t, s_detrend_t, s_fit_t, self._epits_work_dir / self._roi_ts_png)
        plot_roi_powerspec(t, s_detrend_t, self._epits_work_dir / self._roi_ps_png)
        plot_mopar_timeseries(epits_moco_df, self._epits_work_dir / self._mopar_ts_png)
        plot_mopar_powerspec(epits_moco_df, self._epits_work_dir / self._mopar_pspec_png)
        roi_demeaned_ts(epits_moco_nii, rois_nii, self._epits_work_dir / self._rois_demeaned_png)
        orthoslices(tmean_nii, self._epits_work_dir / self._tmean_montage_png, cmap='gray', irng='robust')
        orthoslices(tsd_nii, self._epits_work_dir / self._tsd_montage_png, cmap='viridis', irng='robust')
        orthoslices(rois_nii, self._epits_work_dir / self._rois_montage_png, cmap='Pastel1', irng='noscale')

        # OPTIONAL: Save intermediate images
        if self._save_intermediates:
            nb.save(tmean_nii, self._epits_work_dir / self._tmean_fname)
            nb.save(tsd_nii, self._epits_work_dir / self._tsd_fname)
            nb.save(rois_nii, self._epits_work_dir / self._roi_labels_fname)
            nb.save(tsfnr_nii, self._epits_work_dir / self._tsfnr_fname)

        # Construct filename dictionary to pass to PDF generator
        fnames = dict(WorkDir=self._epits_work_dir,
                      ReportPDF=self._report_pdf,
                      ReportJSON=self._report_json,
                      ROITimeseries=self._epits_work_dir / self._roi_ts_png,
                      ROIPowerspec=self._epits_work_dir / self._roi_ps_png,
                      MoparTimeseries=self._epits_work_dir / self._mopar_ts_png,
                      MoparPowerspec=self._epits_work_dir / self._mopar_pspec_png,
                      TMeanMontage=self._epits_work_dir / self._tmean_montage_png,
                      TSDMontage=self._epits_work_dir / self._tsd_montage_png,
                      ROIsMontage=self._epits_work_dir / self._rois_montage_png,
                      ROIDemeanedTS=self._epits_work_dir / self._rois_demeaned_png,
                      TMean=self._epits_work_dir / self._tmean_fname,
                      TSD=self._epits_work_dir / self._tsd_fname,
                      ROILabels=self._epits_work_dir / self._roi_labels_fname)

        # Build PDF report
        ReportPDF(fnames, meta, metrics)

    def cleanup(self, retain=False):

        if retain:
            print('')
            print(f'Retaining {self._work_dir}')
        else:
            print('')
            print(f'Deleting work directory {self._work_dir}')
            shutil.rmtree(self._work_dir)

    def _moco(self, img_nii, meta, skip=False):
        """
        Motion correction wrapper

        :param img_nii: Nifti
            Nifit image object
        :param meta: dict
            BIDS sidecar metadata for BOLD series image
        :param skip: bool
            Skip motion correction flag
        :return moco_nii: Nifti
            Motion corrected image object
        :return moco_df: dataframe
            Motion parameter table
        """

        if skip:

            moco_nii = img_nii
            moco_pars = np.zeros([img_nii.shape[3], 6])

        else:

            if 'phantom' in self._mode:

                moco_nii, moco_pars = moco_phantom(img_nii)

            elif 'live' in self._mode:

                moco_nii, moco_pars = moco_live(img_nii, self._epits_work_dir)

            else:

                print('      * Unknown QC mode ({})'.format(self._mode))
                sys.exit(1)

        # Post-process raw motion parameters
        # - convert numpy array to pandas dataframe with time column
        # - calculate Power FD and LPF FD and add to dataframe (in vivo only)
        moco_df = moco_postprocess(moco_pars, meta, mode=self._mode)

        return moco_nii, moco_df

    def _get_metrics(self):

        with open(self._report_json, 'r') as fd:
            metrics = json.load(fd)

        return metrics

    def _get_subject_list(self):

        tmp_list = glob(os.path.join(self._bids_dir, 'sub-*'))
        return [os.path.basename(d).replace('sub-', '') for d in tmp_list]

    def _get_epits_list(self):

        # Force magnitude-only quality control
        # Check for presence of BOLD phase images. If they're present, add part-mag tag
        # to avoid running CBICQC on phase images (which won't work)
        print('Magnitude image quality control')
        phase_list = glob(os.path.join(self._bids_dir, 'sub-*', 'ses-*', 'func', '*part-phase*_bold.nii*'))
        if len(phase_list) > 0:
            part_tag = 'part-mag*'
        else:
            part_tag = ''

        if self._no_sessions:
            epits_list = glob(os.path.join(self._bids_dir, 'sub-*', 'func', f'*{part_tag}*_bold.nii.gz'))
        else:
            epits_list = glob(os.path.join(self._bids_dir, 'sub-*', 'ses-*', 'func', f'*{part_tag}_bold.nii.gz'))

        return epits_list

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
