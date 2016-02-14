#!/bin/bash
#
# Run in vivo QA on a single 4D EPI dataset
# Creates an output directory containing results at the same level as the EPI data
#
# USAGE : cbicqalive <4D EPI Nifti-1> <TR seconds>
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech
# DATES  : 2014-02-12 JMT From scratch
#          2016-02-12 JMT Add HTML and PDF report generation
#
# Copyright 2014-2016 California Institute of Technology
# All rights reserved.

if [ $# -lt 2 ]; then
  echo "USAGE : cbicqalive <4D EPI Nifti-1>
  exit
fi

# 4D EPI filename (including .nii.gz extension)
epi_file=$1


# Splash
echo "------------------------------------------"
echo "QALive : in vivo quality assurance metrics"
echo "------------------------------------------"
echo "4D EPI Data : ${epi_file}"
echo "EPI TR      : ${TR_seconds} seconds"
echo "Start time  : `date`"
echo ""

# Check that EPI file exists
if [ ! -s ${epi_file} ]; then
  echo "${epi_file} does not exist - exiting"
  exit
fi

# Extract data dimensions from Nifti header



# TR required for high pass filtering
TR_seconds=$2

# Find containing directory
root_dir=`dirname $epi_file`

# Strip extension from EPI file
epi_stub=${epi_file%%.nii.gz}

# Create a QALive directory at the same level
# Leave deletion of files to user since this script reuses previous results where possible
qa_dir=${epi_stub}.qalive
if [ ! -d ${qa_dir} ]; then
  echo "Creating QALive directory"
  mkdir -p ${qa_dir}
fi

# Key filenames
qa_mcf=${qa_dir}/qa_mcf
qa_filt=${qa_dir}/qa_filt
qa_tmean=${qa_dir}/qa_tmean
qa_tsd=${qa_dir}/qa_tsd
qa_tsnr=${qa_dir}/qa_tsnr
qa_mask=${qa_dir}/qa_mask
qa_brain_mask=${qa_dir}/qa_brain_mask
qa_tsnr_median=${qa_dir}/qa_tsnr_median.txt
qa_mcf_par=${qa_dir}/qa_mcf.par

# Check whether MOCO has already been performed
if [ -s ${qa_mcf}.nii.gz ] && [ -s ${qa_mcf_par} ]; then
  echo "Motion correction has already been done - skipping"
else
  echo "Motion correcting"
  # Run mcflirt on QA Nifti file
  # Output file defaults to qa_mcf.nii.gz, parameters in qa_mcf.par
  mcflirt -in ${epi_file} -out ${qa_mcf} -refvol 0 -plots

fi

#
# Non-linear high pass filtering to remove slow baselines
# Standard step in FEAT pipeline
#
if [ -s ${qa_filt}.nii.gz ]; then
  echo "Temporal high pass filtering has already been done - skipping"
else
  sigma_seconds=50.0
  sigma_vols=`echo $TR_seconds | awk -v s=${sigma_seconds} '{ print s / $1 }'`
  echo "Temporal high pass filtering : sigma = $sigma_seconds seconds (${sigma_vols} volumes)"
  fslmaths ${qa_mcf} -bptf ${sigma_vols} -1 ${qa_filt}
fi

#
# Generate QA metrics
#

echo "Generating QA metrics"

# Timeseries text file
qa_timeseries=${qa_dir}/qa_timeseries.txt

# Temporal mean of registered images
# After motion correction, before demeaning
if [ -s ${qa_tmean}.nii.gz ]
then
  echo "  Mean image exists - skipping"
else
  echo "  Calculating tMean image"
  fslmaths ${qa_mcf} -Tmean ${qa_tmean}
fi

# Temporal SD of registered images
if [ -s ${qa_tsd}.nii.gz ]
then
  echo "  SD image exists - skipping"
else
  echo "  Calculating tSD image"
  fslmaths ${qa_filt} -Tstd ${qa_tsd}
fi

# Voxel-wise tSNR image
if [ -s ${qa_tsnr}.nii.gz ]
then
  echo "  tSNR image exists - skipping"
else
  echo "  Calculating tSNR image"
  fslmaths ${qa_tmean} -div ${qa_tsd} ${qa_tsnr}
fi

# Create regional mask for brain, Nyquist ghost and noise
if [ -s ${qa_mask}.nii.gz ]
then
  echo "  Mask image exists - skipping"
else

  # Temporary Nifti files
  tmp_signal=${qa_dir}/tmp_signal
  tmp_signal_dil=${qa_dir}/tmp_signal_dil
  tmp_brain=${qa_dir}/tmp_brain
  tmp_nyquist=${qa_dir}/tmp_nyquist
  tmp_upper=${qa_dir}/tmp_upper
  tmp_lower=${qa_dir}/tmp_lower
  tmp_noise=${qa_dir}/tmp_noise

  # Signal threshold for basic segmentation
  # 10% of the 99th percentile of intensity
  signal_threshold=`fslstats $qa_tmean -p 99 | awk '{ print $1 * 0.1 }'`
  
  # Signal mask
  echo "  Creating signal mask (threshold = ${signal_threshold})"
  fslmaths ${qa_tmean} -thr ${signal_threshold} -bin ${tmp_signal}
  
  # Erode signal mask (6 mm radius sphere) to create brain mask
  echo "  Creating brain mask"
  fslmaths ${tmp_signal} -kernel sphere 6.0 -ero ${tmp_brain}

  # Dilate brain mask (6 mm radius sphere) *twice* to create dilated signal mask
  echo "  Creating dilated signal mask"
  fslmaths ${tmp_brain} -kernel sphere 6.0 -dilF -dilF ${tmp_signal_dil}

  echo "  Creating Nyquist mask"

  # Determine y dimension (PE dim in EPI)
  half_ny=`fslinfo ${qa_tmean} | awk '{ if ($1 == "dim2") print $2/2 }'`

  echo "Half ny = ${half_ny}"

  # Extract upper and lower halves of dilated volume mask in Y dimension (PE)
  fslroi ${tmp_signal_dil} ${tmp_lower} 0 -1 0 ${half_ny} 0 -1 0 -1
  fslroi ${tmp_signal_dil} ${tmp_upper} 0 -1 ${half_ny} -1 0 -1 0 -1
  
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
  fslmaths ${tmp_brain} -add ${tmp_nyquist} -add ${tmp_noise} ${qa_mask}

  # Save brain mask
  imcp ${tmp_brain} ${qa_brain_mask}

  # Clean up temporary images
  echo "  Cleaning up temporary images"
  rm -rf ${qa_dir}/tmp*.*

fi

# Create orthogonal slice views of mean and sd images
scale_factor=2
slicer ${qa_tmean} -s ${scale_factor} -a ${qa_dir}/qa_tmean_ortho.png
slicer ${qa_tsd} -s ${scale_factor} -a ${qa_dir}/qa_tsd_ortho.png
slicer ${qa_tsnr} -s ${scale_factor} -a ${qa_dir}/qa_tsnr_ortho.png
slicer ${qa_mask} -s ${scale_factor} -a ${qa_dir}/qa_mask_ortho.png

# Extract time-series stats within each ROI
if [ -s ${qa_timeseries} ]; then
  echo "  Signal timecourses exist - skipping"
else
  echo "  Extracting mean signal timecourses for each region"
  # Timecourse of mean signal within each mask label
  fslmeants -i ${qa_filt} -o ${qa_timeseries} --label=${qa_mask}
fi

# Create plot images for motion and ROI mean timeseries
fsl_tsplot -i $qa_mcf_par -o ${qa_mcf}_rot.png -t Rotation_rad -a x,y,z --start=1 --finish=3
fsl_tsplot -i $qa_mcf_par -o ${qa_mcf}_trans.png -t Translation_mm -a x,y,z --start=4 --finish=6

# Calculate median tSNR within brain mask
if [ -s ${qa_tsnr_median} ]; then
  echo "  tSNR median already calculated"
else
  echo "  Calculating median tSNR within brain mask"
  fslstats ${qa_tsnr} -k ${qa_brain_mask} -p 50 > ${qa_tsnr_median}
fi

# Generate HTML report page and convert to PDF
cbicqalive_report.sh

# Done
echo "Finished at : `date`"
