#!/usr/bin/env python3
"""
Statistical analysis of motion corrected QC timeseries

AUTHORS
----
Mike Tyszka, Ph.D., Caltech Brain Imaging Center

DATES
----
2019-05-29 JMT From scratch

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

from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (BaseInterface,
                                    BaseInterfaceInputSpec,
                                    File,
                                    TraitedSpec)

import datetime as dt
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class QCStatsInputSpec(BaseInterfaceInputSpec):

    mcf = File(exists=True,
               mandatory=True,
               desc='Motion corrected 4D timeseries')


class QCStatsOutputSpec(TraitedSpec):

    report_pdf = File(exists=False, desc="Quality control report")


class QCStats(BaseInterface):

    input_spec = QCStatsInputSpec
    output_spec = QCStatsOutputSpec

    def __init__(self):

        super().__init__()

        # Anything that can be initialized prior to run

    def _run_interface(self, runtime):

        # Derive report filename from moco filename
        _, stub, _ = split_filename(self.inputs.mcf)
        self._stats_json = os.path.abspath(stub.replace('_mcf', '') + '_stats.json')

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs['stats_json'] = self._stats_json

        return outputs