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

# Full debug (-d) or quiet movescu
debug=$3

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
#movescu -aet ${movescu_aet} -aem ${movescu_aet} --port ${movescu_port} -aec ${osirix_aet} -S ${debug} -k 0008,0052="STUDY" -k PatientID="qa" -k StudyDate=${qa_date} -od ${qa_import} ${osirix_hostname} ${osirix_port}
movescu --port ${movescu_port} -S ${debug} -k 0008,0052="STUDY" -k PatientID="qa" -k StudyDate=${qa_date} -od ${qa_import} ${osirix_hostname} ${osirix_port}
