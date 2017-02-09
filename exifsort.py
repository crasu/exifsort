#!/usr/bin/env python

import os
import hashlib
import simplejson
from optparse import OptionParser
from datetime import datetime, date, time
import re
import shutil
import errno
import simplejson
import subprocess

def message(msg):
    print(msg)

class FileHashList(dict):

    def hashpath(self, path):
        os.path.walk(path, self._walk, None)

    def bin_compare(self, file1, file2):
        aFile = file(file1, 'r')
        bFile = file(file2, 'r')
        aCont = aFile.read()
        bCont = bFile.read()

        return (aCont == bCont)

    def _walk(self, arg, dirname, names):
        for f in names:
            filename = os.path.join(dirname, f)
            if(os.path.isfile(filename)):
                h = self._hash(filename)
                if(h):
                    if(self.has_key(h)):
                        if(self.bin_compare(filename, self[h])):
                            message("found duplicate file " + filename + " and " + self[h])
                    else:
                        self[h] = filename

    def _hash(self, fileName):
        if not os.path.isfile(fileName):
            return None
        aFile = file(fileName, 'r')
        hasher = hashlib.md5()
        hasher.update(aFile.read(8192))
        return hasher.digest()

def get_exif_date(exiftags, key):
    try:
        if(exiftags.has_key(key)):
            return datetime.strptime(exiftags[key], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        pass
    return None

def parse_exif(filename):
    output = subprocess.Popen(["exiftool", "-json" , filename], stdout=subprocess.PIPE).communicate()[0]
    return simplejson.loads(unicode(output, 'latin1', 'ignore'))[0]

def get_new_filename(filename, destdir):
    exiftags = parse_exif(filename)
    
    dt = get_exif_date(exiftags, 'DateTimeOriginal')
    if(not(dt)):
        dt = get_exif_date(exiftags, 'DateTime')
    if(not(dt)):
        dt = get_exif_date(exiftags, 'ModifyDate')

    if(not(dt)):
        message("Fallback: " + filename)
        sr = os.stat(filename)
        dt = datetime.fromtimestamp(sr.st_mtime)

    return os.path.join(destdir, dt.strftime("%Y/%m"), dt.strftime("IMG-%Y-%m-%d-%H-%M-%S"))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise


def walker(destdir, dirname, filenames):
    for f in filenames:
        filename = os.path.join(dirname, f)
        if(os.path.isfile(filename)):
            ext = re.search("/[^/]*(\.[^\.]+)$", filename)
            if(ext):
                ext = ext.group(1)
            else:
                ext = ""
            try:
                if(ext):
                    new_name = get_new_filename(filename, destdir) + ext
                    message("copy: " + filename + " " + new_name)
                    mkdir_p(os.path.dirname(new_name))
                    shutil.copy2(filename, new_name)
            except ValueError:
                message("ignoring: " + filename)


def check_dups(origdir, destdir):
    fhl = FileHashList()

    message("hashing: " + origdir)
    fhl.hashpath(origdir)

    message("hashing: " + destdir)
    fhl.hashpath(destdir)

def main():
    usage = "usage: %prog [options] orig_directory dest_directory"
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    if(len(args) != 2):
        parser.print_help()
        return    
    (origdir, destdir) = args

    check_dups(origdir, destdir)
    os.path.walk(origdir, walker, destdir)


main()
