#!/bin/bash
# Retrieve daily QA DICOM stack from server into local directory
#
# USAGE: cbicqa_getdicom.sh <CBICQA directory> <study date YYYYMMDD> <search keys> [-d]
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#          2017-03-13 JMT Update for Horos SCP
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
# Copyright 2011-2017 California Institute of Technology.

# Local OsiriX AE Title
osirix_aet=evendim

# Local Osirix host name
#osirix_hostname=evendim.caltech.edu
osirix_hostname=127.0.0.1

# Local Osirix port number
osirix_port=11112

# Local movescu AE Title
movescu_aet=QA

# Local movescu port number
movescu_port=11113

# Full path to study directory for this date
qa_dir=$1

# Date string YYYYMMDD of current study
qa_date=$2

# Search keys used by cbicqa_scanner.sh to locate scanner QA series
search_keys=$3

# Full debug (-d) or quiet movescu
debug=$4

# Temporary DICOM import directory
qa_import=${qa_dir}/DICOM
echo "  Import directory : ${qa_import}"

# Create DICOM import directory (and containing directory)
if [ ! -d ${qa_import} ]
then
    mkdir -p ${qa_import}
fi

# Get QA DICOM stack from OsiriX database
echo "  Retrieving first QA study on ${qa_date} from OsiriX database"

# General pull of Tim32, Tim12 or 4.7T QA data
cmd="movescu --port ${movescu_port} -S ${debug} -k 0008,0052=""STUDY"" ""${search_keys}"" -k StudyDate=${qa_date} -od ${qa_import} ${osirix_hostname} ${osirix_port}"
$cmd
