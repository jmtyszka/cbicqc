# !/usr/bin/env python
"""
QC analysis node for nipype

AUTHOR : Mike Tyszka
PLACE  : Caltech
DATES  : 2019-05-20 JMT Port to

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
import nibabel as nb

from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename


class QCGrabInputSpec(BaseInterfaceInputSpec):

    bids_dir = traits.Str(desc='BIDS root directory')


class QCGrabOutputSpec(TraitedSpec):

    out_files = traits.ListStr(desc='QC images')


class QCGrab(BaseInterface):

    input_spec = QCGrabInputSpec
    output_spec = QCGrabOutputSpec

    def _run_interface(self, runtime):

        from bids import BIDSLayout

        bids_dir = self.inputs.bids_dir

        print('Indexing BIDS directory')
        self._layout = BIDSLayout(root=bids_dir,
                                  validate=False,
                                  ignore=['derivatives', 'sourcedata', 'code', 'work'])

        print('Locating QC series')
        self._qc_list = self._layout.get(suffix='T2star', extensions='.nii.gz')

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["out_files"] = [os.path.abspath(x.filename) for x in self._qc_list]

        return outputs