#!/usr/bin/env python
#
# WORK IN PROGRESS - DO NOT USE!!
#
# DICOM server query and retrieve class
#
# AUTHOR : Mike Tyszka
# PLACE  : Caltech
# DATES  : 2019-05-17 JMT From scratch
#
# This file is part of CBICQC.
#
#    CBICQC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    CBICQC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#   along with CBICQC.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2019 California Institute of Technology.

import os
import sys
import json

from pydicom.dataset import Dataset
from pynetdicom import AE

from pynetdicom import AE, StoragePresentationContexts
from pynetdicom.sop_class import _QR_CLASSES as qrc


"""
_QR_CLASSES = {
    'PatientRootQueryRetrieveInformationModelFind' : '1.2.840.10008.5.1.4.1.2.1.1',
    'PatientRootQueryRetrieveInformationModelMove' : '1.2.840.10008.5.1.4.1.2.1.2',
    'PatientRootQueryRetrieveInformationModelGet' : '1.2.840.10008.5.1.4.1.2.1.3',
    'StudyRootQueryRetrieveInformationModelFind' : '1.2.840.10008.5.1.4.1.2.2.1',
    'StudyRootQueryRetrieveInformationModelMove' : '1.2.840.10008.5.1.4.1.2.2.2',
    'StudyRootQueryRetrieveInformationModelGet' : '1.2.840.10008.5.1.4.1.2.2.3',
    'PatientStudyOnlyQueryRetrieveInformationModelFind' : '1.2.840.10008.5.1.4.1.2.3.1',
    'PatientStudyOnlyQueryRetrieveInformationModelMove' : '1.2.840.10008.5.1.4.1.2.3.2',
    'PatientStudyOnlyQueryRetrieveInformationModelGet' : '1.2.840.10008.5.1.4.1.2.3.3',
    'CompositeInstanceRootRetrieveMove' : '1.2.840.10008.5.1.4.1.2.4.2',
    'CompositeInstanceRootRetrieveGet' : '1.2.840.10008.5.1.4.1.2.4.3',
    'CompositeInstanceRetrieveWithoutBulkDataGet' : '1.2.840.10008.5.1.4.1.2.5.3',
}
"""

class QCRetriever:

    def __init__(self):

        self.load_config()
        self.test_peer()

        return

    def load_config(self):

        home_dir = os.environ.get('HOME')
        cfg_json = os.path.join(home_dir, '.__main__.py.json')

        if os.path.isfile(cfg_json):

            # Load config information
            try:
                with os.open(cfg_json, 'r') as fd:
                    cfg = json.load(fd)
            except IOError:
                print('* Could not load config from %s' % cfg_json)
                print('* Exiting')
                sys.exit(1)

    def test_peer(self):

        # Initialise the Application Entity
        ae = AE()

        # Add the storage SCP's supported presentation contexts
        ae.supported_contexts = StoragePresentationContexts

        # Implement the on_c_store callback
        def on_c_store(ds, context, info):
            # Don't store anything, just return Success
            return 0x0000

        # Start the storage SCP on port 11113
        ae.ae_title = b'QC'
        ae.on_c_store = on_c_store
        scp = ae.start_server(('', 11113), block=False)

        # Add a requested presentation context
        ae.add_requested_context(qrc['StudyRootQueryRetrieveInformationModelMove'])

        # Create out identifier (query) dataset
        ds = Dataset()

        ds.QueryRetrieveLevel = 'STUDY'

        # Unique key for PATIENT level
        ds.PatientID = 'QC'

        # Associate with peer AE at IP 127.0.0.1 and port 11112
        # Note: the peer AE must know the IP and port for our move destination
        assoc = ae.associate('131.215.9.86', 11112)

        if assoc.is_established:

            responses = assoc.send_c_move(ds, b'QC', query_model='S')

            # for (status, identifier) in responses:
            #     if status:
            #         print('C-MOVE query status: 0x{0:04x}'.format(status.Status))
            #         if status.Status in (0xFF00, 0xFF01):
            #             print(identifier)
            #     else:
            #         print('Connection timed out, was aborted or received invalid response')

            assoc.release()

        else:

            print('Association rejected, aborted or never connected')

        # Shutdown the storage SCP
        scp.shutdown()
