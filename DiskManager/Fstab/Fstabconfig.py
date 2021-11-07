# -*- coding: UTF-8 -*-
#
#  config.py : Store all dirs, commands, files used in the same place
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
from subprocess import *

def test_cmd(cmd) :

    return not call(["which " + cmd], stdout=PIPE, stderr=PIPE, \
                        close_fds=True, shell=True)
    
prefix     = "/usr/local"
PACKAGE    = "disk-manager"
VERSION    = "1.1.1"
HOMEPAGE   = "http://flomertens.free.fr/disk-manager/"

DATADIR   = prefix + "/share/" + PACKAGE
GLADEFILE = DATADIR + "/" + PACKAGE + ".glade"
localedir = prefix + "/share/locale"

# Config files :
FSTAB             = "/etc/fstab"
FSTAB_LOG         = "/root/.fstab.log"
MTAB              = "/etc/mtab"
CREATED_PATH_FILE = "/media/.created_by_python-fstab"

# Commands 
# If the path set here are incorrects, please fill a bug
LSOF     = "lsof"
DMESG    = "dmesg"
BLKID    = "/sbin/blkid"
DMSETUP  = "/sbin/dmsetup"
MOUNT    = "/usr/bin/mount"
UMOUNT   = "/usr/bin/umount"
MODPROBE = "/sbin/modprobe"

if os.path.exists("/lib/udev/vol_id") :
    VOLID = "/lib/udev/vol_id"
elif os.path.exists("/sbin/udev_volume_id") :
    VOLID = "/sbin/udev_volume_id"
else :
    VOLID = "vol_id"
    
if test_cmd("udevinfo") :
	UDEVINFO = "udevinfo"
else :
	UDEVINFO = "udevadm info"

