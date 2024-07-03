#!/usr/bin/env python3
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

import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import periodogram
from skimage.util import montage
from skimage.exposure import rescale_intensity
import pandas as pd
from datetime import date

from .moco import total_rotation


def plot_roi_timeseries(t, s_mean_t, s_fit_t, s_detrend_t, plot_fname):
    """
    Plot spatial mean ROI signals vs time

    :param t: float array, time vector (s)
    :param s_mean_t:
    :param s_fit_t:
    :param s_detrend_t:
    :param plot_fname:
    :return:
    """

    roi_names = ['Air', 'Nyquist Ghost', 'Signal']

    fig, axs = plt.subplots(3, 1, figsize=(10, 5))

    for lc in range(0, 3):

        axs[lc].plot(t, s_mean_t[lc, :], label='Raw')
        axs[lc].plot(t, s_detrend_t[lc, :], label='Model')
        axs[lc].plot(t, s_fit_t[lc, :], label='Detrended')
        axs[lc].set_title(roi_names[lc], loc='left')
        axs[lc].grid(color='gray', linestyle=':', linewidth=1)

    # Add x label to final subplot
    axs[2].set_xlabel('Time (s)')

    handles, labels = axs[2].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3)

    # Space subplots without title overlap
    plt.tight_layout()

    # Save plot to file
    plt.savefig(plot_fname, dpi=300)

    # Close plot
    plt.close()


def plot_roi_powerspec(t, s_detrend_t, plot_fname):
    """
    Plot ROI timeseries power spectra

    :param t: float array, time vector (s)
    :param s_detrend_t:
    :param plot_fname:
    :return:
    """

    titles = ['Air (dB)', 'Nyquist Ghost (dB)', 'Signal (dB)']

    # Sampling frequency (Hz)
    fs = 1.0 / (t[1] - t[0])

    # Power spectra of detrending residual for each ROI
    f, pspec = periodogram(s_detrend_t, fs, scaling='spectrum')

    # Drop first time point (zeros)
    pspec = pspec[:, 1:]
    f = f[1:]

    fig, axs = plt.subplots(3, 1, figsize=(10, 5))

    for lc in range(0, 3):

        # Power dB relative to row max
        p = pspec[lc, :]
        p_max = np.max(p)
        if p_max < 1e-10:
            p_db = np.zeros_like(p)
        else:
            p_db = 10.0 * np.log10(p / np.max(p))

        axs[lc].plot(f, p_db)
        axs[lc].set_title(titles[lc], loc='left')
        axs[lc].grid(color='gray', linestyle=':', linewidth=1)

    # Add x label to final subplot
    axs[2].set_xlabel('Frequency (Hz)')

    # Space subplots without title overlap
    plt.tight_layout()

    # Save plot to file
    plt.savefig(plot_fname, dpi=300)

    # Close plot
    plt.close()


def plot_mopar_timeseries(moco_df, plot_fname):
    """
    Plots x, y, z displacement and rotation timeseries from MCFLIRT registrations

    :param moco_df: dataframe
        Motion correction parameters
    :param plot_fname: str
        Output plot filename
    :return:
    """

    fig, axs = plt.subplots(2, 1, figsize=(10, 5))

    # Plot axis displacements in mm
    moco_df.plot(
        x='Time_s',
        y=['Dx_mm', 'Dy_mm', 'Dz_mm'],
        kind='line',
        ax=axs[0]
    )
    axs[0].grid(color='gray', linestyle=':', linewidth=1)

    # Plot axis rotations in radians
    moco_df.plot(
        x='Time_s',
        y=['Rx_rad', 'Ry_rad', 'Rz_rad'],
        kind='line',
        ax=axs[1]
    )
    axs[1].grid(color='gray', linestyle=':', linewidth=1)

    # Space subplots without title overlap
    plt.tight_layout()

    # Save plot to file
    plt.savefig(plot_fname, dpi=300)

    # Close plot
    plt.close()


def plot_mopar_powerspec(moco_df, plot_fname):
    """
    Plot total motion power spectrum

    :param moco_df: dataframe

    :param plot_fname:
    :return:
    """

    # Extract vectors from dataframe
    t = moco_df['Time_s'].values

    # Extract moco par values as numpy arrays
    Dxyz = moco_df[['Dx_mm', 'Dy_mm', 'Dz_mm']].values
    Rxyz = moco_df[['Rx_rad', 'Ry_rad', 'Rz_rad']].values

    # Sampling frequency (Hz)
    fs = 1.0 / (t[1] - t[0])

    # Total displacement timecourse (mm)
    dtot = np.linalg.norm(Dxyz, ord=2, axis=1)

    # Total rotation timecourse (degrees)
    rtot = total_rotation(Rxyz)

    # Total motion array
    mtot = np.array([dtot, rtot])

    # Power spectra of total displacement and rotation timecourses
    f, pspec = periodogram(mtot, fs, scaling='spectrum')

    # Drop first point (zero)
    pspec = pspec[:, 1:]
    f = f[1:]

    fig, axs = plt.subplots(2, 1, figsize=(10, 5))
    titles = ['Displacement (dB)', 'Rotation (dB)']

    for lc in range(0, 2):

        # Power dB relative to row max
        p = pspec[lc, :]
        p_max = np.max(p)
        if p_max < 1e-10:
            p_db = np.zeros_like(p)
        else:
            p_db = 10.0 * np.log10(p / np.max(p))

        axs[lc].plot(f, p_db)
        axs[lc].set_title(titles[lc], loc='left')
        axs[lc].grid(color='gray', linestyle=':', linewidth=1)

    # Add x axis label to last subplot
    axs[1].set_xlabel('Frequency (Hz)')

    # Space subplots without title overlap
    plt.tight_layout()

    # Save plot to file
    plt.savefig(plot_fname, dpi=300)

    # Close plot
    plt.close()


def orthoslices(img_nii, ortho_fname, cmap='viridis', irng='default'):

    img3d = img_nii.get_fdata()

    # Intensity scaling
    if 'robust' in irng:
        vmin, vmax = np.percentile(img3d, (1, 99))
    elif 'noscale' in irng:
        nc = plt.get_cmap(cmap).N
        vmin, vmax = 0, nc
    else:
        vmin, vmax = np.min(img3d), np.max(img3d)

    fig, axs = plt.subplots(1, 3, figsize=(7, 2.4), constrained_layout=True)

    nx, ny, nz = img3d.shape
    hx, hy, hz = int(nx/2), int(ny/2), int(nz/2)

    # Extract central section for each orientation
    # Assumes RAS orientation
    m_sag = img3d[hx, :, :].transpose()
    m_cor = img3d[:, hy, :].transpose()
    m_tra = img3d[:, :, hz].transpose()

    # Use transverse image for colorbar reference
    trafig = axs[0].imshow(
        m_tra,
        cmap=plt.get_cmap(cmap),
        vmin=vmin, vmax=vmax,
        aspect='equal',
        origin='lower'
    )
    axs[0].set_title('Transverse')
    axs[0].axis('off')

    axs[1].imshow(
        m_cor,
        cmap=plt.get_cmap(cmap),
        vmin=vmin, vmax=vmax,
        aspect='equal',
        origin='lower'
    )
    axs[1].set_title('Coronal')
    axs[1].axis('off')

    axs[2].imshow(
        m_sag,
        cmap=plt.get_cmap(cmap),
        vmin=vmin, vmax=vmax,
        aspect='equal',
        origin='lower'
    )
    axs[2].set_title('Sagittal')
    axs[2].axis('off')

    plt.colorbar(trafig, ax=axs, location='right', shrink=0.75)

    # Save plot to file
    plt.savefig(ortho_fname, dpi=300)

    # Close plot
    plt.close()

    return ortho_fname


def orthoslice_montage(img_nii, montage_fname, cmap='viridis', irng='default'):

    orient_name = ['Axial', 'Coronal', 'Sagittal']

    img3d = img_nii.get_fdata()

    plt.subplots(1, 3, figsize=(7, 2.4))

    for ax in [0, 1, 2]:

        # Transpose dimensions for given orientation
        ax_order = np.roll([2, 0, 1], ax)
        s = np.transpose(img3d, ax_order)

        # Downsample to 9 images in first dimension
        nx = s.shape[0]
        xx = np.linspace(0, nx-1, 9).astype(int)
        s = s[xx, :, :]

        # Construct 3x3 montage of slices
        m2d = montage(s, fill='mean', grid_shape=(3, 3))

        # Intensity scaling
        if 'default' in irng:
            m2d = rescale_intensity(m2d, in_range='image', out_range=(0, 1))
        elif 'robust' in irng:
            pmin, pmax = np.percentile(m2d, (1, 99))
            m2d = rescale_intensity(m2d, in_range=(pmin, pmax), out_range=(0, 1))
        else:
            # Do nothing
            pass

        plt.subplot(1, 3, ax+1)
        plt.imshow(m2d,
                   cmap=plt.get_cmap(cmap),
                   aspect='equal',
                   origin='lower')
        plt.title(orient_name[ax])

        plt.axis('off')
        plt.subplots_adjust(bottom=0.0, top=0.9, left=0.0, right=1.0)

    # Remove excess space
    plt.tight_layout()

    # Save plot to file
    plt.savefig(montage_fname, dpi=300)

    # Close plot
    plt.close()


def roi_demeaned_ts(img_nii, rois_nii, residuals_fname):
    """
    TODO: Switch to ROI slice carpet plot (slices x time)
    TODO: Calculate mean signal within ROI for each slice and plot over time

    Create temporal-spatial image of demeaned voxel timecourse
    - one graymap per ROI
    - subsample voxels in each ROI to yield n_samp timeseries

    :param img_nii:
    :param rois_nii:
    :param residuals_fname: str, ROI residuals PNG filename
    :return:
    """

    # Number of voxel samples from each ROI
    n_samp = 200

    roi_name = ['Air', 'Nyquist Ghost', 'Signal']

    rois = rois_nii.get_fdata()
    s = img_nii.get_fdata()

    # Number of time points and labels
    nt = s.shape[3]

    fig, axs = plt.subplots(3, 1, figsize=(7, 9))
    fig.subplots_adjust(left=0.02, bottom=0.06, right=0.95, top=0.94, wspace=0.05)

    for lc in range(3):

        # Skip label 0 - use lc+1 to index ROI labels
        mask3d = np.array(rois == (lc+1))
        mask4d = np.tile(mask3d[:, :, :, np.newaxis], (1, 1, 1, nt))

        nx = np.sum(mask3d)

        s_xt = s[mask4d].reshape(nx, nt)

        # Downsample spatial dimension to n_samp
        inds = np.linspace(0, nx-1, n_samp).astype(int)
        s_xt_d = s_xt[inds, :]

        # Demean rows
        row_means = np.mean(s_xt_d, axis=1)
        res = s_xt_d.astype(np.float64) - np.tile(row_means[:, np.newaxis], (1, nt))

        # Find abs max of residual
        amax = np.abs(res).max()

        # Plot graymap
        pobj = axs[lc].imshow(
            res,
            vmin=-amax,
            vmax=amax,
            cmap=plt.get_cmap('viridis'),
            aspect='auto',
            origin='upper'
        )

        fig.colorbar(pobj, ax=axs[lc])

        axs[lc].set_title(roi_name[lc])
        axs[lc].set_axis_off()

    # Adjust space around plots
    plt.tight_layout()

    # Save plot to file
    plt.savefig(residuals_fname, dpi=300)

    # Close plot
    plt.close()


def metric_trend_plot(mc, metric_name, metrics_df, gridspec, past_months=12):
    """
    Plot session metric trend with median, 5th and 95th percentiles
    Add metric histogram at right

    :param mc: int, index of metric to plot
    :param metric_name: str, metric name to plot
    :param metrics_df: DataFrame, complete metric dataframe for current subject
    :param gridspec: GridSpec, pyplot grid specification
    :param past_months: int, number of past months to plot
    :return:
    """

    # Extract subframe for this metric timeseries
    df = metrics_df[['Date', metric_name, 'Outlier']]

    t1 = pd.Timestamp(date.today())
    t0 = t1 - pd.DateOffset(months=past_months)

    ax0 = plt.subplot(gridspec[mc, 0])

    marker_dict = {'Outlier': 'x', 'Inlier': 'o'}
    color_dict = {'Outlier': 'red', 'Inlier': 'palegreen'}

    for kind in marker_dict:

        inds = df['Outlier'] == kind
        xx = df[inds]['Date']
        yy = df[inds][metric_name]

        ax0.scatter(
            x=xx,
            y=yy,
            c=color_dict[kind],
            ec='black',
        )

    ax0.set_xlim(t0, t1)
    ax0.set_ylabel(metric_name, labelpad=20)
    ax0.xaxis.label.set_size(14)
    ax0.yaxis.label.set_size(14)

    # Calculate metric limits and 5/95 percentiles
    p5, p50, p95 = np.percentile(df[metric_name].values, (5, 50, 95))

    ax0.plot([t0, t1], [p5, p5], 'g:')
    ax0.plot([t0, t1], [p50, p50], 'g')
    ax0.plot([t0, t1], [p95, p95], 'g:')

    ax1 = plt.subplot(gridspec[mc, 1], sharey=ax0)
    df.hist(
        column=metric_name,
        grid=False,
        bins=20,
        orientation='horizontal',
        ec='black',
        fc='palegreen',
        ax=ax1,
    )

    # Simplify graph axes
    ax0.spines['right'].set_visible(False)
    ax0.spines['top'].set_visible(False)
    ax0.yaxis.set_ticks_position('left')
    ax0.xaxis.set_ticks_position('bottom')
    ax1.axis('off')
    ax1.set_title('')
