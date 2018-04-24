#!/bin/bash
#
# Master QC analysis script
#
# USAGE: cbicqc_scanner.sh <Scanner Name> <Search Keys> <Overwrite [Y|N]>
#
# Query and retrieve new QC studies for a given scanner from the local OsiriX database
# Use dcmtk command line functions to generate list of new QC data and 
# copy DICOM files into QC directory tree ready for analysis.
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#          10/16/2012 JMT Add local OsiriX Q&R to get QC study data
#          10/19/2012 JMT Add optional overwrite argument
#          02/19/2014 JMT Add scanner argument
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
# Copyright 2011-2014 California Institute of Technology.

# QC data/website directory
if [ -z "${CBICQC_DATA}" ]; then
  echo "Please define CBICQC_DATA undefined - exiting"
  exit
fi

if [ $# -lt 3 ]; then
  echo "USAGE : cbicqc_scanner.sh <Scanner Name> <Search Keys> <Overwrite [Y|N]>"
  exit
fi

# Assign arguments
scanner_name=$1
search_keys=$2
overwrite=$3

echo "CBIC QC Analysis for $scanner_name"
echo "-----------------------------------"
echo "QC Data Directory : ${CBICQC_DATA}/${scanner_name}"

# Query Osirix database using the provided, scanner-specific key string
echo "Querying local OsiriX database for QC studies"
qc_list=( `findscu -aet QC localhost 11112 -S -k 0008,0052="STUDY" ${search_keys} -k StudyDate= 2>&1 | awk '{ if ( $3 == "DA" ) { print $4 } }'` )

# Report length of QC study list
n_qcs=${#qc_list[@]}
echo "${n_qcs} QC studies found"

# If no studies are found, likely that OsiriX isn't running or communication is failing
if [ ${n_qcs} -lt 1 ]
then
    echo "No QC studies found - check that OsiriX is running"
    exit
fi

#
# Loop over all QC studies returned by OsiriX
#

for q in "${qc_list[@]}":
do

    # Strip any square braces and colons from name
    qc_date=${q/[/}
    qc_date=${qc_date/]/}
    qc_date=${qc_date/:/}

    # Call single study QC analysis
    cbicqc.sh ${scanner_name} ${qc_date} "${search_keys}" ${overwrite}
   
done

# Create QC calendar page for last six months and trend report page
cbicqc_scanner_calendar.py ${scanner_name}
cbicqc_scanner_trends.py ${scanner_name}
