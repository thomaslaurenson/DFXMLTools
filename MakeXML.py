# !/usr/bin/python
"""
MakeXML.py
Description: Make DFXML from files or file_objects
Author: Thomas Laurenson
Website: thomaslaurenson.com
Date: 27/05/2013

Functionality:
Takes files and print output in DFXML format
Takes DFXML <file_object> and prints output in DFXML format

Acknowledgements:
Based on XML class from Simson Garfinkel's dfxml tool:
https://github.com/simsong/dfxml/blob/master/python/dfxml_tool.py
"""

import os
import sys
from xml.sax.saxutils import escape
try:
    import dfxml
except ImportError:
    print("Error: The Python DFXML module is required to run this script")
    print("You can download from: https://github.com/simsong/dfxml")
    print("Now Exiting...")
    sys.exit(1)

__version__ = "0.1"

class XML:
    # Class to define XML output
    def __init__(self):
        self.stack = []

    def set_outfilename(self, fn):
        self.outfilename = fn
    
    def open(self, f, sname="Unknown", stype="Unknown"):
        from datetime import datetime
        # Open the specified output (either stdout or xml file)
        if type(f) == str:
            self.f = open(f, 'w')
        else:
            self.f = f
        self.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        # Write the dfxml meatdata
        xmloutputversion = "0.3"
        self.push("dfxml",{"xmloutputversion":xmloutputversion})
        self.dublin_core({"dc:type":stype,
                       "dc:creator":sname,
                       "dc:dateCreated":datetime.now(),
                       "dc:execution_environment":"Python " + sys.version.split(" ")[0]
                       }
                      )
                      
    def dublin_core(self, dc_record):
        # Use dublin core to populate xml metadata
        dfxml_ns = {"xmlns":"http://afflib.org/fiwalk/",
            "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:dc":"http://purl.org/dc/elements/1.1/"}
        self.push("metadata",dfxml_ns,attrib_delim="\n  ")
        for (n,v) in dc_record.items():
            if v != None:
                self.xmlout(n,v)
        self.pop("metadata")
        self.write("\n")
        
    def push(self, tag, attribs={}, attrib_delim=" "):
        # Enter an XML block, with optional attributes on the tag
        self.tagout(tag,attribs=attribs,attrib_delim=attrib_delim,newline=True)
        self.stack.append(tag)

    def pop(self, v=None):
        # Leave an XML block
        if v: assert v == self.stack[-1]
        self.tagout("/"+self.stack.pop(),newline=True)

    def tagout(self, tag,attribs={}, attrib_delim=" ", newline=None):
        # Outputs a plain XML tag and optional attributes
        self.f.write("<%s" % tag)
        if attribs:
            self.f.write(" ")
            count = len(attribs)
            for (n,v) in attribs.items():
                self.f.write("%s='%s'" % (n,escape(v)))
                count -= 1
                if count>0: self.f.write(attrib_delim)
        self.f.write(">")
        if newline: self.f.write("\n")

    def xmlout(self, tag, value, attribs={}):
        # Output an XML tag and its value
        self.tagout(tag,attribs,newline=False)
        self.write(escape(str(value)))
        self.write("</%s>\n" % tag)

    def write(self, s):
        self.f.write(s)

""" Method to create a DFXML block from a file object (fo) """
def fo2dfxml(x, fo):
    # Write file object properties to dfxml
    x.push("fileobject")
    x.xmlout("filename",fo.filename())
    x.xmlout("filesize",fo.filesize())
    x.xmlout("partition",fo.partition())
    x.xmlout("alloc",fo.allocated())
    x.xmlout("inode",fo.inode())
    
    # Write out timestamp for XML (if they exist)
    if fo.mtime() != None:
        x.xmlout("mtime",fo.mtime(),{"format":"time_t"})
    if fo.atime() != None:
        x.xmlout("atime",fo.atime(),{"format":"time_t"})
    if fo.ctime() != None:
        x.xmlout("ctime",fo.ctime(),{"format":"time_t"})
    if fo.crtime() != None:
        x.xmlout("crtime",fo.crtime(),{"format":"time_t"})
    
    # Write file object byte_runs
    x.push("byte_runs")
    for run in fo.byte_runs():
        try: 
            file_offset = run.file_offset
        except AttributeError: file_offset = None
        try:
            fs_offset = run.fs_offset
        except AttributeError: fs_offset = None
        try:
            img_offset = run.img_offset
        except AttributeError: img_offset = None
        try:
            len = run.len
            if len == None:
                try:
                    len = run.uncompressed_len
                except AttributeError: len = None
        except AttributeError: len = None
        x.write("<byte_run file_offset='%r' fs_offset='%r' img_offset='%r' len='%r'/>\n" % (file_offset,fs_offset,img_offset,len))
    x.pop("byte_runs")

    # Write file object hash value
    x.write("<hashdigest type='MD5'>%s</hashdigest>\n" % fo.md5())
    x.write("<hashdigest type='SHA1'>%s</hashdigest>\n" % fo.sha1())
    x.pop("fileobject")

""" Method to create a DFXML block from a file object (fo)
    Produces simplified output specifically for Application Footprint XML """
def fo2afxml(x, fo):
    # Write file object properties to Application Footprint XML
    x.push("fileobject")
    x.xmlout("filename",fo.filename())
    x.xmlout("filesize",fo.filesize())
    x.write("<hashdigest type='MD5'>%s</hashdigest>\n" % fo.md5())
    x.write("<hashdigest type='SHA1'>%s</hashdigest>\n" % fo.sha1())
    x.pop("fileobject")
    
""" Method to create a DFXML block from an actual file (fi) """
def fi2dfxml(x, fi, piecewise=0, fs_offset=0, img_offset=0):
    import hashlib
    # Try and open the file for processing
    try:
        f = open(fi, 'rb')
    except IOError as e:
        sys.stderr.write("%s: %s" % (fi,str(e)))
        return
    
    # Write file object properties to dfxml
    x.push("fileobject")
    x.xmlout("filename",os.path.basename(fi))
    x.xmlout("filesize",os.path.getsize(fi))
    x.xmlout("mtime",int(os.path.getmtime(fi)),{'format':'time_t'})
    x.xmlout("atime",int(os.path.getatime(fi)),{'format':'time_t'})
    x.xmlout("ctime",int(os.path.getctime(fi)),{'format':'time_t'})

    # Populate byte_runs tag (only write file_offset & length values)
    if piecewise == 0:
        file_offset = 0
        length = os.path.getsize(fi)
        x.push("byte_runs")
        x.write("<byte_run file_offset='%d' fs_offset='%d' img_offset='%d' len='%d'/>\n" % (file_offset,fs_offset,img_offset,length))
        x.pop("byte_runs")
    
    # Define the hash algorithms
    md5_all  = hashlib.md5()
    sha1_all = hashlib.sha1()
    
    # Determine if piecewise hashing is requested
    if piecewise != 0:
        block_size = piecewise
        x.push("byte_runs")
        # Read the file based on block size and then conduct piecewise hash
        start = 0
        while True:
            buf = f.read(block_size)
            if buf == b'':
                break
            md5_all.update(buf)
            sha1_all.update(buf)
            if piecewise:
                x.write("<byte_run file_offset='%d' len='%d'>" % (start,len(buf)))
                md5_part = hashlib.md5()
                md5_part.update(buf)
                x.write("<hashdigest type='MD5'>%s</hashdigest>" % md5_part.hexdigest())
                sha1_part = hashlib.sha1()
                sha1_part.update(buf)
                x.write("<hashdigest type='SHA1'>%s</hashdigest>" % sha1_part.hexdigest())
                x.write("</>\n")
            start += len(buf)
        x.pop("byte_runs")
    
    block_size = 128*md5_all.block_size
    while True:
        buf = f.read(block_size)
        if buf == b'':
            break
        md5_all.update(buf)
        sha1_all.update(buf)        
    # Write the whole file hash value
    x.write("<hashdigest type='MD5'>%s</hashdigest>\n" % (md5_all.hexdigest()))
    x.write("<hashdigest type='SHA1'>%s</hashdigest>\n" % (sha1_all.hexdigest()))
    x.pop("fileobject")
    
def fi2afxml(x, fi):
    # Write file object properties to Application Footprint XML
    import hashlib
    try:
        f = open(fi, 'rb')
    except IOError as e:
        sys.stderr.write("%s: %s" % (fi,str(e)))
        return

    x.push("fileobject")
    x.xmlout("filename",os.path.dirname(fi) + "\\" + os.path.basename(fi))
    x.xmlout("filesize",os.path.getsize(fi))

    md5  = hashlib.md5()
    sha1 = hashlib.sha1()
    block_size = 128*md5.block_size
    while True:
        buf = f.read(block_size)
        if buf == b'':
            break
        md5.update(buf)
        sha1.update(buf)
    x.write("<hashdigest type='MD5'>%s</hashdigest>\n" % (md5.hexdigest()))
    x.write("<hashdigest type='SHA1'>%s</hashdigest>\n" % (sha1.hexdigest()))
    x.pop("fileobject")