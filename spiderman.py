"""
UI for Hilding

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

import os
from pathlib import Path
from tkinter import Tk as teek
from tkinter import ttk
import tkinter as tk
from PIL import ImageTk, Image
import yaml
from tkterminal import Terminal
from hilding.dut import Dut
from hilding.uds import UdsEmptyResponse


class HildingUI:
    """ UI Class for hilding"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=redefined-outer-name
    def __init__(self, window):
        tabcontrol = ttk.Notebook(window)
        automated_tab = ttk.Frame(tabcontrol)
        tester_tab = ttk.Frame(tabcontrol)
        tabcontrol.add(automated_tab, text = 'Automation')
        tabcontrol.add(tester_tab, text = 'Tester')
        tabcontrol.pack(expand = 1, fill = "both")
        self.load_rig_frame_init(automated_tab)
        self.swdl_frame_init(automated_tab)
        self.rig_config_frame_init(automated_tab)
        self.other_frame_init(automated_tab)
        self.run_frame_init(automated_tab)
        self.connect_frame_init(tester_tab)
        self.diag_frame_init(tester_tab)
        self.logger_frame_init(tester_tab)
        self.img = ImageTk.PhotoImage(Image.open("misc/images/hilding.png").resize((400, 120),
                                                                                Image.ANTIALIAS))
        tk.Label(automated_tab, image = self.img, width = 380, height = 100).place(x = 330, y = 25)
        self.terminal = Terminal(pady=5, padx=5, background = "Black",
                                                insertbackground ="White", foreground = "white")
        self.terminal.pack(expand=False, fill='both')
        self.terminal.place(x=40, y=320, height = 360,width = 680)
        self.terminal.basename = "hilding $"

        self.log_terminal = Terminal(pady=5, padx=5, background = "Black",
                                                insertbackground ="White", foreground = "white")
        self.log_terminal.pack(expand=False, fill='both')
        self.log_terminal.place(x=600, y=26, height = 0,width = 0)

        self.log_terminal.basename = "hilding $"

        tabcontrol.bind("<<NotebookTabChanged>>", self.on_tab_selected)
        self.tester = Tester()

    def on_tab_selected(self, event):
        """
        on tabe selected event
        """
        selected_tab = event.widget.select()
        tab_text = event.widget.tab(selected_tab, "text")

        if tab_text == "Automation":
            self.terminal.place(x=40, y=320, height = 360,width = 680)
            self.log_terminal.place(x=600, y=26, height = 0,width = 0)

        if tab_text == "Tester":
            self.log_terminal.place(x=600, y=22, height = 680,width = 600)
            self.terminal.place(x=40, y=320, height = 0,width = 0)
            self.filter_button.configure(text = "F\nI\nL\nT\nE\nR\nE\nD", fg = "Green",
                                                font = ('bold'), height=8, width=2)

    def load_rig_frame_init(self, tab):
        """
        load Rig Frame Init

        Initialize the frame for load rig button
        """
        load_rig_frame = tk.LabelFrame(tab, height=105,width=270, text="Load Configuration")
        load_rig_button = tk.Button(load_rig_frame, text="Load Config", height=2, width=30,
                                                                    command=self.load_rig)
        load_rig_frame.place(x=40, y=20)
        load_rig_button.place(x= 20, y = 20)

    def swdl_frame_init(self, tab):
        """
        SWDL Frame Init

        Initialize the frame for SWDL objects
        """
        swdl_frame = tk.LabelFrame(tab, height=250,width=420, text="Software Download")
        self.vbf_box = tk.Text(swdl_frame,height=5,width=35)
        self.sddb_box = tk.Text(swdl_frame,height = 2, width = 35)
        vbf_label = tk.Label(swdl_frame, text = "VBFs and sddb file")
        load_vbf_button = tk.Button(swdl_frame,text="Reload vbf",height = 7, width = 9,
                                                                command=self.load_vbfs)
        flash_button = tk.Button(swdl_frame,text="Flash ECU",height = 2, width = 39,
                                                                    command=self.flash)
        swdl_frame.place(x=750,y=20)
        flash_button.place(x=20, y=160)
        vbf_label.place(x=20, y=20)
        self.vbf_box.place(x=20, y=40)
        load_vbf_button.place(x=320, y = 40)
        self.sddb_box.place(x=20, y = 120)

    def rig_config_frame_init(self, tab):
        """
        Rig config Frame Init

        Initialize the frame for the rig configuration objects
        """
        rig_config_frame = tk.LabelFrame(tab, height=250,width=420, text="Current Rig Setup")
        save_config_button = tk.Button(rig_config_frame, text="Save Config", height=3,width=10,
                                                                            command=self.set_rig)
        rigs_button = tk.Button(rig_config_frame,text="Sync rig",height=3,width=10,
                                                                        command=self.update_rigs)
        self.current_rig_box = tk.Text(rig_config_frame,height=1,width=30)
        current_rig_label = tk.Label(rig_config_frame, text = "Active rig")
        self.current_hostname = tk.Text(rig_config_frame,height=1,width=30)
        current_hostname_label = tk.Label(rig_config_frame, text = "hostname")
        self.current_user = tk.Text(rig_config_frame,height=1,width=30)
        current_user_label = tk.Label(rig_config_frame, text = "user")
        self.current_platform = tk.Text(rig_config_frame,height=1,width=30)
        current_platform_label = tk.Label(rig_config_frame, text = "platform")
        rig_config_frame.place(x=750,y= 280)
        current_rig_label.place(x=20,y=20)
        current_hostname_label.place(x=20,y=60)
        current_user_label.place(x=20,y=100)
        current_platform_label.place(x=20,y=140)
        rigs_button.place(x=280, y=120)
        self.current_rig_box.place(x=20, y = 40)
        self.current_hostname.place(x=20, y = 80)
        self.current_user.place(x=20, y = 120)
        self.current_platform.place(x=20, y = 160)
        save_config_button.place(x=280, y=40)

    def other_frame_init(self, tab):
        """
        other Frame Init

        Initialize the frame for all the other objects
        """
        additional_frame = tk.LabelFrame(tab, height=120,width=420, text="Other Features")
        nightly_button = tk.Button(additional_frame,text="nightly",height=2,width=8,
                                                                command=self.nightly)
        did_button = tk.Button(additional_frame,text="did_report",height=2,width=8,
                                                            command=self.did_report)
        reset_button = tk.Button(additional_frame,text="reset",height=2,width=8,
                                                            command=self.reset)
        sddb_button = tk.Button(additional_frame,text="sddb",height=2,width=8,
                                                            command=self.sddb)
        additional_frame.place(x=750,y=540)
        sddb_button.place(x=320, y=20)
        nightly_button.place(x=20, y=20)
        did_button.place(x=220, y=20)
        reset_button.place(x=120, y=20)

    def run_frame_init(self, tab):
        """
        Run Frame Init

        Initialize the frame for the run command objects
        """
        run_frame = tk.LabelFrame(tab, height=150,width=680, text="Run script")
        self.run_script_box = tk.Text(run_frame,height=1,width=20)
        self.run_script_box.bind('<Return>', self.run)
        run_button = tk.Button(run_frame,text="Run",height=2,width=7, command=self.run)
        run_selected_button = tk.Button(run_frame,text="Run selected script",height=2,width=16,
                                                                    command=self.run_selected)
        clear_button = tk.Button(run_frame,text="Clear",height=2,width=16, command=self.clear_run)
        run_label = tk.Label(run_frame, text = "Enter the reqprod id to run script")
        self.script_list_box = tk.Listbox(run_frame, height=3, width=105)
        self.script_list_box.pack(side="left")
        scroll_bar = tk.Scrollbar(self.script_list_box)
        self.script_list_box.config(yscrollcommand = scroll_bar.set)
        self.script_list_box.place(x= 20, y= 60)
        scroll_bar.place(x= 615,y=0)
        run_label.place(x=16,y=10)
        self.run_script_box.place(x=20,y=35)
        run_button.place(x=210, y=15)
        run_selected_button.place(x=295,y =15)
        clear_button.place(x=450, y=15)
        run_frame.place(x=40,y=135)

    def connect_frame_init(self, tab):
        """
        Connect Frame Init

        Initialize the frame for the Connect button
        """
        connect_frame = tk.LabelFrame(tab, height=105,width=279, text="Connect/Disconnect")
        self.connect_button = tk.Button(connect_frame,text="Connect",fg = "Green",
                                            height=2,width=32,command=self.connect_disconnect)
        self.connect_button.place(x=20,y=20)
        connect_frame.place(x=40,y=20)

    def diag_frame_init(self, tab):
        """
        Diag Frame Init

        Initialize the frame for the Diagnostics commands.
        """
        diag_frame = tk.LabelFrame(tab, height=500,width=530,
                                                text="Send and receive Diagnostic Commands")
        diag_button = tk.Button(diag_frame,text="Diag Request",height=1,width=20,
                                                                    command=self.diag_send)
        self.diag_request_box = tk.Text(diag_frame,height=2,width=60)
        self.diag_request_box.bind('<Return>', self.diag_send)
        self.diag_response_box = tk.Text(diag_frame,height=22,width=60)
        self.diag_request_box.place(x=20,y=20)
        self.diag_response_box.place(x=20,y=100)
        diag_button.place(x=350,y=66)
        diag_frame.place(x=40,y=150)

    def logger_frame_init(self, tab):
        """
        Logger Frame Init

        Initialize the frame for the Can Logger settings
        """
        self.filter_button = tk.Button(tab,text="F\nI\nL\nT\nE\nR\nE\nD",height=8,width=2,
                                    fg = "Green", font = ('bold'), command=self.log_filter)

        logger_button = tk.Button(tab, text="Start Logging", height=2, width=16,
                                                                    command=self.start_log)
        logger_button.place(x=390,y=55)
        self.filter_button.place(x=575,y=0)

    def update_rigs(self):
        """
        Update Rigs

        button to sync rig with PC
        """
        self.terminal.run_command("python manage.py rigs --update", give_input="CanCase")

    def sddb(self):
        """
        SDDB

        button to sync SDDB with PC
        """
        self.terminal.run_command("python manage.py sddb", give_input=None)

    def reset(self):
        """
        reset

        button to reset ECU
        """
        self.terminal.run_command("python manage.py reset", give_input=None)

    def did_report(self):
        """
        did report

        button to create a did report
        """
        self.terminal.run_command("python manage.py did_report", give_input=None)

    def flash(self):
        """
        Flash

        button to Flash ECU
        """
        self.load_vbfs()
        self.terminal.run_command("python manage.py flash", give_input=None)

    def nightly(self):
        """
        nightly

        button to run nightly test
        """
        self.terminal.run_command("python manage.py nightly", give_input=None)

    def run(self, event = None):
        """
        run

        button to run the script given in the text box by user
        """
        script_to_run = self.run_script_box.get("1.0","end").strip("\n")
        self.run_script_box.delete("1.0", tk.END)
        self.script_list_box.delete(0, tk.END)
        selected_script = self.script_lister(script_to_run)
        if selected_script:
            selected_script = selected_script.split("----->")[0]
            self.terminal.run_command("python manage.py run " +selected_script, give_input=None)

    def clear_run(self):
        """
        clear run

        button to clear the boxes in run frame
        """
        self.script_list_box.delete(0, tk.END)
        self.script_list_box.configure(background="white")

    def run_selected(self):
        """
        run selected

        button to run the selected script when there are multiple options in the list box
        """
        selected_script = self.script_list_box.get(tk.ANCHOR).split("----->")[0]
        self.terminal.run_command("python manage.py run " +selected_script, give_input=None)


    def load_rig(self):
        """
        load rigs

        button to load conf_default
        """
        self.__load_conf_local()
        self.load_vbfs()

    def script_lister(self, script_to_run):
        """
        script lister

        button to list the scripts if there are multiple options available
        """
        files = []
        selected_script = ""
        file_dict = self.__script_picker(script_to_run)
        test_auto_dir = Path(__file__).parent.joinpath("test_folder")

        for key, value in file_dict.items():
            files_temp = [str(f) for f in test_auto_dir.glob(f"*/*{key}.py")]
            if files_temp:
                files.append(files_temp[0]+ "----->"+value)

        if not files:
            files = [str(f) for f in test_auto_dir.glob(f"*/*{script_to_run}.py")]

        if not files:
            self.script_list_box.insert(tk.END, "No related files found")
            self.script_list_box.configure(background="red")
            selected_script = None
        elif len(files) == 1:
            self.script_list_box.insert(tk.END,"Running . . . ")
            self.script_list_box.insert(tk.END, files[0].split("\\")[-1])
            self.script_list_box.configure(background="lightgreen")
            selected_script = files[0].split("\\")[-1]
        else:
            self.script_list_box.insert(tk.END, "Select a file below to run")
            self.script_list_box.configure(background="yellow")
            for file in files:
                self.script_list_box.insert(tk.END, file.split("\\")[-1])
            selected_script = None

        return selected_script

    def connect_disconnect(self):
        """
        connect

        button to connect to the ECU and send wake up frames
        """
        if self.connect_button.cget('text') == "Connect":
            self.load_rig()
            self.tester.connect(self)
            self.connect_button.configure(text="Disconnect",fg = "Red")
        else:
            self.tester.disconnect()
            self.connect_button.configure(text="Connect",fg = "Green")

    def diag_send(self, event = None):
        """
        diag_send

        button to send a diagnostic request to the ECU.
        """
        entry = self.diag_request_box.get("1.0","end").strip('\n')
        self.tester.diag_send(self)
        self.diag_request_box.delete("1.0", tk.END)
        self.diag_request_box.insert(tk.END, entry)

    def start_log(self):
        """
        start_log

        button to start the diagnostic logs from ECU.
        """
        self.load_rig()
        self.tester.start_log(self)

    def log_filter(self):
        """
        diag_send

        button to send a diagnostic request to the ECU.
        """
        if self.filter_button.cget("text") == "F\nI\nL\nT\nE\nR\nE\nD":
            self.filter_button.configure(text = "F\nI\nL\nT\nE\nR", fg = "Black",
                                                font = ('bold'), height=6, width=2)
            self.log_terminal.place(x=600, y=22, height = 0,width = 0)
        else:
            self.filter_button.configure(text = "F\nI\nL\nT\nE\nR\nE\nD", fg = "Green",
                                                font = ('bold'), height=8, width=2)
            self.log_terminal.place(x=600, y=22, height = 680,width = 600)

    @staticmethod
    def __script_picker(reqprod):
        """
        This function returns the script name from the script mapping
        file by taking the reqprod ID as input.
        """

        script_dict = {}
        with open('req_script_mapping.yml') as mapping_file:
            mapping_dict = yaml.safe_load(mapping_file)

        for key, value in mapping_dict.items():
            if reqprod in value:
                for req in value.split(" "):
                    if reqprod in req:
                        script_dict[key] = req

        return script_dict

    def load_vbfs(self):
        """
        load vbfs

        button to load the available vbfs and display in the UI
        """
        dut = Dut()
        vbf_list = os.listdir(dut.conf.rig.vbf_path)
        sddb_path = os.listdir(dut.conf.rig.sddb_path)
        self.__clear_vbf_boxes()
        for vbf in vbf_list:
            self.vbf_box.insert(tk.END, vbf+'\n')
        for sddb in sddb_path:
            self.sddb_box.insert(tk.END,sddb)
        if len(vbf_list) == 0:
            self.vbf_box.insert(tk.END, "No vbfs found.\nPlease configure the current rig\nsetup, "
                                                                    "sync rig and try again.")

    def __load_conf_local(self):
        """
        load conf_local

        function to load conf_local
        """
        with open("conf_local.yml") as conf:
            conf_local_dict = yaml.safe_load(conf)
            current_rig = conf_local_dict["default_rig"]
            current_rig_conf = conf_local_dict["rigs"][current_rig]
            self.__clear_rig_boxes()
            self.current_rig_box.insert(tk.INSERT,conf_local_dict["default_rig"])
            self.current_hostname.insert(tk.INSERT,current_rig_conf["hostname"])
            self.current_user.insert(tk.INSERT,current_rig_conf["user"])
            self.current_platform.insert(tk.INSERT,current_rig_conf["platform"])

    def __clear_rig_boxes(self):
        """
        clear rig boxes

        function to clear the rig boxes
        """
        self.current_rig_box.delete("1.0",tk.END)
        self.current_hostname.delete("1.0",tk.END)
        self.current_user.delete("1.0",tk.END)
        self.current_platform.delete("1.0",tk.END)

    def __clear_vbf_boxes(self):
        """
        clear vbf boxes

        function to clear the vbf boxes in UI
        """
        self.vbf_box.delete("1.0",tk.END)
        self.sddb_box.delete("1.0",tk.END)

    def set_rig(self):
        """
        set rig

        button to save the rig config from UI
        """
        with open("conf_local.yml", mode="rt") as conf:
            conf_local_dict = yaml.safe_load(conf)

            if self.current_rig_box.get('1.0','end').strip('\n') in conf_local_dict["rigs"].keys():
                current_rig = conf_local_dict["default_rig"]
                conf_local_dict["rigs"][current_rig]["hostname"] = self.current_hostname.get('1.0',
                                                                                'end').strip('\n')
                conf_local_dict["rigs"][current_rig]["user"] = self.current_user.get('1.0',
                                                                                'end').strip('\n')
                conf_local_dict["rigs"][current_rig]["platform"] = self.current_platform.get(
                                                                        '1.0','end').strip('\n')
                conf_local_dict["default_rig"] = self.current_rig_box.get('1.0',
                                                                'end').strip('\n')

            else:
                conf_local_dict["default_rig"] = self.current_rig_box.get('1.0','end').strip('\n')
                current_rig = conf_local_dict["default_rig"]
                conf_local_dict["rigs"][current_rig] = {}
                conf_local_dict["rigs"][current_rig] = {}
                conf_local_dict["rigs"][current_rig] = {}

                conf_local_dict["rigs"][current_rig]["hostname"] = self.current_hostname.get(
                                                                        '1.0','end').strip('\n')
                conf_local_dict["rigs"][current_rig]["user"] = self.current_user.get(
                                                                        '1.0','end').strip('\n')
                conf_local_dict["rigs"][current_rig]["platform"] = self.current_platform.get(
                                                                        '1.0','end').strip('\n')

        with open("conf_local.yml", mode="wt", encoding="utf-8") as conf:
            yaml.dump(conf_local_dict, conf)

class Tester:
    """ Tester Class for hilding in UI"""
    def __init__(self):
        self.dut = Dut()
        self.terminal_state = False

    def connect(self, window_obj):
        if self.terminal_state == False:
            window_obj.log_terminal.run_command("ssh " + window_obj.current_hostname.get('1.0',
                        'end').strip('\n') + " candump -ta can0,653:7ff,753:7ff", give_input=None)
            self.terminal_state = True
        self.dut.ecu_wake_up(timeout = 100000)

    def disconnect(self):
        self.dut.ecu_sleep()

    def start_log(self, window_obj):
        if self.terminal_state == False:
            window_obj.log_terminal.run_command("ssh " + window_obj.current_hostname.get('1.0',
                        'end').strip('\n') + " candump -ta can0,653:7ff,753:7ff", give_input=None)
            self.terminal_state = True

    def diag_send(self, window_obj):
        try:
            if window_obj.connect_button.cget('text') == "Disconnect":
                response = self.dut.uds.generic_ecu_call(bytes.fromhex(
                                        window_obj.diag_request_box.get('1.0','end').strip('\n')))

                window_obj.diag_response_box.delete("1.0",tk.END)
                window_obj.diag_response_box.insert(tk.END, response)
            else:
                window_obj.diag_response_box.delete("1.0",tk.END)
                window_obj.diag_response_box.insert(tk.END, 
                    "The ECU is sleeping. Please press connect button and try again")
        except UdsEmptyResponse:
            window_obj.diag_response_box.delete("1.0",tk.END)
            window_obj.diag_response_box.insert(tk.END, 
                    "No response from the ECU Please check if the ECU is connected and working")



if __name__ == '__main__':

    window = teek()
    ttk.Style().theme_use('xpnative')
    HildingUI(window)
    window.title("Manage Hilding")
    window.geometry("1200x700")

    window.mainloop()
