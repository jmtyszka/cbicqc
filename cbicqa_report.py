#!/opt/local/bin/python
#
# Create daily QA HTML report
#
# USAGE : cbicqa_report.py <QA Directory>
#
# AUTHOR : Mike Tyszka
# PLACE  : Caltech
# DATES  : 09/25/2013 JMT From scratch
#          10/23/2013 JMT Add com external call
#          10/24/2013 JMT Move stats calcs to new cbicqa_stats.py
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
# Copyright 2013-2014 California Institute of Technology.

import sys
import os
import string
import numpy as np
from pylab import *

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

<h1 style="background-color:#E0E0FF">CBIC Daily QA Report</h1>

<table>
<tr>

<!-- Scanner and acquisition info -->
<td>
  <table>
  <tr> <td> <b>Acquisition Date</b> <td bgcolor="#E0FFE0"> <b>$acq_date</b> </tr>
  <tr> <td> <b>Scanner ID</b>       <td> $scanner_serno </tr>
  <tr> <td> <b>Frequency</b>        <td> $scanner_freq MHz </tr>
  <tr> <td> <b>TR</b>               <td> $TR_ms ms </tr>
  <tr> <td> <b>Volumes</b>          <td> $num_volumes </tr>
  </table>
</td>

<!-- SNR and absolute signal info -->
<td>
  <table>
  <tr> <td> <b>SNR Phantom</b>      <td bgcolor="#E0FFE0"> <b>$phantom_snr</b> </tr>
  <tr> <td> <b>SNR Nyquist</b>      <td> $nyquist_snr </tr>
  <tr> <td> <b>Mean Phantom</b>     <td> $phantom_mean
  <tr> <td> <b>Mean Nyquist</b>     <td> $nyquist_mean
  <tr> <td> <b>Mean Noise</b>       <td> $noise_mean
  </table>
</td>

<!-- Spikes and drift -->
<td>
  <table>
  <tr> <td> <b>Phantom Spikes</b>   <td> $phantom_spikes </tr>
  <tr> <td> <b>Nyquist Spikes</b>   <td> $nyquist_spikes </tr>
  <tr> <td> <b>Noise Spikes</b>     <td> $noise_spikes </tr>
  <tr> <td> <b>Phantom Drift</b>   <td> $phantom_drift % </tr>
  <tr> <td> <b>Nyquist Drift</b>   <td> $nyquist_drift % </tr>
  <tr> <td> <b>Noise Drift</b>     <td> $noise_drift % </tr>
  </table>
</td>

<!-- Center of mass and apparent motion -->
<td>
  <table>
  <tr> <td> <b>CofM (mm)</b>        <td> ($com_x, $com_y, $com_z)
  <tr> <td> <b>Max Disp (um)</b>    <td> ($max_adx, $max_ady, $max_adz)
  </table>
</td>

<br><br>

<!-- Plotted timeseries -->
<table>

<tr>
<td> <h3>Signal, Drift and Noise</h3>
<td> <h3>Temporal Summary Images and Masks</h3>
</tr>

<tr>
<td valign="top"><img src=qa_timeseries.png />
<td valign="top">
<b>tMean</b><br> <img src=qa_mean_ortho.png /><br><br>
<b>tSD</b><br> <img src=qa_sd_ortho.png /><br><br>
<b>Region Mask</b><br> <img src=qa_mask_ortho.png /><br><br>
</tr>

</table>

"""

# Main function
def main():
    
    # Get QA daily directory from command line args
    if len(sys.argv) > 1:
        qa_dir = sys.argv[1]
    else:
        qa_dir = os.getcwd()
    
    print('  Creating daily QA report for ' + qa_dir)

    #
    # QA Acquisition Info
    #

    # Load QA acquisition info
    qa_info_file = os.path.join(qa_dir, 'qa_info.txt')
    x = np.loadtxt(qa_info_file)
    
    # Parse QA info
    scanner_serno = x[0]
    acq_date      = "%d" % (x[1])
    scanner_freq  = x[2]
    TR_ms         = x[3]
    num_volumes   = x[4]

    # Convert acquisition date to ISO format
    YYYY = acq_date[0:4]
    MM   = acq_date[4:6]
    DD   = acq_date[6:8]
    acq_date = YYYY + '-' + MM + '-' + DD
 
    #
    # QA statistics
    #

    # Construct stats parameter filename
    qa_stats_parfile = os.path.join(qa_dir, 'qa_stats.txt')
    
    if not os.path.isfile(qa_stats_parfile):
        print(qa_stats_parfile + ' does not exist - exiting')
        sys.exit(1)
        
    # Load stats parameters from qa_stats.pars file in the daily QA directory
    print('  Loading stats parameters from ' + qa_stats_parfile)
    x = np.loadtxt(qa_stats_parfile)

    # Parse parameters (in columns for each ROI)
    phantom_a, phantom_tau, phantom_b, phantom_mean, phantom_spikes, phantom_drift = x[0:6]
    nyquist_a, nyquist_tau, nyquist_b, nyquist_mean, nyquist_spikes, nyquist_drift = x[6:12]
    noise_a, noise_tau, noise_b, noise_mean, noise_spikes, noise_drift             = x[12:18]
    phantom_snr, nyquist_snr  = x[18:20]
    com_x, com_y, com_z       = x[20:23]
    max_adx, max_ady, max_adz = x[23:26]

    #
    # HTML report generation
    #

    # Create substitution dictionary for HTML report
    qa_dict = dict([
      ('scanner_serno',  "%d"    % (scanner_serno)),
      ('acq_date',       "%s"    % (acq_date)),
      ('scanner_freq',   "%0.4f" % (scanner_freq)),
      ('TR_ms',          "%0.1f" % (TR_ms)),
      ('num_volumes',    "%d"    % (num_volumes)),
      ('phantom_mean',   "%0.1f" % (phantom_mean)),
      ('nyquist_mean',   "%0.1f" % (nyquist_mean)),
      ('noise_mean',     "%0.1f" % (noise_mean)),
      ('phantom_snr',    "%0.1f" % (phantom_snr)),
      ('nyquist_snr',    "%0.1f" % (nyquist_snr)),
      ('phantom_spikes', "%d"    % (phantom_spikes)),
      ('nyquist_spikes', "%d"    % (nyquist_spikes)),
      ('noise_spikes',   "%d"    % (noise_spikes)),
      ('phantom_drift',  "%0.1f" % (phantom_drift)),
      ('nyquist_drift',  "%0.1f" % (nyquist_drift)),
      ('noise_drift',    "%0.1f" % (noise_drift)),
      ('com_x',          "%0.2f" % (com_x)),
      ('com_y',          "%0.2f" % (com_y)),
      ('com_z',          "%0.2f" % (com_y)),
      ('max_adx',        "%0.1f" % (max_adx)),
      ('max_ady',        "%0.1f" % (max_ady)),
      ('max_adz',        "%0.1f" % (max_adz))
    ])

    # Generate HTML report from template (see above)
    TEMPLATE = string.Template(TEMPLATE_FORMAT)
    html_data = TEMPLATE.safe_substitute(qa_dict)
    
    # Write HTML report page
    qa_report_file = os.path.join(qa_dir, 'index.html')
    open(qa_report_file, "w").write(html_data)

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
