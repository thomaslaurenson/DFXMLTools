# !/usr/bin/python
"""
dfxml2hashdeep.py
Convert DFXML to Hashdeep HashSet format
Author: Thomas Laurenson
Website: thomaslaurenson.com
Date: 26/05/2013
    
Functionality:
Extracts DFXML metadata to produce a Hashdeep DataSet

CHANGELOG:
0.1 --- Base functionality (alpha)
"""

import os
import csv
try:
    import dfxml
except ImportError:
    print("Error: The Python DFXML module is required to run this script")
    print("You can download from: https://github.com/simsong/dfxml")
    print("Now Exiting...")
    sys.exit(1)

def process_file(fi):
    size.append(fi.filesize())
    md5.append(fi.md5())
    filename.append(fi.filename())
    if args.sha1: sha1.append(fi.sha1())
                    
                    
######################################################################
if(__name__=="__main__"):
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.usage =\
    """
    dfxml2hashdeep.py  [args] dfxml
    
    Create Hashdeep HashSet using DFXML metadata.
    """
    parser.add_argument("dfxml",help="Specify the target DFXML file")
    parser.add_argument("-s","--sha1",help="Include SHA-1 hash values in HashSet",action="store_true")
    args = parser.parse_args()

    print("\n>>> Processing:", args.dfxml)
    # Set up CSV output
    hs_name = os.path.splitext(os.path.basename(args.dfxml))[0]
    hs_name = hs_name + '.csv'
    print("\n>>> Writing HashSet to:", hs_name)
    
    csv_out = open(hs_name, 'w', newline='')
    writer = csv.writer(csv_out)
    # Write out HashSet header
    writer.writerow(["%%%% HASHDEEP-1.0"])
    if args.sha1:
        writer.writerow(["%%%% size","md5","sha1","filename"])
    else:
        writer.writerow(["%%%% size","md5","filename"])
    writer.writerow(["## HashSet created from " + args.dfxml])
    writer.writerow(["## HashSet created using dfxml2hashdeep.py"])
    
    # Set up lists for HashSet values
    size = []
    md5 = []
    filename = []
    if args.sha1: sha1 = []
    
    # Read DFXML file for metadata values
    dfxml.read_dfxml(xmlfile=open(args.dfxml,'rb'),callback=process_file)
    
    # Write out the lists to the HashSet
    if args.sha1:
        for row in zip(size,md5,sha1,filename):
            writer.writerow(row)
    else:
        for row in zip(size,md5,filename):
            writer.writerow(row)
    csv_out.close()