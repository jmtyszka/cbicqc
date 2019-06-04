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
2019-05-29 JMT Expand to multiple pages

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
import io
import datetime as dt

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (SimpleDocTemplate,
                                Paragraph,
                                Spacer,
                                Image,
                                Table,
                                TableStyle,
                                PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class ReportPDF:

    def __init__(self, fnames):

        # Output filename
        self._fnames = fnames

        # Contents - list of flowables to be built into a document
        self._contents = []

        # Add a justified paragraph style
        self._pstyles = getSampleStyleSheet()
        self._pstyles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        self._init_pdf()
        self._add_summary()
        self._add_graphs()
        self._add_slices()

        self._doc.build(self._contents)

    def _init_pdf(self):

        # Create a new PDF document
        self._doc = SimpleDocTemplate(self._fnames['ReportPDF'],
                                      pagesize=letter,
                                      rightMargin=0.5 * inch,
                                      leftMargin=0.5 * inch,
                                      topMargin=0.5 * inch,
                                      bottomMargin=0.5 * inch)

    def _add_summary(self):

        ptext = '<font size=24>CBIC Quality Control Report</font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.5 * inch))

        timestamp = dt.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')
        ptext = '<font size=12>Generated automatically by CBICQC on {}</font>'.format(timestamp)
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.5 * inch))

        #
        # Session information
        #

        ptext = '<font size=14><b>Session Information</b></font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.1 * inch))

        info = [['Subject', 'QC'],
                ['Session', '20180531'],
                ['Scan Time', '10:23'],
                ['TR (ms)', '1000.0'],
                ['TE (ms)', '30.0'],
                ['Volumes', '300'],
                ['Voxel Size (mm)', '3.0 x 3.0 x 3.0']]

        info_table = Table(info)

        self._contents.append(info_table)
        self._contents.append(Spacer(1, 0.25 * inch))

        #
        # QC metrics
        #

        ptext = '<font size=14><b>Quality Metrics</b></font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.1 * inch))

        qc_metrics = [['Phantom Temporal SNR', '100.0'],
                      ['Nyquist Temporal SNR', '20.0']]

        qc_table = Table(qc_metrics)

        self._contents.append(qc_table)
        self._contents.append(Spacer(1, 0.25 * inch))

    def _add_graphs(self):

        # Page break
        self._contents.append(PageBreak())

        #
        # ROI Spatial Mean Timeseries
        #

        ptext = '<font size=14><b>ROI Spatial Mean Timeseries</b></font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.25 * inch))

        ptext = """
        <font size=11>
        These three graphs show the spatial mean signal intensity within the phantom, Nyquist ghost and air
        space regions of interest (ROIs). The blue line is the raw spatial mean intensity and the orange line
        has been detrended with an exponential + linear model. 
        </font>
        """
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.1 * inch))

        roi_ts_img = Image(self._fnames['ROITimeseries'], 7.0 * inch, 3.5 * inch, hAlign='LEFT')
        self._contents.append(roi_ts_img)

        self._contents.append(Spacer(1, 0.5 * inch))

        #
        # Motion Parameter Timeseries
        #

        ptext = '<font size=14><b>Motion Parameter Timeseries</b></font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.25 * inch))

        ptext = """
        <font size=11>
        These three graphs show the evolution over time of displacement and rotation parameters required
        to register the phantom image at a given time to the mean phantom image over the entire series. 
        </font>
        """
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.1 * inch))

        roi_ts_img = Image(self._fnames['ROITimeseries'], 7.0 * inch, 3.5 * inch, hAlign='LEFT')
        self._contents.append(roi_ts_img)

    def _add_slices(self):

        # Page break
        self._contents.append(PageBreak())

        #
        # Temporal Mean Image
        #

        ptext = '<font size=14><b>Temporal Mean Image</b></font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.25 * inch))

        ptext = """
        <font size=11>
        Axial, coronal and sagittal sections through the temporal mean image
        following motion correction. 
        </font>
        """
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.1 * inch))

        tmean_montage_img = Image(self._fnames['TMeanMontage'], 7.0 * inch, 2.4 * inch, hAlign='LEFT')
        self._contents.append(tmean_montage_img)

        self._contents.append(Spacer(1, 0.5 * inch))

        #
        # Temporal SD Image
        #

        ptext = '<font size=14><b>Temporal SD Image</b></font>'
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.25 * inch))

        ptext = """
        <font size=11>
        Axial, coronal and sagittal sections through the temporal standard deviation image
        following motion correction. 
        </font>
        """
        self._contents.append(Paragraph(ptext, self._pstyles['Justify']))
        self._contents.append(Spacer(1, 0.1 * inch))

        tsd_montage_img = Image(self._fnames['TSDMontage'], 7.0 * inch, 2.4 * inch, hAlign='LEFT')
        self._contents.append(tsd_montage_img)


