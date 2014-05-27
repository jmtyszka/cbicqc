#!/bin/bash
#
# Master QA analysis script
#
# USAGE: cbicqa_scanner.bash <Scanner Name> <Search Keys> <Overwrite [Y|N]>
#
# Query and retrieve new QA studies for a given scanner from the local OsiriX database
# Use dcmtk command line functions to generate list of new QA data and 
# copy DICOM files into QA directory tree ready for analysis.
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#          10/16/2012 JMT Add local OsiriX Q&R to get QA study data
#          10/19/2012 JMT Add optional overwrite argument
#          02/19/2014 JMT Add scanner argument
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

if [ $# -lt 3 ]; then
  echo "USAGE : cbicqa_scanner.bash <Scanner Name> <Search Keys> <Overwrite [Y|N]>"
  exit
fi

# Assign arguments
scanner_name=$1
search_keys=$2
overwrite=$3

echo "CBIC QA Analysis for $scanner_name"
echo "-----------------------------------"
echo "QA Data Directory : ${CBICQA_DATA}/${scanner_name}"

# Query Osirix database using the provided, scanner-specific key string
echo "Querying local OsiriX database for QA studies"
qa_list=( `findscu -aet QA localhost 11112 -S -k 0008,0052="STUDY" ${search_keys} -k StudyDate= 2>&1 | awk '{ if ( $3 == "DA" ) { print $4 } }'` )

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
    cbicqa.bash ${scanner_name} ${qa_date} "${search_keys}" ${overwrite}
   
done

# Create QA calendar page for last six months and trend report page
cbicqa_scanner_calendar.py ${scanner_name}
cbicqa_scanner_trends.py ${scanner_name}