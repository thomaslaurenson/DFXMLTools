#!/usr/bin/env python3

"""
Author:  Thomas Laurenson
Email:   thomas@thomaslaurenson.com
Website: thomaslaurenson.com
Date:    2015/02/23

Description:
DFXML2sha1deep.py is a script that converts a DFXML report to the sha1deep
(part of the hashdeep toolset) format.

Copyright (c) 2015, Thomas Laurenson

###############################################################################
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

>>> CHANGELOG:
    0.1.0       Base functionality

"""

__version__ = "0.1.0"

import sys
import os

sys.path.append(r'../dfxml/python')
try:
    import Objects
except ImportError:
    print('Error: The DFXML Objects.py module is required to run this program')
    print('You can download from: https://github.com/simsong/dfxml')
    print('Now Exiting...')
    sys.exit(1)

################################################################################      
def process_dfxml(xmlfile):
    """ Process the target DFXML report and produce hashdeep report. """
    for (event, obj) in Objects.iterparse(xmlfile):
        if isinstance(obj, Objects.FileObject):
            process_fi(obj)

def process_fi(fi):
    sha1 = fi.sha1
    if not sha1:
        return
    print("%s  %s" % (sha1, fi.filename))

################################################################################
if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description="""
DFXML2sha1deep.py is a script that converts a DFXML report to the sha1deep
(part of the hashdeep toolset) format. The hash set is printed to standard
output (stdout), so redirect to a file to save the convereted hash set.""")
    parser.add_argument("dfxml",
                        help = "Target DFXML report")
    args = parser.parse_args()
    process_dfxml(args.dfxml)
