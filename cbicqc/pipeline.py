"""
Main quality control analysis class

AUTHOR : Mike Tyszka, Ph.D.
DATES  : 2019-03-28 JMT From scratch
"""

import os
from bids import BIDSLayout

import nipype.pipeline.engine as pe
from nipype.interfaces.io import BIDSDataGrabber, DataSink
from nipype.interfaces import fsl

from .qc import CBICQC

class pipeline:

    def __init__(self, bids_dir):

        self._bids_dir = bids_dir
        self._work_dir = os.path.join(bids_dir, 'work')
        self._derivatives_dir = os.path.join(bids_dir, 'derivatives')

        print('Indexing BIDS directory')
        self._layout = BIDSLayout(root=bids_dir,
                                  validate=False,
                                  ignore=['derivatives', 'sourcedata', 'code', 'work'])
        print('Finished indexing')

        # Save subject and session list
        self._subject_list = self._layout.get_subjects()
        self._session_list = self._layout.get_sessions()

    def run(self):

        qc_workflow = self._workflow()
        qc_workflow.run(plugin='SGEGraph',
                        plugin_args={'dont_resubmit_completed_jobs': True})

        return

    def _workflow(self):

        print('Setting up workflow')

        # Main workflow
        wf = pe.Workflow(name='cbicqc')
        wf.base_dir = self._work_dir

        # Output data sink -> <bids_root>/derivatives/cbicqc
        datasink = pe.Node(interface=DataSink(), name='datasink')
        datasink.inputs.base_directory = self._derivatives_dir
        datasink.inputs.container = 'cbicqc'
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
        cbicqc = pe.MapNode(interface=CBICQC(),
                        name='qc_analysis',
                        iterfield=['in_file'])

        # QC single session report

        # Summary report for all sessions

        #
        # Wire up pipeline
        #

        wf.connect(bids_grab, 'qc_ims', moco, 'in_file')

        wf.connect(moco, 'out_file', tmean, 'in_file')
        wf.connect(moco, 'out_file', cbicqc, 'in_file')

        wf.connect(moco, 'out_file', datasink, 'moco')
        wf.connect(moco, 'mean_img', datasink, 'mean')
        wf.connect(moco, 'std_img', datasink, 'std')
        wf.connect(moco, 'par_file', datasink, 'mocopars')
        wf.connect(moco, 'rms_files', datasink, 'mocorms')
        wf.connect(tmean, 'out_file', datasink, 'tmean')
        wf.connect(cbicqc, 'roi_mask', datasink, 'roi_mask')
        wf.connect(cbicqc, 'roi_timeseries', datasink, 'roi_timeseries')


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


