"""
Quality control workflow class

- Defines nipype workflow with iteration over subjects and sessions

Authors
----
Mike Tyszka, Caltech Brain Imaging Center

Dates
----
2019-03-28 JMT From scratch
2019-05-30 JMT Move QC workflow to separate class and interface

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

from bids import BIDSLayout

import nipype.pipeline.engine as pe
from nipype.interfaces.io import DataSink, BIDSDataGrabber
from nipype.interfaces import fsl, IdentityInterface

from .interfaces import CBICQCInterface


class CBICQCWorkflow:

    def __init__(self, bids_dir):

        self._bids_dir = bids_dir
        self._work_dir = os.path.join(bids_dir, 'work')
        self._derivatives_dir = os.path.join(bids_dir, 'derivatives')

        # Index BIDS directory
        self._layout = BIDSLayout(self._bids_dir,
                                  absolute_paths=True,
                                  ignore=['work', 'derivatives', 'exclude'])

        # Extract lists from BIDS layout
        subject_list = self._layout.get_subjects()
        session_list = self._layout.get_sessions()
        qcs = self._layout.get(suffix='T2star',
                               extensions=['nii', 'nii.gz'],
                               return_type='file')

        # Main workflow
        self._wf = pe.Workflow(name='cbicqc')
        self._wf.base_dir = self._work_dir

        # See https://miykael.github.io/nipype_tutorial/notebooks/basic_data_input_bids.html
        # for approach to loading BIDS image and metadata

        # Setup driving iterator node
        # driver = pe.Node(interface=IdentityInterface(fields=['qc_T2star']),
        #                  name='driver')
        # driver.iterables = [('qc_T2star', qc_list)]

        # BIDS data grabber
        driver = pe.Node(interface=BIDSDataGrabber(infields=['subject', 'session']),
                         name='driver')
        driver.inputs.base_dir = self._bids_dir
        driver.inputs.output_query = {
            'qcs': dict(suffix='T2star',
                        extensions=['nii', 'nii.gz'])}
        driver.iterables = [('subject', subject_list),
                            ('session', session_list)]

        # Motion correction - FSL MCFLIRT
        # TODO: register to mean image
        moco = pe.MapNode(interface=fsl.MCFLIRT(),
                          name='moco',
                          iterfield=['in_file'])
        moco.inputs.cost = 'corratio'
        moco.inputs.mean_vol = True
        moco.inputs.save_plots = True

        # Quality analysis
        qc = pe.MapNode(interface=CBICQCInterface(),
                        name='qc',
                        iterfield=['mcf'])

        # Save QC analysis results in <bids_root>/derivatives/cbicqc
        datasink = pe.Node(interface=DataSink(), name='datasink')
        datasink.inputs.base_directory = self._derivatives_dir
        datasink.inputs.container = 'cbicqc'
        datasink.inputs.parameterization = False

        # Connect up workflow
        self._wf.connect([
            (driver, moco, [('qcs', 'in_file')]),
            (moco, qc, [('out_file', 'mcf'),
                        ('mopars', 'mopars')]),
            (qc, datasink, [('report_pdf', 'reports.@report')]),
            ])

    def run(self, sge=False):

        if sge:
            print('Submitting entire workflow to grid engine')
            print('')
            self._wf.run(plugin='SGEGraph', plugin_args={'dont_resubmit_completed_jobs': True})
        else:
            print('Running workflow sequentially')
            print('')
            self._wf.run()


