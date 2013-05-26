# !/usr/bin/python
"""
dfxml_xtract.py
Extract files from image file using DFXML metadata
Author: Thomas Laurenson
Website: thomaslaurenson.com
Date: 26/05/2013
    
Functionality:
Extracts DFXML file objects from an image file
Performs hash check after file extraction

CHANGELOG:
0.1 --- Base functionality (alpha)
"""

import sys
import os
import hashlib
try:
    import dfxml
except ImportError:
    print("Error: The Python DFXML module is required to run this script")
    print("You can download from: https://github.com/simsong/dfxml")
    print("Now Exiting...")
    sys.exit(1)
    
def extract_file(fi):
    fn = fi.filename()
    print('Processing:', fn)
   
    # open image file and extract the file
    with open(image_path, 'rb') as fimage:
        for item in enumerate(fi.byte_runs()):
            offset = int(item[1].img_offset)
            len = int(item[1].len)        
            fimage.seek(offset)
            contents = fimage.read(len)
            if item[0] == 0:
                with open(fn, 'wb') as newfile:
                    newfile.write(contents)
                    newfile.close()
            else:
                with open(fn, 'ab') as newfile:
                    newfile.write(contents)
                    newfile.close()
    fimage.close()
    
    # Check extracted file by comparing file md5 with file object md5
    with open(fi.filename(), 'rb') as file:
        m = hashlib.md5()
        while True:
            block = file.read(8192)
            if not block:
                break
            m.update(block)
        hashvalue = m.hexdigest()
        print('>>> Extracted Hash =', hashvalue)
        print('>>>  Recorded Hash =', fi.md5())
        if hashvalue == fi.md5():
            print('>>> MATCH')
        elif hashvalue != fi.md5():
            print('\n *** WARNING ***\nFILE HASH MISMATCH\n')
            input('Press enter to continue...')
                    
                    
######################################################################
if(__name__=="__main__"):
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.usage =\
    """
    dfxml_xtract.py  [args] dfxml imagefile
    
    Using the metadata from DFXML file, extract each file object
    from a target image file.
    """
    parser.add_argument("dfxml",help="Specify the target DFXML file")
    parser.add_argument("image",help="Specify the target image file")
    args = parser.parse_args()
    
    # Set up output directory for extracted files
    dfxml_path = os.path.abspath(args.dfxml)
    image_path = os.path.abspath(args.image)
    dir_name = os.getcwd() + "/output"
    if os.path.isdir(dir_name):
        os.chdir(dir_name)
    else:
        os.mkdir('output')
        os.chdir('output')
    
    print("Working Dir :", os.getcwd())
    print("Target DFXML:", dfxml_path)
    print("Target IMAGE:", image_path)

    dfxml.read_dfxml(xmlfile=open(dfxml_path,'rb'),callback=extract_file)