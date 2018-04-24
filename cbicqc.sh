#!/bin/bash
#
# Single QC analysis script
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
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
# Copyright 2011-2013 California Institute of Technology.

if [ $# -lt 2 ]; then
  echo "-----------------"
  echo "SYNTAX : cbicqc.sh <Scanner Name> <QC Date> <Search Keys> <Overwrite [Y|N]>"
  echo "<QC Date> has format: YYYYMMDD"
  echo "This script is designed to be called by cbicqc_scanner.sh, but can be run manually"
  exit
fi

# Assign arguments
scanner_name=$1
qc_date=$2
search_keys=$3
overwrite=$4

# Construct QC output directory
qc_dir=${CBICQC_DATA}/${scanner_name}/${qc_date}

# Full paths to commands (for XGrid if used)
cmd_getdicom=${CBICQC_BIN}/cbicqc_getdicom.sh
cmd_convert=${CBICQC_BIN}/cbicqc_dicom2nifti.sh
cmd_moco=${CBICQC_BIN}/cbicqc_moco.sh
cmd_timeseries=${CBICQC_BIN}/cbicqc_timeseries.sh
cmd_stats=${CBICQC_BIN}/cbicqc_stats.py
cmd_report=${CBICQC_BIN}/cbicqc_report.py

# Check if directory already exists - if not, get data and analyze
if [ ! -d ${qc_dir} -o ${overwrite} == "Y" ]
then

  echo ""
  echo "----------------------------"
  echo "NEW QC ANALYSIS : ${qc_date}"
  echo "----------------------------"
  
  if [ -s ${qc_dir}/qc.nii.gz ]
  then
  
    echo "  DICOM data has already been retrieved and converted - skipping"
  
  else

    # Retrieve QC DICOM stack from local OsiriX
    $cmd_getdicom $qc_dir $qc_date "$search_keys"

    # Convert QC DICOM stack to 4D Nifti-1 volume
    $cmd_convert $qc_dir
	
  fi

  if [ -s ${qc_dir}/qc_mcf.nii.gz ]
  then

    echo "  Motion correction has already been performed - skipping"

  else

    # Motion correct QC series
    $cmd_moco $qc_dir

  fi
  
  # Generate QC timeseries
  $cmd_timeseries $qc_dir

  # Calculate QC stats
  $cmd_stats $qc_dir

  # Generate HTML report and summary files
  $cmd_report $qc_dir
  
  echo "  Complete"
  
fi
