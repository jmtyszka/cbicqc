#!/usr/bin/env python3
"""
Lightweight QC analysis and reporting for daily phantom scans

Authors
----
Mike Tyszka, Caltech Brain Imaging Center

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
import argparse
import pkg_resources
import subprocess

from cbicqc.cbicqc import CBICQC


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Lightweight daily phantom QC analysis and reporting')
    parser.add_argument('-d', '--dir', default='.', help='BIDS QC dataset directory')
    parser.add_argument('-m', '--mode', default='phantom', help="QC Mode (phantom or live)")
    parser.add_argument('-p', '--past', default=12, type=int, help='Number of past months to summarize [12]')
    parser.add_argument('--sub', default='', help='Subject ID')
    parser.add_argument('--ses', default='', help='Session ID')

    # Parse command line arguments
    args = parser.parse_args()
    bids_dir = os.path.realpath(args.dir)
    subj_id = args.sub
    sess_id = args.ses
    mode = args.mode
    past_months = args.past

    # Read version from setup.py
    ver = pkg_resources.get_distribution('cbicqc').version

    # Splash
    print('')
    print('-----------------------------')
    print('CBIC Quality Control Analysis')
    print('-----------------------------')
    print('Version : {}'.format(ver))
    print('')
    print('BIDS Directory : {}'.format(bids_dir))
    print('Subject : {}'.format(subj_id if len(subj_id) > 0 else 'All Subjects'))
    print('Session : {}'.format(sess_id if len(sess_id) > 0 else 'All Sessions'))
    print('Summary : {} months'.format(past_months))

    # Setup QC analysis
    qc = CBICQC(bids_dir=bids_dir, subject=subj_id, session=sess_id, mode=mode, past_months=past_months)

    # Run analysis
    qc.run()

    # Clean exit
    sys.exit(0)


# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
