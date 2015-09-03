#!/usr/bin/env python
"""
  09/01/2015
  Author: Makerbro
  Platforms: Raspberry Pi (Raspbian)
  Language: Python
  File: main.py
  ------------------------------------------------------------------------
  Description: 
  Main loop starter for the USBMonitor program.
  ------------------------------------------------------------------------
  License:
  Beerware License; if you find the code useful, and we happen to cross 
  paths, you're encouraged to buy us a beer. The code is distributed hoping
  that you in fact find it useful, but  without warranty of any kind.
"""
import os,sys,subprocess,time
cwd = os.path.dirname(os.path.abspath(__file__))
os.chdir(cwd) # ensure correct working direcory

import util,usbmonitor
config=util.loadConfig("config.json")
log=util.initLogger(config)

try:
    ignoreAlreadyMounted = len(sys.argv)>1 and sys.argv[1] == "skip"
    app = usbmonitor.USBMonitor(config)
    app.main_loop(not ignoreAlreadyMounted)
    # rerun this and exit
    #subprocess.Popen("./main.py",shell=True)
except KeyboardInterrupt:
    app.unmount_partition()
    log.info("|Killed by Keyboard")
except:
    log.exception("Error in main loop|")
