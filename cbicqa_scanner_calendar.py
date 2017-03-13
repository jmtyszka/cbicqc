#!/usr/bin/env python
#
# Generate an HTML calendar linking QA studies for a given scanner
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 03/13/2014 JMT Adapt from cbicqa_scanner_trends.py
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
# Copyright 2014 California Institute of Technology.

import sys
import os
import string
import calendar
import re
import numpy as np
from matplotlib.pyplot import *
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Define HTML header boilerplate
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

"""

# Main function
def main():

  # Get scanner name from arguments
  if len(sys.argv) > 1:
    scanner_name = sys.argv[1]
  else:
    print('USAGE : cbicqa_scanner_calendar.py <scanner name>')
    sys.exit(1)

  # Get QA data directory from shell environment
  cbicqa_data_dir = os.environ['CBICQA_DATA']

  # Full scanner QA directory path
  scanner_qa_dir = os.path.join(cbicqa_data_dir, scanner_name)

  # Output calendar web page name
  # NOTE : this is the index page for the scanner QA directory
  qa_scanner_calendar = os.path.join(scanner_qa_dir, 'index.html')

  print('Writing scanner calendar to ' + qa_scanner_calendar)

  # Set first day of week to SUNDAY (US)
  calendar.setfirstweekday(calendar.SUNDAY)

  #
  # HTML report generation
  #

  # Open HTML calendar page for this scanner
  fd = open(qa_scanner_calendar, "w")

  # Write HTML header boilerplate
  fd.write(HTML_HEADER)

  # Write header splash for this scanner
  fd.write('<h1 style="background-color:#E0E0FF">CBIC QA Calendar for %s</h1>' %(scanner_name))

  # Create a table to hold month calendars
  # Two rows of three months, from oldest to most recent

  fd.write('<table><tr>')

  # Note today's datetime
  dt_today = datetime.today()

  # Loop over the past twelve months, including current month
  for dmonth in range(-5, 1, 1):
  
    # Create a new row at month -2
    if dmonth == -2:
      fd.write('</tr><tr>')

    # Get the datetime object for dmonths ago
    dt_past = dt_today + relativedelta( months = dmonth)

    # Start new table element
    fd.write('<td>')
    
    # Write table header for this month
    fd.write('<table>')
    fd.write('<tr><td colspan="7"><center><b>%s %d</b></center></tr>' %(dt_past.strftime("%B"), dt_past.year))
    fd.write('<tr><td>Sun<td>Mon<td>Tue<td>Wed<td>Thu<td>Fri<td>Sat</tr>')

    # Create month calendar array
    past_cal = calendar.monthcalendar(dt_past.year, dt_past.month)
    
    # Number of weeks in this month
    nwk = len(past_cal)

    # Loop over weeks
    for wk in range(0, nwk):
    
      # New table row
      fd.write('<tr align="center">')
    
      # Look over days in week
      for d in range(0,7):
      
        this_d = past_cal[wk][d]
        
        if this_d > 0:
        
          # Create QA date string (YYYYMMDD)
          qa_date_str = '%s%02d%02d' %(dt_past.year, dt_past.month, this_d)
          
          # Create path to local daily QA index page
          qa_dir = os.path.join(scanner_qa_dir, qa_date_str)
          qa_index = os.path.join(qa_dir, 'index.html')
          
          # Check if daily QA index exists for this date
          if os.path.isfile(qa_index):
          
            # Create relative URL to this daily QA
            # No need to prefix with scanner name
            qa_url = os.path.join(qa_date_str, 'index.html')
            fd.write('<td><a href="%s">%d</a>' %(qa_url, this_d))
      
          else:
            
            # Just write plain date without link
            fd.write('<td>%d' %(this_d))
      
    
        else:
        
          fd.write('<td>')

      # Finish row for this week
      fd.write('</tr>')

    # Finish table for this month
    fd.write('</table><p>')

  # Finish table of month calendars
  fd.write('</table>')

#---------------------------------------------

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
