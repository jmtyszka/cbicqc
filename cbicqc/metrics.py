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


def signal_metrics(fit_results, tsfnr_nii, rois_nii):
    """
    Calculate signal QC metrics for each ROI

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
    """
    ROI Label Key
    ----
    Undefined       = 0
    Air Space       = 1
    Nyquist Ghost   = 2
    Signal          = 3

    :param tsfnr_nii:
    :param rois_nii:
    :return:
    """

    tsfnr_img = tsfnr_nii.get_data()
    rois_img = rois_nii.get_data()

    return np.mean(tsfnr_img[rois_img == 3])


def moco_metrics(moco_pars):

    # Calculate framewise displacement timecourse from moco_pars
    fd = calc_fd(moco_pars)

    # Create and fill metrics dictionary
    metrics = dict()

    metrics['MeanFD'] = fd.mean()
    metrics['MaxFD'] = fd.max()

    return metrics


def calc_fd(mcf):
    """
    Calculate conventional FD from 6-column FSL MCFLIRT motion parameters

    Reference:
    J. D. Power, K. A. Barnes, A. Z. Snyder, B. L. Schlaggar, and S. E. Petersen,
    “Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion,”
    Neuroimage, vol. 59, pp. 2142–2154, Feb. 2012, doi: 10.1016/j.neuroimage.2011.10.018. [Online].
    Available: http://dx.doi.org/10.1016/j.neuroimage.2011.10.018
    """

    # Rotations (radians)
    rx = mcf[:, 0]
    ry = mcf[:, 1]
    rz = mcf[:, 2]

    # Translations (mm)
    tx = mcf[:, 3]
    ty = mcf[:, 4]
    tz = mcf[:, 5]

    # Backward differences (forward difference + leading 0)

    drx = np.insert(np.diff(rx), 0, 0)
    dry = np.insert(np.diff(ry), 0, 0)
    drz = np.insert(np.diff(rz), 0, 0)

    dtx = np.insert(np.diff(tx), 0, 0)
    dty = np.insert(np.diff(ty), 0, 0)
    dtz = np.insert(np.diff(tz), 0, 0)

    # Total framewise displacement (Power 2012)

    r_sphere = 50.0  # mm

    FD = (np.abs(dtx) +
          np.abs(dty) +
          np.abs(dtz) +
          np.abs(r_sphere * drx) +
          np.abs(r_sphere * dry) +
          np.abs(r_sphere * drz)
          )

    return FD






