#!/bin/bash
#
# Generate HTML report from analysis results in a QA directory
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 09/16/2011 JMT From scratch
#
# Copyright 2012 California Institute of Technology
# All rights reserved
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
  echo "SYNTAX : cbicqa_report.bash <QA Directory>"
  exit
fi

# Directories
qa_dir=$1

echo "  Generating report"

# HTML output file
qa_report=${qa_dir}/qa_report.html

# Info summary file
qa_summary=${qa_dir}/qa_summary.txt

# Use detrended timeseries
qa_timeseries=${qa_dir}/qa_timeseries_detrend.txt

# Moco pars (MCFLIRT format)
qa_mcf_par=${qa_dir}/qa_mcf.par

# Read scan info from file
info=$(<${qa_dir}/qa_info.txt)
set -- $info
scanner_serno=$1
acq_date=$2
scanner_freq=$3
TR_ms=$4
num_volumes=$5

# Analysis date and time
analysis_date=`date "+%Y%m%d-%H%M%S"`

#
# Summary statistics
#

# Timeseries file has three columns for mean signal within:
# 1. Phantom
# 2. Nyquist ghost
# 3. Noise (non-phantom, non-ghost)

# Temporal mean and sd of basic timeseries
tmeansd_phantom=`cbicqa_meansd.bash ${qa_timeseries} 1`
tmeansd_nyquist=`cbicqa_meansd.bash ${qa_timeseries} 2`
tmeansd_noise=`cbicqa_meansd.bash ${qa_timeseries} 3`

# Extract temporal means
tmean_phantom=`echo $tmeansd_phantom | awk '{ printf "%0.2f", $1 }'`
tmean_nyquist=`echo $tmeansd_nyquist | awk '{ printf "%0.2f", $1 }'`
tmean_noise=`echo $tmeansd_noise | awk '{ printf "%0.2f", $1 }'`

# Extract temporal SDs
tsd_phantom=`echo $tmeansd_phantom | awk '{ printf "%0.2f", $2 }'`
tsd_nyquist=`echo $tmeansd_nyquist | awk '{ printf "%0.2f", $2 }'`
tsd_noise=`echo $tmeansd_noise | awk '{ printf "%0.2f", $2 }'`

# Derived measures from basic timeseries: SNR and drift
tmean_snr=`awk '{sum+=$1/$3} END {printf "%0.1f",sum/NR}' ${qa_timeseries}`
sig_drift_perc=`awk 'BEGIN {max=0; min=9999} $1>max {max=$1} $1<min {min=$1} \
  END {printf "%0.1f",(max-min)/(max+min)*200}' ${qa_timeseries}`
  
# Report
echo "    Phantom : $tmean_phantom ($tsd_phantom)"
echo "    Nyquist : $tmean_nyquist ($tsd_nyquist)"
echo "    Noise   : $tmean_noise ($tsd_noise)"
echo "    SNR     : $tmean_snr"
echo "    Drift   : $sig_drift_perc %"

# Center of mass of temporal mean image - calculate on the fly using fslstats -c
com_xyz=`fslstats ${qa_dir}/qa_mean -c`
com_mean_x=`echo ${com_xyz} | awk '{ printf "%.1f", $1 }'`
com_mean_y=`echo ${com_xyz} | awk '{ printf "%.1f", $2 }'`
com_mean_z=`echo ${com_xyz} | awk '{ printf "%.1f", $3 }'`

# Displacement maxima
max_adx=`awk 'BEGIN {amax=0} sqrt($4*$4)>amax {amax=sqrt($4*$4)} END { printf "%.1f", amax * 1000 }' ${qa_mcf_par}`
max_ady=`awk 'BEGIN {amax=0} sqrt($5*$5)>amax {amax=sqrt($5*$5)} END { printf "%.1f", amax * 1000 }' ${qa_mcf_par}`
max_adz=`awk 'BEGIN {amax=0} sqrt($6*$6)>amax {amax=sqrt($6*$6)} END { printf "%.1f", amax * 1000 }' ${qa_mcf_par}`

# Create and clear report HTML file
echo "" > $qa_report

#
# Construct single QA report page
#

# Write HTML header to report file
echo "<html>
<head>
<STYLE TYPE=text/css>
<!--
BODY
   {
   font-family:sans-serif;
   }
-->
</STYLE>
</head>
<body>" >> $qa_report

# Add QA acquisition information to HTML page
echo "<h1>CBIC Quality Assurance Report</h1>
<table>
<tr><td><b>Scanner Serial No</b> <td>$scanner_serno</tr>
<tr><td><b>Acquisition Date</b> <td>$acq_date</tr>
<tr><td><b>Analysis Date</b> <td>$analysis_date</tr>
<tr><td><b>Frequency</b> <td>${scanner_freq} MHz</tr>
<tr><td><b>Volumes</b> <td>${num_volumes}</tr>
<tr><td><b>TR</b> <td>${TR_ms} ms</tr>
<tr><td><td></tr>" >> $qa_report

echo `cbicqa_checklims.bash "Mean Signal" ${tmean_phantom} 550 1000` >> $qa_report
echo `cbicqa_checklims.bash "Mean Nyquist" ${tmean_nyquist} 0 50` >> $qa_report
echo `cbicqa_checklims.bash "Mean Noise" ${tmean_noise} 0 30` >> $qa_report
echo `cbicqa_checklims.bash "SD Signal" ${tsd_phantom} 0 1` >> $qa_report
echo `cbicqa_checklims.bash "SD Nyquist" ${tsd_nyquist} 0 1` >> $qa_report
echo `cbicqa_checklims.bash "SD Noise" ${tsd_noise} 0 0.1` >> $qa_report
echo `cbicqa_checklims.bash "Mean SNR" ${tmean_snr} 25 100` >> $qa_report
echo `cbicqa_checklims.bash "Signal Drift (%)" ${sig_drift_perc} 0 10` >> $qa_report
echo `cbicqa_checklims.bash "CofM x (mm)" ${com_mean_x} -20 20` >> $qa_report
echo `cbicqa_checklims.bash "CofM y (mm)" ${com_mean_y} -20 20` >> $qa_report
echo `cbicqa_checklims.bash "CofM z (mm)" ${com_mean_z} -20 20` >> $qa_report
echo `cbicqa_checklims.bash "Max |dx| (um)" ${max_adx} 0 1000` >> $qa_report
echo `cbicqa_checklims.bash "Max |dy| (um)" ${max_ady} 0 1000` >> $qa_report
echo `cbicqa_checklims.bash "Max |dz| (um)" ${max_adz} 0 1000` >> $qa_report

echo "</table>" >> $qa_report

# Create orthogonal slice views of mean and sd images
scale_factor=2
slicer ${qa_dir}/qa_mean -s ${scale_factor} -a ${qa_dir}/qa_mean_ortho.png
slicer ${qa_dir}/qa_sd -s ${scale_factor} -a ${qa_dir}/qa_sd_ortho.png
slicer ${qa_dir}/qa_mask -s ${scale_factor} -a ${qa_dir}/qa_mask_ortho.png

# Insert mean and sd orthoslice images into HTML page
echo "<h3>Temporal Mean Image</h3><img src=qa_mean_ortho.png /><br>" >> $qa_report
echo "<h3>Temporal SD Image</h3><img src=qa_sd_ortho.png /><br>" >> $qa_report
echo "<h3>Region Mask</h3><img src=qa_mask_ortho.png /><br>" >> $qa_report

# Add timeseries plot (from detrending) to page
echo "<h2>Signal and Noise</h2><img src=qa_detrend.png /><br>" >> $qa_report

# Create translation parameter graph
fsl_tsplot -i ${qa_dir}/qa_mcf.par -t "Translation (mm)" -a x,y,z --start=4 --finish=6 -o ${qa_dir}/qa_trans.png

# Add motion parameter graphs to page
echo "<h2>Apparent rigid body motion</h2>
<img src=qa_trans.png /><br>" >> $qa_report

# Close out HTML report
echo "</body></html>" >> $qa_report

# Write QA summary to text file for gobal reporting
echo "ScannerSerNo $scanner_serno
acq_date $acq_date
analysis_date $analysis_date
scanner_freq $scanner_freq
tmean_phantom $tmean_phantom
tmean_nyquist $tmean_nyquist
tmean_noise $tmean_noise
tsd_phantom $tsd_phantom
tsd_nyquist $tsd_nyquist
tsd_noise $tsd_noise
tmean_snr $tmean_snr
sig_drift_perc $sig_drift_perc
com_mean_x $com_mean_x
com_mean_y $com_mean_y
com_mean_z $com_mean_z
max_adx $max_adx
max_ady $max_ady
max_adz $max_adz" > $qa_summary
