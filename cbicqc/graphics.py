# !/usr/bin/env python
"""
Graph plotting and image figure functions

AUTHOR : Mike Tyszka
PLACE  : Caltech
DATES  : 2019-05-31 JMT From scratch

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

import os
import numpy as np
import nibabel as nb
import pandas as pd
from scipy.optimize import least_squares
import matplotlib.pyplot as plt


def plot_roi_timeseries(s_mean_t, s_detrend_t, fit_results):

    nt = s_mean_t.shape[1]
    roi_names = ['Phantom', 'Nyquist Ghost', 'Air']

    t = np.arange(0, nt)

    fig, axs = plt.subplots(3, 1)

    for lc in range(0, 3):

        plt.subplot(3, 1, lc+1)
        plt.plot(t, s_mean_t[lc, :], t, s_detrend_t[lc, :])
        plt.title(roi_names[lc], loc='left')

    plt.show()






