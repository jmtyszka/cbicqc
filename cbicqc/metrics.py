# !/usr/bin/env python
"""
CBICQC quality metrics

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
from scipy.optimize import least_squares
from scipy.signal import medfilt
import nibabel as nb

def metrics():

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

    metrics = dict()

    return metrics




