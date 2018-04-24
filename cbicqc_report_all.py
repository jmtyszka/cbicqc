#!/usr/bin/env python
#
# Generate top level HTML report page for all scanners
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 2014-03-11 JMT Adapt from cbicqc_report_scanner.py
#
# This file is part of CBICQC.
#
#    CBICQC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    CBICQC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#   along with CBICQC.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2014 California Institute of Technology.

import sys
import os
import string
import numpy as np
from matplotlib.pyplot import *
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Define HTML boilerplate sections
HTML_HEADER = """
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
<h1 style="background-color:#E0E0FF">CBIC QC Home Page</h1>
"""

HTML_FOOTER = """
</body>
</html>
"""

# Main function
def main():

  # Get root QC data directory from shell environment
  cbicqc_data_dir = os.environ['CBICQC_DATA']

  print('----------------')
  print('Creating top level page for all scanners')

  # Home page filename
  qc_home_page = os.path.join(cbicqc_data_dir, 'index.html')
  print('Writing home page to ' + qc_home_page)

  # Open home page to write
  fd = open(qc_home_page, "w")
  
  # Write HTML header
  fd.write(HTML_HEADER)
  
  # Start table
  fd.write('<table><tr><td>Scanner Name<td>QC Calendar<td>QC Trends</tr>')
  
  # Loop over all scanner QC directories within the CBICQC data directory
  for scanner_name in os.listdir(cbicqc_data_dir):
  
    # Full path to scanner QC directory
    scanner_qc_dir = os.path.join(cbicqc_data_dir, scanner_name)
    
    # Daily QC directory
    if os.path.isdir(scanner_qc_dir):
    
      # Report URLs
      qc_cal_url = os.path.join(scanner_name,'index.html')
      qc_trends_url = os.path.join(scanner_name,'trends.html')
    
      # Write table row for this scanner
      fd.write('<tr>')
      fd.write('<td>%s' %(scanner_name))
      fd.write('<td><a href="%s">Calendar</a>' %(qc_cal_url))
      fd.write('<td><a href="%s">Trends</a>' %(qc_trends_url))
      fd.write('</tr>')

  # Finish off page with footer
  fd.write(HTML_FOOTER)


# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
