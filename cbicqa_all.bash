#!/bin/bash
#
# Master QA analysis script
#
# USAGE: cbicqa_all.bash <Overwrite [Y|N]>
#
# Query and retrieve new QA studies from the local OsiriX database
# Use dcmtk command line functions to generate list of new QA data and 
# copy DICOM files into QA directory tree ready for analysis.
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#          10/16/2012 JMT Add local OsiriX Q&R to get QA study data
#          10/19/2012 JMT Add optional overwrite argument
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

# QA data/website directory
if [ "x${CBICQA_DATA}" -eq "x" ]; then
  echo "Environmental variable CBICQA_DATA undefined - exiting"
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

# Query all studies on local OsiriX with PatientID = "qa"
echo "Querying local OsiriX database for QA studies"
qa_list=( `findscu -aet QA localhost 11112 -S -k 0008,0052="STUDY" -k PatientID="qa" -k StudyDate= 2>&1 | awk '{ if ( $3 == "DA" ) { print $4 } }'` )

# Report length of QA study list
n_qas=${#qa_list[@]}
echo "${n_qas} QA studies found"

# If no studies are found, likely that OsiriX isn't running or communication is failing
if [ ${n_qas} -lt 1 ]
then
    echo "No QA studies found - check that OsiriX is running"
    exit
fi

#
# Loop over all QA studies returned by OsiriX
#

for q in "${qa_list[@]}":
do

    # Strip any square braces and colons from name
    qa_date=${q/[/}
    qa_date=${qa_date/]/}
    qa_date=${qa_date/:/}

    # Call single study QA analysis
    cbicqa.bash ${CBICQA_DATA} ${qa_date} ${overwrite}
   
done

# Compile summary report from all individual QA reports
# Final report HTML file is in $qa_data/qa_report.html

cbicqa_report_all.bash $qa_data

echo "-----------"
echo "Done"
