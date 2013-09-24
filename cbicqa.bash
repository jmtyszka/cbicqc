#!/bin/bash
#
# Single QA analysis script
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#
# Copyright 2011 California Institute of Technology
# All rights reserved.

# Localization
user_home=/Users/jmt
bin_dir=${user_home}/bin/CBICQA

if [ $# -lt 3 ]; then
  echo "-----------------"
  echo "SYNTAX : cbicqa.bash <QA Data Directory> <QA Date-Time> <Overwrite [Y|N]>"
  echo "<QA Date-Time> has format: YYYYMMDD-HHMM"
  echo "This script is designed to be called by cbicqa_all.bash, but can be run manually"
  exit
fi

# Construct QA analysis directory name
qa_data=$1
qa_date=$2
qa_overwrite=$3
qa_dir=${qa_data}/${qa_date}

# Full paths to commands (for XGrid if used)
cmd_getdicom=${bin_dir}/cbicqa_getdicom.bash
cmd_convert=${bin_dir}/cbicqa_dicom2nifti.bash
cmd_moco=${bin_dir}/cbicqa_moco.bash
cmd_stats=${bin_dir}/cbicqa_stats.bash
cmd_report=${bin_dir}/cbicqa_report.bash

# Check if directory already exists - if not, get data and analyze
if [ ! -d ${qa_dir} -o ${qa_overwrite} == "Y" ]
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
    $cmd_getdicom $qa_dir $qa_date

    # Convert QA DICOM stack to 4D Nifti-1 volume
    $cmd_convert $qa_dir
	
  fi
  
  # Motion correct QA series
  $cmd_moco $qa_dir
  
  # Generate descriptive QA stats
  $cmd_stats $qa_dir
  
  # Generate HTML report and summary files
  $cmd_report $qa_dir
  
  echo "  Complete"
  
fi