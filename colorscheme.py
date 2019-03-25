from constants import WHITE, BLACK, GOOGLE_COLORS
from kivy.core.window import Window

def make_rgb(hex_color):
    return([(( hex_color >> 16 ) & 0xFF)/255.0,
            (( hex_color >> 8 ) & 0xFF)/255.0,
            (hex_color & 0xFF)/255.0,
            1])

class ColorScheme:

    def __init__(self, color_name = 'light blue'):
        self.optionbutton_font_size = "15sp"
        self.button_font_size = "15sp"
        self.text_font_size = "15sp"

        self.popup_background = (0, 0, 0, 1)
        self.popup_text_color = (1, 1, 1, 1)

        self.datagrid_odd = (224.0/255, 224.0/255, 224.0/255, 1)
        self.datagrid_even = (189.0/255, 189.0/255, 189.0/255, 1)

        self.valid_colors = GOOGLE_COLORS
        
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

    def set_to(self, name):
        self.need_redraw = True
        if name in self.valid_colors:
            self.optionbutton_background = make_rgb(self.valid_colors[name][0])
            self.optionbutton_color = make_rgb(self.valid_colors[name][1])
            self.button_background =  make_rgb(self.valid_colors[name][2])
            self.button_color = make_rgb(self.valid_colors[name][3])
            self.color_scheme = name
        else:
            return('Error: %s is not a valid color scheme.' % (name))
