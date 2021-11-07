# -*- coding: UTF-8 -*-
#
#  FstabData.py : Fstab data
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

# Default options for an fs
defaults = { "ext3"         :   ("defaults", "0", "2"),
             "ext2"         :   ("defaults", "0", "2"),
             "vfat"         :   ("defaults,utf8,umask=0", "0", "2"),
             "ntfs"         :   ("defaults,nls=utf8,umask=0222", "0", "0"),
             "ntfs-3g"      :   ("defaults,locale=autoset", "0", "0"),
             "ntfs-fuse"    :   ("defaults,locale=autoset,umask=0", "0", "0"),
             "jfs"          :   ("defaults,iocharset=utf8", "0", "0"),
             "__default__"  :   ("defaults", "0", "0")}

# Known special driver
special_driver = { "ntfs-3g"    : "Read-write driver",
                   "ntfs-fuse"  : "Read-write driver",
                   "__unknow__" : "Unknow driver" }
                   
# Secondary driver
secondary_driver = { "ext3"     : ("ext2"),
                     "vfat"     : ("msdos"),
                     "__all__"  : ("auto")}
                     
# List type of device that have an FS_TYPE, but that we don't want to configure
ignore_fs = ("swap", "iso9660", "udf", "iso9660,udf", "udf,iso9660")

# List device that we should ignore
ignore_dev = ("/dev/fd0", "/dev/fd1", "/dev/fd2")

# List of virtual device name
virtual_dev = ("proc", "devpts", "tmpfs", "sysfs", "shmfs", "usbfs")


# Common options. Keep them when we change fs    
common = ("atime","noatime","diratime","nodiratime","auto","noauto","dev","nodev","exec",\
          "noexec","mand","nomand","user","nouser","users","group","_netdev","owner","suid","nosuid",\
          "ro","rw","sync","async","dirsync")

# List of options that don't require a remount
dont_need_remount = ("auto", "noauto", "check=none", "nocheck", "errors=continue", "errors=remount-ro", "error=panic")


# Write entry in MntFile in this order :
path_order = ("/", "/usr", "/home")

# System partitions :
system = { "exact"  : ("/", "/home", "/tmp"),
           "extand" : ("/usr", "/var", "/boot", "/sys", "/proc")}


# MntFile header
header = "# /etc/fstab: static file system information.\n" + \
         "#\n" +\
         "# <file system> <mount point>   <type>  <options>       <dump>  <pass>\n\n"

# Categories of an entry
categorie = ("FSTAB_NAME", "FSTAB_PATH", "FSTAB_TYPE", "FSTAB_OPTION", "FSTAB_FREQ", "FSTAB_PASO")


# Divers
special_char = ('"', "'", " ", "<", ">", "&", "$", "(", ")", "`", "-", "|", ";", "~", "{", "}", "^")


