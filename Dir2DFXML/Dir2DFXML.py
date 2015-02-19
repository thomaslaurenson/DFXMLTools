#!/usr/bin/env python3

"""
Author:  Thomas Laurenson
Email:   thomas@thomaslaurenson.com
Website: thomaslaurenson.com
Date:    2015/02/19

Description:
Dir2DFXML.py is a script that creates a DFXML report from a directory.

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
import hashlib
import datetime
import platform
import glob
import io
import xml.dom.minidom

sys.path.append(r'../dfxml/python')
try:
    import Objects
except ImportError:
    print('Error: The DFXML Objects.py module is required to run this program')
    print('You can download from: https://github.com/simsong/dfxml')
    print('Now Exiting...')
    sys.exit(1)

################################################################################
def process_directory(target_dir, recursive, basename):
    """ Process the target directory and produce DFXML report. """
    dc = {"name" : os.path.basename(__file__),
          "type" : "Hash List",
          "date" : datetime.datetime.now().isoformat(),
          "os_sysname" : platform.system(),
          "os_sysname" : platform.system(),
          "os_release" : platform.release(),
          "os_version" : platform.version(),
          "os_host" : platform.node(),
          "os_arch" : platform.machine()}
    dfxml = Objects.DFXMLObject(command_line = " ".join(sys.argv),
                                sources = [target_dir],
                                dc = dc)
    fis = list()
    # Scan for files recursively if specified
    if recursive:
        for root, dirnames, filenames in os.walk(target_dir):
            for filename in filenames:
                fis.append(os.path.join(root, filename))
    else:
        fis = glob.glob(target_dir + "/*")
    for fi in fis:
        if os.path.isfile(fi):
            fo = Objects.FileObject()
            # Only include basename if requested
            if basename:
                fo.filename = os.path.basename(fi)
            else:
                fo.filename = fi
            # Populate the FileObject using a os.stat() call
            fo.populate_from_stat(os.stat(fi))
            fo.sha1 = sha1_file(fi)
            fo.md5 = md5_file(fi)
            dfxml.append(fo)
    # Write a temp DFXML file, format it, then print to stdout
    temp_fi = io.StringIO(dfxml.to_dfxml())
    xml_fi = xml.dom.minidom.parse(temp_fi)
    print(xml_fi.toprettyxml(indent="  "))

def sha1_file(fi):
    """ Helper method to calculate SHA-1 hash of a data file. """
    hasher = hashlib.sha1()
    with open(fi, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def md5_file(fi):
    """ Helper method to calculate MD5 hash of a data file. """
    hasher = hashlib.md5()
    with open(fi, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

################################################################################
if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description="""
Dir2DFXML.py is a script that creates a DFXML report from a directory.""")
    parser.add_argument("directory",
                        help = "Target directory")
    parser.add_argument("-r",
                        help = "Recursively scan",
                        action = "store_true")
    parser.add_argument("-b",
                        help = "Only store file basename",
                        action = "store_true")
    args = parser.parse_args()
    process_directory(args.directory, args.r, args.b)
