#!/bin/bash
#
# Convert DICOM QA series to Nifti-1 4D file
#
# Expects ${qa_dir}/DICOM to exist and contain the QA DICOM files
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
# PLACE  : Caltech Brain Imaging Center
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

if [ $# -lt 1 ]; then
  echo "-----------------"
  echo "Please provide a QA directory name"
  echo "SYNTAX : cbicqa_dicom2nifti <QA Directory>"
  exit
fi

qa_dir=$1

# Check for QA dir and DICOM subdirectory
if [ ! -d ${qa_dir}/DICOM ]
then
    echo "*** ${qa_dir}/DICOM does not exist - exiting"
    exit
fi

echo "  Converting DICOM to Nifti"

# Get the first filename from the DICOM import subdirectory
dc_file=`ls -1 ${qa_dir}/DICOM/* | head -n 1`

# Generate a series info text file
dicom_info=${qa_dir}/qa_info.txt

if [ -s ${dicom_info} ]; then
	
	echo "  DICOM info file present - skipping"
	
else
	
	echo "  Generating DICOM info file from ${dc_file}"

    # Scanner Serial Number
    mri_probedicom --i ${dc_file} --t 0018 1000 >> ${dicom_info}
	
    # Scan date
    mri_probedicom --i ${dc_file} --t 0008 0022 >> ${dicom_info}
	
    # Scanner Frequency
    mri_probedicom --i ${dc_file} --t 0018 0084 >> ${dicom_info}

    # Repetition Time (ms)
    mri_probedicom --i ${dc_file} --t 0018 0080 >> ${dicom_info}

fi

# Output file name
nifti_file=${qa_dir}/qa.nii.gz

# Skip if Nifti file already present
if [ -s ${nifti_file} ]; then

	echo "  QA Nifti file already exists - skipping"

else

	# Convert DICOM stack to Nifti 4D
	echo "  Converting DICOM to Nifti-1 volume"
	mri_convert ${dc_file} ${nifti_file} &> ${qa_dir}/qa_mri_convert.log

	# Delete the DICOM subdirectory if conversion successful (ie qa.nii.gz file exists)
	if [ -s ${nifti_file} ]; then
	echo "  Removing temporary DICOM files"
		rm -rf ${qa_dir}/DICOM
	fi

    # Add number of volumes to info file
    fslinfo ${nifti_file} | awk '{ if ($1 == "dim4") { print $2 } }' >> ${dicom_info}

fi