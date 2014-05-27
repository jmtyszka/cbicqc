#!/bin/bash
#
# Single QA analysis script
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
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

if [ $# -lt 2 ]; then
  echo "-----------------"
  echo "SYNTAX : cbicqa.bash <Scanner Name> <QA Date> <Search Keys> <Overwrite [Y|N]>"
  echo "<QA Date> has format: YYYYMMDD"
  echo "This script is designed to be called by cbicqa_scanner.bash, but can be run manually"
  exit
fi

# Assign arguments
scanner_name=$1
qa_date=$2
search_keys=$3
overwrite=$4

# Construct QA output directory
qa_dir=${CBICQA_DATA}/${scanner_name}/${qa_date}

# Full paths to commands (for XGrid if used)
cmd_getdicom=${CBICQA_BIN}/cbicqa_getdicom.bash
cmd_convert=${CBICQA_BIN}/cbicqa_dicom2nifti.bash
cmd_moco=${CBICQA_BIN}/cbicqa_moco.bash
cmd_timeseries=${CBICQA_BIN}/cbicqa_timeseries.bash
cmd_stats=${CBICQA_BIN}/cbicqa_stats.py
cmd_report=${CBICQA_BIN}/cbicqa_report.py

# Check if directory already exists - if not, get data and analyze
if [ ! -d ${qa_dir} -o ${overwrite} == "Y" ]
then

  echo ""
  echo "----------------------------"
  echo "NEW QA ANALYSIS : ${qa_date}"
  echo "----------------------------"
  
  if [ -s ${qa_dir}/qa.nii.gz ]
  then
  
    echo "  DICOM data has already been retrieved and converted - skipping"
  
  else

    # Retrieve QA DICOM stack from local OsiriX
    $cmd_getdicom $qa_dir $qa_date "$search_keys"

    # Convert QA DICOM stack to 4D Nifti-1 volume
    $cmd_convert $qa_dir
	
  fi

  if [ -s ${qa_dir}/qa_mcf.nii.gz ]
  then

    echo "  Motion correction has already been performed - skipping"

  else

    # Motion correct QA series
    $cmd_moco $qa_dir

  fi
  
  # Generate QA timeseries
  $cmd_timeseries $qa_dir

  # Calculate QA stats
  $cmd_stats $qa_dir

  # Generate HTML report and summary files
  $cmd_report $qa_dir
  
  echo "  Complete"
  
fi
