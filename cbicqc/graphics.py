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
import matplotlib.pyplot as plt
from skimage.util import montage


def plot_roi_timeseries(s_mean_t, s_detrend_t, plot_fname):

    nt = s_mean_t.shape[1]
    roi_names = ['Phantom', 'Nyquist Ghost', 'Air']

    t = np.arange(0, nt)

    plt.subplots(3, 1, figsize=(10, 5))

    for lc in range(0, 3):

        plt.subplot(3, 1, lc+1)
        plt.plot(t, s_mean_t[lc, :], t, s_detrend_t[lc, :])
        plt.title(roi_names[lc], loc='left')

    # Space subplots without title overlap
    plt.tight_layout()

    # Save plot to file
    plt.savefig(plot_fname, dpi=300)


def plot_mopar_timeseries(mopars, plot_fname):
    """
    Plots x, y, z displacement and rotation timeseries from MCFLIRT registrations

    mopars columns: (dx, dy, dz, rx, ry, rz)
    Displacements in mm, rotations in degrees

    :param mopars: float array, nt x 6 motion parameters
    :param plot_fname: str, output plot filename
    :return:
    """

    nt = mopars.shape[0]
    t = np.arange(0, nt)

    plt.subplots(2, 1, figsize=(10, 5))

    plt.subplot(2, 1, 1)
    plt.plot(t, mopars[:, 0:3] * 1e3)
    plt.legend(['x', 'y', 'z'])
    plt.title('Displacement (um)', loc='left')

    plt.subplot(2, 1, 2)
    plt.plot(t, mopars[:, 3:6] * 1e3)
    plt.legend(['x', 'y', 'z'])
    plt.title('Rotation (mdeg)', loc='left')

    # Space subplots without title overlap
    plt.tight_layout()

    # Save plot to file
    plt.savefig(plot_fname, dpi=300)


def orthoslice_montage(img_nii, montage_fname):

    orient_name = ['Axial', 'Coronal', 'Sagittal']

    img3d = img_nii.get_data()

    plt.subplots(1, 3, figsize=(7, 2.4))

    for ax in [0, 1, 2]:

        # Transpose dimensions for given orientation
        ax_order = np.roll([2, 0, 1], ax)
        s = np.transpose(img3d, ax_order)

        # Downsample to 9 images in first dimension
        nx = s.shape[0]
        xx = np.linspace(0, nx-1, 9).astype(int)
        s = s[xx, :, :]

        m2d = montage(s, fill='mean', grid_shape=(3, 3))

        plt.subplot(1, 3, ax+1)
        plt.imshow(m2d,
                   cmap=plt.get_cmap('viridis'),
                   aspect='equal',
                   origin='lower')
        plt.title(orient_name[ax])

        plt.axis('off')
        plt.subplots_adjust(bottom=0.0, top=0.9, left=0.0, right=1.0)

    # Space subplots without title overlap
    # plt.tight_layout()

    # Save plot to file
    plt.savefig(montage_fname, dpi=300)

    return montage_fname







