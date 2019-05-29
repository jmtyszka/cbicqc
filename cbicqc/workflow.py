"""
Quality control workflow class

- Defines nipype workflow with iteration over subjects and sessions

Authors
----
Mike Tyszka, Caltech Brain Imaging Center

Dates
----
2019-03-28 JMT From scratch

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
from nipype.interfaces.io import BIDSDataGrabber, DataSink
from nipype.interfaces import fsl

from .roi_labels import ROILabels
from .report import Report


class QCPipeline:

    def __init__(self, bids_dir):

        self._bids_dir = bids_dir
        self._work_dir = os.path.join(bids_dir, 'work')
        self._derivatives_dir = os.path.join(bids_dir, 'derivatives')

    def setup_workflow(self):

        # Main workflow
        wf = pe.Workflow(name='cbicqc')
        wf.base_dir = self._work_dir

        # BIDS layout search
        bids_layout = BIDSLayout(self._bids_dir,
                                 absolute_paths=True,
                                 ignore=['work', 'derivatives', 'exclude'])
        subject_list = bids_layout.get_subjects()
        session_list = bids_layout.get_sessions()

        # See https://miykael.github.io/nipype_tutorial/notebooks/basic_data_input_bids.html
        # for approach to loading BIDS image and metadata

        # BIDS QC grabber - iterates over provided subject and session lists
        imgsrc = pe.Node(interface=BIDSDataGrabber(infields=['subject', 'session']),
                          name='imgsrc')
        imgsrc.inputs.base_dir = self._bids_dir
        imgsrc.inputs.index_derivatives = False
        imgsrc.raise_on_empty = True
        imgsrc.iterables = [('subject', subject_list),
                             ('session', session_list)]
        imgsrc.inputs.output_query = {
            'qc': {'datatype': 'anat',
                   'suffix': 'T2star',
                   'extensions': ['nii', 'nii.gz']}
        }

        # Motion correction
        moco = pe.MapNode(interface=fsl.MCFLIRT(),
                          name='moco',
                          iterfield=['in_file'])
        moco.inputs.cost = 'corratio'
        moco.inputs.save_mats = True
        moco.inputs.save_plots = True

        # Generate HTML report from all analysis results
        report = pe.MapNode(interface=Report(),
                            name='report',
                            iterfield=['mcf'])

        # Save QC analysis results in <bids_root>/derivatives/cbicqc
        datasink = pe.Node(interface=DataSink(), name='datasink')
        datasink.inputs.base_directory = self._derivatives_dir
        datasink.inputs.container = 'cbicqc'
        datasink.inputs.parameterization = False

        # Connect up workflow
        wf.connect([
            (imgsrc, moco, [('qc', 'in_file')]),
            (moco, report, [('out_file', 'mcf')]),
            (report, datasink, [('report_pdf', 'reports.@report')])
            ])

        return wf


