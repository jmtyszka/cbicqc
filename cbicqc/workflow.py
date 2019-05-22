"""
Main quality control analysis class

AUTHOR : Mike Tyszka, Ph.D.
DATES  : 2019-03-28 JMT From scratch
"""

import os
from bids import BIDSLayout

import nipype.pipeline.engine as pe
from nipype.interfaces.io import DataGrabber, DataSink
from nipype.interfaces import fsl

from .qc import CBICQC


class QCPipeline:

    def __init__(self, bids_dir):

        self._bids_dir = bids_dir
        self._work_dir = os.path.join(bids_dir, 'work')
        self._derivatives_dir = os.path.join(bids_dir, 'derivatives')

    def setup_workflow(self):

        # Main workflow
        wf = pe.Workflow(name='cbicqc')
        wf.base_dir = self._work_dir

        # Grab all T2star datasets from BIDS QC directory
        qc_grab = pe.Node(interface=DataGrabber(outfields=['out_files']), name="qc_grab")
        qc_grab.inputs.sort_filelist = False
        qc_grab.inputs.base_directory = self._bids_dir
        qc_grab.inputs.template = 'sub-*/ses-*/anat/*T2star.nii.gz'

        # Save QC analysis results in <bids_root>/derivatives/cbicqc
        qc_results = pe.Node(interface=DataSink(), name='qc_results')
        qc_results.inputs.base_directory = self._derivatives_dir
        qc_results.inputs.container = 'cbicqc'
        qc_results.inputs.parameterization = False
        qc_results.inputs.substitutions = [("_subject_id_", ""), ("_session_id_", "")]

        # Motion correction
        moco = pe.MapNode(interface=fsl.MCFLIRT(save_mats=True,
                                                save_plots=True),
                          name='moco',
                          iterfield=['in_file'])

        # Temporal mean image following moco
        tmean = pe.MapNode(interface=fsl.MeanImage(),
                           name='tmean',
                           iterfield=['in_file'])
        tmean.dimension = 'T'

        # QC single session analysis
        cbicqc = pe.MapNode(interface=CBICQC(),
                            name='qc_analysis',
                            iterfield=['in_file'])

        wf.connect([
            (qc_grab, moco, [('out_files', 'in_file')]),
            (moco, tmean, [('out_file', 'in_file')]),
            (moco, cbicqc, [('out_file', 'in_file')]),
            (moco, qc_results, [('out_file', 'moco'),
                              ('mean_img', 'mean'),
                              ('std_img', 'std'),
                              ('par_file', 'mocopars'),
                              ('rms_files', 'mocorms')]),
            (tmean, qc_results, [('out_file', 'tmean')]),
            (cbicqc, qc_results, [('roi_mask', 'roi_mask'),
                                ('roi_timeseries', 'roi_timeseries')])
            ])

        return wf

    def _session_workflow(self):


        # Single QC session workflow
        session_wf = pe.Workflow(name='qc')
        session_wf.base_dir = self._work_dir

        # Output data sink -> <bids_root>/derivatives/qc
        datasink = pe.Node(interface=DataSink(), name='datasink')
        datasink.inputs.base_directory = self._derivatives_dir
        datasink.inputs.container = 'qc'
        datasink.inputs.parameterization = False
        datasink.inputs.substitutions = [("_subject_id_", ""), ("_session_id_", "")]

        # BIDS data importer
        # T2star EPI nii.gz images only from QC sessions
        bids_grab = pe.Node(interface=BIDSDataGrabber(), name="bids_grab")
        bids_grab.inputs.base_dir = self._bids_dir
        bids_grab.iterables = [('subject', self._subject_list), ('session', self._session_list)]
        bids_grab.inputs.output_query = {'qc_ims': {'suffix':'T2star', 'extensions': '.nii.gz'}}

        #
        # Single session workflow
        #

        # Motion correction
        moco = pe.MapNode(interface=fsl.MCFLIRT(save_mats=True,
                                                save_plots=True),
                          name='moco',
                          iterfield=['in_file'])

        # Temporal mean image following moco
        tmean = pe.MapNode(interface=fsl.MeanImage(),
                           name='tmean',
                           iterfield=['in_file'])
        tmean.dimension = 'T'

        # QC single session analysis

        # QC single session report

        # Summary report for all sessions

        #
        # Wire up pipeline
        #

        session_wf.connect(moco, 'out_file', datasink, 'moco')
        session_wf.connect(moco, 'mean_img', datasink, 'mean')
        session_wf.connect(moco, 'std_img', datasink, 'std')
        session_wf.connect(moco, 'par_file', datasink, 'mocopars')
        session_wf.connect(moco, 'rms_files', datasink, 'mocorms')
        session_wf.connect(moco, 'out_file', tmean, 'in_file')
        session_wf.connect(tmean, 'out_file', datasink, 'tmean')

        return session_wf


