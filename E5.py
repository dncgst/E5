# Logic bug, if E5 starts on a cfg with errors, hitting esacpe crashes it
# When selecting a bad cfg, errors don't show and it goes onto first field

# Once I have factor figured out, consider doing factory register for validating data and other things

# Debug and test conditionals

# Load records into grid in recno reverse order
# Consider putting a dropdown menu into the grid view for sorting and maybe searching

# Need to establish a unique key for each record
# E4 conditions seem to accept OR at the end - check other options and implement
# Add a CFG option to sort menus

# Long term
#   Think about whether to allow editing of CFG in the program
#   Get location data from GPS

__version__ = '1.0.0'

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ListProperty, StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.config import Config

import os 
import random
import datetime
import logging
import logging.handlers as handlers
import time
import ntpath
from string import ascii_uppercase

logger = logging.getLogger('E5')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('E4.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

logger.addHandler(fh)

# My libraries for this project
from blockdata import blockdata
from dbs import dbs

# The database - pure Python
from tinydb import TinyDB, Query, where

from collections import OrderedDict

SCROLLBAR_WIDTH = 5
BLACK = 0x000000
WHITE = 0xFFFFFF

class ColorScheme:

    def __init__(self, color_name = None):
        self.optionbutton_font_size = "15sp"
        self.button_font_size = "15sp"
        self.text_font_size = "15sp"

        self.popup_background = (0, 0, 0, 1)
        self.popup_text_color = (1, 1, 1, 1)

        self.datagrid_odd = (224.0/255, 224.0/255, 224.0/255, 1)
        self.datagrid_even = (189.0/255, 189.0/255, 189.0/255, 1)

        # Color from Google material design
        # https://material.io/design/color/the-color-system.html#tools-for-picking-colors
        self.valid_colors = {'red': [0xFF8A80, BLACK, 0xFF1744, WHITE],
                                'pink': [0xFF80AB, BLACK, 0xF50057, WHITE],
                                'purple': [0xEA80FC, BLACK, 0xD500F9, WHITE],
                                'deep purple': [0xB388FF, BLACK, 0x651FFF, WHITE],
                                'indigo': [0x8C9EFF, BLACK, 0x3D5AFE, WHITE],
                                'blue': [0x82B1FF, BLACK, 0x2979FF, WHITE],
                                'light blue': [0x80D8FF, BLACK, 0x00B0FF, BLACK],
                                'cyan': [0x84FFFF, BLACK, 0x00E5FF, BLACK],
                                'teal': [0xA7FFEB, BLACK, 0x1DE9B6, BLACK],
                                'green': [0xB9F6CA, BLACK, 0x00E676, BLACK],
                                'light green': [0xCCFF90, BLACK, 0x76FF03, BLACK],
                                'lime': [0xF4FF81, BLACK, 0xC6FF00, BLACK],
                                'yellow': [0xFFFF8D, BLACK, 0xFFEA00, BLACK],
                                'amber': [0xFFE57F, BLACK, 0xFFC400, BLACK],
                                'orange': [0xFFD180, BLACK, 0xFF9100, BLACK],
                                'deep orange': [0xFF9E80, BLACK, 0xFF3D00, WHITE],
                                'brown': [0x8D6E63, WHITE, 0x6D4C41, WHITE]}

        if color_name.lower() in self.valid_colors:
            self.set_to(color_name)
        else:
            self.set_to('light blue')

        self.set_to_lightmode()
        self.need_redraw = False

    def set_to_darkmode(self):
        self.need_redraw = True
        self.window_background = (0, 0, 0, 1)
        self.text_color = (1, 1, 1, 1)
        self.darkmode = True
        Window.clearcolor = self.window_background

    def set_to_lightmode(self):
        self.need_redraw = True
        self.window_background = (1, 1, 1, 1)
        self.text_color = (0, 0, 0, 1)
        self.darkmode = False
        Window.clearcolor = self.window_background

    def color_names(self):
        return(self.valid_colors.keys())

    def make_rgb(self, hex_color):
        return([(( hex_color >> 16 ) & 0xFF)/255,
                (( hex_color >> 8 ) & 0xFF)/255,
                (hex_color & 0xFF)/255,
                1])

    def set_to(self, name):
        self.need_redraw = True
        if name in self.valid_colors:
            self.optionbutton_background = self.make_rgb(self.valid_colors[name][0])
            self.optionbutton_color = self.make_rgb(self.valid_colors[name][1])
            self.button_background =  self.make_rgb(self.valid_colors[name][2])
            self.button_color = self.make_rgb(self.valid_colors[name][3])
            self.color_scheme = name
        else:
            return('Error: %s is not a valid color scheme.' % (name))


POPUP_BACKGROUND = (0, 0, 0, 1)
POPUP_TEXT_COLOR = (1, 1, 1, 1)


SPLASH_HELP = "[b]E5[/b]\n\nE5 is a generalized data entry program intended "
SPLASH_HELP += "for archaeologists but likely useful for others as well.  It works with a "
SPLASH_HELP += "configuration file where the data entry fields are defined.  Importantly, E5 "
SPLASH_HELP += "makes it simple to make entry in one field conditional on values previously "
SPLASH_HELP += "entered for other fields.  The goal is to make data entry fast, efficient "
SPLASH_HELP += "and error free.\n\n"
SPLASH_HELP += "E5 is a complete, from scratch re-write of E4.  It is backwards compatible "
SPLASH_HELP += "with E4 configuration files, but it supports a great many new features. "
SPLASH_HELP += "For one, it is now built on Python to be cross-platform compatible, and the "
SPLASH_HELP += "source code is available at GitHub.  E5 will run on Windows, Mac OS, Linux "
SPLASH_HELP += "and Android tablets and phones.  For this reason and others, E5 now uses an "
SPLASH_HELP += "open database format.  All data are stored in human readable, ASCII formatted "
SPLASH_HELP += "JSON files.  Data can also be exported to CSV files for easy import into any "
SPLASH_HELP += "database, statistics or spreadsheet software.\n\n"
SPLASH_HELP += "To start using this program, you will need to open CFG file.  Example CFG files "
SPLASH_HELP += "and documentation on writing your own CFG file can be found at the E5 GitHub site."

class db(dbs):
    MAX_FIELDS = 300
    db = None
    filename = None
    db_name = 'data'
    datagrid_doc_id = None

    def __init__(self, filename):
        if filename=='':
            filename = 'e4_data.json'
        self.filename = filename
        self.db = TinyDB(self.filename)

    def status(self):
        txt = 'The data file is %s\n' % self.filename
        txt += 'There are %s records in the data file.\n' % len(self.db)
        return(txt)

    def create_defaults(self):
        pass

    def get(self, name):
        unit, id = name.split('-')
        p = self.db.search( (where('unit')==unit) & (where('id')==id) )
        if p:
            return(p)
        else:
            return(None)

    # Can likely delete this or use a DB key or the first unique field
    def names(self):
        name_list = []
        for row in self.db:
            name_list.append(row['unit'] + '-' + row['id'])
        return(name_list)

    def fields(self, tablename = ''):
        if not tablename:
            table = self.db.table(tablename)
        else:
            table = self.db.table('_default')
        fieldnames = []
        for row in table:
            for fieldname in row.keys():
                if not fieldname in fieldnames:
                    fieldnames.append(fieldname) 
        return(fieldnames)

    def delete_all(self):
        self.db.purge()

    def export_csv(self):
        pass

    def delete_record(self):
        pass

    def add_record(self):
        pass

class ini(blockdata):
    
    def __init__(self, filename):
        if filename=='':
            filename = 'E4.ini'
        self.filename = filename
        self.incremental_backups = False
        self.backup_interval = 0
        self.blocks = self.read_blocks()
        self.is_valid()
        self.incremental_backups = self.get_value('E5','IncrementalBackups').upper() == 'TRUE'
        self.backup_interval = int(self.get_value('E5','BackupInterval'))

    def is_valid(self):
        for field_option in ['DARKMODE','INCREMENTALBACKUPS']:
            if self.get_value('E5',field_option):
                if self.get_value('E5',field_option).upper() == 'YES':
                    self.update_value('E5',field_option,'TRUE')
            else:
                self.update_value('E5',field_option,'FALSE')

        if self.get_value('E5', "BACKUPINTERVAL"):
            test = False
            try:
                test = int(self.get_value('E5', "BACKUPINTERVAL"))
                if test < 0:
                    test = 0
                elif test > 200:
                    test = 200
                self.update_value('E5', 'BACKUPINTERVAL', test)
            except:
                self.update_value('E5', 'BACKUPINTERVAL', 0)
        else:
            self.update_value('E5', 'BACKUPINTERVAL', 0)

    def update(self):
        self.update_value('E5','CFG', e4_cfg.filename)
        self.update_value('E5','ColorScheme', e5_colors.color_scheme)
        self.update_value('E5','DarkMode', e5_colors.darkmode)
        self.update_value('E5','IncrementalBackups', self.incremental_backups)
        self.update_value('E5','BackupInterval', self.backup_interval)
        self.save()

    def save(self):
        self.write_blocks()

    def status(self):
        txt = 'The INI file is %s.\n' % self.filename
        return(txt)

class field:
    def __init__(self, name):
        self.name = name
        self.inputtype = ''
        self.prompt = ''
        self.length = 0
        self.menu = ''
        self.conditions = []
        self.increment = False
        self.carry = False 
        self.unique = False
        self.info = ''
        self.infofile = ''
        self.data = ''
        self.key = False
        self.required = False

class cfg(blockdata):

    def __init__(self, filename):
        self.initialize()
        if not filename=='':
            self.load(filename)

    def initialize(self):
        self.blocks = []
        self.filename = ""
        self.path = ""
        self.current_field = None
        self.current_record = {}
        self.BOF = True
        self.EOF = False
        self.has_errors = False
        self.has_warnings = False
        self.key_field = None   # not implimented yet
        self.description = ''   # not implimented yet

    def empty_record(self):
        if self.current_record:
            for key in self.current_record:
                if not self.get(key).carry:
                    self.current_record[key] = ''
                if self.get(key).inputtype == 'DATETIME':
                    self.current_record[key] = datetime.datetime.now()

    def validate_current_record(self):
        return(True)

    def get(self, field_name):
        if not field_name:
            return('')
        else:
            f = field(field_name)
            f.name = field_name
            f.inputtype = self.get_value(field_name, 'TYPE')
            f.prompt = self.get_value(field_name, 'PROMPT')
            f.length = self.get_value(field_name, 'LENGTH')
            f.unique = self.get_value(field_name,"UNIQUE").upper() == 'TRUE'
            f.increment = self.get_value(field_name,"INCREMENT").upper() == 'TRUE'
            f.carry = self.get_value(field_name,"CARRY").upper() == 'TRUE'
            f.required = self.get_value(field_name,"REQUIRED").upper() == 'TRUE'
            if self.get_value(field_name, 'MENU'):
                f.menu = self.get_value(field_name, 'MENU').split(",")
            else:
                f.menu = ''
            f.info = self.get_value(field_name, 'INFO')
            f.infofile = self.get_value(field_name, 'INFO FILE')
            for condition_no in range(1, 6):
                if self.get_value(field_name, "CONDITION%s" % condition_no):
                    f.conditions.append(self.get_value(field_name, "CONDITION%s" % condition_no))
            return(f)

    def put(self, field_name, f):
        self.update_value(field_name, 'PROMPT', f.prompt)
        self.update_value(field_name, 'LENGTH', f.length)
        self.update_value(field_name, 'TYPE', f.inputtype)
        #self.update_value(field_name, 'MENU', f.menu)

    def get_field_data(self, field_name = None):
        f = field_name
        if not f:
            if self.current_field:
                f = self.current_field.name
            else:
                return(None)
        if f in self.current_record.keys():
            return(self.current_record[f])
        else:
            return(None)

    def fields(self):
        field_names = self.names()
        del_fields = ['E5']
        for del_field in del_fields:
            if del_field in field_names:
                field_names.remove(del_field)
        return(field_names)

    def build_default(self):
        pass

    def data_is_valid(self):
        if self.current_field.required and self.current_record[self.current_field.name]=='':
            return('\nError: This field is marked as required.  Please provide a response.')
        if self.current_field.unique:
            if self.current_record[self.current_field.name]=='':
                return('\nError: This field is marked as unique.  Empty entries are not allowed in unique fields.')
            for data_row in e4_data.db:
                if self.current_field.name in data_row:
                    if data_row[self.current_field.name] == self.current_record[self.current_field.name]:
                        return('\nError: This field is marked as unique and you are trying to add a duplicate entry.')
        if self.current_field.inputtype == 'NUMERIC':
            try:
                val = int(self.current_record[self.current_field.name])
            except ValueError:
                return('\nError: This field is marked as numeric but a non-numeric value was provided.')
        return(True)

    def is_valid(self):
        # Check to see that conditions are numbered 
        self.has_errors = False
        self.has_warnings = False
        self.errors = []
        if len(self.fields())==0:
            self.errors.append('Error: No fields defined in the CFG file.')
            self.errors.has_errors = True
        else:
            prior_fieldnames = []
            for field_name in self.fields():

                for field_option in ['UNIQUE','CARRY','INCREMENT','REQUIRED']:
                    if self.get_value(field_name, field_option):
                        if self.get_value(field_name, field_option).upper() == 'YES':
                            self.update_value(field_name, field_option, 'TRUE')

                f = self.get(field_name)

                if self.get_value(field_name, "LENGTH"):
                    test = False
                    try:
                        test = int(f.length) > 0 and int(f.length) < 256
                    except:
                        pass
                    if not test:
                        self.errors.append('Error: The length specified for field %s must be between 1 and 255.' % field_name)
                        self.has_errors = True

                if f.prompt == '':
                    f.prompt = field_name

                f.inputtype = f.inputtype.upper()
                if not f.inputtype in ['TEXT','NUMERIC','MENU','DATETIME','BOOLEAN','CAMERA','GPS','INSTRUMENT']:
                    self.errors.append('Error: The value %s for the field %s is not a valid input type.  Valid input types include Text, Numeric, Instrument, Menu, Datetime, Boolean, Camera and GPS.' % (f.inputtype, field_name))
                    self.has_errors = True

                if f.inputtype == 'MENU' and len(f.menu)==0:
                    self.errors.append('Error: The field %s is listed a menu, but no menu list was provided with a MENU option.' % field_name)
                    self.has_errors = True

                if any((c in set(r' !@#$%^&*()?/\{}<.,.|+=_-~`')) for c in field_name):
                    self.errors.append('Warning: The field %s has non-standard characters in it.  E5 will attempt to work with it, but it is highly recommended that you rename it as it will likely cause problems elsewhere.' % field_name)
                    self.has_warnings = True

                if len(f.conditions)>0:
                    n = 0
                    for condition in f.conditions:
                        n += 1
                        condition_parsed = condition.split(' ')
                        if len(condition_parsed)<2 or len(condition_parsed)>3:
                            self.errors.append('Error: Condition number %s for the field %s is not correctly formatted.  A condition requires a target field and a matching value.' % (n, field_name))
                            self.has_errors = True
                        else:
                            condition_fieldname = condition_parsed[0]
                            if not condition_fieldname in prior_fieldnames:
                                self.errors.append('Error: Condition number %s for the field %s references field %s which has not been defined prior to this.' % (n, field_name, condition_fieldname))
                                self.has_errors = True
                            else:
                                condition_field = self.get(condition_fieldname)
                                if condition_field.inputtype == 'MENU':
                                    if condition_parsed[1] == 'NOT':
                                        condition_matches = condition_parsed[2].split(',')
                                    else:
                                        condition_matches = condition_parsed[1].split(',')
                                    for condition_match in condition_matches:
                                        if condition_match.upper() not in [x.upper() for x in condition_field.menu]:
                                            self.errors.append('Warning: Condition number %s for the field %s tries to match the value "%s" to the menulist in field %s, but field %s does not contain this value.' % (n, field_name, condition_match, condition_fieldname, condition_fieldname))
                                            self.has_warnings = True
                self.put(field_name, f)
                prior_fieldnames.append(field_name)
        return(self.has_errors)

    def save(self):
        self.write_blocks()

    def load(self, filename):
        self.filename = filename 
        self.path = ntpath.split(filename)[0]
        self.blocks = self.read_blocks()
        if self.blocks==[]:
            self.build_default()
        self.BOF = True
        if len(self.blocks)>0:
            self.EOF = False
        else:
            self.EOF = True
        self.current_field = None
        self.is_valid()

    def status(self):
        txt = 'CFG file is %s\n' % self.filename
        txt += 'and contains %s fields.' % len(self.blocks)
        return(txt)

    def next(self):
        if self.EOF:
            self.current_field = None
        else:
            if self.BOF:
                self.BOF = False
                self.EOF = False
                self.current_field = self.get(self.fields()[0])
            else:
                field_index = self.fields().index(self.current_field.name)
                while True:
                    field_index += 1
                    if field_index > (len(self.fields()) - 1):
                        self.EOF = True
                        self.current_field = None
                        break
                    else:
                        self.current_field = self.get(self.fields()[field_index])
                        if self.condition_test():
                            self.EOF = False
                            self.BOF = False
                            break
        return(self.current_field)

    def previous(self):
        if self.BOF:
            self.current_field = None
        else:
            if self.EOF:
                self.BOF = False
                self.EOF = False
                self.current_field = self.get(self.fields()[-1])
            else:
                field_index = self.fields().index(self.current_field.name)
                while True:
                    field_index -= 1
                    if field_index < 0:
                        self.BOF = True
                        self.current_field = None
                        break
                    else:
                        self.current_field = self.get(self.fields()[field_index])
                        if self.condition_test():
                            self.EOF = False
                            self.BOF = False
                            break
        return(self.current_field)

    def start(self):
        if len(self.fields())>0 and not self.has_errors:
            self.BOF = False
            self.EOF = False
            self.current_field = self.get(self.fields()[0])
            self.empty_record()
        else:
            self.BOF = True
            self.EOF = True
            self.current_field = None
            self.current_record = {}
        return(self.current_field)

    def condition_test(self):
        if len(self.current_field.conditions) == 0:
            return(True)
        condition_value = True
        for condition in self.current_field.conditions:
            condition = condition.split(" ")
            condition_field = condition[0]
            if len(condition) == 2:
                condition_matches = condition[1].upper().split(',')
                condition_not = False
            else:
                condition_matches = condition[2].upper().split(',')
                condition_not = True
            if condition_field in self.current_record.keys():
                if not self.current_record[condition_field].upper() in condition_matches:
                    if not condition_not:
                        condition_value = False 
                else:
                    condition_value = False
            else:
                if not condition_not:
                    condition_value = False
            if not condition_value:
                break
        return(condition_value)

    def write_csvs(self, filename, table):
        try:
            f = open(filename, 'w')
            for row in table:
                csv_row = ''
                for fieldname in self.fields():
                    if fieldname in row.keys():
                        if self.get(fieldname).inputtype in ['NUMERIC','INSTRUMENT']:
                            if csv_row:
                                csv_row = csv_row + ',%s' % row[fieldname] 
                            else:
                                csv_row = "%s" % row[fieldname] 
                        else:
                            if csv_row:
                                csv_row = csv_row + ',"%s"' % row[fieldname]
                            else: 
                                csv_row = '"%s"' % row[fieldname]
                    else:
                        if self.get(fieldname).inputtype in ['NUMERIC','INSTRUMENT']:
                            if csv_row:
                                csv_row = csv_row + ','
                        else:
                            if csv_row:
                                csv_row = csv_row + ',""'
                            else: 
                                csv_row = '""'
                f.write(csv_row + '\n')
            f.close()
            return(None)
        except:
            return('Could not write data to %s.' % (filename))

class LoadDialog(FloatLayout):
    start_path =  ObjectProperty(None)
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    button_color = ObjectProperty(None)
    button_background = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
    button_color = ObjectProperty(None)
    button_background = ObjectProperty(None)
    start_path = ObjectProperty(None)

class MainTextNumericInput(ScrollView):
    def __init__(self, **kwargs):
        super(MainTextNumericInput, self).__init__(**kwargs)
        self.size_hint = (1, None)
        self.size = (Window.width, Window.height/1.9)
        content = GridLayout(cols = 1, spacing = 5, size_hint_y = None)
        content.bind(minimum_height=content.setter('height'))
        content.add_widget(TextInput(size_hint_y = None, multiline = False, id = 'new_item'))
        self.add_widget(content)

class YesNo(Popup):
    def __init__(self, title, message, yes_callback, no_callback, **kwargs):
        super(YesNo, self).__init__(**kwargs)
        content = BoxLayout(orientation = 'vertical')
        label = Label(text = message,
                        size_hint=(1, 1),
                        valign='middle',
                        halign='center')
        label.bind(
            width=lambda *x: label.setter('text_size')(label, (label.width, None)),
            texture_size=lambda *x: label.setter('height')(label, label.texture_size[1]))
        content.add_widget(label)
        button1 = Button(text = 'Yes', size_hint_y = .2,
                            color = e5_colors.button_color,
                            background_color = e5_colors.button_background,
                            background_normal = '')
        content.add_widget(button1)
        button1.bind(on_press = yes_callback)
        button2 = Button(text = 'No', size_hint_y = .2,
                            color = e5_colors.button_color,
                            background_color = e5_colors.button_background,
                            background_normal = '')
        content.add_widget(button2)
        button2.bind(on_press = no_callback)
        self.title = title
        self.content = content
        self.size_hint = (.8, .8)
        self.size=(400, 400)
        self.auto_dismiss = False

class MessageBox(Popup):
    def __init__(self, title, message, call_back = None, button_text = 'OK', **kwargs):
        super(MessageBox, self).__init__(**kwargs)
        popup_contents = GridLayout(cols = 1, spacing = 5)
        popup_contents.add_widget(e5_scrollview_label(message, color = POPUP_TEXT_COLOR))
        if not call_back:
            call_back = self.dismiss
        popup_contents.add_widget(e5_button(button_text,
                                            call_back = call_back,
                                            selected = True,
                                            button_height = .1))
        self.title = title
        self.content = popup_contents
        self.size_hint = (.8, .8)
        self.size = (400, 400)
        self.auto_dismiss = False

class e5_label(Label):
    def __init__(self, text, popup = False, **kwargs):
        super(e5_label, self).__init__(**kwargs)
        self.text = text
        if not popup:
            self.color = e5_colors.text_color
        else:
            self.color = e5_colors.popup_text_color

class e5_side_by_side_buttons(GridLayout):
    def __init__(self, text, id = ['',''], selected = [False, False],
                     call_back = [None,None], button_height = None, **kwargs):
        super(e5_side_by_side_buttons, self).__init__(**kwargs)
        self.cols = 2
        self.spacing = 5
        self.size_hint_y = button_height
        self.add_widget(e5_button(text[0], id = id[0], selected = selected[0], call_back = call_back[0], button_height=button_height))
        self.add_widget(e5_button(text[1], id = id[1], selected = selected[1], call_back = call_back[1], button_height=button_height))

class e5_button(Button):
    def __init__(self, text, id = '', selected = False, call_back = None, button_height = None, **kwargs):
        super(e5_button, self).__init__(**kwargs)
        self.text = text
        self.size_hint_y = button_height
        self.id = id
        self.color = e5_colors.button_color
        if selected:
            self.background_color = e5_colors.button_background
            self.id = '*' + self.id 
        else:
            self.background_color = e5_colors.optionbutton_background
        if call_back:
            #self.on_press = call_back
            self.bind(on_press = call_back)
        self.background_normal = ''

class e5_scrollview_menu(ScrollView):
    def __init__(self, menu_list, menu_selected, widget_id = '', call_back = None, ncols = 1, **kwargs):
        super(e5_scrollview_menu, self).__init__(**kwargs)
        scrollbox = GridLayout(cols = ncols,
                                size_hint_y = None,
                                id = widget_id + '_box',
                                spacing = 5)
        scrollbox.bind(minimum_height = scrollbox.setter('height'))

        for menu_item in menu_list:
            if menu_item == menu_selected:
                scrollbox.add_widget(e5_button(menu_item, menu_item,
                                        selected = True, call_back = call_back))
            else:
                scrollbox.add_widget(e5_button(menu_item, menu_item,
                                        selected = False, call_back = call_back))
        self.size_hint = (1,1)
        self.id = widget_id + '_scroll'
        self.add_widget(scrollbox)

class e5_scrollview_label(ScrollView):
    def __init__(self, text, widget_id = '', color = None, **kwargs):
        super(e5_scrollview_label, self).__init__(**kwargs)
        scrollbox = GridLayout(cols = 1,
                                size_hint_y = None,
                                id = widget_id + '_box',
                                spacing = 5)
        scrollbox.bind(minimum_height = scrollbox.setter('height'))

        if not color:
            color = e5_colors.text_color

        info = Label(text = text, markup = True,
                    size_hint_y = None,
                    color = color,
                    id = widget_id + '_label',
                    text_size = (self.width, None),
                    font_size = e5_colors.text_font_size)

        info.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        info.bind(width=lambda instance, value: setattr(instance, 'text_size', (value * .95, None)))

        #info.bind(texture_size=lambda *x: info.setter('height')(info, info.texture_size[1]))
        scrollbox.add_widget(info)
        
        self.bar_width = SCROLLBAR_WIDTH
        self.size_hint = (1,1)
        self.id = widget_id + '_scroll'
        self.add_widget(scrollbox)

class MainScreen(Screen):

    popup = ObjectProperty(None)
    popup_open = False
    event = ObjectProperty(None)
    widget_with_focus = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Used for KV file settings
        self.text_color = e5_colors.text_color
        self.button_color = e5_colors.button_color
        self.button_background = e5_colors.button_background

        self.add_widget(BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
                                id = 'mainscreen',
                                padding = 20,
                                spacing = 20))

        self.fpath = ''

        self.build_mainscreen()


    def build_mainscreen(self):

        mainscreen = self.get_widget_by_id('mainscreen')
        mainscreen.clear_widgets()

        if e4_cfg.filename:
            e4_cfg.start()

            if not e4_cfg.EOF or not e4_cfg.BOF:
                self.data_entry()
                if e4_cfg.has_warnings:
                    self.event = Clock.schedule_once(self.show_popup_message, 1)
            else:
                self.cfg_menu()
                self.event = Clock.schedule_once(self.show_popup_message, 1)

        else:
            self.cfg_menu()

    def set_dropdown_menu_colors(self):
        pass

    def get_path(self):
        if e4_ini.get_value("E5", "CFG"):
            return(ntpath.split(e4_ini.get_value("E5", "CFG"))[0])
        else:
            return(os.getcwd())

    def get_files(self, fpath, exts = None):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(fpath):
            files.extend(filenames)
            break
        if exts:
            return([filename for filename in files if filename.upper().endswith(exts.upper())])
        else:
            return(files)

    def cfg_menu(self):

        mainscreen = self.get_widget_by_id('mainscreen')

        self.cfg_files = self.get_files(self.get_path(), 'cfg')

        if self.cfg_files:

            self.cfg_file_selected = self.cfg_files[0]
        
            lb = Label(text = 'Begin data entry with one of these CFG files',
                        color = e5_colors.text_color,
                        size_hint_y = .1)
            mainscreen.add_widget(lb)

            mainscreen.add_widget(e5_scrollview_menu(self.cfg_files,
                                                     self.cfg_file_selected,
                                                     widget_id = 'cfg',
                                                     call_back = self.cfg_selected))
            self.scroll_menu = self.get_widget_by_id('cfg_scroll')
            self.make_scroll_menu_item_visible()
            self.widget_with_focus = self.scroll_menu

        else:
            label_text = '\nBefore data entry can begin, you need to have a CFG file.  The current folder contains none.  Either switch to a folder that contains CFG files or create one.' 
            mainscreen.add_widget(Label(text = label_text, id = 'label',
                                        color = e5_colors.text_color))
            self.widget_with_focus = mainscreen

    def cfg_selected(self, value):
        self.cfg_load(os.path.join(self.get_path(), value.text))
        
    def cfg_load(self, cfgfile_name):
        e4_cfg.load(cfgfile_name)
        e4_ini.update()
        self.build_mainscreen()

    def show_popup_message(self, dt):
        self.event.cancel()
        message_text = SPLASH_HELP
        title = 'E5'
        if e4_cfg.has_errors:
            message_text = 'The following errors in the configuration file %s must be fixed before data entry can begin.\n\n' % e4_cfg.filename
            e4_cfg.filename = ''
            title = 'CFG File Errors'                
        elif e4_cfg.has_warnings:
            e4_cfg.has_warnings = False
            message_text = '\nThough data entry can start, there are the following warnings in the configuration file %s.\n\n' % e4_cfg.filename
            title = 'Warnings'
        message_text = message_text + '\n\n'.join(e4_cfg.errors)
        self.popup = MessageBox(title, message_text, call_back = self.close_popup)
        self.popup.open()
        self.popup_open = True

    def message(self, message_text):
        mainscreen = self.get_widget_by_id('mainscreen')
        mainscreen.clear_widgets()
        mainscreen.add_widget(e5_scrollview_label(text = message_text))

    def data_entry(self):

        mainscreen = self.get_widget_by_id('mainscreen')
        #inputbox.bind(minimum_height = inputbox.setter('height'))

        label = Label(text = e4_cfg.current_field.prompt,
                    size_hint = (1, .1),
                    color = e5_colors.text_color,
                    id = 'field_prompt',
                    halign = 'center',
                    font_size = e5_colors.text_font_size)
        mainscreen.add_widget(label)
        label.bind(texture_size = label.setter('size'))
        label.bind(size_hint_min_x = label.setter('width'))

        kb = TextInput(size_hint = (1, .07),
                            multiline = False,
                            write_tab = False,
                            id = 'field_data',
                            font_size = e5_colors.text_font_size)
        mainscreen.add_widget(kb)
        self.widget_with_focus = kb
        self.scroll_menu = None
        kb.focus = True

        scroll_content = BoxLayout(orientation = 'horizontal',
                                    size_hint = (1, .6),
                                    id = 'scroll_content',
                                    spacing = 20)
        self.add_scroll_content(scroll_content)
        mainscreen.add_widget(scroll_content)

        buttons = GridLayout(cols = 2, size_hint = (1, .2), spacing = 20)
        
        buttons.add_widget(e5_button('Back', id = 'back', selected = True, call_back = self.go_back))
        
        buttons.add_widget(e5_button('Next', id = 'next', selected = True, call_back = self.go_next))
        
        mainscreen.add_widget(buttons)
        
        #self.add_widget(mainscreen)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down = self._on_keyboard_down)
        self._keyboard = None

    def scroll_menu_clear_selected(self):
        for widget in self.scroll_menu.children[0].children:
            if widget.id[0] == '*':
                widget.id = widget.id[1:]
                widget.background_color = e5_colors.optionbutton_background
                break

    def scroll_menu_get_selected(self):
        for widget in self.scroll_menu.children[0].children:
            if widget.id[0] == '*':
                return(widget)

    def scroll_menu_set_selected(self, text):
        for widget in self.scroll_menu.children[0].children:
            if widget.text == text:
                widget.background_color = e5_colors.button_background
                if not widget.id[0] == "*":
                    widget.id = "*" + widget.id
                break

    def scroll_menu_list(self):
        menu_list = []
        for widget in self.scroll_menu.children[0].children:
            menu_list.append(widget.text)
        menu_list.reverse()
        return(menu_list)
        # return([widget.text for widget in self.scroll_menu.children])

    def make_scroll_menu_item_visible(self):
        if self.scroll_menu:
            self.scroll_menu.scroll_to(self.scroll_menu_get_selected())

    def move_scroll_menu_item(self, ascii_code):
        menu_list = self.scroll_menu_list()
        index_no = menu_list.index(self.scroll_menu_get_selected().text)

        if index_no >= 0:
            new_index = -1
            if ascii_code == 279:
                new_index = len(menu_list) - 1
            elif ascii_code == 278:
                new_index = 0
            elif ascii_code in [273, 276] and index_no > 0:
                new_index = index_no - 1
            elif ascii_code in [274, 275] and index_no < (len(menu_list) - 1):
                new_index = index_no + 1
            if new_index >= 0:
                self.scroll_menu_clear_selected()
                self.scroll_menu_set_selected(menu_list[new_index])
                self.make_scroll_menu_item_visible()
                if self.get_widget_by_id('field_data'):
                    self.get_widget_by_id('field_data').text = menu_list[new_index]

    def scroll_menu_char_match(self, match_str):

        menu_list = self.scroll_menu_list()
        index_no = menu_list.index(self.scroll_menu_get_selected().text)

        new_index = (index_no + 1) % len(menu_list)
        while not new_index == index_no:
            if menu_list[new_index].upper()[0] == match_str.upper():
                self.scroll_menu_clear_selected()
                self.scroll_menu_set_selected(menu_list[new_index])
                self.make_scroll_menu_item_visible()
                if self.get_widget_by_id('field_data'):
                    self.get_widget_by_id('field_data').text = menu_list[new_index]
                break
            else:
                new_index = (new_index + 1) % len(menu_list)
                # need new logic to auto select when only one case is available

    def get_widget_by_id(self, id):
        for widget in self.walk():
            if widget.id == id:
                return(widget)
        return(None)

    def _on_keyboard_down(self, *args):
        ascii_code = args[1]
        text_str = args[3]  
        print('INFO: The key %s has been pressed %s' % (ascii_code, text_str))
        if not self.popup_open:
            if ascii_code == 9 or ascii_code == 8:
                if self.widget_with_focus.id == 'menu_scroll':
                    self.widget_with_focus = self.get_widget_by_id('field_data')
                    self.widget_with_focus.focus = True
                elif self.widget_with_focus.id == 'field_data' and e4_cfg.current_field.inputtype in ['MENU','BOOLEAN']:
                    self.widget_with_focus.focus = False
                    self.widget_with_focus = self.get_widget_by_id('menu_scroll')
                return False
            if ascii_code == 27:
                if e4_cfg.filename:
                    self.go_back(None)
            if ascii_code == 13:
                if e4_cfg.filename:
                    if e4_cfg.current_field.inputtype in ['MENU','BOOLEAN'] and self.get_widget_by_id('field_data').text =='':
                        self.get_widget_by_id('field_data').text = self.scroll_menu_get_selected().text 
                    self.go_next(None)
                else:
                    self.cfg_selected(self.scroll_menu_get_selected())
            if ascii_code == 51:
                return True 
            if ascii_code in [273, 274, 275, 276, 278, 279] and self.scroll_menu:
                self.move_scroll_menu_item(ascii_code)
                return False 
            if text_str:
                if text_str.upper() in ascii_uppercase:
                    self.scroll_menu_char_match(text_str)
                    return False
        else:
            if ascii_code == 13:
                self.close_popup(None)
                self.widget_with_focus.focus = True
                return False
        return True # return True to accept the key. Otherwise, it will be used by the system.

    def add_scroll_content(self, content_area):
    
        content_area.clear_widgets()

        info_exists = e4_cfg.current_field.info or e4_cfg.current_field.infofile
        menu_exists = e4_cfg.current_field.inputtype == 'BOOLEAN' or e4_cfg.current_field.menu
        camera_exists = e4_cfg.current_field.inputtype == 'CAMERA'

        if menu_exists or info_exists or camera_exists:

            if camera_exists:
                bx = BoxLayout(orientation = 'vertical')
                bx.add_widget(Camera(play=True, size_hint_y = .8,
                                         resolution = (320,160)))
                bx.add_widget(e5_button(text = "Snap",
                                        id = "snap", selected = True))                
                content_area.add_widget(bx)

            if menu_exists:
                if info_exists:
                    no_cols = int(content_area.width/2/150)
                else:
                    no_cols = int(content_area.width/150)
                if no_cols < 1:
                    no_cols = 1

                if e4_cfg.current_field.inputtype == 'BOOLEAN':
                    menu_list = ['True','False']
                else:
                    menu_list = e4_cfg.current_field.menu

                selected_menu = e4_cfg.get_field_data('')
                if not selected_menu:
                    selected_menu = menu_list[0]

                if info_exists:
                    ncols = int(content_area.width / 400)
                else:
                    ncols = int(content_area.width / 200)
                if ncols < 1:
                    ncols = 1

                content_area.add_widget(e5_scrollview_menu(menu_list,
                                                           selected_menu,
                                                           widget_id = 'menu',
                                                           call_back = self.menu_selection,
                                                           ncols = ncols))
                self.scroll_menu = self.get_widget_by_id('menu_scroll')
                self.make_scroll_menu_item_visible()
                self.widget_with_focus = self.scroll_menu

            if info_exists:
                content_area.add_widget(e5_scrollview_label(self.get_info()))

    def get_info(self):
        if e4_cfg.current_field.infofile:
            fname = os.path.join(e4_cfg.path, e4_cfg.current_field.infofile)
            if os.path.exists(fname):
                try:
                    with open(fname, 'r') as f:
                        return(f.read())
                except:
                    return('Could not open file %s.' % fname)
            else:
                return('The file %s does not exist.' % fname)
        else:
            return(e4_cfg.current_field.info)

    def on_enter(self):
        pass

    def on_pre_enter(self):
        Window.bind(on_key_down = self._on_keyboard_down)
        print('mainscreen')
        if e5_colors.need_redraw:
            pass

    def exit_program(self):
        e4_ini.update_value('E5','TOP', Window.top)
        e4_ini.update_value('E5','LEFT', Window.left)
        e4_ini.update_value('E5','WIDTH', Window.width)
        e4_ini.update_value('E5','HEIGHT', Window.height)
        e4_ini.save()
        App.get_running_app().stop()

    def show_save_csvs(self):
        content = SaveDialog(start_path = e4_cfg.path,
                            save = self.save_csvs, 
                            cancel = self.dismiss_popup,
                            button_color = e5_colors.button_color,
                            button_background = e5_colors.button_background)
        self.popup = Popup(title = "Select a folder for the  CSV files", content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def save_csvs(self, path):

        self.popup.dismiss()

        filename = ntpath.split(e4_cfg.filename)[1].split(".")[0]
        filename = os.path.join(path, filename + '.csv' )

        table = e4_data.db.table('_default')

        errors = e4_cfg.write_csvs(filename, table)
        title = 'CSV Export'
        if errors:
            self.popup = MessageBox(title, errors, call_back = self.close_popup)
        else:
            self.popup = MessageBox(title, '%s successfully written.' % filename, call_back = self.close_popup)
        self.popup.open()
        self.popup_open = True

    def show_load_cfg(self):
        content = LoadDialog(load = self.load, 
                            cancel = self.dismiss_popup,
                            start_path = os.path.dirname(os.path.abspath( __file__ )),
                            button_color = e5_colors.button_color,
                            button_background = e5_colors.button_background)
        self.popup = Popup(title = "Load CFG file", content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def load(self, path, filename):
        self.dismiss_popup()
        self.cfg_load(os.path.join(path, filename[0]))

    def dismiss_popup(self):
        self.popup.dismiss()
        self.parent.current = 'MainScreen'

    def update_mainscreen(self):
        for widget in self.walk():
            if widget.id=='field_prompt':
                widget.text = e4_cfg.current_field.name
            if widget.id == 'field_data':
                if e4_cfg.current_field.name in e4_cfg.current_record.keys():
                    widget.text = e4_cfg.current_record[e4_cfg.current_field.name]
                else:
                    widget.text = ''
                self.widget_with_focus = widget
                self.scroll_menu = None
            if widget.id=='scroll_content':
                self.add_scroll_content(widget)    
                break
        self.widget_with_focus.focus = True

    def save_field(self):
        widget = self.get_widget_by_id('field_data')
        e4_cfg.current_record[e4_cfg.current_field.name] = widget.text 
        widget.text = ''

    def go_back(self, *args):
        if e4_cfg.filename:
            self.save_field()
            e4_cfg.previous()
            if e4_cfg.BOF:
                e4_cfg.filename = ''
                self.build_mainscreen()
            else:
                self.update_mainscreen()

    def go_next(self, *args):
        self.save_field()
        valid_data = e4_cfg.data_is_valid()
        if valid_data == True:
            e4_cfg.next()
            if e4_cfg.EOF:
                self.save_record()
                e4_cfg.start()
            self.update_mainscreen()
        else:
            widget = self.get_widget_by_id('field_data')
            widget.text = e4_cfg.current_record[e4_cfg.current_field.name] 
            widget.focus = True
            self.popup = MessageBox(e4_cfg.current_field.name, valid_data, call_back = self.close_popup)
            self.popup.open()
            self.popup_open = True

    def menu_selection(self, value):
        self.get_widget_by_id('field_data').text = value.text
        self.go_next(value)

    def save_record(self):
        valid = e4_cfg.validate_current_record()
        if valid:
            e4_data.db.insert(e4_cfg.current_record)
        else:
            self.popup = MessageBox('Save Error', valid, call_back=self.close_popup)
            self.popup.open()
            self.popup_open = True

    def close_popup(self, value):
        self.popup.dismiss()
        self.popup_open = False
        self.event = Clock.schedule_once(self.set_focus, 1)

    def set_focus(self, value):
        self.widget_with_focus.focus = True

class MenuList(Popup):
    def __init__(self, title, menu_list, call_back, **kwargs):
        super(MenuList, self).__init__(**kwargs)
        
        pop_content = GridLayout(cols = 1, size_hint_y = 1, spacing = 5, padding = 5)

        new_item = GridLayout(cols = 2, spacing = 5, size_hint_y = .1)
        new_item.add_widget(TextInput(id = 'new_item', size_hint_y = .1))
        new_item.add_widget(e5_button('Add', id = title,
                                             selected = True,
                                             call_back = call_back,
                                             button_height = .1))
        pop_content.add_widget(new_item)

        ncols = int(Window.width / 200)
        if ncols < 1:
            ncols = 1

        pop_content.add_widget(e5_scrollview_menu(menu_list, '', call_back = call_back, ncols = ncols))

        pop_content.add_widget(e5_button('Back', selected = True, call_back = self.dismiss))

        self.content = pop_content
        
        self.title = title
        self.size_hint = (.8, .8)
        self.auto_dismiss = True

class TextNumericInput(Popup):
    def __init__(self, title, call_back, **kwargs):
        super(TextNumericInput, self).__init__(**kwargs)
        content = GridLayout(cols = 1, spacing = 5, padding = 5, size_hint_y = None)
        content.add_widget(TextInput(size_hint_y = .1, multiline = False, id = 'new_item'))
        content.add_widget(e5_side_by_side_buttons(['Back','Next'],
                                                    button_height = .2,
                                                    id = [title,title],
                                                    selected = [True, True],
                                                    call_back = [self.dismiss, call_back]))
        self.title = title
        self.content = content
        self.size_hint = (.8, .3)
        self.auto_dismiss = True

class TextLabel(Label):
    def __init__(self, text, **kwargs):
        super(TextLabel, self).__init__(**kwargs)
        self.text = text
        self.color = e5_colors.text_color
        self.font_size = e5_colors.text_font_size
        self.size_hint_y = None
        
class EditCFGScreen(Screen):

    def on_pre_enter(self):
        #super(Screen, self).__init__(**kwargs)
        self.clear_widgets()

        layout = GridLayout(cols = 1,
                            size_hint_y = None, id = 'fields')
        layout.bind(minimum_height=layout.setter('height'))

        for field_name in e4_cfg.fields():
            f = e4_cfg.get(field_name)
            bx = GridLayout(cols = 1, size_hint_y = None)
            bx.add_widget(TextLabel("[" + f.name + "]"))
            layout.add_widget(bx)

            bx = GridLayout(cols = 2, size_hint_y = None)
            bx.add_widget(TextLabel("Prompt"))
            bx.add_widget(TextInput(text = f.prompt,
                                        multiline = False, size_hint_y = None))
            layout.add_widget(bx)

            bx = GridLayout(cols = 2, size_hint_y = None)
            bx.add_widget(TextLabel("Type"))
            bx.add_widget(Spinner(text="Text", values=("Text", "Numeric", "Menu"),
                                        #id = 'station',
                                        size_hint=(None, None),
                                        pos_hint={'center_x': .5, 'center_y': .5},
                                        color = e5_colors.optionbutton_color,
                                        background_color = e5_colors.optionbutton_background,
                                        background_normal = ''))
            #self.StationMenu.size_hint  = (0.3, 0.2)
            layout.add_widget(bx)

            bx = GridLayout(cols = 6, size_hint_y = None)
            
            bx.add_widget(TextLabel("Carry"))
            bx.add_widget(Switch(active = f.carry))

            bx.add_widget(TextLabel("Unique"))
            bx.add_widget(Switch(active = f.unique))

            bx.add_widget(TextLabel("Increment"))
            bx.add_widget(Switch(active = f.increment))

            layout.add_widget(bx)
            
            if f.inputtype == 'MENU':
                bx = GridLayout(cols = 1, size_hint_y = None)
                button1 = Button(text = 'Edit Menu', size_hint_y = None,
                                color = e5_colors.optionbutton_color,
                                background_color = e5_colors.optionbutton_background,
                                background_normal = '',
                                id = f.name)
                bx.add_widget(button1)
                button1.bind(on_press = self.show_menu)
                layout.add_widget(bx)

        root = ScrollView(size_hint=(1, .8))
        root.add_widget(layout)
        self.add_widget(root)

        buttons = GridLayout(cols = 2, spacing = 10, size_hint_y = None)

        button2 = Button(text = 'Back', size_hint_y = None,
                        color = e5_colors.button_color,
                        background_color = e5_colors.button_background,
                        background_normal = '')
        buttons.add_widget(button2)
        button2.bind(on_press = self.go_back)

        button3 = Button(text = 'Save Changes', size_hint_y = None,
                        color = e5_colors.button_color,
                        background_color = e5_colors.button_background,
                        background_normal = '')
        buttons.add_widget(button3)
        button3.bind(on_press = self.save)

        self.add_widget(buttons)

    def go_back(self, value):
        self.parent.current = 'MainScreen'

    def save(self, value):
        self.parent.current = 'MainScreen'

    def show_menu(self):
        pass

class E5SettingsScreen(Screen):
    def __init__(self,**kwargs):
        super(E5SettingsScreen, self).__init__(**kwargs)

        self.build_screen()

    def build_screen(self):
        self.clear_widgets()
        layout = GridLayout(cols = 1,
                                size_hint_y = 1,
                                id = 'settings_box',
                                spacing = 5, padding = 5)
        layout.bind(minimum_height = layout.setter('height'))

        darkmode = GridLayout(cols = 2, size_hint_y = .1, spacing = 5, padding = 5)
        darkmode.add_widget(e5_label('Dark Mode'))
        darkmode_switch = Switch(active = e5_colors.darkmode)
        darkmode_switch.bind(active = self.darkmode)
        darkmode.add_widget(darkmode_switch)
        layout.add_widget(darkmode)

        colorscheme = GridLayout(cols = 2, size_hint_y = .6, spacing = 5, padding = 5)
        colorscheme.add_widget(e5_label('Color Scheme'))
        colorscheme.add_widget(e5_scrollview_menu(e5_colors.color_names(),
                                                  menu_selected = '',
                                                  call_back = self.color_scheme_selected))
        current_scheme = e5_colors.color_scheme
        for widget in colorscheme.walk():
            if widget.id in e5_colors.color_names():
                e5_colors.set_to(widget.text)
                widget.background_color = e5_colors.button_background
        layout.add_widget(colorscheme)
        e5_colors.set_to(current_scheme)
        
        backups = GridLayout(cols = 2, size_hint_y = .3, spacing = 5, padding = 5)
        backups.add_widget(e5_label('Auto-backup after\nevery how many\nrecords entered?'))
        backups.add_widget(Slider(min = 0, max = 200,
                                 value = 0, orientation = 'horizontal', id = 'backup_interval',
                                 value_track = True, value_track_color= e5_colors.button_background))
        backups.add_widget(e5_label('Use incremental backups?'))
        backups_switch = Switch(active = False)
        backups_switch.bind(active = self.incremental_backups)
        backups.add_widget(backups_switch)
        layout.add_widget(backups)

        settings_layout = GridLayout(cols = 1, size_hint_y = 1, spacing = 5, padding = 5)
        scrollview = ScrollView(size_hint = (1, 1),
                                 bar_width = SCROLLBAR_WIDTH)
        scrollview.add_widget(layout)
        settings_layout.add_widget(scrollview)
        settings_layout.add_widget(e5_button('Back', selected = True, call_back = self.go_back))
        self.add_widget(settings_layout)

    def incremental_backups(self, instance, value):
        e4_ini.incremental_backups = value

    def darkmode(self, instance, value):
        if value:
            e5_colors.set_to_darkmode()
        else:
            e5_colors.set_to_lightmode()
        self.build_screen()

    def color_scheme_selected(self, instance):
        e5_colors.set_to(instance.text)
        self.build_screen()

    def go_back(self, instance):
        for widget in self.walk():
            if widget.id == 'backup_interval':
                e4_ini.backup_interval = int(widget.value)
        e4_ini.update()
        self.parent.current = 'MainScreen'

class InfoScreen(Screen):

    content = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(InfoScreen, self).__init__(**kwargs)
        layout = GridLayout(cols = 1, size_hint_y = 1, spacing = 5, padding = 5)
        layout.add_widget(e5_scrollview_label(text = '', widget_id = 'content'))
        layout.add_widget(e5_button('Back', selected = True, call_back = self.go_back))
        self.add_widget(layout)
        for widget in self.walk():
            if widget.id == 'content_label':
                self.content = widget

    def go_back(self, *args):
        self.parent.current = 'MainScreen'

class StatusScreen(InfoScreen):
    def on_pre_enter(self):
        txt = e4_data.status() + e4_cfg.status() + e4_ini.status()
        self.content.text = txt

class LogScreen(InfoScreen):
    def on_pre_enter(self):
        with open('E4.log','r') as f:
            self.content.text = f.read()

class AboutScreen(InfoScreen):
    def on_pre_enter(self):
        self.content.text = '\n\nE4py by Shannon P. McPherron\n\nVersion ' + __version__ + ' Alpha\nApple Pie\n\nAn OldStoneAge.Com Production\n\nJanuary, 2019'
        self.content.halign = 'center'
        self.content.valign = 'middle'

class CFGScreen(InfoScreen):
    def on_pre_enter(self):
        with open(e4_cfg.filename,'r') as f:
            self.content.text = f.read()

class INIScreen(InfoScreen):
    def on_pre_enter(self):
        with open(e4_ini.filename,'r') as f:
            self.content.text = f.read()

class EditPointsScreen(Screen):
    def __init__(self,**kwargs):
        super(EditPointsScreen, self).__init__(**kwargs)
        if e4_data:
            self.add_widget(DfguiWidget(e4_data, e4_cfg.fields()))

    def on_pre_enter(self):
        Window.bind(on_key_down = self._on_keyboard_down)

    def _on_keyboard_down(self, *args):
        print('key')
        ### On key down, see if there is a current record,
        # get the next record in the db,
        # and then try to fire the highlight record stuff
        return True

    def on_leave(self):
        Window.unbind(on_key_down = self._on_keyboard_down)

# Code from https://github.com/MichaelStott/DataframeGUIKivy/blob/master/dfguik.py

class HeaderCell(Button):
    def __init__(self,**kwargs):
        super(HeaderCell, self).__init__(**kwargs)
        self.background_color = e5_colors.button_background
        self.background_normal = ''
        self.color = e5_colors.button_color

class TableHeader(ScrollView):
    """Fixed table header that scrolls x with the data table"""
    header = ObjectProperty(None)

    def __init__(self, titles = None, *args, **kwargs):
        super(TableHeader, self).__init__(*args, **kwargs)

        for title in titles:
            self.header.add_widget(HeaderCell(text = title))

class ScrollCell(Button):
    text = StringProperty(None)
    is_even = BooleanProperty(None)
    datagrid_odd = [224.0/255, 224.0/255, 224.0/255, 1]
    datagrid_even = [189.0/255, 189.0/255, 189.0/255, 1]
    def __init__(self,**kwargs):
        super(ScrollCell, self).__init__(**kwargs)
        self.color = e5_colors.button_color
        self.background_normal = ''
        self.datagrid_even = e5_colors.datagrid_even
        self.datagrid_odd = e5_colors.datagrid_odd

class TableData(RecycleView):
    nrows = NumericProperty(None)
    ncols = NumericProperty(None)
    rgrid = ObjectProperty(None)

    popup = ObjectProperty(None)

    def __init__(self, list_dicts=[], column_names = None, df_name = None, *args, **kwargs):
        self.nrows = len(list_dicts)
        self.ncols = len(column_names) 

        super(TableData, self).__init__(*args, **kwargs)

        self.data = []
        for i, ord_dict in enumerate(list_dicts):
            is_even = i % 2 == 0
            for text, value in ord_dict.items():
                self.data.append({'text': value, 'is_even': is_even,
                                    'callback': self.editcell,
                                    'key': ord_dict['doc_id'], 'field': text,
                                    'db': df_name, 'id': 'datacell' })

    def sort_data(self):
        #TODO: Use this to sort table, rather than clearing widget each time.
        pass

    def clear_highlight_row(self):
        if self.parent.parent.parent.parent.datagrid_doc_id:
            key = self.parent.parent.parent.parent.datagrid_doc_id
            for widget in self.get_editcell_row(key):
                widget.background_color = self.parent.parent.parent.parent.datagrid_background_color
            self.parent.parent.parent.parent.datagrid_doc_id = ''        
            self.parent.parent.parent.parent.datagrid_widget_row = []

    def set_highlight_row(self):
        if self.parent.parent.parent.parent.datagrid_doc_id:
            key = self.parent.parent.parent.parent.datagrid_doc_id
            widget_row = self.get_editcell_row(key)
            for widget in widget_row:
                widget.background_color = e5_colors.optionbutton_background
            self.parent.parent.parent.parent.datagrid_widget_row = widget_row

    def get_editcell_row(self, key):
        row_widgets = []
        for widget in self.walk():
            if widget.id == 'datacell':
                if widget.key == key:
                    row_widgets.append(widget)
        return(row_widgets)

    def get_editcell(self, key, field):
        for widget in self.walk():
            if widget.id == 'datacell':
                if widget.field == field and widget.key == key:
                    return(widget)
        return(None)

    def editcell(self, key, field, db):
        self.key = key
        self.clear_highlight_row()
        self.parent.parent.parent.parent.datagrid_doc_id = key
        editcell_widget = self.get_editcell(key, field)
        self.parent.parent.parent.parent.datagrid_background_color = editcell_widget.background_color
        self.set_highlight_row()
        self.field = field
        self.db = db
        cfg_field = e4_cfg.get(field)
        self.inputtype = cfg_field.inputtype
        if cfg_field.inputtype == 'MENU':
            self.popup = MenuList(field, cfg_field.menu, self.menu_selection)
            self.popup.open()
        if cfg_field.inputtype in ['TEXT','NUMERIC']:
            self.popup = TextNumericInput(field, self.menu_selection)
            self.popup.open()

    def menu_selection(self, value):
        ### need some data validation
        print(value.id)
        new_data = {}
        if self.inputtype=='MENU':
            new_data[self.field] = value.text
        else:
            for widget in self.popup.walk():
                if widget.id == 'new_item':
                    new_data[self.field] = widget.text
        field_record = Query()
        e4_data.db.update(new_data, field_record.doc_id == self.key)
        for widget in self.walk():
            if widget.id=='datacell':
                if widget.key == self.key and widget.field == self.field:
                    widget.text = new_data[self.field]
        self.popup.dismiss()

class Table(BoxLayout):

    def __init__(self, list_dicts=[], column_names = None, df_name = None, *args, **kwargs):

        super(Table, self).__init__(*args, **kwargs)
        self.orientation = "vertical"

        self.header = TableHeader(column_names)
        self.table_data = TableData(list_dicts = list_dicts, column_names = column_names, df_name = df_name)

        self.table_data.fbind('scroll_x', self.scroll_with_header)

        self.add_widget(self.header)
        self.add_widget(self.table_data)

    def scroll_with_header(self, obj, value):
        self.header.scroll_x = value

class DataframePanel(BoxLayout):
    """
    Panel providing the main data frame table view.
    """

    def populate_data(self, df, df_fields):
        self.df_orig = df
        self.sort_key = None
        self.column_names = ['doc_id'] + df_fields
        self.df_name = df.db_name
        self.df_fields = df_fields
        self._generate_table()

    def _generate_table(self, sort_key=None, disabled=None):
        self.clear_widgets()
        data = []
        for db_row in self.df_orig.db:
            reformatted_row = {}
            reformatted_row['doc_id'] = str(db_row.doc_id)
            for field in self.df_fields:
                if field in db_row:
                    reformatted_row[field] = db_row[field]
                else:
                    reformatted_row[field] = ''
            data.append(reformatted_row)
        #data = sorted(data, key=lambda k: k[self.sort_key]) 
        self.add_widget(Table(list_dicts = data, column_names = self.column_names, df_name = self.df_name))

class AddNewPanel(BoxLayout):
    
    def populate(self, df, df_fields):
        self.df_name = df.db_name            
        self.addnew_list.bind(minimum_height=self.addnew_list.setter('height'))
        for col in df.fields():
            self.addnew_list.add_widget(AddNew(col, df.db_name))

    def get_addnews(self):
        result=[]
        for opt_widget in self.addnew_list.children:
            result.append(opt_widget.get_addnew())
        return(result)

class AddNew(BoxLayout):

    popup = ObjectProperty(None)
    sorted_result = None

    def __init__(self, col, df_name, **kwargs):
        super(AddNew, self).__init__(**kwargs)
        self.update_db = False
        self.df_name = df_name
        self.widget_type = 'data'
        self.height = "30sp"
        self.size_hint = (0.9, None)
        self.spacing = 10
        label = Label(text = col, color = e5_colors.text_color)
        txt = TextInput(multiline = False,
                                size_hint=(0.75, None),
                                font_size="15sp",
                                id = col)
        txt.bind(minimum_height=txt.setter('height'))
        self.add_widget(label)
        self.add_widget(txt)

    def text_input(self, instance, text):
        pass

    def get_addnew(self):
        return (self.label.text, self.txt.text)

    def append_data(self, instance):
        result = {}
        message = ''
        for obj in instance.parent.parent.children:
            if obj.widget_type=='data':
                result[obj.label.text] = obj.txt.text 
                obj.txt.text = ''
        sorted_result = {}
        ### this code needs one set of if/then that then sets a variable that refres
        ### to the class that is being operated on
        #if self.df_name == 'prisms':
        #    for f in edm_prisms.fields():
        #        sorted_result[f] = result[f]
        #    if edm_prisms.duplicate(sorted_result):
        #        message = 'Overwrite existing prism named %s' % sorted_result['name']
        #    else:
        #        message = edm_prisms.valid(sorted_result)
        #        if not message:
        #            edm_prisms.db.insert(sorted_result)
        #if self.df_name == 'units':
        #    for f in edm_units.fields():
        #        sorted_result[f] = result[f]
        #    edm_units.db.insert(sorted_result)
        #if self.df_name == 'datums':
        #    for f in edm_datums.fields():
        #        sorted_result[f] = result[f]
        #    edm_datums.db.insert(sorted_result)
        if message:
            self.sorted_result = sorted_result
            self.popup = YesNo('Edit', message, self.replace, self.do_nothing)
        else:
            for obj in instance.parent.parent.children:
                if obj.widget_type=='data':
                    obj.txt.text = ''

    def replace(self, value):
        #if self.df_name == 'prisms':
        #    edm_prisms.replace(self.sorted_result)
        #if self.df_name == 'units':
        #    edm_units.replace(self.sorted_result)
        #if self.df_name == 'datums':
        #    edm_datums.replace(self.sorted_result)
        ### Need to clear form here as well
        self.popup.dismiss()

    def do_nothing(self, value):
        self.popup.dismiss()

class DfguiWidget(TabbedPanel):
    datagrid_doc_id = None
    datagrid_background_color = None
    datagrid_widget_row = []
    def __init__(self, df, df_fields, **kwargs):
        super(DfguiWidget, self).__init__(**kwargs)
        self.textboxes_will_update_db = False
        self.df = df
        self.df_name = df.db_name
        self.df_fields = df_fields
        self.panel1.populate_data(df, df_fields)
        self.panel2.populate(df, df_fields)
        self.color = e5_colors.text_color
        self.background_color = e5_colors.window_background
        self.background_image = ''
        for tab_no in [0,1,2]:
            self.tab_list[tab_no].color = e5_colors.button_color
            self.tab_list[tab_no].background_color = e5_colors.button_background

    def open_panel1(self):
        self.textboxes_will_update_db = False

    def open_panel2(self):
        if self.datagrid_doc_id:
            data_record = self.df.db.get(doc_id=int(self.datagrid_doc_id))
            for widget in self.ids.add_new_panel.children[0].walk():
                if widget.id in self.df_fields:
                    if widget.id in data_record:
                        widget.text = data_record[widget.id]
                    else:
                        widget.text = ''
                    widget.bind(text = self.update_db)
            self.textboxes_will_update_db = True

    def update_db(self, instance, value):
        if self.textboxes_will_update_db:
            for widget in self.datagrid_widget_row:
                if widget.field == instance.id and widget.key == self.datagrid_doc_id:
                    widget.text = value
                    update = {widget.field: value}
                    self.df.db.update(update, doc_ids = [int(self.datagrid_doc_id)])
                    break

    def close_panels(self):
        self.parent.parent.current = 'MainScreen'
        
    def cancel(self):
        pass


# End code from https://github.com/MichaelStott/DataframeGUIKivy/blob/master/dfguik.py

class E5py(App):

    def build(self):
        #Window.clearcolor = e5_colors.window_background
        Window.minimum_width = 450
        Window.minimum_height = 450
        if not e4_ini.get_value("E5","TOP") == '':
            temp = int(e4_ini.get_value("E5","TOP"))
            if temp < 0 : 
                temp = 0
            Window.top = temp
        if not e4_ini.get_value("E5","LEFT") == '':
            temp = int(e4_ini.get_value("E5","LEFT"))
            if temp < 0 : 
                temp = 0
            Window.left = temp
        window_width = None
        window_height = None
        if not e4_ini.get_value("E5","WIDTH") == '':
            window_width = int(e4_ini.get_value("E5","WIDTH"))
            if window_width < 450:
                window_width = 450
        if not e4_ini.get_value("E5","HEIGHT") == '':
            window_height = int(e4_ini.get_value("E5","HEIGHT"))
            if window_height < 450:
                window_height = 450
        if window_width and window_height:
            Window.size = (window_width, window_height)
        self.title = "E5 " + __version__
   
Factory.register('E5', cls=E5py)

if __name__ == '__main__':
    logger.info('E5 started.')
    e4_ini = ini('E5.ini')
    e5_colors = ColorScheme(e4_ini.get_value('E5','ColorScheme'))
    if e4_ini.get_value('E5','DarkMode').upper() == 'TRUE':
        e5_colors.set_to_darkmode()
    if e4_ini.get_value("E5", "CFG"):
        e4_cfg = cfg(e4_ini.get_value("E5", "CFG"))
        database = e4_ini.get_value("E5", "TABLE")
        if not database:
            database = ntpath.split(e4_cfg.filename)[1]
        if "." in database:
            database = database.split('.')[0]
        e4_data = db(database + '.json')
        e4_cfg.save()
        e4_ini.update()
        e4_ini.save()
    else:
        e4_cfg = cfg('')
        e4_data = None
    e5_colors.need_redraw = False    
    E5py().run()