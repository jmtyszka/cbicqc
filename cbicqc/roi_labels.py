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
from skimage.filters import threshold_otsu

from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (BaseInterface,
                                    BaseInterfaceInputSpec,
                                    File,
                                    TraitedSpec)


class ROILabelsInputSpec(BaseInterfaceInputSpec):

    mean_img = File(exists=True,
                    desc='Motion corrected 3D mean image',
                    mandatory=True)


class ROILabelsOutputSpec(TraitedSpec):

    roi_labels = File(exists=False, desc="Phantom ROI labels")


class ROILabels(BaseInterface):

    input_spec = ROILabelsInputSpec
    output_spec = ROILabelsOutputSpec

    def _run_interface(self, runtime):

        import numpy as np
        from scipy.ndimage.morphology import (binary_dilation,
                                              binary_erosion,
                                              generate_binary_structure,
                                              iterate_structure)

        # Threshold method - possible future argument
        threshold_method = 'percentile'

        mean_fname = self.inputs.mean_img

        # Load temporal mean 3D image
        mean_nii = nb.load(mean_fname)
        mean_img = np.array(mean_nii.get_data())

        # Grab mean image dimensions
        nx, ny, nz = mean_img.shape

        # Signal threshold
        if 'otsu' in threshold_method:
            th = threshold_otsu(mean_img)
        elif 'percentile' in threshold_method:
            th = np.percentile(mean_img, 99) * 0.1
        else:
            th = np.max(mean_img) * 0.1

        # Main signal mask
        signal_mask = mean_img > th

        # Construct 3D binary sphere structuring element, radius 5 voxels
        k0 = generate_binary_structure(3, 2)
        k = iterate_structure(k0, 5)

        # Erode signal mask once, then dilate twice
        signal_mask_ero = binary_erosion(signal_mask, structure=k, iterations=1)
        signal_mask_dil = binary_dilation(signal_mask_ero, structure=k, iterations=2)

        # Create Nyquist mask by rolling dilated signal mask by FOVy/2
        nyquist_mask = np.roll(signal_mask_dil, (0, int(ny/2), 0))

        # Remove overlap from Nyquist ghost mask by XORing with dilated signal mask
        xor_mask = np.logical_xor(nyquist_mask, signal_mask_dil)

        # Create air mask
        air_mask = 1 - signal_mask_dil - xor_mask

        # Finally merge all masks into an ROI label file
        # Undefined       = 0
        # Signal          = 1
        # Nyquist Ghost   = 2
        # Air Space       = 3
        roi_labels_img = signal_mask + 2 * nyquist_mask + 3 * air_mask

        # Save ROI labels
        roi_labels_nii = nb.Nifti1Image(roi_labels_img, mean_nii.get_affine())
        roi_labels_fname = self._roi_labels_fname()
        nb.save(roi_labels_nii, roi_labels_fname)

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs['roi_labels'] = self._roi_labels_fname()

        return outputs

    def _roi_labels_fname(self):

        _, stub, _ = split_filename(self.inputs.mean_img)
        return os.path.abspath(stub + '_rois.nii.gz')
