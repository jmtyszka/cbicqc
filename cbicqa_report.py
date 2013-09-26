#!/opt/local/bin/python
# Create daily QA HTML report from detrended data
#
# AUTHOR : Mike Tyszka
# PLACE  : Caltech
# DATES  : 09/25/2013 JMT From scratch
#
# This file is part of CBICQA.
#
#    CBICQA is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    CBICQA is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#   along with CBICQA.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2013 California Institute of Technology.

import sys
import os
import numpy as np
from pylab import *
from scipy.optimize import curve_fit

# Main function
def main():
    
    # Report python version
    # print(sys.version_info)
    # print(sp.__version__)
    
    # QA root directory
    qa_root = '/Library/Server/Web/Data/Sites/Default/QA'
    
    # Get QA date from command line args
    if len(sys.argv) >= 2:
        qa_dir = sys.argv[1]
    else:
        qa_dir = os.getcwd()

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
