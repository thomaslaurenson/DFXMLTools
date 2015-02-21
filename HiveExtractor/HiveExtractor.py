#!/usr/bin/env python3

# >>>>>> DISCLAIMER <<<<<<
# This software is heavily derived from the regxml_extractor project
# originally researched and written by Alex Nelson. The project website
# is available at: https://github.com/ajnelson/regxml_extractor
# The following files from the project were used for reference:
# 1) rx_extract_hives.py
# 2) regxml_extractor.sh
#
# The original project requests the following copyright be retained:
# Copyright (c) 2012, Regents of the University of California
# All rights reserved.

"""
Author:  Thomas Laurenson
Email:   thomas@thomaslaurenson.com
Website: thomaslaurenson.com
Date:    2015/02/15

Description:
HiveExtractor.py is a script to extract Windows Registry hive files from
a target forensic image (evidence file) using a DFXML report generated
by the fiwalk program. Two outputs are produced:
1) Directory of extracted hive files
2) DFXML report of file system and file metadata for extracted hive files

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
import io
import shutil
import hashlib
import datetime
import platform
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
class HiveExtractor:
    def __init__(self, imagefile=None, xmlfile=None, outputdir=None, allocated=False):
        self.imagefile = imagefile
        self.xmlfile = xmlfile
        self.outputdir = outputdir
        self.allocated = allocated
        self.hives = list()
        self.target_fi_count = 0

    def process_target(self):
        """ Process the target image. """
        print('\n>>> Processing target image for hive files ...')
        for (event, obj) in Objects.iterparse(self.xmlfile):
            if isinstance(obj, Objects.FileObject):
                self.extract_hives(obj)
        return

    def extract_hives(self, fi):
        """ Match hives based on file names from DFXML. Hive file names are
            taken from: Windows Registry Forensics by Carvey (2011, p.18),
            which is referenced in the regxml_extractor project. """
        # If file name is None skip file object
        if fi.filename is None:
            return
        fn = fi.filename.lower()
        self.target_fi_count += 1
        if self.target_fi_count % 5000 == 0:
            print("    Processed %d files from target DFXML file" % self.target_fi_count)
        # List of known hive file names
        hive_names = ['ntuser.dat',
                      'repair/sam',
                      'repair/security',
                      'repair/software',
                      'repair/system',
                      'system32/config/sam',
                      'system32/config/security',
                      'system32/config/software',
                      'system32/config/system',
                      'system32/config/components',
                      'local settings/application data/microsoft/windows/usrclass.dat']
        # Find hive files using file name matching from fiwalk DFXML output
        for hive_name in hive_names:
            if fn.endswith(hive_name) and (self.allocated and fi.is_allocated()):
                self.extract(fi)
            elif not allocated and fn.endswith(hive_name):
                self.extract(fi)

    def extract(self, fi):
        out_fn = fi.filename + '.hive'
        out_fn = out_fn.replace('/','-').replace(' ','-')
        out_fpath = os.path.join(self.outputdir, out_fn)
        # Open output file and write file contents
        with open(out_fpath, 'wb') as f:
            contents = fi.byte_runs.iter_contents(self.imagefile)
            contents = b"".join(contents)
            f.write(contents)
        f.close()
        # Check the SHA-1 of fileobject VS extracted hive
        if fi.sha1 is not None:
            sha1 = self.sha1_file(out_fpath)
            if sha1 != fi.sha1:
                print("    Warning: SHA-1 hash mismatch for: %s" % os.path.basename(out_fpath))
        # Add extracted hive file to 'hives' list
        self.hives.append(fi)

    def sha1_file(self, fi):
        """ Helper method to calculate SHA-1 hash of extracted hive file. """
        hasher = hashlib.sha1()
        with open(fi, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def dfxml_report(self):
        """ Generate a DFXML report. """
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
                                    sources = [self.imagefile],
                                    dc = dc,
                                    files = self.hives)
        # Write a temp DFXML file, format it, then write to logfile
        temp_fi = io.StringIO(dfxml.to_dfxml())
        xml_fi = xml.dom.minidom.parse(temp_fi)
        report_fn = os.path.splitext(os.path.basename(self.imagefile))[0] + ".xml"
        report_fn = os.path.join(self.outputdir, report_fn)
        print("\n>>> DFXML Report: %s\n" % report_fn)
        with open(report_fn, 'w') as f:
            f.write(xml_fi.toprettyxml(indent="  "))

################################################################################
if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description="""
HiveExtractor.py is a script to extract Windows Registry hive files from
a target forensic image (evidence file) using a DFXML report generated
by the fiwalk program. Two outputs are produced:
1) Directory of extracted hive files
2) DFXML report of file system and file metadata for extracted hive files"""
, formatter_class = argparse.RawTextHelpFormatter)
    parser.add_argument("imagefile",
                        help = "Target disk image (e.g. target.E01)")
    parser.add_argument('outputdir',
                        help = 'Output directory')
    parser.add_argument("--dfxml",
                        metavar = 'DFXML',
                        action = 'store',
                        help = "Previously generated DFXML report output from the fiwalk tool (e.g. target.dfxml)")
    parser.add_argument("-a",
                        help = "Only extract allocated hive files",
                        action = "store_true",
                        default = False)
    parser.add_argument("-z",
                        help = "Zap (delete) the output directory if it exists",
                        action = "store_true",
                        default = False)

    args = parser.parse_args()

    imagefile = args.imagefile
    outputdir = args.outputdir
    xmlfile = args.dfxml
    allocated = args.a
    zapdir = args.z

    # Make output directory
    if os.path.exists(outputdir):
        if zapdir:
            shutil.rmtree(outputdir)
            os.makedirs(outputdir)
    elif not os.path.exists(outputdir):
        os.makedirs(outputdir)

    # Check for DFXML input, generate if not supplied
    if xmlfile == None:
        print("\n>>> No fiwalk DFXML report provided")
        print("    Running fiwalk now...")
        print("    This may take a long time depending on target disk size...")
        xmlfile = os.path.splitext(imagefile)[0] + ".xml"
        command = "fiwalk -X " + xmlfile + " " + imagefile
        sysrc = os.system(command)
        if sysrc:
            print("\nAn error occured when running fiwalk.")

    # Generate REGXML
    registry_fis = list()
    print("    -------------------------")
    print(">>> EXTRACTING REGISTRY HIVES")
    print("    -------------------------")
    he = HiveExtractor(imagefile = imagefile,
                       xmlfile = xmlfile,
                       outputdir = outputdir,
                       allocated = allocated)
    he.process_target()
    he.dfxml_report()
