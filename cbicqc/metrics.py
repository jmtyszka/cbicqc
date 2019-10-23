# !/usr/bin/env python
"""
Quality control metric calculations from ROI timeseries fit results

AUTHOR : Mike Tyszka
PLACE  : Caltech
DATES  : 2019-06-04 JMT From scratch

This file is part of CBICQC.

   CBICQC is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   CBICQC is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
  along with CBICQC.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2019 California Institute of Technology.
"""

import numpy as np


def qc_metrics(fit_results, tsfnr_nii, rois_nii):
    """
    Calculate QC metrics for each ROI

    :param fit_results: list, fit objects from scipy least_squares
    :return metrics:, dict, QC metric results dictionary
    """

    # TODO:
    # EMI analysis with zipper identification
    # Coil element SNR and fluctuation analysis
    # - Requires separate labels for each coil element

    air_mean = fit_results[0].x[3]

    nyquist_mean = fit_results[1].x[3]

    signal_a_warm = fit_results[2].x[0]
    signal_t_warm = fit_results[2].x[1]
    signal_drift = fit_results[2].x[2]
    signal_mean = fit_results[2].x[3]

    # Calculate main signal tSFNR
    tsfnr = calc_tsfnr(tsfnr_nii, rois_nii)

    # Create and fill dictionary of QC metrics
    metrics = dict()

    metrics['SignalMean'] = signal_mean
    metrics['SNR'] = signal_mean / air_mean
    metrics['SFNR'] = tsfnr
    metrics['SArtR'] = signal_mean / nyquist_mean
    metrics['Drift'] = signal_drift / signal_mean * 100
    metrics['WarmupAmp'] = signal_a_warm / signal_mean * 100
    metrics['WarmupTime'] = signal_t_warm

    # SNR relative to mean noise
    # Estimate spatial noise sigma (assuming underlying Gaussian and Half-Normal distribution)
    # sigma = mean(noise) * sqrt(pi/2)
    # See for example http://en.wikipedia.org/wiki/Half-normal_distribution

    metrics['NoiseSigma'] = air_mean * np.sqrt(np.pi/2)
    metrics['NoiseFloor'] = air_mean
    metrics['SignalSpikes'] = spike_count(fit_results[0].fun)
    metrics['NyquistSpikes'] = spike_count(fit_results[1].fun)
    metrics['AirSpikes'] = spike_count(fit_results[2].fun)

    return metrics


def spike_count(points, thresh=3.5):
    """

    :param points:
    :param thresh:
    :return:
    """

    if len(points.shape) == 1:
        points = points[:, None]

    # Median absolute deviation from the median (MAD)
    med = np.median(points, axis=0)
    dev = np.abs(points - med)
    mad = np.median(dev)

    modified_z_score = 0.6745 * dev / mad

    # Cast to int to prevent JSON encoding errors later
    return int(np.sum(modified_z_score > thresh))


def calc_tsfnr(tsfnr_nii, rois_nii):

    tsfnr_img = tsfnr_nii.get_data()
    rois_img = rois_nii.get_data()

    return np.mean(tsfnr_img[rois_img == 1])




