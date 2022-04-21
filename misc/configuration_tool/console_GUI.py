from tkinter import Frame
from tkinter import Label
from tkinter import ttk


from supportfunctions.support_file_io import SupportFileIO
from hilding.conf import get_conf


SupportFileIO = SupportFileIO()
CONF = get_conf()



class consoleTab():

    def __init__(self, parent, console_var):
        # pylint: disable=too-many-instance-attributes, too-many-statements
        self.parent = parent

        # Variables
        self.console_var = console_var

        # Top
        self.top_field = Frame(self.parent)
        self.top_field.grid(row = 0)

        # Configuration Textbox
        self.console_frame = Frame(self.top_field)
        self.console_frame.grid(column=0, row=0)
        self.console_text = Label(self.console_frame,
            textvariable=self.console_var,
            bg="black",
            fg="white",
            font="Consolas 12 bold",
            anchor="w",
            width="150")
        self.console_text.grid(column=0, row=0)
