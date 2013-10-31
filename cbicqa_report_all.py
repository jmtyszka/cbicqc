#!/opt/local/bin/python
#
# Generate HTML report from analysis results in a QA directory
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
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
# Copyright 2011-2013 California Institute of Technology.

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
td {
  padding-left   : 10px;
  padding-right  : 10px;
  padding-top    : 0px;
  padding-bottom : 0px;
  vertical-align : top;
}
</STYLE>
</head>

<body>

<h1 style="background-color:#E0E0FF">CBIC QA Trend Report</h1>
<h2>Report generated on $report_date</h2>

<!-- Plotted timeseries -->
<table>
<tr><td> <h3>QA Metric Trends</h3></tr>
<tr><td valign="top"><img src=qa_trends.png /></tr>
</table>

"""

# Main function
def main():
  
  # Get QA data directory from shell environment
  qa_data_dir = os.environ['CBICQA_DATA']
  
  # Day counter
  ndays = 0
  
  print('Collecting QA metrics')
  
  # Loop over all daily QA directories
  for direl in os.listdir(qa_data_dir):
  
    # Full path to daily QA directory
    qa_daily_dir = os.path.join(qa_data_dir, direl)
    
    # Daily QA directory
    if os.path.isdir(qa_daily_dir):
    
      print(qa_daily_dir)
  
      # Load daily QA metrics
      qa_info_file = os.path.join(qa_daily_dir, 'qa_stats.txt')
      x = np.loadtxt(qa_info_file)

      # Parse directory name into ISO format date
      YYYY = int(direl[0:4])
      MM   = int(direl[4:6])
      DD   = int(direl[6:8])
      dt = datetime(YYYY,MM,DD)

      # Append new column to trend and date arrays
      if ndays < 1:
        dt_all = dt
        trend = x
        npars = x.size
      else:
        dt_all = np.append(dt_all, dt)
        trend = np.append(trend, x)

      ndays = ndays + 1

  trend = trend.reshape(ndays,npars)
  
  # Extract most import metrics
  phantom_drift_all  = trend[:,5]
  nyquist_spikes_all = trend[:,10]
  noise_spikes_all   = trend[:,16]
  phantom_snr_all    = trend[:,18]
  nyquist_snr_all    = trend[:,19]
  
  #
  # Trends for previous 3 months
  #
  
  dt_today = datetime.today()
  dt_3months_ago = dt_today + relativedelta( months = -3)
  dt_6months_ago = dt_today + relativedelta( months = -6)
  
  # Plot trend graphs for most important metrics
  fig = figure(figsize = (16,16))

  subplot(511)
  plot(dt_all, phantom_snr_all, 'or')
  title("Phantom SNR", x = 0.5, y = 0.8)
  xlim(dt_6months_ago, dt_today)
  ylim(0, 50)
    
  subplot(512)
  plot(dt_all, nyquist_snr_all, 'or')
  title("Nyquist SNR", x = 0.5, y = 0.8)
  xlim(dt_6months_ago, dt_today)
  ylim(0, 3)
  
  subplot(513)
  plot(dt_all, nyquist_spikes_all, 'or')
  title("Nyquist Spikes", x = 0.5, y = 0.8)
  xlim(dt_6months_ago, dt_today)
  ylim(0, 10)
  
  subplot(514)
  plot(dt_all, noise_spikes_all, 'or')
  title("Noise Spikes", x = 0.5, y = 0.8)
  xlim(dt_6months_ago, dt_today)
  ylim(0, 10)

  subplot(515)
  plot(dt_all, phantom_drift_all, 'or')
  title("Phantom Drift (%)", x = 0.5, y = 0.8)
  xlim(dt_6months_ago, dt_today)
  ylim(-3, 1)

  # Pack all subplots and labels tightly
  fig.subplots_adjust(hspace = 0.2)

  # Save figure in QA data directory
  savefig(os.path.join(qa_data_dir, 'qa_trends.png'), dpi = 72, bbox_inches = 'tight')

  #
  # HTML report generation
  #

  # Create substitution dictionary for HTML report
  qa_dict = dict([
    ('report_date',  datetime.today().isoformat()),
   ])

  # Generate HTML report from template (see above)
  TEMPLATE = string.Template(TEMPLATE_FORMAT)
  html_data = TEMPLATE.safe_substitute(qa_dict)
    
  # Write HTML report page
  qa_trend_report = os.path.join(qa_data_dir, 'index.html')
  print('Writing trend report to ' + qa_trend_report)
  open(qa_trend_report, "w").write(html_data)

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
