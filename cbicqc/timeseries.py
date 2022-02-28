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

    qc = qc_moco_nii.get_data()

    # Temporal mean of 4D timeseries
    tmean = np.mean(qc, axis=3)
    tsd = np.std(qc, axis=3)
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
    :return: fit_results, s_detrend_t, s_fit_t
    """

    # Mean label ROI signal (n_labels x n_timepoints)
    nl, nt = s_mean_t.shape

    # Time vector
    t = np.arange(0, nt)

    s_detrend_t = np.zeros_like(s_mean_t)
    s_fit_t = np.zeros_like(s_mean_t)

    fit_results = []

    # Loop over each label ROI mean timeseries
    for lc in range(0, nl):

        s_t = s_mean_t[lc, :]

        s_min, s_max, s_mean = np.min(s_t), np.max(s_t), np.mean(s_t)
        s_rng = s_max - s_min

        # [Exp Amp, Exp Tau, Linear slope, Offset]
        x0 = [s_rng, 1, -s_rng / float(nt), s_mean]
        bounds = ([0.0, 0, -np.inf, 0],
                  [s_rng, nt, np.inf, np.inf])

        # Robust non-linear curve fit (Huber loss function)
        result = least_squares(explin, x0,
                               method='trf',
                               loss='huber',
                               bounds=bounds,
                               args=(t, s_t))

        # Fitted curve - note sign change from residual definition
        s_fit_t[lc, :] = -explin(result.x, t, 0)

        # Detrended timeseries = y_fit(t) - y(t) + mean(y(t))
        s_detrend_t[lc, :] = result.fun + s_mean

        fit_results.append(result)

    return fit_results, s_detrend_t, s_fit_t


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

    y_fit = x[0] * np.exp(-t / x[1]) + x[2] * t + x[3]

    return y - y_fit
