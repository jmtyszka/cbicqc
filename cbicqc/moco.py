#!/usr/bin/env python3
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

import os
import subprocess
import numpy as np
import nibabel as nb
import pandas as pd

from scipy.ndimage.measurements import center_of_mass
from scipy.ndimage import shift
from scipy.spatial.transform import Rotation
from scipy import signal


def moco_phantom(img_nii):
    """
    Spherical QC phantom requires simpler registration approach.
    Use center of mass registration only.

    :param img_nii: Nifti object,
        4D QC time series
    :return moco_nii: Nifti object,
        Motion corrected 4D QC time series
    :return moco_pars: array,
        Motion parameter array (nt x 6)
    """

    img = img_nii.get_fdata()
    nt = img.shape[3]
    vox_mm = img_nii.header.get('pixdim')[1:4]

    # Clip intensity range to 1st, 99th percentile for robust CoM
    p1, p99 = np.percentile(img, (1, 99))
    img_clip = np.clip(img, p1, p99)

    moco_img = img.copy()
    moco_pars = np.zeros([nt, 6])

    # Reference center of mass
    com_0 = np.array(center_of_mass(img_clip[:, :, :, 0]))

    for tc in range(1, nt):

        # Center of mass of current volume
        com_t = np.array(center_of_mass(img_clip[:, :, :, tc]))

        # Center of mass shift required to register current and zeroth volumes
        com_d = com_0 - com_t

        # Translate with spline interpolation
        # Use 'nearest neighbor' mode to minimize motion x signal artifacts at image edges
        moco_img[:, :, :, tc] = shift(img[:, :, :, tc], com_d, mode='nearest')

        # Save CoM translation
        # FSL MCFLIRT convention: [rx, ry, rz, dx, dy, dz]
        moco_pars[tc, 3:6] = com_d * vox_mm

    # Create motion corrected Nifti volume
    moco_nii = nb.Nifti1Image(moco_img, img_nii.affine)

    return moco_nii, moco_pars


def moco_live(img_nii, work_dir):
    """
    MCFLIRT-based rigid body motion correction

    :param img_nii: Nifti, image object
    :param work_dir: str, working directory
    :return moco_nii: Nifti, motion corrected image object
    :return moco_pars: array, motion parameter timeseries
    """

    in_fname = os.path.join(work_dir, 'qc.nii.gz')
    out_stub = os.path.join(work_dir, 'qc_mcf')
    out_image = out_stub + '.nii.gz'
    out_pars = out_stub + '.par'

    # Save QC timeseries for MCFLIRT
    if os.path.isfile(in_fname):
        print('      * Raw QC series already exists in work directory - skipping')
    else:
        nb.save(img_nii, in_fname)

    # Check for existing moco series in work directory
    if not os.path.isfile(out_image):

        mcflirt_cmd = os.path.join(os.environ['FSLDIR'], 'bin', 'mcflirt')

        # Check that MCFLIRT binary exists
        if os.path.isfile(mcflirt_cmd):
            subprocess.run([mcflirt_cmd,
                            '-in', in_fname,
                            '-out', out_stub,
                            '-plots'])
        else:
            print('      * MCFLIRT not available - please install FSL and update your environment')

    else:

        print('      * Motion corrected QC series already exists in work directory - skipping')

    # Load motion corrected QC timeseries
    moco_nii = nb.load(out_image)

    # Import motion parameter table as a pandas dataframe
    moco_pars = np.genfromtxt(out_pars)

    return moco_nii, moco_pars


def total_rotation(rot):
    """
    FSL defaults to an Euler angle rotation representation: R = Rx * Ry * Rz
    The parameter order in the MCFLIRT .par output is [Rx Ry Rz Dx Dy Dz]
    See FSL mcflirt/mcflirt.cc, mcflirt/Globaloptions.h and mathsutils/mathsutils.cc

    :param rot: array, axis degree rotations for each volume (nt x 3) [Rx, Ry, Rz]
    :return: phi_tot: array, total degree rotation angles (nt x 1)
    """

    # Convert axis rotations from degrees to radians
    rot *= np.pi / 180.0

    nt = rot.shape[0]

    phi_tot = np.zeros([nt,])

    for tc in range(0, nt):

        phix, phiy, phiz = rot[tc, :]

        # Individual axis rotation matrices
        Rx = Rotation.from_rotvec([phix, 0, 0])
        Ry = Rotation.from_rotvec([0, phiy, 0])
        Rz = Rotation.from_rotvec([0, 0, phiz])

        # Compose rotations
        Rtot = Rx * Ry * Rz

        # Total rotation from norm of rotation vector (see scipy definition)
        phi_tot[tc] = np.linalg.norm(Rtot.as_rotvec()) * 180.0 / np.pi

    return phi_tot


def moco_postprocess(moco_pars, meta, mode='phantom'):

    # Dataframe column names
    column_names = [
        "Time_s",
        "Rx_rad",
        "Ry_rad",
        "Rz_rad",
        "Dx_mm",
        "Dy_mm",
        "Dz_mm",
        "FD_mm",
        "FD_LPF_mm"
    ]

    # Time vector (seconds)
    TR_s = meta['RepetitionTime']
    nt = moco_pars.shape[0]
    t = np.arange(0, nt).reshape(-1, 1) * TR_s

    # Calculate FD variants
    if mode == 'phantom':
        # Do not calculate FD and LPF FD for phantom QC
        fd, fd_lpf = np.zeros((nt, 1)), np.zeros((nt, 1))
    else:
        fd, fd_lpf = calc_fd(moco_pars, TR_s)

    # Create and fill numpy array
    moco_arr = np.hstack((t, moco_pars, fd, fd_lpf))

    # Construct dataframe
    moco_df = pd.DataFrame(moco_arr, columns=column_names)

    return moco_df


def calc_fd(mocopars, TR_s):
    """
    Calculate Power FD and LPF FD from 6-column mocopar array (FSL MCFLIRT format)
    NOTE: Linear LPF performed on final FD rather than individual motion parameters since rotation non-linear
    for larger angles

    Column order: Rx_rad, Ry_rad, Rz_rad, Tx_mm, Ty_mm, Tz_mm

    References:
    J. D. Power, K. A. Barnes, A. Z. Snyder, B. L. Schlaggar, and S. E. Petersen,
    “Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion,”
    Neuroimage, vol. 59, pp. 2142–2154, Feb. 2012, doi: 10.1016/j.neuroimage.2011.10.018. [Online].
    Available: http://dx.doi.org/10.1016/j.neuroimage.2011.10.018

    Gratton, C., Dworetsky, A., Coalson, R. S., Adeyemo, B., Laumann, T. O., Wig, G. S., Kong, T. S., Gratton, G.,
    Fabiani, M., Barch, D. M., Tranel, D., Dominguez, O. M.-, Fair, D. A., Dosenbach, N. U. F., Snyder, A. Z.,
    Perlmutter, J. S., Petersen, S. E. & Campbell, M. C.
    Removal of high frequency contamination from motion estimates in single-band fMRI saves data without biasing
    functional connectivity. Neuroimage 116866 (2020). doi:10.1016/j.neuroimage.2020.116866
    """

    # Rotations (radians)
    rx = mocopars[:, 0]
    ry = mocopars[:, 1]
    rz = mocopars[:, 2]

    # Translations (mm)
    tx = mocopars[:, 3]
    ty = mocopars[:, 4]
    tz = mocopars[:, 5]

    # Backward differences (forward difference + leading 0)

    drx = np.insert(np.diff(rx), 0, 0)
    dry = np.insert(np.diff(ry), 0, 0)
    drz = np.insert(np.diff(rz), 0, 0)

    dtx = np.insert(np.diff(tx), 0, 0)
    dty = np.insert(np.diff(ty), 0, 0)
    dtz = np.insert(np.diff(tz), 0, 0)

    # Total framewise displacement (Power 2012)
    r_sphere = 50.0  # mm
    fd = np.abs(dtx) + np.abs(dty) + np.abs(dtz) + r_sphere * (np.abs(drx) + np.abs(dry) + np.abs(drz))

    # Create 0.2 Hz Butterworth LPF for this TR
    b, a = butterworth_lpf(TR_s)

    # Apply forward-backward LPF to FD timeseries
    fd_lpf = signal.filtfilt(b, a, fd, axis=0)

    # Return single-column 2D arrays for hstacking
    return fd.reshape(-1, 1), fd_lpf.reshape(-1, 1)


def butterworth_lpf(TR=1.0):
    """
    Construct a 0.2 Hz low-pass Butterworth filter

    param: TR, float
        EPI TR in seconds [1.0 s]
    """

    # Sampling rate (Hz)
    fs = 1.0 / TR

    # Butterworth order
    N = 5

    # Critical frequency (Hz - same units as fs)
    fc = 0.2

    # Design filter
    b, a = signal.butter(N, fc, 'low', analog=False, output='ba', fs=fs)

    return b, a












