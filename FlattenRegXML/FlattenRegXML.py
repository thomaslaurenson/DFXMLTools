#!/usr/bin/env python3

"""
Author:  Thomas Laurenson
Email:   thomas@thomaslaurenson.com
Website: thomaslaurenson.com
Date:    2015/02/19

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

import os
import sys
sys.path.append(r'../dfxml/python')
import dfxml
import Objects

__version__ = "0.1.0"

class xml_reader:
    def __init__(self):
        self.cdata = None
        self.tagstack = ['xml']

    def _char_data(self, data):
        """Handles XML data"""
        if self.cdata != None:
            self.cdata += data

    def process_xml_stream(self,xml_stream,callback,preserve_fis=False):
        "Run the reader on a given XML input stream"
        self.callback = callback
        self.preserve_fis = preserve_fis
        self.fi_history = []
        import xml.parsers.expat
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler  = self._start_element
        p.EndElementHandler    = self._end_element
        p.CharacterDataHandler = self._char_data
        p.ParseFile(xml_stream)

class regxml_reader_Objects(xml_reader):
    def __init__(self,flags=None):
        self.flags = flags
        xml_reader.__init__(self)
        self.objectstack = []
        self.registry_object = None
        self.nonce = 0

    def _start_element(self, name, attrs):
        new_object = None
        if name in ["msregistry", "hive"]:
            new_object = dfxml.registry_object()
            self.objectstack.append(new_object)
            self.registry_object = new_object
        elif name in ["key", "node"]:
            new_object = Objects.CellObject()
            new_object.name_type = "k"
            if attrs.get("root", None) == "1":
                new_object.root = True
            else:
                new_object.root = False
            if len(self.objectstack) > 1:
                new_object.parent_object = self.objectstack[-1]
            #Sanity check: root key implies no parent
            if new_object.root:
                assert new_object.parent_object == None
            #Sanity check: no parent implies root key
            if new_object.parent_object == None:
                assert new_object.root == True
            #Define new_object.name
            name_data = attrs.get("name")
            if name_data == None:
                new_object.basename = "__DFXML_NONCE_" + str(self.nonce)
                self.nonce += 1
            else:
                enc = attrs.get("name_encoding")
                if enc == "base64":
                    new_object.basename = safe_b64decode(name_data)
                else:
                    new_object.basename = name_data
            if new_object.parent_object == None:
                new_object.cellpath = "\\" + new_object.basename
            else:
                new_object.cellpath = new_object.parent_object.cellpath + "\\" + new_object.basename
            self.objectstack.append(new_object)
        elif name in ["value"]:
            new_object = Objects.CellObject()
            new_object.parent_object = self.objectstack[-1]
            # Set cell name type
            new_object.name_type = "v"
            # Get then set the value data type
            data_type = attrs.get("type", None)
            if data_type == "none" and attrs.get("encoding", None) == "base64":
                new_object.data_type = "REG_SZ"
            elif data_type == "unknown":
                new_object.data_type = "REG_NONE"
            elif data_type == "string-list":
                new_object.strings = []
                new_object.data_type = "REG_MULTI_SZ"
            elif data_type == "string":
                new_object.data_type = "REG_SZ"
            elif data_type == "int32":
                new_object.data_type = "REG_DWORD"
            elif data_type == "int64":
                new_object.data_type = "REG_QWORD"
            elif data_type == "expand":
                new_object.data_type = "REG_EXPAND_SZ"
            elif data_type == "binary":
                new_object.data_type = "REG_BINARY"
            elif data_type == "resource-requirements":
                new_object.data_type = "REG_FULL_RESOURCE_DESCRIPTOR"
            elif data_type == "resource-list":
                new_object.data_type = "REG_RESOURCE_LIST"
            else:
                new_object.data_type = data_type
            #Store decoded name
            if attrs.get("default", None) == "1":
                new_object.basename = "Default"
                if attrs.get("name", attrs.get("key", None)) is not None:
                    pass
            else:
                enc = attrs.get("name_encoding", attrs.get("key_encoding"))
                name_data = attrs.get("name", attrs.get("key",None))
                if enc == "base64":
                    try:
                        new_object.basename = base64.b64decode(name_data.encode("ascii")).decode("unicode_escape")
                    except:
                        sys.stderr.write("name_data={}  type={}\n".format(name_data,type(name_data)))
                        raise
                else:
                    new_object.basename = name_data
            new_object.cellpath = new_object.parent_object.cellpath + "\\" + new_object.basename
            #Store decoded value
            new_object.data = self.decoded_value(attrs)
            self.objectstack.append(new_object)
        elif name in ["mtime"]:
            self.cdata = ""
        elif name in ["string"]:
            self.cdata = ""
        elif name in ["byte_runs"]:
            pass
        elif name in ["byte_run"]:
            parent = self.objectstack[-1]
            byte_run = Objects.ByteRun(file_offset=attrs.get("file_offset"), len=attrs.get("len"))
            run_list = [byte_run]
            byte_runs = Objects.ByteRuns(run_list = run_list)
            parent.byte_runs = byte_runs
        else:
            raise ValueError("regxml_reader_Objects._start_element: Don't know how to start element %s.\n" % name)
        if new_object != None:
            new_object.registry_handle = self.registry_object

    def decoded_value(self, attrs):
        value_data = attrs.get("value", None)
        if value_data:
            value_encoding = attrs.get("encoding", attrs.get("value_encoding"))
##            if value_encoding == "base64":
##                print("B4",type(value_data))
##                print("B4",value_data)
##                value_data = bytes(value_data,encoding='ascii')
##                value_data = base64.b64decode(value_data)
##                value_data = value_data.decode("ascii", errors='ignore')
##                print("AF",type(value_data))
##                print("AF",value_data)
##                return value_data
##            else:
            return value_data
        else:
            return None

    def _end_element(self, name):
        if name in ["msregistry","hive"]:
            pass
        elif name in ["key","node"]:
            finished_object = self.objectstack.pop()
            #Add finished object to object index
            if finished_object.cellpath in self.registry_object.object_index:
                raise ValueError("regxml_reader_Objects._end_element:  Same key path found more than once: " +
                                 finished_object.cellpath)
            self.registry_object.object_index[finished_object.cellpath] = finished_object
            self.callback(finished_object)
        elif name in ["mtime"]:
            self.objectstack[-1].mtime = dfxml.dftime(self.cdata)
            self.cdata = None
        elif name in ["value"]:
            finished_object = self.objectstack.pop()
            if finished_object.data == None:
                finished_object.data = self.cdata
            self.callback(finished_object)
        elif name in ["string"]:
            value_object = self.objectstack[-1]
            if value_object.strings == None:
                raise ValueError("regxml_reader_Objects._end_element:  parsing error, string element found, but parent's type can't support a string list.")
            value_object.strings.append(self.cdata)
            self.cdata = None
        elif name in ["byte_runs","byte_run"]:
            pass
        else:
            raise ValueError("regxml_reader_Objects._end_element: Don't know how to end element %s.\n" % name)

def read_regxml_Objects(xmlfile=None,flags=0,callback=None):
    """Processes an image using expat, calling a callback for node encountered."""
    import xml.parsers.expat
    if not callback:
        raise ValueError("callback must be specified")
    if not xmlfile:
        raise ValueError("regxml file must be specified")
    r = regxml_reader(flags=flags)
    try:
        r.process_xml_stream(xmlfile,callback)
    except xml.parsers.expat.ExpatError as e:
        stderr.write("XML parsing error for file \"" + xmlfile.name + "\".  Object stack:\n")
        for x in r.objectstack:
            stderr.write(str(x) + "\n")
        stderr.write("(Done.)\n")
        raise e
    return r

def cell_callback(cell):
    hive.append(cell)

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='''FlattenRegXML.py''')
    parser.add_argument("regxml",
                        help = "Target RegXML file")
    args = parser.parse_args()

    regxml_filename = args.regxml
    regxml = Objects.RegXMLObject(command_line = " ".join(sys.argv),                              program = os.path.basename(__file__),                              program_version = __version__)
    hive = Objects.HiveObject(filename = regxml_filename)

    read_regxml_Objects(xmlfile = open(regxml_filename, 'rb'),
                        callback = cell_callback)

    regxml.append(hive)
    print(regxml.to_regxml())
