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
import nibabel as nb
import numpy as np
from skimage.filters import threshold_otsu
from scipy.ndimage.morphology import (binary_dilation,
                                      binary_erosion,
                                      generate_binary_structure,
                                      iterate_structure)


def roi_labels(tmean_nii):

    # Threshold method - possible future argument
    threshold_method = 'percentile'

    tmean = tmean_nii.get_data()

    # Grab mean image dimensions
    nx, ny, nz = tmean.shape

    # Signal threshold
    if 'otsu' in threshold_method:
        th = threshold_otsu(tmean)
    elif 'percentile' in threshold_method:
        th = np.percentile(tmean, 99) * 0.1
    else:
        th = np.max(tmean) * 0.1

    # Main signal mask
    signal_mask = tmean > th

    # Construct 3D binary sphere structuring element
    k = generate_binary_structure(3, 1)  # 3D, 1-connected
    # k = iterate_structure(k, iterations=1)

    # Erode signal mask once, then dilate twice (open + dilate)
    signal_mask_ero = binary_erosion(signal_mask, structure=k, iterations=1)
    signal_mask_dil = binary_dilation(signal_mask_ero, structure=k, iterations=2)

    # Create Nyquist mask by rolling eroded signal mask by FOVy/2
    nyquist_mask = np.roll(signal_mask_ero, (0, int(ny / 2), 0))

    # Exclusive Nyquist ghost mask (remove overlap with dilated signal mask)
    nyquist_only_mask = np.logical_and(nyquist_mask, np.logical_not(np.logical_and(nyquist_mask, signal_mask_dil)))

    # Create air mask
    air_mask = 1 - signal_mask_dil - nyquist_only_mask

    # Finally merge all masks into an ROI label file
    # Undefined       = 0
    # Signal          = 1
    # Nyquist Ghost   = 2
    # Air Space       = 3
    rois = np.uint8(signal_mask_ero + 2 * nyquist_only_mask + 3 * air_mask)

    rois_nii = nb.Nifti1Image(rois, tmean_nii.affine)

    return rois_nii
