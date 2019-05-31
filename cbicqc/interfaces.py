#!/usr/bin/env python3
"""
Nipype interface classes for CBICQC

AUTHORS
----
Mike Tyszka, Ph.D., Caltech Brain Imaging Center

DATES
----
2019-05-30 JMT From scratch to support CBICQC class

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

from nipype.interfaces.base import (BaseInterface,
                                    BaseInterfaceInputSpec,
                                    File,
                                    TraitedSpec)

from .cbicqc import CBICQC


class CBICQCInterfaceInputSpec(BaseInterfaceInputSpec):

    mcf = File(exists=True,
               mandatory=True,
               desc='Motion corrected 4D timeseries')


class CBICQCInterfaceOutputSpec(TraitedSpec):

    report_pdf = File(exists=False, desc="Quality control report")


class CBICQCInterface(BaseInterface):

    input_spec = CBICQCInterfaceInputSpec
    output_spec = CBICQCInterfaceOutputSpec

    def _run_interface(self, runtime):

        qc = CBICQC(self.inputs.mcf, '/Users/jmt/sandbox/cbicqc')

        qc_results = qc.run()

        self._pdf_fname = qc_results['ReportPDF']

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs['report_pdf'] = self._pdf_fname

        return outputs