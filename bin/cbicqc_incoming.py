#!/usr/bin/env python3
"""
Rename and organize Horos QC exported data in <BIDS Root>/incoming and place in <BIDS Root>/sourcedata

AUTHOR
----
Mike Tyszka, Ph.D.

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
from glob import glob
import argparse
from pathlib import Path
import pydicom
from shutil import rmtree


def main():

    parser = argparse.ArgumentParser(description='Fix subject and session directory naming in Horos output')

    parser.add_argument('-d', '--dataset', default='.',
                        help='BIDS dataset directory containing sourcedata subdirectory')

    # Parse command line arguments
    args = parser.parse_args()
    dataset_dir = os.path.realpath(args.dataset)

    incoming_dir = os.path.join(dataset_dir, 'incoming')
    sourcedata_dir = os.path.join(dataset_dir, 'sourcedata')
    qc_dir = os.path.join(sourcedata_dir, 'QC')

    # Create single QC subject
    print("Checking that QC subject exists in sourcedata")
    if os.path.isdir(qc_dir):
        print("  It does - continuning")
    else:
        print("  QC subject does not exist - creating QC subject in sourcedata")
        os.makedirs(qc_dir, exist_ok=True)

    # Loop over all Qc study directories in sourcedata
    # Expect subject/session directory names in the form "Qc_<session ID>_*/<session dir>/"
    # Move session subdirectories from Qc_*/<session dir> to Qc/<ScanDate>

    print("Scanning for incoming QC studies")

    for inc_qc_dir in glob(os.path.join(incoming_dir, 'Qc*')):

        print("")
        print("  Processing {}".format(inc_qc_dir))

        # There should be only one session subdirectory
        dlist = list(glob(os.path.join(inc_qc_dir, '*')))

        if len(dlist) > 0:

            ses_dir = dlist[0]

            # Get first DICOM file in ses_dir at any level
            first_dcm = str(list(Path(ses_dir).rglob("*.dcm"))[0])

            # Get acquisition date from DICOM header
            acq_date = acquisition_date(first_dcm)

            # Destination session directory name in QC subject folder
            dest_dir = os.path.join(qc_dir, acq_date)

            # Move and rename session subdirectory
            print('  Moving %s to %s' % (ses_dir, dest_dir))
            os.rename(ses_dir, dest_dir)

        # Delete incoming Qc_* directory
        print('  Deleting %s' % inc_qc_dir)
        rmtree(inc_qc_dir)


def acquisition_date(dcm_fname):
    """
    Extract acquisition date from DICOM header
    :param dcm_fname: DICOM filename
    :return acq_date: str, acquisition date (YYYYMMDD)
    """

    # Default return date
    acq_date = '19010101'

    if not os.path.isfile(dcm_fname):
        print('* File not found - %s' % dcm_fname)

    try:
        ds = pydicom.read_file(dcm_fname, force=True)
    except IOError:
        print("* Problem opening %s" % dcm_fname)
        raise
    except AttributeError:
        print("* Problem opening %s" % dcm_fname)
        raise

    if ds:
        acq_date = ds.AcquisitionDate
    else:
        print('* DICOM header problem - returning %s' % acq_date)

    return acq_date


if 'main' in __name__:

    main()