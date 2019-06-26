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

import os
import subprocess
import numpy as np
import nibabel as nb
from scipy.ndimage.measurements import center_of_mass
from scipy.ndimage import shift
from scipy.spatial.transform import Rotation


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

    img = img_nii.get_data()
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

    # Save QC timeseries for MCFLIRT
    nb.save(img_nii, in_fname)

    mcflirt_cmd = os.path.join(os.environ['FSLDIR'], 'bin', 'mcflirt')
    subprocess.run([mcflirt_cmd,
                    '-in', in_fname,
                    '-out', out_stub,
                    '-plots'])

    # Load motion corrected QC timeseries
    moco_nii = nb.load(out_stub + '.nii.gz')
    moco_pars = np.genfromtxt(out_stub + '.par')

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












