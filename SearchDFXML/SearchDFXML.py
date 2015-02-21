#!/usr/bin/env python3

"""
Author:  Thomas Laurenson
Email:   thomas@thomaslaurenson.com
Website: thomaslaurenson.com
Date:    2015/02/21

Description:
SearchDFXML.py is a script which takes a specified keyword argument and 
searches a fileobjects filename (full path).

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
import datetime
import platform
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
class SearchDFXML:
    def __init__(self, xmlfile=None, keyword=None, output=None):
        self.xmlfile = xmlfile
        self.keyword = keyword
        self.output = output
        self.matches = list()
        self.target_fi_count = 0

    def process_dfxml(self):
        """ Process the target DFXML report. """
        print('\n>>> Processing target DFXML report ...')
        for (event, obj) in Objects.iterparse(self.xmlfile):
            if isinstance(obj, Objects.FileObject):
                self.search_dfxml(obj)
        return
        
    def search_dfxml(self, fi):
        self.target_fi_count += 1
        if self.target_fi_count % 5000 == 0:
            print("    Processed %d files from target DFXML file" % self.target_fi_count)
        if self.keyword in fi.filename.lower():
            self.matches.append(fi)
            
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
                                    sources = [self.xmlfile],
                                    dc = dc,
                                    files = self.matches)                      
        # Write a temp DFXML file, format it, then print to stdout
        temp_fi = io.StringIO(dfxml.to_dfxml())
        xml_fi = xml.dom.minidom.parse(temp_fi)
        with open(self.output, 'w') as f:
            f.write(xml_fi.toprettyxml(indent="  "))
        print('\n>>> DFXML report: %s\n' % self.output)
        
################################################################################
if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description="""
SearchDFXML.py is a script which takes a specified keyword argument and 
searches a fileobjects filename (full path).""")
    parser.add_argument("dfxml",
                        help = "Target DFXML report (e.g. target.xml)")
    parser.add_argument("output",
                        help = "Output DFXML report (e.g. results.xml)")                        
    args = parser.parse_args()

    xmlfile = args.dfxml
    output = args.output
    keyword = input("\n>>> Enter search keyword: ")
    
    search = SearchDFXML(xmlfile = xmlfile,
                         keyword = keyword,
                         output = output)
    search.process_dfxml()
    search.dfxml_report()
