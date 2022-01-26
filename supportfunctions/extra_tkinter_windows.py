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
from tkinter import Label
from tkinter import Button
from tkinter import Text
from tkinter import Toplevel

def string_from_list(lst):
    """Converts a list to a string

    Args:
        lst (list): A list containing strings

    Returns:
        str: A nice looking string
    """
    string_list = ""
    for entry in lst:
        if "\n" in entry:
            string_list += entry
        elif entry != "":
            string_list += f"{entry}\n"

    return string_list

def remove_empty_chars(string):
    """Removes spaces from string

    Args:
        string (string): A string in which the spaces will be removed

    Returns:
        string: Modified version of the input not containing the spaces
    """
    return string.replace(" ","")

class popup_update_list:
    # pylint: disable=too-few-public-methods
    """A tkinter window that can be used as a popup.

    Args:
        object (tkinter window): The master window to the popup
    """
    def __init__(self, master, lst, category):
        self.list_to_update = string_from_list(lst[1:])

        self.category = category

        top = self.top = Toplevel(master)

        self.master = master

        self.label_explanation = Label(top, text="Update below list and press save")
        self.label_explanation.pack()

        self.text_list = Text(top)
        self.text_list.insert("1.0", self.list_to_update)
        self.text_list.pack()

        self.button_save = Button(top,text='Save and exit',command=self.save_and_exit)
        self.button_save.pack()

    def save_and_exit(self):
        """Saves the modified list to a text file and kills the popup
        """
        old_content = []
        try:
            with open("pretty_print_GUI_dids.txt", 'r') as save_file:
                cat_found = False
                for line in save_file:
                    if cat_found and "--" in line:
                        cat_found = False
                    if self.category in line:
                        cat_found = True
                    if not cat_found:
                        old_content.append(line.strip("\n"))
        except FileNotFoundError:
            pass # No old content to save

        with open("pretty_print_GUI_dids.txt", 'w') as save_file:
            save_file.write(f"--{self.category}--\n")
            save_file.write(remove_empty_chars(self.text_list.get("1.0", "end")))
            save_file.write(string_from_list([x for x in old_content if x not in ("","\n")]))

        self.top.destroy()
