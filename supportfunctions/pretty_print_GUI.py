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

import time
import logging

from tkinter import messagebox
from tkinter import IntVar
from tkinter import StringVar
from tkinter import Frame
from tkinter import Label
from tkinter import Entry
from tkinter import Button
from tkinter import Checkbutton
from tkinter import Tk
from tkinter import Text

from tkinter import ttk
import supportfunctions.pretty_print as pp

class MainWindow():
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Main window of GUI
    """

    def __init__(self, window, dut):
        # pylint: disable=too-many-instance-attributes, too-many-statements
        self.dut = dut
        self.window = window

        #Variables

        #The variable shown on screen as "Currently active did:"
        self.did_id = StringVar()
        self.did_id.set("")

        #Used for dropdown selection. Feel free to add more options
        self.did_list_cms = ["",
                            "FD40",
                            "FD41",
                            "FD61",
                            "FD62",
                            "DB8A",
                            "DB8B",
                            "DAE4"]

        self.did_list_cvtn = ["",
                            "DAE6",
                            "DAE7",
                            "DBA0",
                            "DBF0",
                            "FD09",
                            "FD0B",
                            "FD0C",
                            "FD0E",
                            "FD0F",
                            "FD10"]

        #Connected to the checkbox that decides if did value should be continiously updated
        self.subscribe = IntVar()

        self.subscribe_time = StringVar()
        self.subscribe_time.set("-1")

        # Content

        # Labels:
        # -If it is plain text that never changes name them "static"
        # -If they are connected to a value that might/will change, name them dynamic

        #Content 1
        #Row 1
        self.grid_0_0 = Frame()
        self.grid_0_0.grid(column=0, row=0)

        self.label_select_did_static = Label(self.grid_0_0, text= 'Did to monitor:')
        self.label_select_did_static.grid(column=0, row=0)

        #Row 2
        self.grid_1_1 = Frame()
        self.grid_1_1.grid(column=1, row=1)

        self.label_active_did_static = Label(self.grid_1_1, text= 'Currently active did:')
        self.label_active_did_static.grid(column=0, row=0)

        self.label_active_did_dynamic = Label(self.grid_1_1, text="", font="none 10 bold")
        self.label_active_did_dynamic.grid(column=1, row=0)

        #Row 3
        self.pretty_print_frame = Frame()
        self.pretty_print_frame.grid(column=0, row=2)

        self.text_pretty_print = Text(self.pretty_print_frame,
            bg = "white",
            font="Consolas 12 bold",
            width='70',
            height='40',
            wrap='none')
        self.text_pretty_print.insert("1.0",
            "DID info will appear here once Monitor DID is pressed")

        self.scrollbar = ttk.Scrollbar(self.pretty_print_frame,
                                        orient='horizontal',
                                        command=self.text_pretty_print.xview)

        self.text_pretty_print.config(xscrollcommand=self.scrollbar.set)
        self.text_pretty_print.grid(column=0, row=0)
        self.scrollbar.grid(column=0, row=1, sticky="NESW")

        #Content 2. This split (between content 1 and 2)
        #is needed because of a bug with threading causing
        #variables not to be accessable if defined after use.
        #Row 1
        self.entry_select_did = Entry(self.grid_0_0, text = "")
        self.entry_select_did.grid(column=1, row=0)

        self.button_start_monitoring = Button(window, text = "Monitor DID", command=self.monitor)
        self.button_start_monitoring.grid(column=1, row=0)

        #Row 2
        self.grid_2_1 = Frame()
        self.grid_2_1.grid(column=2, row=1)

        self.chk_button_subscribe = Checkbutton(self.grid_2_1, variable=self.subscribe)
        self.chk_button_subscribe.grid(column=1, row=0)

        self.label_subscribe_info_static = Label(self.grid_2_1,
                                        text = "Subscribe to DID info for seconds:")
        self.label_subscribe_info_static.grid(column=2, row=0)

        self.entry_subscribe_for = Entry(self.grid_2_1, textvariable=self.subscribe_time)
        self.entry_subscribe_for.grid(column=3, row=0)

        #Row 3
        self.grid_1_2 = Frame()
        self.grid_1_2.grid(column=1, row=2)

        self.dropdown_cms = ttk.Combobox(self.grid_1_2, values=self.did_list_cms)
        self.dropdown_cms.grid(column=1, row=0)
        self.label_dropdown_cms = Label(self.grid_1_2, text = "CMS dids:")
        self.label_dropdown_cms.grid(column=0, row=0)

        self.grid_2_2 = Frame()
        self.grid_2_2.grid(column=2, row=2)

        self.dropdown_cvtn = ttk.Combobox(self.grid_2_2, values=self.did_list_cvtn)
        self.dropdown_cvtn.grid(column=1, row=0)
        self.label_dropdown_cvtn = Label(self.grid_2_2, text = "CVTN dids:")
        self.label_dropdown_cvtn.grid(column=0, row=0)

    def monitor(self):
        """Function that is triggered when "monitor button" is pressed.
        """
        def __empty_all_input():
            """Clears all input (dropdowns and entry box)
            """
            self.entry_select_did.delete(0, len(self.entry_select_did.get()))
            self.dropdown_cvtn.set("")
            self.dropdown_cms.set("")

        def __update_pretty_print():
            """Updates the textbox with pretty print
            """
            pp_string = pp.get_did_pretty_print(self.dut, self.did_id.get())
            logging.info("\n %s", pp_string)
            self.text_pretty_print.delete("1.0","end")
            self.text_pretty_print.insert("1.0", pp_string)
            #self.label_pretty_print_dynamic.configure(text = pp_string, anchor='w')
            self.window.update()
            return True

        #List containing info about if the inputs (dropdown and entry box)
        #are empty or not
        check_inputs = [self.entry_select_did.get() != "",
                        self.dropdown_cms.get() != "",
                        self.dropdown_cvtn.get() != ""]

        #If more than one input is used
        if check_inputs.count(True) > 1:
            __empty_all_input()
            messagebox.showerror('error', "More than one way of choosing DID used.\
             Either use ONE of the dropdowns OR enter did ID manually")

        #If only one is used we go for it
        elif True in check_inputs:
            if self.entry_select_did.get() != "":
                self.did_id.set(self.entry_select_did.get())
            if self.dropdown_cvtn.get() != "":
                self.did_id.set(self.dropdown_cvtn.get())
            if self.dropdown_cms.get() != "":
                self.did_id.set(self.dropdown_cms.get())

            if __update_pretty_print():
                self.label_active_did_dynamic.configure(text = self.did_id.get(), bg = "green")

            #Needed to restore subscribe time afterwards
            subscribe_time_copy = self.subscribe_time.get()

            start_time = time.time()
            #Keep updating until time has passed ot checkbox in unticket
            while self.subscribe.get() and time.time() - start_time < int(subscribe_time_copy):
                self.subscribe_time.set(str(int(subscribe_time_copy) - (time.time() - start_time)))
                __update_pretty_print()

            self.subscribe_time.set(subscribe_time_copy)

        #If no input is given
        else:
            messagebox.showerror('error', "No DID selected")

def run(dut):
    # pylint: disable=unused-variable
    """Function that starts the GUI

    Args:
        dut (dut): In instance of Dut
    """
    #Initial setup of window
    window = Tk()
    MainWindow(window, dut)
    window.title("DIDalyzer")
    window.geometry("1200x1000+100+100")

    #Main loop
    window.mainloop()
