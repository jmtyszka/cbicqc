#!/bin/bash
#
# Calculate ROI timeseries
# - output to text file for further use
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech
# DATES  : 09/16/2011 JMT From scratch
#          10/03/2012 JMT Replace corner airspace mask with systematic
#                         noise estimate in artifact mask
#          10/12/2012 JMT Use signal volume for estimating artifact volume
#                         given known phantom volume
#          09/25/2013 JMT Rename from cbicqc_stats to cbicqc_timeseries
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

# CBIC FBIRN phantom volume in ml
phantom_volume_ml=2500

# Check arguments
if [ $# -lt 1 ]; then
  echo "Please provide a QC date to process (in form YYYYMMDD)"
  echo "SYNTAX : cbicqc_timeseries.sh <QC Date>"
  exit
fi

# QC series working directory
qc_dir=$1

echo "  Generating descriptive QC statistics"

# Image filenames
qc_mcf=${qc_dir}/qc_mcf
qc_mean=${qc_dir}/qc_mean
qc_sd=${qc_dir}/qc_sd
qc_mask=${qc_dir}/qc_mask

# Timeseries text file
qc_timeseries=${qc_dir}/qc_timeseries.txt

# Temporal mean of registered images
if [ -s ${qc_mean}.nii.gz ]
then
	echo "  Mean image exists - skipping"
else
	echo "  Calculating temporal mean image"
	fslmaths $qc_mcf -Tmean $qc_mean
fi

# Temporal SD of registered images
if [ -s ${qc_sd}.nii.gz ]
then
	echo "  SD image exists - skipping"
else
	echo "  Calculating temporal SD image"
	fslmaths $qc_mcf -Tstd $qc_sd
fi

# Create regional mask for phantom, Nyquist ghost and noise
if [ -s ${qc_mask}.nii.gz ]
then
	echo "  Mask image exists - skipping"
else

	# Temporary Nifti files
	tmp_signal=${qc_dir}/tmp_signal
	tmp_signal_dil=${qc_dir}/tmp_signal_dil
	tmp_phantom=${qc_dir}/tmp_phantom
	tmp_nyquist=${qc_dir}/tmp_nyquist
	tmp_upper=${qc_dir}/tmp_upper
	tmp_lower=${qc_dir}/tmp_lower
	tmp_noise=${qc_dir}/tmp_noise

	# Signal threshold for basic segmentation
	signal_threshold=`fslstats $qc_mean -p 99 | awk '{ print $1 * 0.1 }'`
	
	# Signal mask
	echo "  Creating signal mask (threshold = ${signal_threshold})"
	fslmaths ${qc_mean} -thr ${signal_threshold} -bin ${tmp_signal}
	
	# Erode signal mask (6 mm radius sphere) to create phantom mask
	echo "  Creating phantom mask"
	fslmaths ${tmp_signal} -kernel sphere 6.0 -ero ${tmp_phantom}

	# Dilate phantom mask (6 mm radius sphere) *twice* to create dilated signal mask
    echo "  Creating dilated signal mask"
    fslmaths ${tmp_phantom} -kernel sphere 6.0 -dilF -dilF ${tmp_signal_dil}

	echo "  Creating Nyquist mask"
	# Extract upper and lower halves of dilated volume mask in Y dimension (PE)
	fslroi ${tmp_signal_dil} ${tmp_lower} 0 -1 0 32 0 -1 0 -1
	fslroi ${tmp_signal_dil} ${tmp_upper} 0 -1 32 -1 0 -1 0 -1
	
	# Create shifted (Nyqusit) mask from swapped upper and lower masks
	fslmerge -y ${tmp_nyquist} ${tmp_upper} ${tmp_lower}
	
	# Correct y offset in sform matrix
	sform=`fslorient -getsform ${tmp_signal}`
	fslorient -setsform ${sform} ${tmp_nyquist}
	
	# XOR Nyquist and dilated signal masks
	fslmaths ${tmp_nyquist} -mul ${tmp_signal_dil} -mul -1.0 -add ${tmp_nyquist} ${tmp_nyquist}
	
	echo "  Creating noise mask"
	# Create noise mask by subtracting Nyquist mask from NOT dilated signal mask
	fslmaths ${tmp_signal_dil} -binv -sub ${tmp_nyquist} ${tmp_noise}
	
	# Finally merge all three masks into an indexed file
	# Phantom = 1
	# Nyquist = 2
	# Noise   = 3
	fslmaths ${tmp_nyquist} -mul 2 ${tmp_nyquist}
	fslmaths ${tmp_noise} -mul 3 ${tmp_noise}
	fslmaths ${tmp_phantom} -add ${tmp_nyquist} -add ${tmp_noise} ${qc_mask}

	# Clean up temporary images
    rm -rf ${qc_dir}/tmp*.*

fi

# Create orthogonal slice views of mean and sd images
scale_factor=2
slicer ${qc_dir}/qc_mean -s ${scale_factor} -a ${qc_dir}/qc_mean_ortho.png
slicer ${qc_dir}/qc_sd -s ${scale_factor} -a ${qc_dir}/qc_sd_ortho.png
slicer ${qc_dir}/qc_mask -s ${scale_factor} -a ${qc_dir}/qc_mask_ortho.png

# Extract time-series stats within each ROI
if [ -s ${qc_timeseries} ]; then
	echo "  Signal timecourses exist - skipping"
else
	echo "  Extracting mean signal timecourses for each region"
	# Timecourse of mean signal within each mask label
	fslmeants -i ${qc_mcf} -o ${qc_timeseries} --label=${qc_mask}
fi
