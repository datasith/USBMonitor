"""
  09/01/2015
  Author: Makerbro
  Platforms: Raspberry Pi (Raspbian)
  Language: Python
  File: util.py
  ------------------------------------------------------------------------
  Description: 
  Utility functions for usbmonitor.
  ------------------------------------------------------------------------
  License:
  Beerware License; if you find the code useful, and we happen to cross 
  paths, you're encouraged to buy us a beer. The code is distributed hoping
  that you in fact find it useful, but  without warranty of any kind.
"""

import json
import datetime
import time
import os,os.path
import codecs
import subprocess

def getMountPoint(devid):
    """ find out the mount point given a device path """
    for mount in codecs.open('/proc/mounts'):
        dev, mountpoint, fstype = mount.split()[:3]
        if dev.decode('ascii') == devid:
            return mountpoint.decode('unicode_escape')
    return None

def getPartitions():
    """ gets a list of sd?? partitions like sda1,sda2,sdb1,sdc1"""
    devlist=open("/proc/partitions").read().strip().split("\n")[2:]
    devlist=map(lambda x:x.split()[-1],devlist)
    return [dev for dev in devlist if len(dev)==4 and dev[0:2]=="sd"]

def mountPartition(dev,mnt):
    p = subprocess.Popen(["mount","-t","auto",dev,mnt],
                         stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    time.sleep(1.5)
    if not os.path.ismount(mnt):
        out, err = p.communicate()
        raise IOError(out.strip('\n')) 

def unmountPartition(dev,mnt):
    p = subprocess.Popen(["umount",dev],
                         stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    p.wait()
    time.sleep(1.5)
    out, err = p.communicate()
    # If it's still mounted raise an IOError!
    if os.path.ismount(mnt):
        raise IOError(err) 

def cleanupDirectory(directory):
    p = subprocess.Popen(["rm","-rf",directory],
                         stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    out, err = p.communicate()

def copyFiles(src,dst):
    p = subprocess.Popen(["cp","-r",src,dst],
                         stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE)
    p.wait()
    out, err = p.communicate()

def loadConfig(fname):
    """ load a json config file, use *.sample if it does not exist """
    if not os.path.isfile(fname):
        import shutil
        shutil.copy(fname+".sample",fname)
    with open(fname) as jsonfile:
        try:
            config = json.load(jsonfile)
        except:
            print("FATAL ERROR: errors in config file")
            raise
    formatdict(config,config)
    return config

def relpathjoin(a,b):
    """ join(/mountpoint, /DCIM) returns /mountpoint/DCIM in contrast to os.path.join"""
    return os.path.join(a,b.lstrip("/"))

def getVersion():
    from subprocess import check_output as run
    return int(run("git rev-list HEAD --count",shell=True).decode('utf-8'))

def initLogger(config):
    """ create a file logger """
    import logging
    import logging.handlers
    loggername = config['devicename']
    logger = logging.getLogger(loggername)
    if not os.path.exists("log"):
        os.mkdir("log")
    filelog = logging.handlers.RotatingFileHandler(
            "log/"+loggername+".log",
            maxBytes=1024*1024,
            backupCount=20)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s|%(name)s|%(levelname)s|%(message)s')
    filelog.setFormatter(formatter)
    console.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    filelog.setLevel(logging.DEBUG)
    console.setLevel(logging.DEBUG)
    logger.addHandler(console)
    logger.addHandler(filelog)
    return logger


def folderInfo(path):
    """ get total size and file count in a directory """
    size = 0
    filecount = 0
    for root, _, files in os.walk(path):
        fullpath = os.path.join(path, root)
        for fname in files:
            fullname=os.path.join(fullpath, fname)
            if os.path.isfile(fullname):
                filecount += 1
                size += os.path.getsize(fullname)
    return (size, filecount)

def int2base(num,b,numerals='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'):
    if num == 0: return numerals[0]
    return int2base(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]


def formatdict(sourceDict, replacementDict):
    """ 
    formats all strings in a dict using the other values in the dict 
    example: {a:"test",b:"/root/{a}"} becomes {a:"test",b:"/root/test"}
    """
    for key,value in sourceDict.items():
        if type(value) == dict:
            formatdict(value,replacementDict)
        if type(value) == str:
            sourceDict[key] = value.format(**replacementDict)

