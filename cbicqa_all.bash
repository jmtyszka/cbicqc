#!/bin/bash
#
# Master QA analysis script
#
# USAGE: cbicqa_all.bash <Overwrite [Y|N]>
#
# Query and retrieve new QA studies for all scanners from the local OsiriX database
# Use dcmtk command line functions to generate list of new QA data and 
# copy DICOM files into QA directory tree ready for analysis.
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#          10/16/2012 JMT Add local OsiriX Q&R to get QA study data
#          10/19/2012 JMT Add optional overwrite argument
#          02/19/2014 JMT Generalize to multiple scanners
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

# QA data/website directory
if [ -z "${CBICQA_DATA}" ]; then
  echo "Please define CBICQA_DATA undefined - exiting"
  exit
fi

if [ $# -lt 1 ]; then
  overwrite="N"
else
  overwrite=$1
fi

echo "CBIC QA Analysis"
echo "----------------"
echo "QA Data Directory : ${CBICQA_DATA}"

# Call cbicqa_scanner.bash for each scanner

# Siemens TIM32
cbicqa_scanner.bash TIM_32 "-k 0008,1000=35077 -k 0010,0010=Qa -k 0010,0020=qa" ${overwrite}

# Siemens TIM12
# cbicqa_scanner.bash TIM_12 "-k 0008,1000=35408 -k 0010,0010=Qa -k 0010,0020=qa" ${overwrite}

# 4.7T Bruker
#cbicqa_scanner.bash BRK_47 "-k 0008,0070=Bruker -k 0010,0010=QA" ${overwrite}

# Create home page for QA reports linking each scanner's report
# Final report HTML file is in $qa_data/qa_report.html

cbicqa_report_all.py ${CBICQA_DATA}
