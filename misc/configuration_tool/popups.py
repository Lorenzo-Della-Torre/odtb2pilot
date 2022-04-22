from tkinter import Label, Toplevel, Entry, Button, Frame
from turtle import title
from tkinter import ttk

class PasswordPrompt(Toplevel):

    def __init__(self, master, passwords):
        Toplevel.__init__(self, master, height="100", width="250")
        self.title = "Password prompt"
        self.master = master

        # add label
        self.instructions_label = Label(self, text="Since no ssh keys are configured a "
                "password is required")
        self.instructions_label.grid(column=0, row=0)
        # add an entry widget
        self.e1 = Entry(self, show="*")
        self.e1.grid(column=0, row=1)

        self.button_frame = Frame(self,padx="10", pady="10")
        self.button_frame.grid(column=0, row=2)

        # add a submit button
        b1 = Button(self.button_frame, text="Submit password", command=lambda: self.submit(passwords), padx="10")
        b1.grid(column=0, row=0)

        # add a exit button
        b1 = Button(self.button_frame, text="Skip password", command=self.exit_popup, padx="10")
        b1.grid(column=1, row=0)

        self.e1.index(0)
        self.focus()

    def submit(self, passwords):
        passwords['password'] = self.e1.get()
        self.exit_popup()

    def exit_popup(self):
        self.destroy()

class KeysPrompt(Toplevel):

    def __init__(self, master, ret):
        Toplevel.__init__(self, master, height="100", width="250")
        self.title = "Keys prompt"
        self.master = master
        self.ret = ret

        # add label
        self.instructions_label = Label(self, text="Enter your local ssh key, usually found in "
            " C:/Users/<user>/.ssh/id_rsa \n"
            "Note: You must first enter the password by pressing 'Manually enter ssh key', "
            "if no key is yet added for your local machine")
        self.instructions_label.grid(column=0, row=0)
        # add an entry widget
        self.e1 = Entry(self, show="*")
        self.e1.grid(column=0, row=1)

        self.button_frame = Frame(self,padx="10", pady="10")
        self.button_frame.grid(column=0, row=2)

        # add a submit button
        b1 = Button(self.button_frame, text="Add key", command=self.submit, padx="10")
        b1.grid(column=0, row=0)

        # add a exit button
        b1 = Button(self.button_frame, text="Cancel", command=self.exit_popup, padx="10")
        b1.grid(column=1, row=0)

        self.e1.index(0)
        self.focus()

    def submit(self):
        self.ret['key'] = self.e1.get()
        self.exit_popup()

    def exit_popup(self):
        self.destroy()

class AddRig(Toplevel):

    def __init__(self, master, platforms, return_dict):
        Toplevel.__init__(self, master, height="100", width="250")
        self.title = "Add rig"
        self.master = master
        self.return_dict = return_dict

        # add label
        self.instructions_label = Label(self, text="Add new rig")
        self.instructions_label.grid(column=0, row=0)
        # add an entry widget
        self.e1 = Entry(self, show="*")
        self.e1.grid(column=0, row=1)

        # Rig name
        self.rigname_frame = Frame(self, padx="10", pady="10")
        self.rigname_frame.grid(column=0, row=1)

        self.rigname_label = Label(self.rigname_frame, text="Rigname: ")
        self.rigname_label.grid(column=0, row=0)

        self.rigname_entry = Entry(self.rigname_frame)
        self.rigname_entry.grid(column=1, row=0)

        # Hostname
        self.host_name_frame = Frame(self, padx="10", pady="10")
        self.host_name_frame.grid(column=0, row=2)

        self.hostname_label = Label(self.host_name_frame, text="Hostname: ")
        self.hostname_label.grid(column=0, row=0)

        self.hostname_entry = Entry(self.host_name_frame)
        self.hostname_entry.grid(column=1, row=0)

        # Platform
        self.platform_frame = Frame(self, padx="10", pady="10")
        self.platform_frame.grid(column=0, row=3)

        self.platform_label = Label(self.platform_frame, text="Platform: ")
        self.platform_label.grid(column=0, row=0)

        self.platform_dropdown = ttk.Combobox(self.platform_frame, values=platforms)
        self.platform_dropdown.grid(column=1, row=0)

        # user
        self.user_frame = Frame(self, padx="10", pady="10")
        self.user_frame.grid(column=0, row=4)

        self.user_label = Label(self.user_frame, text="User: ")
        self.user_label.grid(column=0, row=0)

        self.user_entry = Entry(self.user_frame)
        self.user_entry.grid(column=1, row=0)

        # signal_broker
        self.signal_broker_frame = Frame(self, padx="10", pady="10")
        self.signal_broker_frame.grid(column=0, row=5)

        self.signal_broker_label = Label(self.signal_broker_frame, text="Signalbroker port: ")
        self.signal_broker_label.grid(column=0, row=0)

        self.signal_broker_entry = Entry(self.signal_broker_frame)
        self.signal_broker_entry.insert(0, "50051")
        self.signal_broker_entry.grid(column=1, row=0)

        # Buttons
        self.button_frame = Frame(self,padx="10", pady="10")
        self.button_frame.grid(column=0, row=6)

        # add a submit button
        b1 = Button(self.button_frame, text="Add rig", command=self.create_rig, padx="10")
        b1.grid(column=0, row=0)

        # add a exit button
        b1 = Button(self.button_frame, text="Cancel", command=self.exit_popup, padx="10")
        b1.grid(column=1, row=0)

        self.e1.index(0)
        self.focus()

    def create_rig(self):
        self.return_dict["rigname"] = self.rigname_entry.get()
        self.return_dict["hostname"] = self.hostname_entry.get()
        self.return_dict["platform"] = self.platform_dropdown.get()
        self.return_dict["user"] = self.user_entry.get()
        self.return_dict["signal_broker_port"] = self.signal_broker_entry.get()
        self.exit_popup()

    def exit_popup(self):
        self.destroy()

class NoRig(Toplevel):

    def __init__(self, master, return_dict):
        Toplevel.__init__(self, master, height="100", width="250")
        self.title = "No rigs found"
        self.master = master

        self.return_dict = return_dict

        # add label
        self.instructions_label = Label(self, text="No rigs found. Do you want to add one?")
        self.instructions_label.grid(column=0, row=0)

        # Buttons
        self.button_frame = Frame(self,padx="10", pady="10")
        self.button_frame.grid(column=0, row=2)

        # add a submit button
        b1 = Button(self.button_frame, text="Add rig", command=self.add_rig, padx="10")
        b1.grid(column=0, row=0)

        # add a exit button
        b1 = Button(self.button_frame, text="Cancel", command=self.exit_popup, padx="10")
        b1.grid(column=1, row=0)
        self.focus()

    def add_rig(self):
        self.return_dict["ret"] = True
        self.destroy()

    def exit_popup(self):
        self.return_dict["ret"] = False
        self.destroy()