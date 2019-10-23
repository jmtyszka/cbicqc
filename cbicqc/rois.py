# !/usr/bin/env python
"""
QC analysis node for nipype

AUTHOR : Mike Tyszka
PLACE  : Caltech
DATES  : 2019-05-22 JMT From scratch

MIT License

Copyright (c) 2019 Mike Tyszka

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import subprocess
import pkg_resources
import nibabel as nb
import numpy as np
from scipy.ndimage.morphology import (binary_dilation,
                                      binary_erosion,
                                      generate_binary_structure)


def register_template(tmean_nii, work_dir, mode='phantom'):
    """
    Register the appropriate template to the provided tmean image
    - for phantom QC, a translation-only registration is performed
    - for in vivo QC, an affine registration is performed

    :param tmean_nii: Nifti object,
        Temporal mean image
    :param work_dir: str,
        Full path to working directory
    :param mode: str,
        QC mode, 'phantom' or 'live'
    :return:
    """

    # Save temporal mean image for use by FLIRT
    tmean_fname = os.path.join(work_dir, 'fixed.nii.gz')
    nb.save(tmean_nii, tmean_fname)

    # Link appropriate template for mode
    if 'phantom' in mode:
        dof = 6
        template_fname = pkg_resources.resource_filename(
            __name__,
            os.path.join('templates', 'fbirn_sphere.nii.gz')
        )
        labels_fname = pkg_resources.resource_filename(
            __name__,
            os.path.join('templates', 'fbirn_labels.nii.gz')
        )
    else:
        dof = 12
        template_fname = pkg_resources.resource_filename(
            __name__,
            os.path.join('templates', 'MNI152_T1_2mm.nii.gz')
        )
        labels_fname = pkg_resources.resource_filename(
            __name__,
            os.path.join('templates', 'MNI-maxprob-thr25-2mm.nii.gz')
        )

    template_xfm_fname = os.path.join(work_dir, 'template_xfm.nii.gz')
    labels_xfm_fname = os.path.join(work_dir, 'labels_xfm.nii.gz')

    fsl_dir = os.environ['FSLDIR']
    flirt_cmd = os.path.join(fsl_dir, 'bin', 'flirt')
    xfm_fname = os.path.join(work_dir, 'xfm.mat')

    # Run FLIRT registration
    print('      Registering template to subject ({} DOF)'.format(dof))
    cmd = [flirt_cmd,
           '-in', template_fname,
           '-ref', tmean_fname,
           '-out', template_xfm_fname,
           '-dof', str(dof),
           '-omat', xfm_fname,
    ]
    subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)

    # Apply resulting transform to label image
    print('      Resampling labels to subject space')
    cmd = [flirt_cmd,
           '-in', labels_fname,
           '-ref', tmean_fname,
           '-out', labels_xfm_fname,
           '-applyxfm',
           '-init', xfm_fname,
           '-interp', 'nearestneighbour',
    ]
    subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)

    # Load labels transformed to subject space
    print('      Loading resampled labels')
    labels_nii = nb.load(labels_xfm_fname)

    return labels_nii


def make_rois(labels_nii):
    """
    Organize labels and add air space and Nyquist ROIs

    :param labels_nii: Nifti object,
        Raw labels in subject space
    :return rois_nii: Nifti object,
        Integer ROI image include air and Nyquist ghost
    """

    # Extract label image
    labels_img = labels_nii.get_data().astype(np.uint)

    # Create signal mask from sum of all ROI labels
    signal_mask = labels_img > 0

    # Construct 3D binary sphere structuring element
    k = generate_binary_structure(3, 2)  # 3D, 2-connected

    # Erode signal mask x N, then dilate x 2N
    n_iter = 2
    signal_mask_ero = binary_erosion(signal_mask, structure=k, iterations=n_iter)
    signal_mask_dil = binary_dilation(signal_mask_ero, structure=k, iterations=n_iter * 2)

    # Create Nyquist mask by rolling eroded signal mask by FOVy/2
    ny = signal_mask.shape[1]
    nyquist_mask = np.roll(signal_mask_ero, int(ny / 2), axis=1)

    # Exclusive Nyquist ghost mask (remove overlap with dilated signal mask)
    nyquist_only_mask = np.logical_and(nyquist_mask, np.logical_not(np.logical_and(nyquist_mask, signal_mask_dil))).astype(np.uint)

    # Create air mask
    air_mask = (1 - signal_mask_dil - nyquist_only_mask).astype(np.uint)

    # Finally merge all masks into an ROI label file
    # Undefined       = 0
    # Air Space       = 1
    # Nyquist Ghost   = 2
    # Other ROIs      = 3, 4, 5, ...
    rois = air_mask + 2 * nyquist_only_mask + labels_img + 2 * signal_mask

    # Wrap image in a Nifti object
    rois_nii = nb.Nifti1Image(rois, labels_nii.affine)

    return rois_nii
