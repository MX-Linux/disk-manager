# -*- coding: UTF-8 -*-
#
#  ToolsBackend.py : DiskInfo Backend that use various tools
#                    to get device informations
#  Copyright (C) 2007 Mertens Florent <flomertens@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#


import os
import re
import logging
from subprocess import *

from Fstabconfig import *
from FstabError import *
import FstabData
from DiskInfo import DiskInfoBase

class ToolsBackend(DiskInfoBase) :

    def __init__(self) :
    
        DiskInfoBase.__init__(self)

    def _backend_score(self) :
        ''' Return the reliability score of the backend (0-100) '''
        
        return 50

    def _exec(self, cmd):
        
        logging.debug("Executing : %s" % cmd)
        process = Popen(cmd, stderr=STDOUT, stdout=PIPE, close_fds=True, shell=True)
        sts = process.wait()
        if not sts :
            res = "Success"
        else :
            res = "Failure"
        logging.debug("-> Exit status : %s (%s)" % (str(sts), res))
        return (sts, process.stdout.readlines())
        
    def _get_device_info(self, device) :
            
        dev = {}
        # Get dev, size, major and minor directly from /proc/partitions
        dev["DEV"] = device.strip().split()[3]
        logging.debug("Looking at : " + dev["DEV"])
        dev["SIZE"] = float(device.strip().split()[2])*1024.
        dev["MAJOR"] = device.strip().split()[0]
        dev["MINOR"] = device.strip().split()[1]
        
        # See if this partition is from a parent already in the database
        try :
            drive = re.search("(\w{1,3})[0-9]", dev["DEV"]).groups()[0]
            dev["PARENT"] = self[drive]["DEV"]
        except NotInDatabase :
            dev["PARENT"] = None
        except AttributeError :
            dev["PARENT"] = None
        logging.debug("-> Set   PARENT :" + str(dev["PARENT"]))
            
        # Set sysfs_path and /removable path depending of the previous result
        if dev["PARENT"] :
            dev["SYSFS_PATH"] = "/sys/block/" + dev["PARENT"] + "/" + dev["DEV"]
            removable = "/sys/block/" + dev["PARENT"] + "/removable"
        else :
            dev["SYSFS_PATH"] = "/sys/block/" + dev["DEV"]
            removable = "/sys/block/" + dev["DEV"] + "/removable"
            
        # Set removable
        if os.path.exists(removable) :
            fd = open(removable)
            dev["REMOVABLE"] = bool(int(fd.readline()))
        else :
            dev["REMOVABLE"] = False
        logging.debug("-> Set   REMOVABLE :" + str(dev["REMOVABLE"]))
        
        # Get the more info posible about the device from udevinfo
        cmd = UDEVINFO + " -p " + dev["SYSFS_PATH"].replace("/sys","") + " -q all"
        (sts, result) = self._exec(cmd)
        if not sts :
            for line in result :
                logging.debug("(udevinfo output) " + line.strip())
                try :
                    device = "/dev/" + re.search("N: (\S+)", line).groups()[0]
                    dev["DEVICE"] = device
                    logging.debug("-> Found DEVICE : " + device)
                except AttributeError :
                    pass
                # Used for debugging blkid & vol_id :
                # continue
                try :
                    (attr, value) = re.search("E: ID_(\S+)=(.+)", line).groups()
                    dev[attr] = value
                    logging.debug("-> Found " + attr + " : "+ value)
                except AttributeError :
                    pass
                
        # Used for debugging dmsetup :
        #if not dev["DEV"].find("dm-") == -1 and dev.has_key("DEVICE") :
        #    del dev["DEVICE"]
                
        # If udevinfo fail or didn't give DEVICE, it's might be a mapped device.
        # Try to get DEVICE from dmsetup
        if not dev.has_key("DEVICE") and "dm-" in dev["DEV"] :
            cmd = DMSETUP + " info -j " + dev["MAJOR"] + " -m " + dev["MINOR"] + " | grep Name"
            (sts, result) = self._exec(cmd)
            result = "".join(result)
            logging.debug("(dmsetup output) " + result.strip())
            if not sts and result :
                device = "/dev/mapper/" + result.split()[-1]
                logging.debug("-> Found DEVICE : " + device)
                if os.path.exists(device) :
                    logging.debug("-> Check DEVICE : ok")
                    dev["DEVICE"] = device
                else :
                    logging.debug("-> Check DEVICE : fail")
            else :
                logging.debug("Warning : First attempt failed. Trying something else...")
                cmd = "%s ls |grep '(%s, %s)'" % (DMSETUP, dev["MAJOR"], dev["MINOR"])
                (sts, result) = self._exec(cmd)
                result = "".join(result)
                logging.debug("(dmsetup output) " + result.strip())
                if not sts and result :
                    device = "/dev/mapper/" + result.split()[0]
                    logging.debug("-> Found DEVICE : " + device)
                    if os.path.exists(device) :
                        logging.debug("-> Check DEVICE : ok")
                        dev["DEVICE"] = device
                    else :
                        logging.debug("-> Check DEVICE : fail")
        # If still no DEVICE, try /dev/ + DEV
        if not dev.has_key("DEVICE") :
            device = "/dev/" + dev["DEV"]
            if os.path.exists(device) :
                logging.debug("Warning : no DEVICE found, try " + device)
                stat = os.stat(device)
                if stat.st_rdev == os.makedev(int(dev["MAJOR"]), int(dev["MINOR"])) :
                    logging.debug("-> Check DEVICE : ok")
                    logging.debug("-> Set   DEVICE : " + device)
                    dev["DEVICE"] = device
                else :
                    logging.debug("-> Check DEVICE : fail")
                                
        # Try to get slaves, set removable depending of the slave, and set FS_USAGE to other
        # if it is not already set. Here we don't really care what kind of type it is.
        # If it is manageable by the system, udeinfo or vol_id should have given us it real FS_USAGE.
        if os.path.isdir(dev["SYSFS_PATH"] + "/slaves") and os.listdir(dev["SYSFS_PATH"] + "/slaves") :
            dev["SLAVES"] = os.listdir(dev["SYSFS_PATH"] + "/slaves")
            dev["REMOVABLE"] = True
            for slave in dev["SLAVES"] :
                if self.search(slave) :
                    logging.debug("-> Add   SLAVES : " + slave)
                    if not self[slave].has_key("FS_USAGE") or self[slave] == "filesystem" :
                        self[slave]["FS_USAGE"] = "other"
                        logging.debug("-> Set   %s FS_USAGE : other" % slave)
                    dev["REMOVABLE"] = dev["REMOVABLE"] and self[slave]["REMOVABLE"] 
            logging.debug("-> Set   REMOVABLE : " + str(dev["REMOVABLE"]) )
        
        # Call vol_id to complete informations. This is important even if udevinfo
        # worked successfully, because udev db might be not up to date, and udev
        # might be wrong on some FS_LABEL (ones with " for exemple)    
        if dev.has_key("DEVICE") :
            cmd = VOLID + " --export " + dev["DEVICE"]
            (sts, result) = self._exec(cmd)
            if not sts :
                for line in result :
                    logging.debug("(vol_id output) " + line.strip())
                    try :
                        (attr, value) = re.search("ID_(\S+)=(.+)", line).groups()
                        dev[attr] = value
                        logging.debug("-> Found " + attr + " : " + value)
                    except AttributeError :
                        pass
            else :
                logging.debug("Warning : First attempt failed. Trying something else...")
                cmd = VOLID + " " + dev["DEVICE"] 
                (sts, result) = self._exec(cmd)
                if not sts :
                    d = {"F" : "FS_USAGE", "T" : "FS_TYPE", "U" : "FS_UUID", "L" : "FS_LABEL"}
                    for line in result :
                        logging.debug("(vol_id output) " + line.strip())
                        try :
                            (attr, value) = re.search("(\S+):(.+)", line).groups()
                            if d.has_key(attr) and not dev.has_key(d[attr]) :
                                dev[d[attr]] = value
                                logging.debug("-> Found " + d[attr] + " : " + value)
                        except AttributeError :
                            pass
            # If vol_id fail, call blkid. Don't overwrite info, blkid is less reliable
            # than any of the other tools.
            if sts and not dev.has_key("FS_USAGE") :
                logging.debug("Warning : vol_id failled, call blkid")
                cmd = BLKID + " " + dev["DEVICE"]
                (sts, result) = self._exec(cmd)
                result = "".join(result)
                if not sts :
                    logging.debug("(blkid output) " + result.strip())
                    for attr in ("TYPE", "LABEL", "UUID") :
                        try :
                            pattern = "\\b" + attr + "=\"([^\"]+)\""
                            value = re.search(pattern, result).groups()[0]
                            if not dev.has_key("FS_" + attr) :
                                dev["FS_" + attr] = re.search(pattern, result).groups()[0]
                                logging.debug("-> Found " + attr + " : " + dev["FS_" + attr])
                            if attr == "TYPE" :
                                if value not in FstabData.ignore_fs :
                                    dev["FS_USAGE"] = "filesystem"
                                else :
                                    dev["FS_USAGE"] = "other"
                                logging.debug("-> Set   FS_USAGE : " + dev["FS_USAGE"])
                        except AttributeError : 
                            pass
                    
        for attr in ("UUID", "LABEL") :
            # If no UUID, LABEL try to get them manually
            if dev.has_key("DEVICE") and not dev.has_key("FS_" + attr) :
                if os.path.exists(dev["DEVICE"]) and os.path.isdir("/dev/disk/by-" + attr.lower()) :
                    for file in os.listdir("/dev/disk/by-" + attr.lower()) :
                        if os.path.samefile("/dev/disk/by-" + attr.lower() + "/" + file, dev["DEVICE"]) :
                            logging.debug("-> Set   " + attr + " : " + file)
                            dev["FS_" + attr] = file

        return dev

