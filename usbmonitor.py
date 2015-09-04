"""
  09/01/2015
  Author: Makerbro
  Platforms: Raspberry Pi (Raspbian)
  Language: Python
  File: usbmonitor.py
  ------------------------------------------------------------------------
  Description: 
  Monitors usb devices and copies their contents to a local directory
  ------------------------------------------------------------------------
  License:
  Beerware License; if you find the code useful, and we happen to cross 
  paths, you're encouraged to buy us a beer. The code is distributed hoping
  that you in fact find it useful, but  without warranty of any kind.
"""
import pyudev, time, os, sys
import logging
import util

class USBMonitor:
    def __init__(self,config):
        self.config=config
        self.log=logging.getLogger(config['devicename'])
        self.devname = ''
        self.devlabel = ''
        self.mountpoint = ''

    def handle_usb(self, action, device):
        """
        handle a device plugin event
        """
        if action not in ['add','remove']:
            return

        if action == 'add':
            devname = device['DEVNAME']
            if device['DEVTYPE'] == "disk":
                # added main disk like /dev/sda, happens before OS scans for partitions
                self.log.debug("Added disk {0}, waiting for partitions".format(devname))
                return
            if device['DEVTYPE'] != "partition":
                return
            # get readable disk name if it exists
            self.devname = devname
            self.devlabel = device['ID_FS_LABEL'] if 'ID_FS_LABEL' in device else "Unknown"
            self.mount_partition()
            self.xfer_files()

        elif action == 'remove':
            if device['DEVTYPE'] == "disk":
                devname = device['DEVNAME']
                self.log.debug("Disk {0} was removed".format(devname))
                return
            if device['DEVTYPE'] != "partition":
                return
            self.unmount_partition() 

    def unmount_partition(self):
        if not len(self.mountpoint):
            return
        if not os.path.ismount(self.mountpoint):
            return
        self.unmountcount += 1
        self.log.info("Unmounting {0} from {1} (attempt #{2})"
                  .format(self.devname, self.mountpoint, self.unmountcount))
        try:
            util.unmountPartition(self.devname,self.mountpoint)
            if not os.path.ismount(self.mountpoint):
                self.log.info("Unmounted successfully {0}"
                          .format(self.devname))
        except IOError, e:
            if e is not None: 
                self.log.error(e)
            if self.unmountcount < self.config['unmountretries']:
                self.unmount_partition()

    def mount_partition(self):
        self.unmountcount = 0
        self.log.info("addedPartition|{0}|{1}|waiting for mount"
                 .format(self.devlabel, self.devname))
        _mountpoint = None
        _retries = 0
        while _mountpoint == None and _retries < self.config['automountretries']:
            # wait 15 seconds for the OS to automount the drive
            time.sleep(1.5)
            _retries += 1
            self.mountpoint = util.getMountPoint(self.devname)

        if _mountpoint == None:
            self.log.warning("automountFail|Device {0}({1}) was not automounted." 
                             "Trying manually..."
                      .format(self.devlabel, self.devname))
            _mountpoint = os.path.join(self.config['tmpmountpoint'], self.devlabel)
            if not os.path.exists(_mountpoint):
                os.makedirs(_mountpoint)
            self.log.info("createDirectory|Mount point {0} created"
                      .format(_mountpoint))
            self.mountpoint = _mountpoint

            try:
                util.mountPartition(self.devname, self.mountpoint)
                self.log.info("mountDevice|Successfully mounted {0} onto {1}"
                          .format(self.devname, self.mountpoint))
            except IOError, e:
                self.log.error(e)

        elif not os.path.exists(mountpoint):
            self.log.info("invalidDevice|Device does not seem to be a fitting drive, " +
                          "aborting (404 "+campath+")")

    def xfer_files(self):
        _xferdir = self.config['xferdirectory']
        if not os.path.exists(_xferdir):
            os.makedirs(_xferdir)
        util.cleanupDirectory(_xferdir)
        self.log.warning("cleanup|Cleaning up {0} subdirectory."
                  .format(_xferdir))
        try:
            util.copyFiles(self.mountpoint, _xferdir)
            self.log.info("fileCopy|Files copied from {0} to {1}"
                      .format(self.mountpoint, _xferdir))
            util.changePermissions(self.config['ownername'], _xferdir)
            self.log.info("permissionsChanged|Changing owner of {0} to {1}"
                      .format(_xferdir,self.config['ownername']))
        except IOError, e:
            self.log.error(e)

        self.unmount_partition()

    def handle_first(self):
        """ scan for devices added before starting the udev monitor """
        for partition in util.getPartitions():
            self.devname = "/dev/"+partition
            self.devlabel = "Unknown"
            self.mount_partition()
            self.xfer_files()

    def main_loop(self,handleAlreadyMounted=True):
        """ begin the main event loop monitoring devices """
        if handleAlreadyMounted: 
            self.handle_first()
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('block')#,'partition')

        self.log.info("boot|Started USB wait loop")
        for action, device in monitor:
            try:
                self.handle_usb(action,device)
            except KeyboardInterrupt:
                raise
            except:
                self.log.exception("Exception while handling device|")
