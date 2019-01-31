__version__ = '1.0.0'

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
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

import os 
import random
import datetime
import logging

# My libraries for this project
from blockdata import blockdata
from dbs import dbs

# The database - pure Python
from tinydb import TinyDB, Query, where

from collections import OrderedDict

OPTIONBUTTON_BACKGROUND = (128/255, 216/255, 255/255, 1) #80D8FF (lighter blue)
OPTIONBUTTON_COLOR = (0, 0, 0, 1) # black
BUTTON_BACKGROUND = (0, .69, 255/255, 1) #00B0FF (deep blue)
BUTTON_COLOR =  (0, 0, 0, 1) # black
WINDOW_BACKGROUND = (255/255, 255/255, 255/255, 1) #FFFFFF
WINDOW_COLOR = (0, 0, 0, 1)

DATAGRID_ODD = (224.0/255, 224.0/255, 224.0/255, 1)
DATAGRID_EVEN = (189.0/255, 189.0/255, 189.0/255, 1)

class points(dbs):
    MAX_FIELDS = 30
    db = None
    filename = None
    db_name = 'points'

    def __init__(self, filename):
        if filename=='':
            filename = 'EDM_points.json'
        self.filename = filename
        self.db = TinyDB(self.filename)

    def status(self):
        txt = 'The points file is %s\n' % self.filename
        txt += '%s points in the data file\n' % len(self.db)
        txt += 'with %s fields per point' % self.field_count()
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

    def names(self):
        name_list = []
        for row in self.db:
            name_list.append(row['unit'] + '-' + row['id'])
        return(name_list)

    def fields(self):
        global edm_cfg 
        return(edm_cfg.fields())

    def delete_all(self):
        self.db.purge()

    def export_csv(self):
        pass

    def delete_record(self):
        pass

    def add_record(self):
        pass

class ini(blockdata):
    
    blocks = []
    filename = ''

    def __init__(self, filename):
        if filename=='':
            filename = 'EDMpy.ini'
        self.filename = filename
        self.blocks = self.read_blocks()

    def update(self):
        global edm_station
        global edm_cfg
        self.update_value('STATION','TotalStation', edm_station.make)
        self.update_value('STATION','Communication', edm_station.communication)
        self.update_value('STATION','COMPort', edm_station.comport)
        self.update_value('STATION','BAUD', edm_station.baudrate)
        self.update_value('STATION','Parity', edm_station.parity)
        self.update_value('STATION','DataBits', edm_station.databits)
        self.update_value('STATION','StopBits', edm_station.stopbits)
        self.update_value('EDM','CFG', edm_cfg.filename)
        self.save()

    def save(self):
        self.write_blocks()

class cfg(blockdata):

    blocks = []
    filename = ""

    class field:
        name = ''
        inputtype = ''
        prompt = ''
        length = 0
        menu = ''
        increment = False
        required = False
        carry = False 
        unique = False
        link_fields = []
        def __init__(self, name):
            self.name = name

    def __init__(self, filename):
        if filename=='':
            filename = 'EDMpy.cfg'
        self.load(filename)
        self.validate()
    
    def valid_datarecord(self, data_record):
        for field in data_record:
            f = self.get(field)
            value = data_record[field]
            if f.required and not value:
                return('Required field %s is empty.  Please provide a value.' % field)
            if f.length!=0 and len(value) > f.length:
                return('Maximum length for %s is set to %s.  Please shorten your response.  Field lengths can be set in the CFG file.  A value of 0 means no length limit.')
        return(True)

    def get(self, field_name):
        f = self.field(field_name)
        f.inputtype = self.get_value(field_name, 'TYPE')
        f.prompt = self.get_value(field_name, 'PROMPT')
        f.length = self.get_value(field_name, 'LENGTH')
        f.menu = self.get_value(field_name, 'MENU').split(",")
        f.link_fields = self.get_value(field_name, 'LINKED').split(",")
        return(f)

    def put(self, field_name, f):
        self.update_value(field_name, 'PROMPT', f.prompt)
        self.update_value(field_name, 'LENGTH', f.length)
        self.update_value(field_name, 'TYPE', f.inputtype)
        #self.update_value(field_name, 'MENU', f.menu)

    def fields(self):
        field_names = self.names()
        del_fields = ['BUTTON1','BUTTON2','BUTTON3','BUTTON4','BUTTON5','BUTTON6','EDM','TIME']
        for del_field in del_fields:
            if del_field in field_names:
                field_names.remove(del_field)
        return(field_names)

    def build_default(self):
        self.update_value('UNIT', 'Prompt', 'Unit :')
        self.update_value('UNIT', 'Type', 'Text')
        self.update_value('UNIT', 'Length', 6)

        self.update_value('ID', 'Prompt', 'ID :')
        self.update_value('ID', 'Type', 'Text')
        self.update_value('ID', 'Length', 6)

        self.update_value('SUFFIX', 'Prompt', 'Suffix :')
        self.update_value('SUFFIX', 'Type', 'Numeric')

        self.update_value('LEVEL', 'Prompt', 'Level :')
        self.update_value('LEVEL', 'Type', 'Menu')
        self.update_value('LEVEL', 'Length', 20)

        self.update_value('CODE', 'Prompt', 'Code :')
        self.update_value('CODE', 'Type', 'Menu')
        self.update_value('CODE', 'Length', 20)

        self.update_value('EXCAVATOR', 'Prompt', 'Excavator :')
        self.update_value('EXCAVATOR', 'Type', 'Menu')
        self.update_value('EXCAVATOR', 'Length', 20)

        self.update_value('PRISM', 'Prompt', 'Prism :')
        self.update_value('PRISM', 'Type', 'Numeric')

        self.update_value('X', 'Prompt', 'X :')
        self.update_value('X', 'Type', 'Numeric')

        self.update_value('Y', 'Prompt', 'Y :')
        self.update_value('Y', 'Type', 'Numeric')

        self.update_value('Z', 'Prompt', 'Z :')
        self.update_value('Z', 'Type', 'Numeric')

        self.update_value('DATE', 'Prompt', 'Date :')
        self.update_value('DATE', 'Type', 'Text')
        self.update_value('DATE', 'Length', 24)

        # should add hangle, vangle, sloped 

    def validate(self):
        for field_name in self.fields():
            f = self.get(field_name)
            if f.prompt == '':
                f.prompt = field_name
            f.inputtype = f.inputtype.upper()
            if field_name in ['UNIT','ID','SUFFIX','X','Y','Z']:
                f.required = True
            self.put(field_name, f)
        
        # This is a legacy issue.  Linked fields are now listed with each field.
        unit_fields = self.get_value('EDM', 'UNITFIELDS')
        if unit_fields:
            f = self.get('UNIT')
            f.link_fields = unit_fields
            self.put('UNIT', f)
            # Delete UNITIFIELDS from the EDM block of teh CFG

    def save(self):
        self.write_blocks()

    def load(self, filename):
        self.filename = filename 
        self.blocks = self.read_blocks()
        if self.blocks==[]:
            self.build_default()
    
    def status(self):
        txt = 'CFG file is %s\n' % self.filename
        return(txt)

class record_button(Button):
    def __init__(self,id,text,**kwargs):
        super(Button, self).__init__(**kwargs)
        self.text = text
        self.id = id
        self.size_hint_y = None
        self.id = id
        self.color = BUTTON_COLOR
        self.background_color = BUTTON_BACKGROUND
        self.background_normal = ''

class MainScreen(Screen):

    global edm_prisms
    global edm_station

    popup = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(MainScreen, self).__init__(**kwargs)

        global edm_cfg

        layout = GridLayout(cols = 3, spacing = 10, size_hint_y = .8)
        button_count = 0

        if edm_cfg.get_value('BUTTON1','TITLE'):
            button1 = record_button(text = edm_cfg.get_value('BUTTON1','TITLE'), id = 'button1')
            layout.add_widget(button1)
            button1.bind(on_press = self.take_shot)
            button_count += 1

        if edm_cfg.get_value('BUTTON2','TITLE'):
            button2  = record_button(text = edm_cfg.get_value('BUTTON2','TITLE'), id = 'button2')
            layout.add_widget(button2)
            button2.bind(on_press = self.take_shot)
            button_count += 1

        if edm_cfg.get_value('BUTTON3','TITLE'):
            button3  = record_button(text = edm_cfg.get_value('BUTTON3','TITLE'), id = 'button3')
            layout.add_widget(button3)
            button3.bind(on_press = self.take_shot)
            button_count += 1

        if edm_cfg.get_value('BUTTON4','TITLE'):
            button4  = record_button(text = edm_cfg.get_value('BUTTON4','TITLE'), id = 'button4')
            layout.add_widget(button4)
            button4.bind(on_press = self.take_shot)
            button_count += 1

        if edm_cfg.get_value('BUTTON5','TITLE'):
            button5  = record_button(text = edm_cfg.get_value('BUTTON5','TITLE'), id = 'button5')
            layout.add_widget(button5)
            button5.bind(on_press = self.take_shot)
            button_count += 1

        if edm_cfg.get_value('BUTTON6','TITLE'):
            button6  = record_button(text = edm_cfg.get_value('BUTTON6','TITLE'), id = 'button6')
            layout.add_widget(button6)
            button6.bind(on_press = self.take_shot)
            button_count += 1

        if button_count % 3 !=0:
            button_empty = Button(text = '', size_hint_y = None, id = '',
                            color = WINDOW_BACKGROUND,
                            background_color = WINDOW_BACKGROUND,
                            background_normal = '')
            layout.add_widget(button_empty)

        if button_count % 3 == 2:
            layout.add_widget(button_empty)
            
        button_rec = Button(text = 'Record', size_hint_y = None, id = 'record',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button_rec)
        button_rec.bind(on_press = self.take_shot)

        button_continue = Button(text = 'Continue', size_hint_y = None, id = 'continue',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button_continue)
        button_continue.bind(on_press = self.take_shot)

        button_measure = Button(text = 'Measure', size_hint_y = None, id = 'measure',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button_measure)
        button_measure.bind(on_press = self.take_shot)

        self.add_widget(layout)

    def take_shot(self, value):
        
        edm_station.take_shot()

        layout_popup = GridLayout(cols = 1, spacing = 10, size_hint_y = None)
        layout_popup.bind(minimum_height=layout_popup.setter('height'))
        for prism in edm_prisms.names():
            button1 = Button(text = prism, size_hint_y = None, id = prism,
                        color = OPTIONBUTTON_COLOR,
                        background_color = OPTIONBUTTON_BACKGROUND,
                        background_normal = '')
            layout_popup.add_widget(button1)
            button1.bind(on_press = self.show_edit_screen)
        button2 = Button(text = 'Back', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout_popup.add_widget(button2)
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        root.add_widget(layout_popup)
        self.popup = Popup(title = 'Prism Height',
                    content = root,
                    size_hint = (None, None),
                    size = (400, 400),
                    #pos_hint = {None, None},
                    auto_dismiss = False)
        button2.bind(on_press = self.popup.dismiss)
        self.popup.open()

    def show_edit_screen(self, value):
        self.popup.dismiss()
        edm_station.prism = edm_prisms.get(value.text).height 
        self.parent.current = 'EditPointScreen'

    def show_load_cfg(self):
        content = LoadDialog(load = self.load, 
                            cancel = self.dismiss_popup,
                            start_path = os.path.dirname(os.path.abspath( __file__ )))
        self._popup = Popup(title = "Load CFG file", content = content,
                            size_hint = (0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        global edm_cfg, edm_ini
        edm_cfg.load(os.path.join(path, filename[0]))
        edm_ini.update()
        self.dismiss_popup()

    def dismiss_popup(self):
        self.popup.dismiss()
        self.parent.current = 'MainScreen'

class InitializeOnePointHeader(Label):
    pass

class InitializeDirectScreen(Screen):

    popup = ObjectProperty(None)

    def datum_list(self):
        layout_popup = GridLayout(cols = 1, spacing = 10, size_hint_y = None)
        layout_popup.bind(minimum_height=layout_popup.setter('height'))
        for datum in datums.names(EDMpy.edm_datums):
            button1 = Button(text = datum, size_hint_y = None, id = datum,
                        color = OPTIONBUTTON_COLOR,
                        background_color = OPTIONBUTTON_BACKGROUND,
                        background_normal = '')
            layout_popup.add_widget(button1)
            button1.bind(on_press = self.initialize_direct)
        button2 = Button(text = 'Cancel', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout_popup.add_widget(button2)
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        root.add_widget(layout_popup)
        self.popup = Popup(title = 'Initial Direct',
                    content = root,
                    size_hint = (None, None),
                    size=(400, 400),
                    #pos_hint = {None, None},
                    auto_dismiss = False)
        button2.bind(on_press = self.popup.dismiss)
        self.popup.open()

    def initialize_direct(self, value):
        EDMpy.edm_station.X = EDMpy.edm_datums.datums[EDMpy.edm_datums.datums.Name==value.id].iloc[0]['X']
        EDMpy.edm_station.Y = EDMpy.edm_datums.datums[EDMpy.edm_datums.datums.Name==value.id].iloc[0]['X']
        EDMpy.edm_station.Z = EDMpy.edm_datums.datums[EDMpy.edm_datums.datums.Name==value.id].iloc[0]['X']
        self.popup.dismiss()
        self.parent.current = 'MainScreen'

class InitializeSetAngleScreen(Screen):
    def set_angle(self, foreshot, backshot):
        if foreshot:
            totalstation.set_horizontal_angle(foreshot)
        elif backshot:
            # flip angle 180
            totalstation.set_horizontal_angle(foreshot)
        self.parent.current = 'MainScreen'

class InitializeOnePointScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeOnePointScreen, self).__init__(**kwargs)
        self.add_widget(InitializeOnePointHeader())
        self.add_widget(DatumLister())

class InitializeTwoPointScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeTwoPointScreen, self).__init__(**kwargs)
        self.add_widget(InitializeOnePointHeader())
        self.add_widget(DatumLister())

class InitializeThreePointScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeThreePointScreen, self).__init__(**kwargs)
        self.add_widget(InitializeOnePointHeader())
        self.add_widget(DatumLister())

class MenuList(Popup):
    def __init__(self, title, menu_list, call_back, **kwargs):
        super(MenuList, self).__init__(**kwargs)
        __content = GridLayout(cols = 1, spacing = 5, size_hint_y = None)
        __content.bind(minimum_height=__content.setter('height'))
        for menu_item in menu_list:
            __button = Button(text = menu_item, size_hint_y = None, id = title,
                        color = OPTIONBUTTON_COLOR,
                        background_color = OPTIONBUTTON_BACKGROUND,
                        background_normal = '')
            __content.add_widget(__button)
            __button.bind(on_press = call_back)
        if title!='PRISM':
            __new_item = GridLayout(cols = 2, spacing = 5, size_hint_y = None)
            __new_item.add_widget(TextInput(size_hint_y = None, id = 'new_item'))
            __add_button = Button(text = 'Add', size_hint_y = None,
                                    color = BUTTON_COLOR,
                                    background_color = BUTTON_BACKGROUND,
                                    background_normal = '', id = title)
            __new_item.add_widget(__add_button)
            __add_button.bind(on_press = call_back)
            __content.add_widget(__new_item)
        __button1 = Button(text = 'Back', size_hint_y = None,
                                color = BUTTON_COLOR,
                                background_color = BUTTON_BACKGROUND,
                                background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = self.dismiss)
        __root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        __root.add_widget(__content)
        self.title = title
        self.content = __root
        self.size_hint = (None, None)
        self.size = (400, 400)
        self.auto_dismiss = True

class TextNumericInput(Popup):
    def __init__(self, title, call_back, **kwargs):
        super(TextNumericInput, self).__init__(**kwargs)
        __content = GridLayout(cols = 1, spacing = 5, size_hint_y = None)
        __content.bind(minimum_height=__content.setter('height'))
        __content.add_widget(TextInput(size_hint_y = None, multiline = False, id = 'new_item'))
        __add_button = Button(text = 'Next', size_hint_y = None,
                                    color = BUTTON_COLOR,
                                    background_color = BUTTON_BACKGROUND,
                                    background_normal = '', id = title)
        __content.add_widget(__add_button)
        __add_button.bind(on_press = call_back)
        __button1 = Button(text = 'Back', size_hint_y = None,
                                color = BUTTON_COLOR,
                                background_color = BUTTON_BACKGROUND,
                                background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = self.dismiss)
        __root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        __root.add_widget(__content)
        self.title = title
        self.content = __root
        self.size_hint = (None, None)
        self.size = (400, 400)
        self.auto_dismiss = True

class MessageBox(Popup):
    def __init__(self, title, message, **kwargs):
        super(MessageBox, self).__init__(**kwargs)
        __content = BoxLayout(orientation = 'vertical')
        __label = Label(text = message, size_hint=(1, 1), valign='middle', halign='center')
        __label.bind(
            width=lambda *x: __label.setter('text_size')(__label, (__label.width, None)),
            texture_size=lambda *x: __label.setter('height')(__label, __label.texture_size[1]))
        __content.add_widget(__label)
        __button1 = Button(text = 'Back', size_hint_y = .2,
                            color = BUTTON_COLOR,
                            background_color = BUTTON_BACKGROUND,
                            background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = self.dismiss)
        self.title = title
        self.content = __content
        self.size_hint = (.8, .8)
        self.size=(400, 400)
        self.auto_dismiss = True

class YesNo(Popup):
    def __init__(self, title, message, yes_callback, no_callback, **kwargs):
        super(YesNo, self).__init__(**kwargs)
        __content = BoxLayout(orientation = 'vertical')
        __label = Label(text = message, size_hint=(1, 1), valign='middle', halign='center')
        __label.bind(
            width=lambda *x: __label.setter('text_size')(__label, (__label.width, None)),
            texture_size=lambda *x: __label.setter('height')(__label, __label.texture_size[1]))
        __content.add_widget(__label)
        __button1 = Button(text = 'Yes', size_hint_y = .2,
                            color = BUTTON_COLOR,
                            background_color = BUTTON_BACKGROUND,
                            background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = yes_callback)
        __button2 = Button(text = 'No', size_hint_y = .2,
                            color = BUTTON_COLOR,
                            background_color = BUTTON_BACKGROUND,
                            background_normal = '')
        __content.add_widget(__button2)
        __button2.bind(on_press = no_callback)
        self.title = title
        self.content = __content
        self.size_hint = (.8, .8)
        self.size=(400, 400)
        self.auto_dismiss = True

class EditPointScreen(Screen):

    global edm_cfg
    global edm_station
    global edm_prisms
    global edm_points

    popup = ObjectProperty(None)

    def on_pre_enter(self):
        #super(Screen, self).__init__(**kwargs)
        self.clear_widgets()
        layout = GridLayout(cols = 2, spacing = 10, size_hint_y = None, id = 'fields')
        layout.bind(minimum_height=layout.setter('height'))
        for field_name in edm_cfg.fields():
            f = edm_cfg.get(field_name)
            layout.add_widget(Label(text = field_name,
                                size_hint_y = None, color = BUTTON_COLOR))
            if field_name in ['SUFFIX','X','Y','Z','PRISM','DATE','VANGLE','HANGLE','SLOPED']:
                if field_name == 'SUFFIX':
                    layout.add_widget(Label(text = str(edm_station.suffix), id = 'SUFFIX',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'X':
                    layout.add_widget(Label(text = str(edm_station.x), id = 'X',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'Y':
                    layout.add_widget(Label(text = str(edm_station.y), id = 'Y',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'Z':
                    layout.add_widget(Label(text = str(edm_station.z), id = 'Z',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'SLOPED':
                    layout.add_widget(Label(text = str(edm_station.sloped), id = 'SLOPED',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'HANGLE':
                    layout.add_widget(Label(text = edm_station.hangle, id = 'HANGLE',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'VANGLE':
                    layout.add_widget(Label(text = edm_station.vangle, id = 'VANGLE',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'DATE':
                    layout.add_widget(Label(text = "%s" % datetime.datetime.now(), id = 'DATE',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'PRISM':
                    prism_button = Button(text = str(edm_station.prism), size_hint_y = None,
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '',
                                    id = field_name)
                    layout.add_widget(prism_button)
                    prism_button.bind(on_press = self.show_menu)
            else:
                if f.inputtype == 'TEXT':
                    layout.add_widget(TextInput(multiline=False, id = field_name))
                if f.inputtype == 'NUMERIC':
                    layout.add_widget(TextInput(id = field_name))
                if f.inputtype == 'MENU':
                    button1 = Button(text = 'MENU', size_hint_y = None,
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '',
                                    id = field_name)
                    layout.add_widget(button1)
                    button1.bind(on_press = self.show_menu)
        button2 = Button(text = 'Save', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button2)
        button2.bind(on_press = self.save)
        button3 = Button(text = 'Back', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button3)
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        root.add_widget(layout)
        self.add_widget(root)

    def show_menu(self, value):
        if value.id!='PRISM':  
            self.popup = MenuList(value.id, edm_cfg.get(value.id).menu, self.menu_selection)
        else:
            self.popup = MenuList(value.id, edm_prisms.names(), self.prism_change)
        self.popup.open()

    def prism_change(self, value):
        edm_station.z = edm_station.z + edm_station.prism
        edm_station.prism = edm_prisms.get(value.text).height 
        edm_station.z = edm_station.z - edm_station.prism
        for child in self.walk():
            if child.id == value.id:
                child.text = str(edm_station.prism)
            if child.id == 'Z':
                child.text = str(edm_station.z)
        self.popup.dismiss()

    def menu_selection(self, value):
        for child in self.walk():
            if child.id == value.id:
                if value.text == 'Add':
                    for widget in self.popup.walk():
                        if widget.id == 'new_item':
                            child.text = widget.text
                            edm_cfg.update_value(value.id,'MENU',
                                                edm_cfg.get_value(value.id,'MENU') + "," + widget.text) 
                else:
                    child.text = value.text
        self.popup.dismiss()

    def save(self, value):
        new_record = {}
        for widget in self.walk():
            for f in edm_points.fields():
                if widget.id == f:
                    new_record[f] = widget.text
        valid = edm_cfg.valid_datarecord(new_record)
        if valid:
            edm_points.db.insert(new_record)
            edm_units.update_defaults(new_record)
            self.parent.current = 'MainScreen'
        else:
            self.popup = MessageBox('Save Error', valid_record)
            self.popup.open()

class EditPointsScreen(Screen):
    def __init__(self,**kwargs):
        super(EditPointsScreen, self).__init__(**kwargs)
        global edm_points
        self.add_widget(DfguiWidget(edm_points))

class EditPrismsScreen(Screen):
    def __init__(self,**kwargs):
        super(EditPrismsScreen, self).__init__(**kwargs)
        global edm_prisms
        self.add_widget(DfguiWidget(edm_prisms))

class EditUnitsScreen(Screen):
    def __init__(self,**kwargs):
        super(EditUnitsScreen, self).__init__(**kwargs)
        global edm_units
        self.add_widget(DfguiWidget(edm_units))

class EditDatumsScreen(Screen):
    def __init__(self,**kwargs):
        super(EditDatumsScreen, self).__init__(**kwargs)
        global edm_datums
        self.add_widget(DfguiWidget(edm_datums))

class datumlist(RecycleView, Screen):
    def __init__(self, **kwargs):
        super(datumlist, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in range(100)]

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """ Adds selection and focus behaviour to the view. """
    selected_value = StringProperty('')
    btn_info = ListProperty(['Button 0 Text', 'Button 1 Text', 'Button 2 Text'])

class SelectableButton(RecycleDataViewBehavior, Button):
    """ Add selection support to the Label """
    index = None

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

    def on_press(self):
        self.parent.selected_value = 'Selected: {}'.format(self.parent.btn_info[int(self.id)])

    def on_release(self):
        MessageBox().open()

class RV(RecycleView):
    rv_layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [{'text': "Datum " + str(x), 'id': str(x)} for x in range(30)]

class DatumLister(BoxLayout,Screen):
    def __init__(self, list_dicts=[], *args, **kwargs):

        super(DatumLister, self).__init__(*args, **kwargs)
        self.orientation = "vertical"
        self.add_widget(RV())

class EditDatumScreen(Screen):
    pass

class StationConfigurationScreen(Screen):
    def __init__(self,**kwargs):
        super(StationConfigurationScreen, self).__init__(**kwargs)
    
        layout = GridLayout(cols = 2, spacing = 5)

        # Station type menu
        self.StationLabel = Label(text="Station type", color = WINDOW_COLOR)
        layout.add_widget(self.StationLabel)
        self.StationMenu = Spinner(text="Simulate", values=("Leica", "Wild", "Topcon", "Simulate"), id = 'station',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.StationMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.StationMenu)

        # Communications type menu
        self.CommTypeLabel = Label(text="Communications", color = WINDOW_COLOR)
        layout.add_widget(self.CommTypeLabel)
        self.CommTypeMenu = Spinner(text="None", values=("Serial", "Bluetooth"), id = 'communications',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.CommTypeMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.CommTypeMenu)

        # Port number
        self.PortNoLabel = Label(text="Port Number", color = WINDOW_COLOR)
        layout.add_widget(self.PortNoLabel)
        self.PortNoMenu = Spinner(text="COM1", values=("COM1", "COM2","COM3","COM4","COM5","COM6"), id = 'comport',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.PortNoMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.PortNoMenu)

        # Speed
        self.SpeedLabel = Label(text="Speed", color = WINDOW_COLOR)
        layout.add_widget(self.SpeedLabel)
        self.SpeedMenu = Spinner(text="1200", values=("1200", "2400","4800","9600"), id = 'baudrate',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.SpeedMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.SpeedMenu)

        # Parity
        self.ParityLabel = Label(text="Parity", color = WINDOW_COLOR)
        layout.add_widget(self.ParityLabel)
        self.ParityMenu = Spinner(text="Even", values=("Even", "Odd","None"), id = 'parity',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.ParityMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.ParityMenu)

        # Databits
        self.DataBitsLabel = Label(text="Data bits", color = WINDOW_COLOR)
        layout.add_widget(self.DataBitsLabel)
        self.DataBitsMenu = Spinner(text="7", values=("7", "8"), id = 'databits',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.DataBitsMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.DataBitsMenu)

        # Stopbits
        self.StopBitsLabel = Label(text="Stop bits", color = WINDOW_COLOR)
        layout.add_widget(self.StopBitsLabel)
        self.StopBitsMenu = Spinner(text="1", values=("0", "1", "2"), id = 'stopbits',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.StopBitsMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.StopBitsMenu)

        button1 = Button(text = 'Save', size_hint_y = None, id = 'save',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button1)
        button1.bind(on_press = self.close_screen)
        button2 = Button(text = 'Back', size_hint_y = None, id = 'cancel',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button2)
        button2.bind(on_press = self.close_screen)

        self.add_widget(layout)

    def close_screen(self, instance):
        if instance.id=='save':
            for child in self.children[0].children:
                if child.id=='stopbits':
                    EDMpy.edm_station.stopbits = child.text
                if child.id=='baudrate':
                    EDMpy.edm_station.baudrate = child.text
                if child.id=='databits':
                    EDMpy.edm_station.databits = child.text
                if child.id=='comport':
                    EDMpy.edm_station.comport = child.text
                if child.id=='parity':
                    EDMpy.edm_station.parity = child.text
                if child.id=='communications':
                    EDMpy.edm_station.communications = child.text
                if child.id=='station':
                    EDMpy.edm_station.make = child.text
                ## need code to open com port here
        self.parent.current = 'MainScreen'

class AboutScreen(Screen):
    pass

class DebugScreen(Screen):
    pass

class LogScreen(Screen):
    pass

class StatusScreen(Screen):
    def __init__(self,**kwargs):
        super(StatusScreen, self).__init__(**kwargs)

        global edm_station, edm_datums, edm_units, edm_prisms
        global edm_cfg

        layout = GridLayout(cols = 1, size_hint_y = None)
        layout.bind(minimum_height=layout.setter('height'))
        txt = edm_station.status() + edm_datums.status() + edm_prisms.status()
        txt += edm_units.status()
        label = Label(text = txt, size_hint_y = None,
                     color = (0,0,0,1), id = 'content',
                     halign = 'left',
                     font_size = 20)
        layout.add_widget(label)
        label.bind(texture_size = label.setter('size'))
        label.bind(size_hint_min_x = label.setter('width'))
        button = Button(text = 'Back', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        root.add_widget(layout)
        self.add_widget(root)
        self.add_widget(button)
        button.bind(on_press = self.go_back)

    def on_pre_enter(self):
        global edm_station, edm_datums, edm_units, edm_prisms
        global edm_cfg
        for widget in self.walk():
            if widget.id=='content':
                txt = edm_station.status() + edm_datums.status() + edm_prisms.status()
                txt += edm_units.status() + edm_cfg.status()
                widget.text = txt

    def go_back(self, value):
        self.parent.current = 'MainScreen'

# Code from https://github.com/MichaelStott/DataframeGUIKivy/blob/master/dfguik.py

class HeaderCell(Button):
    color = BUTTON_COLOR
    background_color = BUTTON_BACKGROUND
    background_normal = ''

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
    color = BUTTON_COLOR
    background_normal = ''

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
            #row_vals = ord_dict.values()
            k = -1
            if df_name=='points':
                key = list(ord_dict)[0] + '-' + list(ord_dict)[1]
            else:
                key = list(ord_dict)[0]
            for text in ord_dict:
                k += 1
                self.data.append({'text': str(text), 'is_even': is_even,
                                    'callback': self.editcell,
                                    'key': key, 'field': column_names[k],
                                    'db': df_name, 'id': 'datacell' })

    def sort_data(self):
        #TODO: Use this to sort table, rather than clearing widget each time.
        pass

    def editcell(self, key, field, db):
        self.key = key
        self.field = field
        self.db = db
        if db == 'points':
            cfg_field = edm_cfg.get(field)
            self.inputtype = cfg_field.inputtype
            if cfg_field.inputtype == 'MENU':
                self.popup = MenuList(field, edm_cfg.get(field).menu, self.menu_selection)
                self.popup.open()
            if cfg_field.inputtype in ['TEXT','NUMERIC']:
                self.popup = TextNumericInput(field, self.menu_selection)
                self.popup.open()
        else:
            self.popup = TextNumericInput(field, self.menu_selection)
            self.popup.open()

    def menu_selection(self, value):
        ### need some data validation
        if self.db == 'points':
            print(value.id)
            unit, id = self.key.split('-')
            new_data = {}
            if self.inputtype=='MENU':
                new_data[self.field] = value.text
            else:
                for widget in self.popup.walk():
                    if widget.id == 'new_item':
                        new_data[self.field] = widget.text
            field_record = Query()
            edm_points.db.update(new_data, (field_record.UNIT == unit) & (field_record.ID == id))
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

    def populate_data(self, df):
        self.df_orig = df
        self.sort_key = None
        self.column_names = self.df_orig.fields()
        self.df_name = df.db_name 
        self._generate_table()

    def _generate_table(self, sort_key=None, disabled=None):
        self.clear_widgets()
        data = []
        for row in self.df_orig.db:
            data.append(row.values())
        #data = sorted(data, key=lambda k: k[self.sort_key]) 
        self.add_widget(Table(list_dicts = data, column_names = self.column_names, df_name = self.df_name))

class AddNewPanel(BoxLayout):
    
    def populate(self, df):
        self.df_name = df.db_name            
        self.addnew_list.bind(minimum_height=self.addnew_list.setter('height'))
        for col in df.fields():
            self.addnew_list.add_widget(AddNew(col, df.db_name))
        self.addnew_list.add_widget(AddNew('Save', df.db_name))

    def get_addnews(self):
        result=[]
        for opt_widget in self.addnew_list.children:
            result.append(opt_widget.get_addnew())
        return(result)

class AddNew(BoxLayout):

    global edm_datums
    global edm_prisms
    global edm_units
    
    popup = ObjectProperty(None)
    sorted_result = None

    def __init__(self, col, df_name, **kwargs):
        super(AddNew, self).__init__(**kwargs)
        self.df_name = df_name
        self.widget_type = 'data'
        self.height="30sp"
        self.size_hint=(0.9, None)
        self.spacing=10
        if col=='Save':
            self.label = Label(text = "")
            self.button = Button(text = "Save", size_hint=(0.75, 1), font_size="15sp",
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
            self.button.bind(on_press = self.append_data)
            self.add_widget(self.label)
            self.add_widget(self.button)
            self.widget_type = 'button'
        else:
            self.label = Label(text = col, color = WINDOW_COLOR)
            self.txt = TextInput(multiline=False, size_hint=(0.75, None), font_size="15sp")
            self.txt.bind(minimum_height=self.txt.setter('height'))
            self.add_widget(self.label)
            self.add_widget(self.txt)

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
        if self.df_name == 'prisms':
            for f in edm_prisms.fields():
                sorted_result[f] = result[f]
            if edm_prisms.duplicate(sorted_result):
                message = 'Overwrite existing prism named %s' % sorted_result['name']
            else:
                message = edm_prisms.valid(sorted_result)
                if not message:
                    edm_prisms.db.insert(sorted_result)
        if self.df_name == 'units':
            for f in edm_units.fields():
                sorted_result[f] = result[f]
            edm_units.db.insert(sorted_result)
        if self.df_name == 'datums':
            for f in edm_datums.fields():
                sorted_result[f] = result[f]
            edm_datums.db.insert(sorted_result)
        if message:
            self.sorted_result = sorted_result
            self.popup = YesNo('Edit', message, self.replace, self.do_nothing)
        else:
            for obj in instance.parent.parent.children:
                if obj.widget_type=='data':
                    obj.txt.text = ''

    def replace(self, value):
        if self.df_name == 'prisms':
            edm_prisms.replace(self.sorted_result)
        if self.df_name == 'units':
            edm_units.replace(self.sorted_result)
        if self.df_name == 'datums':
            edm_datums.replace(self.sorted_result)
        ### Need to clear form here as well
        self.popup.dismiss()

    def do_nothing(self, value):
        self.popup.dismiss()

class DfguiWidget(TabbedPanel):

    def __init__(self, df, **kwargs):
        super(DfguiWidget, self).__init__(**kwargs)
        self.df = df
        self.df_name = df.db_name
        self.panel1.populate_data(df)
        self.panel4.populate(df)
        self.color = BUTTON_COLOR
        self.background_color = WINDOW_BACKGROUND
        self.background_image = ''

    # This should be changed so that the table isn't rebuilt
    # each time settings change.
    def open_panel1(self):
        self.panel1._generate_table()
    
    def cancel(self):
        pass

# End code from https://github.com/MichaelStott/DataframeGUIKivy/blob/master/dfguik.py

class YesNoCancel(Popup):
    def __init__(self, caption, cancel = False, **kwargs):
        super(YesNoCancel, self).__init__(**kwargs)
        box = BoxLayout()
        self.label = Label(text = caption)
        self.button1 = Button(text = "Yes", size_hint=(0.75, 1), font_size="15sp")
        self.button1.bind(on_press = self.yes)
        self.button2 = Button(text = "No", size_hint=(0.75, 1), font_size="15sp")
        self.button2.bind(on_press = self.no)
        box.add_widget(self.label)
        box.add_widget(self.button1)
        box.add_widget(self.button2)
        if cancel == True:
            box.button3 = Button(text = "Cancel", size_hint=(0.75, 1), font_size="15sp")
            box.button3.bind(on_press = self.cancel)
            box.add_widget(self.button3)
        self.add_widget(box)
        self.open()
    def yes(self, instance):
        return('Yes')
    def no(self, instance):
        return('No')
    def cancel(self, instance):
        return('Cancel')

class E4py(App):

    def build(self):
        Window.clearcolor = WINDOW_BACKGROUND
        self.title = "E4py " + __version__

        #sm.current = 'main'
        #df = create_dummy_data(0)
        #df = edm_datums.datums 
        #test = YesNoCancel("This is a test of a yes no popup box", cancel=False)
        #print(test)
        #return(DfguiWidget(EDMpy.edm_datums.datums, "datums"))
    
Factory.register('EDMpy', cls=EDMpy)

if __name__ == '__main__':
    logging.basicConfig(filename='E4.log', filemode='w', level=logging.DEBUG)
    database = 'E4'
    e4_ini = ini('E4.ini')
    e4_cfg = cfg(edm_ini.get_value("E4", "CFG"))
    e4_points = points(database + '_points.json')
    if not e4_cfg.filename:
        e4_cfg.filename = 'EDMpy.cfg'
    e4_cfg.save()
    e4_ini.update()
    e4_ini.save()
    
    E4py().run()