"""
GUI for pretty print
"Might be updated to contain more GUIs to Dut

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
from tkinter import StringVar, Tk
from tkinter import ttk

from supportfunctions.support_file_io import SupportFileIO
from hilding.conf import get_conf

from misc.configuration_tool.overviewtab_GUI import overviewTab
from misc.configuration_tool.rigstab_GUI import rigsTab
from misc.configuration_tool.console_GUI import consoleTab

SupportFileIO = SupportFileIO()
CONF = get_conf()

class MainWindow():
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Main window of GUI
    """

    def __init__(self, window):
        # pylint: disable=too-many-instance-attributes, too-many-statements
        self.window = window

        # Variables
        self.platforms = list(CONF.platforms.keys())
        self.rigs = list(CONF.rigs)
        self.ssh_passwords = dict()
        self.console_content = StringVar(value="Console output will end up here\n")

        # Content

        # Tabs
        tab_parent = ttk.Notebook(self.window)
        tab1 = ttk.Frame(tab_parent)
        tab2 = ttk.Frame(tab_parent)
        tab3 = ttk.Frame(tab_parent)
        tab4 = ttk.Frame(tab_parent)

        tab_parent.add(tab1, text="Overview")
        tab_parent.add(tab2, text="Rig manager")
        tab_parent.add(tab3, text="SWRS and requirements")
        tab_parent.add(tab4, text="Console")

        tab_parent.pack(expand=1, fill='both')

        overviewTab(tab1, self.ssh_passwords, self.console_content)
        rigsTab(tab2, self.ssh_passwords, self.console_content)
        consoleTab(tab4, self.console_content)

def run():
    # pylint: disable=unused-variable
    """Function that starts the GUI

    Args:
        dut (dut): In instance of Dut
    """
    # Initial setup of window
    window = Tk()
    ttk.Style().theme_use('xpnative')
    MainWindow(window)
    window.title("Hilding Configuration tool")
    window.geometry("1600x1000+100+100")

    #Main loop
    window.mainloop()
