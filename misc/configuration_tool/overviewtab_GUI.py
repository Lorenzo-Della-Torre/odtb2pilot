import os
from pprint import pformat
from paramiko import SSHClient
import tempfile
import yaml
from ast import literal_eval

from tkinter import Frame
from tkinter import Label
from tkinter import Button
from tkinter import Text
from tkinter import ttk

from misc.configuration_tool.popups import PasswordPrompt, AddRig, NoRig, KeysPrompt
from supportfunctions.support_file_io import SupportFileIO
from hilding.conf import get_conf
from misc.configuration_tool.overviewtab_functions import get_filenames_from_rig, get_rig_files, add_ssh_key

SupportFileIO = SupportFileIO()
CONF = get_conf()

class overviewTab():
    """This class contains an overview tab. Which is kind of the main page in the gui
    """

    def __get_files_from_rig(self, selected_rig):
        """This function will return temp files for all VBFs found on the remote rig.
        It also returns a list with sddb files found (note, not temp files, just paths)

        Args:
            selected_rig (string): name of rig as it is known in conf_local

        Returns:
            bool, list, list: Result. List with VBF temp files. List with paths to sddb files
        """
        ssh = SSHClient()
        ssh.load_system_host_keys()
        remote_vbfs = []

        result, remote_vbf_paths, remote_sddbs_paths, sftp = get_filenames_from_rig(
            selected_rig,
            self.ssh_passwords,
            self.console_content)

        if remote_vbf_paths:
            for remote_path in remote_vbf_paths:
                temp_local_file = tempfile.NamedTemporaryFile(mode='w+')
                temp_local_file.name = remote_path.name

                if remote_path.as_posix().endswith('.vbf'):
                    with sftp.open(remote_path.as_posix(), 'rb') as temp_remote_file:
                        for line in temp_remote_file.readlines():
                            try:
                                temp_local_file.write(line.decode("latin1"))
                            except UnicodeEncodeError:
                                # No big deal if some lines are not readable
                                temp_local_file.write("Missing line")
                        temp_local_file.seek(0)
                remote_vbfs.append(temp_local_file)

        sddb_file_names = [sddb.name for sddb in remote_sddbs_paths]

        return result, remote_vbfs, sddb_file_names

    def update_config_text(self, event, selected_platform_input=""):
        """Update the text field containing config from conf_default

        Args:
            event (_type_): Dummy value (not used)
            selected_platform_input (str, optional): If other value than the one found in dropdown is to be used.
            Defaults to "".
        """
        if not selected_platform_input:
            selected_platform = self.dropdown_platforms.get()
        else:
            selected_platform = selected_platform_input
        pp_string = pformat(CONF.platforms.get(selected_platform))
        self.configuration_text['state'] = "normal"
        self.configuration_text.delete("1.0","end")
        self.configuration_text.insert("1.0", pp_string)
        self.configuration_text['state'] = "disabled"

    def update_ymls(self):
        """Update the conf_local yml file
        """
        config_string = self.configuration_text.get("1.0", "end")
        rigs_string = self.rigs_text.get("1.0", "end")

        current_config_data = dict()
        current_rig_data = dict()
        current_config_data[self.dropdown_platforms.get()] = literal_eval(config_string)
        current_rig_data[self.dropdown_rigs.get()] = literal_eval(rigs_string)
        current_rig_data.get(self.dropdown_rigs.get())["platform"] = self.dropdown_platforms.get()
        yml_config_data = dict()
        yml_rig_data = dict()
        yml_config_data["platforms"] = CONF.platforms
        yml_rig_data["default_rig"] = self.dropdown_rigs.get()
        yml_rig_data["rigs"] = CONF.rigs

        yml_config_data["platforms"].update(current_config_data)
        yml_rig_data["rigs"].update(current_rig_data)

        with open("conf_local.yml", 'w') as conf_local_file:
            yaml.safe_dump(yml_rig_data, conf_local_file, indent=4)

        CONF.__init__()
        self.update_rig_info("")

    def update_rig_info(self, event):
        """Update text field containing info from conf_local

        Args:
            event (_type_): Dummy value (not used)
        """
        selected_rig = self.dropdown_rigs.get()
        pp_string = pformat(CONF.rigs.get(selected_rig))
        self.rigs_text.delete("1.0","end")
        self.rigs_text.insert("1.0", pp_string)
        self.update_config_text("", selected_platform_input=CONF.rigs.get(selected_rig).get("platform"))
        self.dropdown_platforms.set(CONF.rigs.get(selected_rig).get("platform"))
        self.VBF_text.delete("1.0","end")
        self.VBF_text.insert("1.0", self.get_rig_files_info(selected_rig))

    def get_rig_files_info(self, rig):
        """Builds the string containing info about VBF and SDDB files on both local machine and remote

        Args:
            rig (string): Chosen ring, named as in yml config files
        """

        def __extract_vbf_info(file):
            """Builds string with info from a VBF file

            Args:
                file (file): A VBF file

            Returns:
                string: String with info about VBF
            """
            internal_ret_string = ""
            internal_ret_string += str(file.name)
            if isinstance(file, os.PathLike):
                vbf_file = open(file, "r", encoding="latin1")
            else:
                vbf_file = file
            built_time, part_type = "", ""
            for line in vbf_file.readlines():
                line = line.replace("\n", "")
                if "Build time" in line:
                    built_time = line.split("Build time:")[1].replace(",", "")
                    built_time = built_time.replace("\"", "")
                if "sw_part_type =" in line:
                    part_type = line.split("sw_part_type = ")[1].split(";")[0]
                if part_type and built_time:
                    internal_ret_string += f" ({part_type}) -{built_time}"
                    break
            return internal_ret_string

        # VBFs From local machine
        vbf_folder = CONF.hilding_root.joinpath("rigs", rig, "vbf")
        ret_string = f"VBF file(s) found in {vbf_folder}: \n"
        if os.path.exists(vbf_folder):
            vbf_files = vbf_folder.glob("*.vbf")
            for file in vbf_files:
                ret_string += __extract_vbf_info(file) + "\n"

        # VBFs From hilding
        connection_result, remote_vbfs, remote_sddbs = self.__get_files_from_rig(rig)
        ret_string += f"\nVBF file(s) found in {rig}: \n"
        if not connection_result:
            ret_string += f"Not able to get VBFs from {rig}. Make sure ssh keys are set up\n" +\
            f"(Hint: press 'Manually enter ssh key' to enter the password \n for user {rig}) \n"
        else:
            for remote_vbf in remote_vbfs:
                ret_string += __extract_vbf_info(remote_vbf) + "\n"
                remote_vbf.close()

        # Sddb from local machine
        sddb_folder = CONF.hilding_root.joinpath("rigs", rig, "sddb")
        ret_string += f"\nSddb file(s) found in {sddb_folder}: \n"
        if os.path.exists(sddb_folder):
            sddb_files = sddb_folder.glob("*.sddb")
            for file in sddb_files:
                ret_string += file.name + "\n"

        # Sddbs from hilding
        ret_string += f"\nSddb file(s) found in {rig}: \n"
        if not connection_result:
            ret_string += f"Not able to get VBFs from {rig}. Make sure ssh keys are set up\n" +\
            f"(Hint: press 'Manually enter ssh key' to enter the password \n for user {rig}) \n"
        else:
            for sddb_file in remote_sddbs:
                ret_string += sddb_file + "\n"

        return ret_string

    def add_rig_to_yml(self, rig_dict):
        """Add new rig to conf_local

        Args:
            rig_dict (dict): Info about new rig to be added
        """
        added_to_conf_local = {rig_dict["rigname"] : {}}
        added_to_conf_local[rig_dict["rigname"]] = {"hostname" : rig_dict["hostname"],
            "platform" : rig_dict["platform"],
            "user" : rig_dict["user"],
            "signal_broker_port" : int(rig_dict["signal_broker_port"])}
        new_conf_local = dict()
        new_conf_local["rigs"] = {**CONF.rigs, **added_to_conf_local}
        new_conf_local["default_rig"] = rig_dict["rigname"]
        with open("conf_local.yml", 'w') as conf_local_file:
            yaml.safe_dump(new_conf_local, conf_local_file, indent=4)

    def add_rig_popup(self):
        """Summons a popup for adding rig and calls backend functionality to add in to conf_local

        Returns:
            No return: None
        """
        add_rig_return = dict()
        add_rig_popup = AddRig(self.parent, self.platforms, add_rig_return)
        self.parent.wait_window(add_rig_popup)
        self.add_rig_to_yml(add_rig_return)
        self.update_screen()


    def update_files(self):
        """Download files from remote to local machine (VBFs and SDDBs)
        """
        self.update_files_result['text'] = ""
        selected_rig = self.dropdown_rigs.get()
        result, remote_vbf_paths, remote_sddbs_paths, sftp = get_filenames_from_rig(
            selected_rig,
            self.ssh_passwords,
            self.console_content)
        result = get_rig_files(self.ssh_passwords,
            selected_rig,
            remote_vbf_paths + remote_sddbs_paths) and result
        if result:
            self.update_rig_info("")
            self.update_files_result['text'] = "Successfully updated files!"
        else:
            self.update_files_result['text'] = "Update not successful"

    def update_ssh_passwords(self):
        """Add currently selected rig to dict containing ssh passwords
        """
        passwords_popup_return_values = dict()
        pass_popupp = PasswordPrompt(self.parent, passwords_popup_return_values)
        self.parent.wait_window(pass_popupp)
        self.ssh_passwords[self.dropdown_rigs.get()] = passwords_popup_return_values["password"]
        self.update_rig_info("")

    def update_ssh_keys(self):
        """Add key to selected rigs ssh keys
        """
        ret_values = dict()
        pass_popupp = KeysPrompt(self.parent, ret_values)
        self.parent.wait_window(pass_popupp)
        result = add_ssh_key(self.dropdown_rigs.get(),
            self.ssh_passwords,
            self.console_content,
            ret_values["key"])
        self.update_rig_info("")
        if result:
            self.update_rig_info("")
            self.update_files_result['text'] = "Successfully added key"
        else:
            self.update_files_result['text'] = "Key not added"

    def update_screen(self):
        """Update all text boxes etc. that are on screen
        """
        CONF.__init__()
        self.platforms = list(CONF.platforms.keys())
        self.rigs = list(CONF.rigs)

        # If elements are not yet created
        try:
            self.dropdown_rigs["values"] = self.rigs
            self.dropdown_rigs.set(CONF.default_rig)
            self.dropdown_platforms["values"] = self.platforms
            self.dropdown_platforms.set(CONF.default_platform)
            self.update_rig_info("")
        except AttributeError:
            pass

    def __init__(self, parent, ssh_passwords, console_content):
        # pylint: disable=too-many-instance-attributes, too-many-statements
        self.parent = parent

        # Variables
        self.platforms = list(CONF.platforms.keys())
        self.rigs = list(CONF.rigs)
        self.ssh_passwords = ssh_passwords
        self.console_content = console_content

        # If no rigs are found in conf_local
        if len(self.rigs) == 1 and 'piX' in self.rigs:
            self.parent.master.master.withdraw()
            no_rig_return = dict()
            no_rig_popup = NoRig(self.parent, no_rig_return)
            self.parent.wait_window(no_rig_popup)

            if no_rig_return["ret"]:
                self.add_rig_popup()
        self.parent.master.master.deiconify()

        # Top
        self.top_field = Frame(parent)
        self.top_field.grid(row = 0)

        self.top_text = Label(self.top_field, text="Overview", height="2")
        self.top_text.grid()

        # Top left -------------------------------------------------
        self.left_top_grid = Frame(parent, bg="#ABF5BC", padx="10", pady="10", height="800", width="700")
        self.left_top_grid.grid_propagate(0)
        self.left_top_grid.grid(column=0, row=1)

        # Rig selection
        self.rig_selection_frame = Frame(self.left_top_grid)
        self.rig_selection_frame.grid(row=0)
        self.default_rigs_label = Label(self.rig_selection_frame, bg="#ABF5BC", text="Default rig:")
        self.default_rigs_label.grid(column=0, row=0)
        self.dropdown_rigs = ttk.Combobox(self.rig_selection_frame, values=self.rigs)
        self.dropdown_rigs.grid(column=1, row=0, sticky="N")
        self.dropdown_rigs.set(CONF.selected_rig)
        self.dropdown_rigs.bind("<<ComboboxSelected>>", func=self.update_rig_info)
        self.add_rig_button = Button(self.rig_selection_frame, text="Add rig", command=self.add_rig_popup)
        self.add_rig_button.grid(column=2, row=0)
        # Rig infotext
        self.rigs_info_frame = Frame(self.left_top_grid)
        self.rigs_info_frame.grid(column=0, row=1)
        self.rigs_text = Text(self.rigs_info_frame,
            bg = "white",
            font="Consolas 12 bold",
            width='70',
            height='10',
            wrap='none')
        self.rigs_text.grid(column=0, row=0)

        #Save button
        self.save_config_button = Button(self.left_top_grid,
            text="Save Configuration to yml",
            command=self.update_ymls)
        self.save_config_button.grid(row=2)

        # VBFs info
        self.VBF_info_frame = Frame(self.left_top_grid)
        self.VBF_info_frame.grid(column=0, row=3)
        self.VBF_text = Text(self.VBF_info_frame,
            bg = "white",
            font="Consolas 12 bold",
            width='70',
            height='25',
            wrap='none')

        self.VBF_text.grid(column=0, row=0)

        self.buttons_frame = Frame(self.left_top_grid)
        self.buttons_frame.grid(column=0, row=4)

        # Update button
        self.update_files_button = Button(self.buttons_frame,
            text="Download files from hilding to local machine",
            command=self.update_files)
        self.update_files_button.grid(column=0, row=0)

        # Password Button
        self.shh_passwords_button = Button(self.buttons_frame,
            text="Manually enter ssh password",
            command=self.update_ssh_passwords)
        self.shh_passwords_button.grid(column=1, row=0)

        # Add ssh key button
        self.shh_keys_button = Button(self.buttons_frame,
            text="Add ssh key to remote rig",
            command=self.update_ssh_keys)
        self.shh_keys_button.grid(column=2, row=0)

        self.update_files_result = Label(self.left_top_grid, bg="#ABF5BC", text="")
        self.update_files_result.grid(column=0, row=5)

        # Top middle --------------------------------------------
        self.middle_top_grid = Frame(parent, bg="#E46482", padx="10", pady="10", height="800", width="700")
        self.middle_top_grid.grid(column=1, row=1)
        self.middle_top_grid.grid_propagate(0)

        # Platform selection
        self.dropdown_platforms = ttk.Combobox(self.middle_top_grid, values=self.platforms)
        self.dropdown_platforms.grid(column=0, row=0, sticky="N")
        self.dropdown_platforms.set(CONF.default_platform)
        self.dropdown_platforms.bind("<<ComboboxSelected>>", func=self.update_config_text)

        # Configuration Textbox
        self.configuration_frame = Frame(self.middle_top_grid)
        self.configuration_frame.grid(column=0, row=1)
        self.configuration_text = Text(self.configuration_frame,
            bg = "white",
            font="Consolas 12 bold",
            width='70',
            height='33',
            wrap='none',
            state="disabled")
        self.scrollbar = ttk.Scrollbar(self.configuration_frame,
                                        orient='horizontal',
                                        command=self.configuration_text.xview)

        self.configuration_text.config(xscrollcommand=self.scrollbar.set)
        self.configuration_text.grid(column=0, row=0)
        self.scrollbar.grid(column=0, row=1, sticky="NESW")

        # Top right -------------------------------------------------
        self.right_top_grid = Frame(parent)
        self.right_top_grid.grid(column=2, row=1)

        self.update_rig_info("")
        self.update_config_text("")