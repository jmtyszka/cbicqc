#!/bin/bash
#
# Register all volumes over time (use mcflirt)
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
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

if [ $# -lt 1 ]; then
  echo "Please provide a QC directory name"
  echo "SYNTAX : cbicqc_moco.sh <QC Directory>"
  exit
fi

# Key directories and files
qc_dir=$1
qc_nifti=${qc_dir}/qc
qc_mcf=${qc_dir}/qc_mcf
qc_mcf_par=${qc_dir}/qc_mcf.par

# Check whether MOCO has already been performed
if [ -s ${qc_mcf}.nii.gz ] && [ -s ${qc_mcf_par} ]; then
	echo "  Motion correction has already been done - skipping"
else
	echo "  Motion correcting (this may take some time)"
	# Run mcflirt on QC Nifti file
	# Output file defaults to qc_mcf.nii.gz, parameters in qc_mcf.par
	mcflirt -in ${qc_nifti} -out ${qc_mcf} -refvol 0 -plots &> /dev/null
fi
