#!/usr/bin/env python
#
# Generate graphical trends report page for a given scanner
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
#          03/12/2014 JMT Switch to trend report page format
#
# This file is part of CBICQA.
#
#    CBICQA is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    CBICQA is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#   along with CBICQA.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2011-2014 California Institute of Technology.

import sys
import os
import string
import numpy as np
from matplotlib.pyplot import *
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Define template
TEMPLATE_FORMAT = """
<html>

<head>
<STYLE TYPE="text/css">
BODY {
  font-family    : sans-serif;
}
td, th {
  padding-left   : 10px;
  padding-right  : 10px;
  padding-top    : 0px;
  padding-bottom : 0px;
  vertical-align : top;
  text-align     : left;
}
</STYLE>
</head>

<body>

<h1 style="background-color:#E0E0FF">CBIC QA Trend Report</h1>

<!-- Plotted timeseries -->
<table>
<tr><td> <h2>$scanner_name QA Metric Trends</h2></tr>
<tr><td> <h4>Report generated on $report_date</h4></tr>
<tr><td> <center> Metric  Median  [ 5th Percentile to 95th Percentile ] </center> </tr>
<tr><td valign="top"><img src=qa_trends.png /></tr>
</table>

"""

# Main function
def main():

    # Get scanner name from arguments
    if len(sys.argv) > 1:
        scanner_name = sys.argv[1]
    else:
        print('USAGE : cbicqa_scanner_trends.py <scanner name>')
        sys.exit(1)

    # Get QA data directory from shell environment
    cbicqa_data_dir = os.environ['CBICQA_DATA']

    # Full scanner QA directory path
    scanner_qa_dir = os.path.join(cbicqa_data_dir, scanner_name)

    # Check that scanner QA directory exists
    if not os.path.isdir(scanner_qa_dir):
        print('QA directory does not exist - skipping')
        sys.exit(1)

    # Day counter
    ndays = 0

    print('Collecting QA metrics')

    # Loop over all daily QA directories
    for direl in os.listdir(scanner_qa_dir):

        # Full path to daily QA directory
        qa_daily_dir = os.path.join(scanner_qa_dir, direl)

        # Daily QA directory
        if os.path.isdir(qa_daily_dir):

            # Load daily QA metrics
            qa_info_file = os.path.join(qa_daily_dir, 'qa_stats.txt')
            x = np.loadtxt(qa_info_file)

            # Parse directory name into ISO format date
            YYYY = int(direl[0:4])
            MM   = int(direl[4:6])
            DD   = int(direl[6:8])
            this_dt    = datetime(YYYY,MM,DD)

            # Append new column to trend and date arrays
            if ndays < 1:
                dt_all = this_dt
                trend = x
                npars = x.size
            else:
                dt_all = np.append(dt_all, this_dt)
                trend = np.append(trend, x)

            ndays = ndays + 1

    trend = trend.reshape(ndays,npars)

    # Create time mask for past 12 months
    dt1 = datetime.today()
    dt0 = dt1 + relativedelta( months = -12 )
    mask = np.where(np.logical_and(dt_all >= dt0, dt_all <= dt1))

    # Crop time and metrics to past 12 months
    dt = dt_all[mask,]
    pDrift = trend[mask,5]
    nySpike = trend[mask,10]
    nSpike = trend[mask,16]
    pSNR = trend[mask,18]
    nySNR = trend[mask,19]

    # Median, 5th and 95th percentiles for each metric over previous 12 months
    pSNR_5, pSNR_50, pSNR_95 = np.percentile(pSNR,(5,50,95))
    nySNR_5, nySNR_50, nySNR_95 = np.percentile(nySNR,(5,50,95))
    pDrift_5, pDrift_50, pDrift_95 = np.percentile(pDrift, (5,50,95))
    nySpike_5, nySpike_50, nySpike_95 = np.percentile(nySpike, (5,50,95))
    nSpike_5, nSpike_50, nSpike_95 = np.percentile(nSpike, (5,50,95))

    # Plot metric graphs for past 12 months
    fig = figure(figsize = (16,16))

    subplot(511)
    plot([dt0, dt1], [pSNR_5, pSNR_5], 'g:')
    plot([dt0, dt1], [pSNR_50, pSNR_50], 'g')
    plot([dt0, dt1], [pSNR_95, pSNR_95], 'g:')
    plot(dt, pSNR, 'or')
    title("Phantom SNR  %0.3f  [ %0.3f to %0.3f ]" % (pSNR_5, pSNR_50, pSNR_95), x = 0.5, y = 0.8)
    ylim(0, 50)

    subplot(512)
    plot([dt0, dt1], [nySNR_5, nySNR_5], 'g:')
    plot([dt0, dt1], [nySNR_50, nySNR_50], 'g')
    plot([dt0, dt1], [nySNR_95, nySNR_95], 'g:')
    plot(dt, nySNR, 'or')
    title("Nyquist SNR  %0.3f  [ %0.3f to %0.3f ]" % (nySNR_5, nySNR_50, nySNR_95), x = 0.5, y = 0.8)
    ylim(0, 3)

    subplot(513)
    plot([dt0, dt1], [nySpike_5, nySpike_5], 'g:')
    plot([dt0, dt1], [nySpike_50, nySpike_50], 'g')
    plot([dt0, dt1], [nySpike_95, nySpike_95], 'g:')
    plot(dt, nySpike, 'or')
    title("Nyquist Spikes  %0.3f  [ %0.3f to %0.3f ]" % (nySpike_5, nySpike_50, nySpike_95), x = 0.5, y = 0.8)
    ylim(0, 25)

    subplot(514)
    plot([dt0, dt1], [nSpike_5, nSpike_5], 'g:')
    plot([dt0, dt1], [nSpike_50, nSpike_50], 'g')
    plot([dt0, dt1], [nSpike_95, nSpike_95], 'g:')
    plot(dt, nSpike, 'or')
    title("Noise Spikes  %0.3f  [ %0.3f to %0.3f ]" % (nSpike_5, nSpike_50, nSpike_95), x = 0.5, y = 0.8)
    ylim(0, 25)

    subplot(515)
    plot([dt0, dt1], [pDrift_5, pDrift_5], 'g:')
    plot([dt0, dt1], [pDrift_50, pDrift_50], 'g')
    plot([dt0, dt1], [pDrift_95, pDrift_95], 'g:')
    plot(dt, pDrift, 'or')
    title("Phantom Drift (%%)  %0.3f  [ %0.3f to %0.3f ]" % (pDrift_5, pDrift_50, pDrift_95), x = 0.5, y = 0.8)
    ylim(-3, 1)

    # Pack all subplots and labels tightly
    fig.subplots_adjust(hspace = 0.2)

    # Save figure in QA data directory
    savefig(os.path.join(scanner_qa_dir, 'qa_trends.png'), dpi = 72, bbox_inches = 'tight')

    #
    # HTML report generation
    #

    # Create substitution dictionary for HTML report
    qa_dict = dict([
        ('report_date',  datetime.today().ctime()),
        ('scanner_name', scanner_name),
    ])

    # Generate HTML report from template (see above)
    TEMPLATE = string.Template(TEMPLATE_FORMAT)
    html_data = TEMPLATE.safe_substitute(qa_dict)

    # Write HTML report page
    qa_trend_report = os.path.join(scanner_qa_dir, 'trends.html')
    print('Writing trends report')
    open(qa_trend_report, "w").write(html_data)


# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
