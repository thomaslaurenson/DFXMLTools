# !/usr/bin/python
"""
dfxml_creator.py
Author: Thomas Laurenson
Website: thomaslaurenson.com
Date: 27/05/2013

Functionality:
Produce dfxml output of directories and/or files. Creates fileobjects for each file encountered, and can output the following properties:
*** File name
*** File size
*** MAC timestampts
*** Whole file hash (MD5/SHA-1)
*** Piecewise hash (MD5/SHA-1) with byte-run values

Based on: Simson Garfinkels dfxml_tool.py (https://github.com/simsong/dfxml/blob/master/python/dfxml_tool.py)
Rewritten for Python 3 with various usability changes.

CHANGELOG:
0.1 --- Base functionality (alpha)
"""

import os, sys
try:
    import MakeXML
except ImportError:
    print("Error: dfxml_creator requires the MakeXML module")
    print("Now Exiting...")
    sys.exit(1)

__version__ = "0.1"

######################################################################
if(__name__=="__main__"):
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.usage =\
    """
    dfxml_creator.py  [args] file1 [file2...]     --- Create DFXML from files
                      [args] dir1  [dir2...]      --- Create DFXML from directories
    """
    parser.add_argument("targets",help="Specify the target directory or file",nargs="+")
    parser.add_argument("-p",metavar="INTEGER",help="Specify to use piecewise hashing, followed by desired block size",default=0,type=int)
    parser.add_argument("-a","--afxml",help="Output in AFXML mode",action="store_true")
    parser.add_argument("-o",metavar="OUTPUT",help="Specify output file for dfxml (default output is stdout)")
    args = parser.parse_args()

    x = MakeXML.XML()
    stype="DFXML Directory Listing"
    sname="dfxml_creator.py"
    if args.o:
        x.open(args.o, sname, stype)
    else:
        x.open(sys.stdout, sname, stype)
    
    # Generate the dfxml file_object data for each file discovered
    for fn in args.targets:
        if os.path.isdir(fn):
            for (dirpath,dirnames,filenames) in os.walk(fn):
                for fn in filenames:
                    if args.afxml:
                        MakeXML.fi2afxml(x, os.path.join(dirpath,fn))
                    else:
                        MakeXML.fi2dfxml(x, os.path.join(dirpath,fn),args.p)
        else:
            if args.afxml:
                MakeXML.fi2afxml(x,fn)
            else:
                MakeXML.fi2dfxml(x,fn,args.p)
    x.pop("dfxml")