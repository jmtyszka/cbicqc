#!/usr/bin/env python3
"""
Create HTML report from QC analysis results

AUTHORS
----
Mike Tyszka, Ph.D., Caltech Brain Imaging Center

DATES
----
2013-09-25 JMT From scratch
2013-10-23 JMT Add com external call
2013-10-24 JMT Move stats calcs to new stats.py
2019-05-28 JMT Recode as a nipype interface class

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

import sys
import os
import string
import numpy as np

from pylab import *

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (BaseInterface,
                                    BaseInterfaceInputSpec,
                                    File,
                                    TraitedSpec)


class ReportInputSpec(BaseInterfaceInputSpec):

    mcf = File(exists=True,
               mandatory=True,
               desc='Motion corrected 4D timeseries')


class ReportOutputSpec(TraitedSpec):

    report_pdf = File(exists=False, desc="Quality control report")


class Report(BaseInterface):

    input_spec = ReportInputSpec
    output_spec = ReportOutputSpec

    def _run_interface(self, runtime):

        pdf_fname = self._report_fname()

        doc = SimpleDocTemplate(pdf_fname,
                                pagesize=letter,
                                rightMargin=72,
                                leftMargin=72,
                                topMargin=72,
                                bottomMargin=18)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        Story = []

        ptext = '<font size=24>CBIC Quality Control Report</font>'
        Story.append(Paragraph(ptext, styles['Justify']))
        Story.append(Spacer(1, 12))

        doc.build(Story)

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs['report_pdf'] = self._report_fname()

        return outputs

    def _report_fname(self):

        # Derive report filename from moco filename
        _, stub, _ = split_filename(self.inputs.mcf)
        return os.path.abspath(stub.replace('_mcf','') + '_report.pdf')