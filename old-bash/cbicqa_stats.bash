#!/bin/bash
#
# Calculate important QA stats for phantom QA dataset
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
#          10/03/2012 JMT Replace corner airspace mask with systematic noise estimate in artifact mask
#          10/12/2012 JMT Use signal volume for estimating artifact volume given known phantom volume
#
# Copyright 2011-2012 California Institute of Technology.
# All rights reserved.

# CBIC FBIRN phantom volume in ml
phantom_volume_ml=2500

# Check arguments
if [ $# -lt 1 ]; then
  echo "Please provide a QA directory name"
  echo "SYNTAX : cbicqa_stats.bash <QA Directory>"
  exit
fi

# Directory containing QA study
qa_dir=$1

echo "  Generating descriptive QA statistics"

# Image filenames
qa_mcf=${qa_dir}/qa_mcf
qa_mean=${qa_dir}/qa_mean
qa_sd=${qa_dir}/qa_sd
qa_mask=${qa_dir}/qa_mask

# Timeseries text file
qa_timeseries=${qa_dir}/qa_timeseries.txt

# Temporal mean of registered images
if [ -s ${qa_mean}.nii.gz ]
then
	echo "  Mean image exists - skipping"
else
	echo "  Calculating temporal mean image"
	fslmaths $qa_mcf -Tmean $qa_mean
fi

# Temporal SD of registered images
if [ -s ${qa_sd}.nii.gz ]
then
	echo "  SD image exists - skipping"
else
	echo "  Calculating temporal SD image"
	fslmaths $qa_mcf -Tstd $qa_sd
fi

# Create regional mask for phantom, Nyquist ghost and noise
if [ -s ${qa_mask}.nii.gz ]
then
	echo "  Mask image exists - skipping"
else

	# Temporary Nifti files
	tmp_signal=${qa_dir}/tmp_signal
	tmp_signal_dil=${qa_dir}/tmp_signal_dil
	tmp_phantom=${qa_dir}/tmp_phantom
	tmp_nyquist=${qa_dir}/tmp_nyquist
	tmp_upper=${qa_dir}/tmp_upper
	tmp_lower=${qa_dir}/tmp_lower
	tmp_noise=${qa_dir}/tmp_noise

	# Signal threshold for basic segmentation
	signal_threshold=`fslstats $qa_mean -p 99 | awk '{ print $1 * 0.1 }'`
	
	# Signal mask
	echo "  Creating signal mask (threshold = ${signal_threshold})"
	fslmaths ${qa_mean} -thr ${signal_threshold} -bin ${tmp_signal}
	
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
	fslmaths ${tmp_phantom} -add ${tmp_nyquist} -add ${tmp_noise} ${qa_mask}

	# Clean up temporary images
    rm -rf ${qa_dir}/tmp*.*

fi

# Extract time-series stats within each ROI
if [ -s ${qa_timeseries} ]; then
	echo "  Signal timecourses exist - skipping"
else
	echo "  Extracting mean signal timecourses for each region"
	# Timecourse of mean signal within each mask label
	fslmeants -i ${qa_mcf} -o ${qa_timeseries} --label=${qa_mask}
fi