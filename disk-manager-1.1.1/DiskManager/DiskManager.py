# -*- coding: UTF-8 -*-
#
#  DiskManager.py : Manage main interfaces
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
import sys
import time
import logging
import threading
from subprocess import Popen
from xml.sax.saxutils import escape as escape_mkup

import pygtk
pygtk.require("2.0")
import gtk
import pango
import gtk.glade
import gobject
from SimpleGladeApp import SimpleGladeApp
from gettext import gettext as _

from Utility import *

try :
    import pynotify
    NOTIFICATION = True
except :
    print >>sys.stderr, "WARNING : python-notify is not installed, disable notification"
    NOTIFICATION = False

if not gtk.check_version( 2, 10, 0 ) == None :
    TRAYTYPE = "egg"
else :
    try :
        pynotify.Notification.attach_to_status_icon
        TRAYTYPE = "gtk"
    except :
        TRAYTYPE = "egg"
        
if TRAYTYPE == "egg" :
    try :
        import egg.trayicon
    except :
        if not gtk.check_version( 2, 10, 0 ) == None :
            print >>sys.stderr, "WARNING : Can't find a valid tray icon module"
            TRAYTYPE = None
        else :
            TRAYTYPE = "gtk"
            NOTIFICATION = False
            print >>sys.stderr, "WARNING : python-notify is too old, disable notification"
            
ICON_THEME = gtk.icon_theme_get_default()
ICON_THEME.append_search_path("%s/.icons" % get_user("dir"))
ICON_THEME.append_search_path("%s/.local/share/icons" % get_user("dir"))
try :
    PIX_MOUNT = ICON_THEME.load_icon("gnome-dev-harddisk", 24, 0)
except :
    try :
        PIX_MOUNT = ICON_THEME.load_icon("hdd_mount", 24, 0)
    except :
        PIX_MOUNT = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 1, 1)
try :
    PIX_UNMOUNT = ICON_THEME.load_icon("gnome-dev-removable", 24, 0)
except :
    try :
        PIX_UNMOUNT = ICON_THEME.load_icon("hdd_unmount", 24, 0)
    except :
        PIX_UNMOUNT = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 1, 1)       

from config import *
from Config import Config
from Dialogs import *
from Fstab.FstabHandler import *

gtk.glade.bindtextdomain("disk-manager",localedir)
gtk.glade.textdomain("disk-manager")


class DiskManager(SimpleGladeApp) :
    ''' Class that manage the main window '''

    def __init__(self) :

        SimpleGladeApp.__init__(self, GLADEFILE, "window_main", domain = "disk-manager")
        self.window_main.set_title(_("Disk Manager"))
        
        # Start configuration
        self.conf = Config()

        # Perform sanity check
        check = SanityCheck(parent = self.window_main, conf = self.conf)
        check.unknow()
        check.duplicate()

        # Start fstab handler
        naming = self.conf.get("General", "fstab_naming")
        backend = self.conf.get("General", "backend")
        self.disk = FstabHandler(FSTAB, naming = naming, backend = backend, \
                parent = self.window_main, external_change_watch = True)
        
        # Draw stuff
        try :
            self.window_main.resize(\
                self.conf.getint("Gui Config", "main_width"), \
                self.conf.getint("Gui Config", "main_height"))
        except :
            self.conf.set_default("Gui Config", "main_width")
            self.conf.set_default("Gui Config", "main_height")
        self.width = self.conf.getint("Gui Config", "main_width")
        self.height = self.conf.getint("Gui Config", "main_width")
        self.window_main.show()
        self.setupTreeView()
        self.update_main()
                
        # Store all detected device
        detected = " ".join([ k["DEVICE"] for k in self.disk.get_all() ])
        self.conf.set("Detected Device", "detected", detected)
        
        # Connect events
        self.quit_menu.connect("activate", self.on_close_clicked)
        self.window_main.connect("destroy", self.on_close_clicked)
        self.window_main.connect("configure-event", self.on_resize)
        self.undo_menu.connect("activate", self.on_revert_clicked)
        self.save_menu.connect("activate", self.on_save_clicked)
        self.history_menu.connect("activate", self.on_history_clicked)
        self.about_menu.connect("activate", about_dialog, self.window_main)
        self.edit_button.connect("clicked",  self.on_edit_clicked)
        self.mount_button.connect("clicked",  self.on_mount_clicked)
        self.info_button.connect("clicked", self.on_info_clicked)
        self.treeview.connect("row-activated", self.on_row_activated)
        self.treeview.connect("cursor_changed", self.on_cursor_changed)
        self.disk.connect("any_changed", gobject.idle_add, self.update_main)
                
        gtk.gdk.threads_init()
        
    def setupTreeView(self) :
        ''' treeview setup '''
        
        renderer= gtk.CellRendererToggle()
        renderer.set_property("activatable", True)
        renderer.connect("toggled", self.on_enable_toggled)
        column = gtk.TreeViewColumn(_("Enable"), renderer, active=0, sensitive=1, activatable=1)
        column.set_sort_column_id(0)
        column.set_reorderable(True)
        self.treeview.append_column(column)
        
        pix_renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn(_("Device"))
        column.pack_start(pix_renderer, False)
        column.set_attributes(pix_renderer, pixbuf=6)
        pix_renderer.set_property("xpad", 3)
        text_renderer = gtk.CellRendererText()
        column.pack_end(text_renderer, False)
        column.set_attributes(text_renderer, text=2, sensitive=0, style=5)
        column.set_sort_column_id(2)
        column.set_reorderable(True)
        column.set_expand(True)
        self.treeview.append_column(column)
        
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Mount point"), renderer, text=3, sensitive=0, style=5)
        column.set_sort_column_id(3)
        column.set_expand(True)
        column.set_reorderable(True)
        self.treeview.append_column(column)
       
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Type"), renderer, text=4, sensitive=0, style=5)
        column.set_sort_column_id(4)
        column.set_expand(True)
        column.set_reorderable(True)
        self.treeview.append_column(column)
        
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Total"), renderer, text=7, sensitive=0, style=5)
        column.set_sort_column_id(7)
        column.set_expand(True)
        column.set_reorderable(True)
        self.treeview.append_column(column)
        
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Free"), renderer, text=8, sensitive=0, style=5)
        column.set_sort_column_id(8)
        column.set_expand(True)
        column.set_reorderable(True)
        self.treeview.append_column(column)
        
        renderer = gtk.CellRendererProgress()
        column = gtk.TreeViewColumn(_("Used"), renderer, text=9, value=10, sensitive=0)
        column.set_sort_column_id(9)
        column.set_expand(True)
        column.set_reorderable(True)
        renderer.set_property("ypad", 4)
        renderer.set_property("xpad", 4)
        self.treeview.append_column(column)
        
        self.tree_store = gtk.ListStore(bool, bool, str, str, str, int, \
                    gtk.gdk.Pixbuf, str, str, str, int)
        self.tree_store.set_sort_func(7, self.sort_size, "size")
        self.tree_store.set_sort_func(8, self.sort_size, "free")
        self.tree_store.set_sort_func(9, self.sort_size, "used")
        try :
            self.tree_store.set_sort_column_id( \
                int(self.conf.get("Gui Config", "selected")), \
                getattr(gtk,"SORT_" + self.conf.get("Gui Config", \
                    "selected_order").upper()))
        except ValueError :
            self.tree_store.set_sort_column_id( \
                int(self.conf.set_default("Gui Config", "selected")), \
                getattr(gtk,"SORT_" + self.conf.set_default("Gui Config", \
                    "selected_order").upper()))
        self.treeview.set_model(self.tree_store)
        
    def update_main(self) :
        ''' Update the window '''
    
        focus_path = self.treeview.get_cursor()[0]
        if focus_path :
            l = self.tree_store[focus_path]
            current_focus = (l[2], l[3])

        self.undo_menu.set_sensitive(self.disk.original_has_changed())
        self.save_menu.set_sensitive(self.disk.lastsave_has_changed())
                        
        (self.total, self.total_free, self.total_used, self.total_avail) = (0,0,0,0)
        configured = self.disk.get_configured()
        self.tree_store.clear()
        for entry in self.disk :
            device = entry["DEV"]
            type = entry["FSTAB_TYPE"]
            path = entry["FSTAB_PATH"]
            sensitive = not entry.get_is_system() or not entry in configured
            size_real  = entry.get_size()
            size = size_renderer(size_real)
            if entry in configured :
                self.total += size_real
                enable = True
                style = pango.STYLE_NORMAL
            else :
                enable = False
                style = pango.STYLE_ITALIC
            if entry.get_is_mounted() :
                pix = PIX_MOUNT
                free_real = entry.get_free_size()
                free = size_renderer(free_real)
                used_real = entry.get_used_size()
                used = size_renderer(used_real)
                try :
                    per_use = used_real  / float(size_real) * 100
                except ZeroDivisionError :
                    per_use = 0
                if entry in configured :
                    self.total_free += free_real 
                    self.total_used += used_real 
                    self.total_avail += entry.get_available_size()
            else :
                pix = PIX_UNMOUNT
                free = used = ""
                per_use = 0
            self.tree_store.append((enable, sensitive, device, path, type, \
                    style, pix, size, free, used, per_use))
                                        
        if focus_path :
            for path in range(len(self.tree_store)) :
                l = self.tree_store[path]
                if current_focus == (l[2], l[3]) :
                    self.treeview.set_cursor(path)
                    break
                elif current_focus[0] == l[2] and len(self.disk.search(l[2], keys = ["DEV"])) < 2 :
                    self.treeview.set_cursor(path)
                    break
        if not self.treeview.get_cursor()[0] :
            self.info_button.set_sensitive(False)
            self.mount_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)

    def sort_size(self, treemodel, iter1, iter2, type) :
    
        iter = [iter1, iter2]
        size = [0, 0]
        for i in range(2) :
            if not self.tree_store.get_value(iter[i], 3) :
                return 0
            entry = self.tree_store.get_value(iter[i], 3)
            if type == "size" :
                size[i] = self.disk.get_property(entry, type)
            else :
                size[i] = self.disk.get_property(entry, "%s_size" % type)
        if size[0] < size[1] :
            return -1
        return 1
             
    def on_edit_clicked(self, button) :

        path = self.treeview.get_cursor()[0]
        entry = self.disk[self.tree_store[path][3]]
        if entry.get_is_system() :
            ret = dialog("question", _("Editing system partition?"), \
                _("<i>%s</i> is an important system partition.\n" \
                "Be really careful when editing it, or you may have\n" \
                "serious problems. Do you want to continue?") % entry["DEV"], \
                parent = self.window_main)
            if ret[0] == gtk.RESPONSE_REJECT :
                return
        dial = EditPartition(self.disk, entry, parent = self.window_main)
        dial.dialog_edit.run()

    def on_mount_clicked(self, button) :
    
        path = self.treeview.get_cursor()[0]
        entry = self.disk[self.tree_store[path][3]]
        if entry.get_is_mounted() : 
            self.disk.umount(entry)
        else : 
            self.disk.mount(entry)
        
    def on_info_clicked(self, button) :
    
        path = self.treeview.get_cursor()[0]
        col = path[0]
        dial = InfoDialog(None, self.disk, parent = self.window_main)
        res = 0
        while not res in (gtk.RESPONSE_CLOSE, gtk.RESPONSE_DELETE_EVENT) :
            dial.entry = self.disk[self.tree_store[path][3]]
            dial.update_dial()
            if col == 0 :
                dial.back_button.set_sensitive(False)
            if col == len(self.tree_store) - 1 :
                dial.forward_button.set_sensitive(False)                
            res = dial.dialog_info.run()
            if res == 1 : 
                col = col - 1
                dial.forward_button.set_sensitive(True)
            if res == 2 :
                col = col + 1
                dial.back_button.set_sensitive(True)
            path = (col,)
            self.treeview.set_cursor(path)
        dial.dialog_info.destroy()
        
    def on_row_activated(self, treeview, path, view_column) :
        ''' Start browser on double click. '''
    
        entry = self.disk[self.tree_store[path][3]]
        if not self.disk.mount(entry) :
            open_url(entry["FSTAB_PATH"])
        
    def on_enable_toggled(self, renderer, path) :
    
        use = self.tree_store[path][0]
        entry = self.disk[self.tree_store[path][3]]
        self.treeview.set_cursor(path)
        if use :
            self.disk.unconfigure(entry)
        else :
            self.disk.configure(entry)
        
    def on_cursor_changed(self, treeview) :
        ''' Set button when we change device in the advance configuration '''

        path = self.treeview.get_cursor()[0]
        try :
            entry = self.disk[self.tree_store[path][3]]
        except NotInDatabase :
            self.info_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
            self.mount_button.set_sensitive(False)
            return
        sensitive = self.tree_store[path][1]
        self.info_button.set_sensitive(True)
        self.edit_button.set_sensitive(True)
        self.mount_button.set_sensitive(sensitive)
        if entry.get_is_mounted() :
            self.icon_mount.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON)
            self.label_mount.set_label(_("Unmount"))
        else :
            self.icon_mount.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
            self.label_mount.set_label(_("Mount"))
            
    def on_revert_clicked(self, button) :
        ''' Come back to the original fstab when we click on revert '''
    
        ret = dialog("question", _("Reverting to an older version?"), \
            [_("This will apply the following changes:"), _("Do you want to continue?")],
            "\n".join(self.disk.get_changes_current_to_original()), parent = self.window_main)
        if ret[0] == gtk.RESPONSE_YES :
            self.disk.undo()
        
    def on_history_clicked(self, button) :
        ''' Start HistoryDialog. '''
    
        dial = HistoryDialog(self.disk, parent = self.window_main)
        dial.dialog_history.run()
        
    def on_save_clicked(self, button) :
    
        self.disk.savelog()
        self.update_main()
        
    def on_resize(self, widget, event) :
    
        self.width = event.width
        self.height = event.height
    
    def on_close_clicked(self, button) :
        ''' Save the log when we clo            AddWizard.py \
se the app '''

        self.window_main.hide()
        while gtk.events_pending() :
            gtk.main_iteration()
        self.conf.set("Gui Config", "selected", \
                self.tree_store.get_sort_column_id()[0])
        self.conf.set("Gui Config", "selected_order", \
                self.tree_store.get_sort_column_id()[1].value_nick)
        self.conf.set("Gui Config", "main_width", self.width)
        self.conf.set("Gui Config", "main_height", self.height)
        self.disk.shutdown()
        gtk.main_quit()
