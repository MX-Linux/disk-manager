# -*- coding: UTF-8 -*-
#
#  FstabDialogs.py : Provide dialogs for FstabHandler
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

import pygtk
pygtk.require("2.0")
import gtk
import pango
from gettext import gettext as _

from Fstabconfig import *
from SimpleGladeApp import SimpleGladeApp


ACCEPTED_TYPE = ["warning", "info", "error", "question"]


class WrongDialogType(Exception) : 

    def __init__(self, value) :
    
        self.value = value
        
    def __str__(self) :
        
        return "'%s' is not an accepted dialog type. " \
            "Should be '%s'" % (self.value, "' or '".join(ACCEPTED_TYPE))


class DialogBuilder(SimpleGladeApp) :
    ''' This class will create a builder with widget appropriate to the data you give hime '''

    def __init__(self, type, buttons, title, text, data = None, options = None, parent = None) :
        ''' See dialog doc for more information. You should not need to call this method
            directly, but use the dialog fct instead '''
    
        self.type = type
        self.buttons = buttons
        self.title = title
        self.text = text
        self.data = data
        self.options = options
        if not self.buttons :
            self.buttons = []
        elif isinstance(self.buttons, str) :
            self.buttons = [ self.buttons ]    
        if type in ("warning", "info", "error") :
            if not self.buttons :
                self.buttons = ["close"]
            else :
                self.buttons.insert(0, "cancel")
        elif type == "question" :
            self.buttons.insert(0, "yes")
            self.buttons.insert(0, "no")
        else :
            raise WrongDialogType(type)
        SimpleGladeApp.__init__(self, GLADEFILE, "dialog_template", domain = PACKAGE)
        self.dialog_main = self.dialog_template
        self.dialog_main.set_title("")
        if parent :
            self.dialog_main.set_transient_for(parent)
        self.build_advance_dialog()
        self.set_size()
        
    def build_advance_dialog(self) :

        for button in self.buttons :
            if not isinstance(button, str) :
                continue
            try :
                response = getattr(gtk, "RESPONSE_%s" % button.upper())
            except :
                response = 0
            if hasattr(gtk, "STOCK_%s" % button.upper()) :
                button = getattr(gtk, "STOCK_%s" % button.upper())
            widget = self.dialog_main.add_button(button, response)
        self.dialog_main.set_focus(widget)
        self.title_label.set_label("<big><b>" + self.title + "</b></big>")
        try :
            self.image.set_from_stock(getattr(gtk, "STOCK_DIALOG_%s" % self.type.upper()), gtk.ICON_SIZE_DIALOG)
        except :
            pass
        if isinstance(self.text, list) :
            self.text_top_label.set_label(self.text[0])
            self.text_down_label.set_property("wrap", False)
            self.text_down_label.set_label(self.text[1])
        else :
            self.text_down_label.hide()
            self.text_top_label.set_label(self.text)
        if self.options :
            self.setup_check_button()
        if isinstance(self.data, list) :
            self.setup_treeview()
        elif isinstance(self.data, str) :
            self.setup_textview()
            
    def on_treeview_toggled(self, widget) :

        path = self.treeview.get_cursor()[0]  
        self.tree_store[path][0] = not self.tree_store[path][0]
    
    def setup_treeview(self) :
    
        self.treeview  = gtk.TreeView()
        self.treeview.set_headers_visible(False)
        self.scrolledwindow.add(self.treeview)
        if len(self.data) > 1 and isinstance(self.data[1], bool) :
            sensitive = self.data[1]
            data = self.data[0]
        else :
            sensitive = True
            data = self.data
        renderer1 = gtk.CellRendererToggle()
        renderer1.set_property("sensitive", sensitive)
        if sensitive :
            self.treeview.connect("cursor-changed", self.on_treeview_toggled)
        column = gtk.TreeViewColumn("", renderer1, active=0)
        self.treeview.append_column(column)
        renderer2 = gtk.CellRendererText()
        column = gtk.TreeViewColumn("", renderer2, text=1)
        self.treeview.append_column(column)
        self.tree_store = gtk.ListStore(bool, str)
        self.treeview.set_model(self.tree_store)
        for entry in data :
            if isinstance(entry, list) :
                value = entry[1]
                entry = entry[0]
            else :
                value = True
            self.tree_store.append((value, entry))
        self.scrolledwindow.show_all()
        
    def setup_textview(self) :
    
        self.textview = gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.scrolledwindow.add(self.textview)
        buf = gtk.TextBuffer()
        buf.set_text(self.data)
        self.textview.set_buffer(buf)
        self.scrolledwindow.show_all()
        
    def setup_check_button(self) :
    
        box = gtk.VBox(homogeneous=True, spacing = 0)
        if len(self.options) > 1 and isinstance(self.options[1], bool) :
            grouped = self.options[1]
            options = self.options[0]
        else :
            grouped = False
            options = self.options
        widget = None
        for option in options :
            if isinstance(option, list) :
                option = option[0]
                value = option[1]
            else :
                value = False
            if grouped :
                widget = gtk.RadioButton(label = option, group = widget)
            else :
                widget = gtk.CheckButton(option)
            widget.set_active(value)
            box.pack_start(widget, expand=False)
        self.check_box = box
        self.vbox.pack_end(self.check_box, expand=False)
        self.check_box.show_all()
        
    def set_size(self) :
    
        if hasattr(self, "treeview") :
            widget = self.treeview
            if len(self.data) > 1 and isinstance(self.data[1], bool) :
                sample = self.data[0]
            else :
                sample = self.data
            ypad = 6
            maxrow = 8
        elif hasattr(self, "textview") :
            widget = self.textview
            sample = self.data.split("\n")
            ypad = 2
            maxrow = 8
        else :
            return
        ctx = widget.get_pango_context()
        layout = pango.Layout(ctx)
        row = min(len(sample) + 2, maxrow)
        if self.options and row > 5 :
            row -= min(len(self.options), 3)
        w = []
        for k in sample :
            if isinstance(k, list) :
                k = k[0]
            layout.set_text(k + "O" * 2 * row)
            w.append(layout.get_pixel_size()[0])
        width = min(max(w), 450)
        height = (layout.get_pixel_size()[1] + ypad) * row
        widget.set_size_request(width, height)
        
    def run(self) :

        ret = self.dialog_main.run()
        if ret in (gtk.RESPONSE_DELETE_EVENT, gtk.RESPONSE_CANCEL, gtk.RESPONSE_CLOSE, gtk.RESPONSE_NO) :
            ret = gtk.RESPONSE_REJECT
        result = [ret, None, None]
        if not ret == gtk.RESPONSE_REJECT :
            if hasattr(self, "treeview") :
                select = []
                unselect = []
                iter = self.tree_store.get_iter_first()
                for i in range(len(self.tree_store)) :
                    if self.tree_store.get_value(iter, 0) :
                        select.append(i)
                    else :
                        unselect.append(i)
                    iter = self.tree_store.iter_next(iter)
                result[1] = [select, unselect]
            if hasattr(self, "check_box") :
                select = []
                unselect = []
                i = 0
                for widget in self.check_box.get_children() :
                    if widget.get_active() :
                        select.append(i)
                    else :
                        unselect.append(i)
                    i += 1
                result[2] = [select, unselect]
        self.dialog_main.hide()
        return result

def dialog(type, title, text, data = None, action = None, options = None, parent = None) :
    ''' dialog(type, title, text, [data], [action], [options], [parent] -> launch a graphical dialog\n
        type : type of the dialog. should be "warning", "error", "info" or "question"
        title : title of the dialog
        text : the text to show in the dialog. If text = [text1, text2] text1 will be shown on top
               text2 will be shown on the bottom
        data : data to show in the dialog. If data is a list, show it in a treeview. otherwise,
               show it in a textview. 
               If treeview, list should be of the type : [[data, value], sensitive]
               sensitive : True/False, set the sensitivity of the check button. Default to True
               [data, value] : a list of data and it respectives values. Default value are False
               exemples : [ [data1, data2], False] : show a treeview with 2 unactivable, unselected row.
                          [data1, data2] : show a treeview with 2 activable, unselected row.
                          [[data1, True], [data2, False]] : show a treeview with 2 activable row, the first 
                                selected, the second unselected.
        options : list of options to show at the bottom of the dialog.
               options should be of the type : [[[option, value]], group]
               group : True/False, if True options are grouped and only one could be selected. Default to False
               [option, value] : a list of options and their respective values. Default values are False.
               See data for an exemple of how it works, it is nearly the same
        parent : the parent window\n
        return code : [dialog return code, [(selected data, unselected data)], [(selected opt, unselected opt)]]'''

    dialog = DialogBuilder(type, action, title, text, data, options, parent)
    return dialog.run()

