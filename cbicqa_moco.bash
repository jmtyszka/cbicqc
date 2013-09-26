#!/bin/bash
#
# Register all volumes over time (use mcflirt)
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
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
  echo "Please provide a QA directory name"
  echo "SYNTAX : cbicqa_moco.bash <QA Directory>"
  exit
fi

# Key directories and files
qa_dir=$1
qa_nifti=${qa_dir}/qa
qa_mcf=${qa_dir}/qa_mcf
qa_mcf_par=${qa_dir}/qa_mcf.par

# Check whether MOCO has already been performed
if [ -s ${qa_mcf}.nii.gz ] && [ -s ${qa_mcf_par} ]; then
	echo "  Motion correction has already been done - skipping"
else
	echo "  Motion correcting"
	# Run mcflirt on QA Nifti file
	# Output file defaults to qa_mcf.nii.gz, parameters in qa_mcf.par
	mcflirt -in ${qa_nifti} -out ${qa_mcf} -refvol 0 -plots

fi