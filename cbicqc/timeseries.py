# !/usr/bin/env python
"""
CBICQC timeseries analysis node

AUTHOR : Mike Tyszka
PLACE  : Caltech
DATES  : 2019-05-22 JMT From scratch

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
from scipy.optimize import least_squares
import nibabel as nb


def temporal_mean_sd(qc_moco_nii):

    # Temporal mean of 4D timeseries
    tmean = np.mean(qc_moco_nii.get_data(), axis=3)
    tsd = np.std(qc_moco_nii.get_data(), axis=3)
    tsfnr = tmean / (tsd + np.finfo(float).eps)

    tmean_nii = nb.Nifti1Image(tmean, qc_moco_nii.affine)
    tsd_nii = nb.Nifti1Image(tsd, qc_moco_nii.affine)
    tsfnr_nii = nb.Nifti1Image(tsfnr, qc_moco_nii.affine)

    return tmean_nii, tsd_nii, tsfnr_nii


def extract_timeseries(qc_moco_nii, rois_nii):

    rois = rois_nii.get_data()
    s = qc_moco_nii.get_data()

    # Number of time points
    nt = s.shape[3]

    # ROI label indices
    # 0 : unassigned
    # 1 : air space
    # 2 : Nyquist ghost
    # 3 : signal

    labels = [1, 2, 3]
    nl = len(labels)

    s_mean_t = np.zeros([nl, nt])

    for lc in range(0, nl):
        mask = np.array(rois == labels[lc])
        for tc in range(0, nt):
            s_t = s[:, :, :, tc]
            s_mean_t[lc, tc] = np.mean(s_t[mask])

    return s_mean_t


def detrend_timeseries(s_mean_t):
    """
    :param s_mean_t: spatial mean ROI timeseries
    :return:
    """

    nl, nt = s_mean_t.shape

    # Time vector
    t = np.arange(0, nt)

    s_detrend_t = np.zeros_like(s_mean_t)

    fit_results = []

    for lc in range(0, nl):

        s_t = s_mean_t[lc, :]

        s_min, s_max, s_mean = np.min(s_t), np.max(s_t), np.mean(s_t)
        s_rng = s_max - s_min

        x0 = [s_rng, 5, -s_rng / nt, s_mean]
        bounds = ([0,      0, -np.inf,      0],
                  [s_rng, nt,       0, np.inf])

        # Robust non-linear curve fit (Huber loss function)
        result = least_squares(explin, x0,
                               method='trf',
                               loss='huber',
                               bounds=bounds,
                               args=(t, s_t))

        # Fitted curve
        s_fit = explin(result.x, t, 0)

        # Add fit residual to temporal mean - detrended timeseries
        s_detrend_t[lc, :] = s_mean + result.fun

        fit_results.append(result)

    return fit_results, s_detrend_t


def explin(x, t, y):
    """
    Exponential + linear trend model

    :param x: list, parameters
        0: Exponential amplitude
        1: Exponential time constant
        2: Linear slope
        3: Offset
    :param t: array, time vector
    :param y: array, data
    :return: array, residuals
    """

    return x[0] * np.exp(-t / x[1]) + x[2] * t + x[3] - y

#     # Residual Gaussian sigma estimation
#     # Assumes Gaussian white noise + sparse outlier spikes
#     # Use robust estimate of residual sd (MAD * 1.4826)
#     phantom_res_sigma = np.median(np.abs(phantom_res)) * 1.4826
#     nyquist_res_sigma = np.median(np.abs(nyquist_res)) * 1.4826
#     noise_res_sigma = np.median(np.abs(noise_res)) * 1.4826
#
#     # Count spikes, defined as residuals more than 5 SD from zero
#     phantom_spikes = (np.abs(phantom_res) > 5 * phantom_res_sigma).sum()
#     nyquist_spikes = (np.abs(nyquist_res) > 5 * nyquist_res_sigma).sum()
#     noise_spikes = (np.abs(noise_res) > 5 * noise_res_sigma).sum()
#
#     # Calculate percent drift over course of acquisition (use fitted curve)
#     phantom_drift = (phantom_fit[nv - 1] - phantom_fit[0]) / phantom_fit[0] * 100.0
#     nyquist_drift = (nyquist_fit[nv - 1] - nyquist_fit[0]) / nyquist_fit[0] * 100.0
#     noise_drift = (noise_fit[nv - 1] - noise_fit[0]) / noise_fit[0] * 100.0
#
#     # Append mean, spike count, drift to fit parameters
#     phantom_opt = np.append(phantom_opt, [phantom_mean, phantom_spikes, phantom_drift])
#     nyquist_opt = np.append(nyquist_opt, [nyquist_mean, nyquist_spikes, nyquist_drift])
#     noise_opt = np.append(noise_opt, [noise_mean, noise_spikes, noise_drift])
#
#     # SNR relative to mean noise
#     # Estimate spatial noise sigma (assuming underlying Gaussian and Half-Normal distribution)
#     # sigma = mean(noise) * sqrt(pi/2)
#     # See for example http://en.wikipedia.org/wiki/Half-normal_distribution
#
#     noise_sigma = noise_mean * sqrt(pi / 2)
#     phantom_snr = phantom_mean / noise_sigma
#     nyquist_snr = nyquist_mean / noise_sigma
#
#     # Generate detrended timeseries - add back constant offset for each ROI
#     phantom_0 = phantom_res + phantom_mean
#     nyquist_0 = nyquist_res + nyquist_mean
#     noise_0 = noise_res + noise_mean
#
#     # Create array with detrended timeseries in columns (for output by np.savetxt)
#     ts_detrend = np.array([phantom_0, nyquist_0, noise_0])
#     ts_detrend = ts_detrend.transpose()
#
#     # Create array with timeseries detrend parameters in rows for each model
#     # Parameter order : Exp amp, Exp tau, linear, const, spike count
#     stats_pars = np.row_stack([phantom_opt, nyquist_opt, noise_opt])
#
#     #
#     # Apparent motion parameters
#     #
#     print('    Analyzing motion parameters')
#     qc_mcf_parfile = os.path.join(qc_dir, 'qc_mcf.par')
#
#     if not os.path.isfile(qc_mcf_parfile):
#         print(qc_mcf_parfile + ' does not exist - exiting')
#         sys.exit(0)
#
#     # N x 6 array (6 motion parameters in columns)
#     x = np.loadtxt(qc_mcf_parfile)
#
#     # Extract displacement timeseries for each axis
#     dx = x[:, 3]
#     dy = x[:, 4]
#     dz = x[:, 5]
#
#     # Calculate max absolute displacements (in microns) for each axis
#     max_adx = (np.abs(dx)).max() * 1000.0
#     max_ady = (np.abs(dy)).max() * 1000.0
#     max_adz = (np.abs(dz)).max() * 1000.0
#
#     #
#     # Finalize stats array for writing
#     #




