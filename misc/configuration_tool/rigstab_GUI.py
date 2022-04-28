from tkinter import IntVar
from tkinter import Frame
from tkinter import Label
from tkinter import Button
from tkinter import Checkbutton
from tkinter import Text
from tkinter import filedialog as fd

from supportfunctions.support_file_io import SupportFileIO
from hilding.conf import get_conf
from misc.configuration_tool.rigstab_functions import upload_files, run_command


SupportFileIO = SupportFileIO()
CONF = get_conf()



class rigsTab():

    def chose_vbfs(self):
        """Chose VBFs from local disk and update text field with info
        """
        self.vbf_files = fd.askopenfilenames()
        files_string = "VBF file(s) selected: \n"
        for file in self.vbf_files:
            files_string += file.split("/")[-1] + "\n"
        self.selected_files_text.delete("1.0", "end")
        self.selected_files_text.insert("1.0", files_string)

    def chose_sddbs(self):
        """Chose SDDBs from local disk and update text field with info
        """
        self.sddb_files = fd.askopenfilenames()
        files_string = "SDDB file(s) selected: \n"
        for file in self.sddb_files:
            files_string += file.split("/")[-1] + "\n"
        self.selected_files_text.delete("1.0", "end")
        self.selected_files_text.insert("1.0", files_string)

    def upload_vbfs(self):
        """Upload chosen VBFs to all checked rigs
        """
        for rig_dict in self.rigs_entries:
            result = False
            for rig, active_status in rig_dict.items():
                if isinstance(active_status, IntVar):
                    if active_status.get():
                        result = upload_files(self.ssh_passwords, rig, self.vbf_files, self.console_content, "vbf")
                        if result:
                            rig_dict["check_box"]["text"] = "Successfully updated VBFs"
                        else:
                            rig_dict["check_box"]["text"] = "Update failed"

    def upload_sddbs(self):
        """Upload chosen SDDBs to all checked rigs
        """
        for rig_dict in self.rigs_entries:
            result = False
            for rig, active_status in rig_dict.items():
                if isinstance(active_status, IntVar):
                    if active_status.get():
                        result = upload_files(self.ssh_passwords, rig, self.sddb_files, self.console_content, "sddb")

                        sddb_parsing_result = False
                        stdout_lines, stderr_lines = run_command(
                            "cd Repos/odtb2pilot ; python manage.py sddb",
                            self.ssh_passwords,
                            rig)

                        # If command fails it might be due to python not being mapped to python3
                        if len(stderr_lines) > 0:
                            stdout_lines, stderr_lines = run_command(
                                "cd Repos/odtb2pilot ; python3 manage.py sddb",
                                self.ssh_passwords,
                                rig)

                        for line in stdout_lines:
                            self.console_content.set(self.console_content.get() + line)
                            print(line)
                            if "INFO sddb Services for primary bootloader," in line:
                                sddb_parsing_result = True

                        if result and sddb_parsing_result:
                            rig_dict["check_box"]["text"] = "Successfully updated SDDB"
                        else:
                            rig_dict["check_box"]["text"] = "Update failed"

    def flash(self):
        """Fash all checked rigs by running "manage.py flash" on the rigs
        """
        for rig_dict in self.rigs_entries:
            for rig, active_status in rig_dict.items():
                if isinstance(active_status, IntVar):
                    if active_status.get():
                        flashing_result = False
                        self.selected_files_text.delete("1.0", "end")
                        self.selected_files_text.insert("1.0", "Flashing started, this will take some time (approx. 400 seconds/ECU)")
                        self.parent.update()
                        stdout_lines, stderr_lines = run_command(
                            "cd Repos/odtb2pilot ; python manage.py flash",
                            self.ssh_passwords,
                            rig,
                            timeout=650)
                        if len(stderr_lines) > 0:
                            stdout_lines, stderr_lines = run_command(
                                "cd Repos/odtb2pilot ; python3 manage.py flash",
                                self.ssh_passwords,
                                rig)

                        for line in stdout_lines:
                            self.console_content.set(self.console_content.get() + line)
                            print(line)
                            if "INFO dut Testcase result: PASSED" in line:
                                flashing_result = True

                        if flashing_result:
                            rig_dict["check_box"]["text"] = "Successfully flashed ECU"
                        else:
                            rig_dict["check_box"]["text"] = "Flashing failed"

                        self.selected_files_text.delete("1.0", "end")
                        self.selected_files_text.insert("1.0", "")

    def __init__(self, parent, ssh_passwords, console_content):
        # pylint: disable=too-many-instance-attributes, too-many-statements
        self.parent = parent

        # Variables
        CONF.__init__()
        self.platforms = list(CONF.platforms.keys())
        self.rigs = list(CONF.rigs)
        self.ssh_passwords = ssh_passwords
        self.vbf_files = list()
        self.sddb_files = list()
        self.console_content = console_content

        # Top
        self.top_field = Frame(parent)
        self.top_field.grid(row = 0)

        self.top_text = Label(self.top_field, text="Rigs management", height="2")
        self.top_text.grid()

        # Top left -------------------------------------------------
        self.left_top_grid = Frame(parent, bg="#ABF5BC", padx="10", pady="10", height="800", width="700")
        self.left_top_grid.grid_propagate(0)
        self.left_top_grid.grid(column=0, row=1)

        self.rigs_entries = list()
        for r, rig in enumerate(self.rigs):
            tmp_frame = Frame(self.left_top_grid, bg="#ABF5BC", padx="10", pady="10", width="300")
            tmp_frame.grid(row = r)

            tmp_label = Label(tmp_frame, text=rig, bg="#ABF5BC")
            tmp_label.grid(column=0)

            tmp_intvar = IntVar()
            tmp_checkbox = Checkbutton(tmp_frame, text="Select rig", bg="#ABF5BC", variable=tmp_intvar, width="30")
            tmp_checkbox.grid(column=1)

            self.rigs_entries.append({rig : tmp_intvar,
                "check_box" : tmp_checkbox})

        self.chose_vbfs_button = Button(self.left_top_grid, text="Select VBFs", command=self.chose_vbfs)
        self.chose_vbfs_button.grid(row=0, column=1)

        self.chose_vbfs_button = Button(self.left_top_grid, text="Upload VBFs", command=self.upload_vbfs)
        self.chose_vbfs_button.grid(row=0, column=2)

        self.chose_sddbs_button = Button(self.left_top_grid, text="Select SDDB", command=self.chose_sddbs)
        self.chose_sddbs_button.grid(row=1, column=1)

        self.chose_sddbs_button = Button(self.left_top_grid, text="Upload SDDB", command=self.upload_sddbs)
        self.chose_sddbs_button.grid(row=1, column=2)

        self.flash_button = Button(self.left_top_grid, text="Flash ECU(s)", command=self.flash)
        self.flash_button.grid(row=2, column=1)


        # Top middle --------------------------------------------
        self.middle_top_grid = Frame(parent, bg="#E46482", padx="10", pady="10", height="800", width="700")
        self.middle_top_grid.grid(column=1, row=1)
        self.middle_top_grid.grid_propagate(0)

        self.selected_files_frame = Frame(self.middle_top_grid)
        self.selected_files_frame.grid(column=0, row=0)
        self.selected_files_text = Text(self.selected_files_frame,
            bg = "white",
            font="Consolas 12 bold",
            width='70',
            height='10',
            wrap='none')
        self.selected_files_text.grid(column=0, row=0)

        # Top right -------------------------------------------------
        self.right_top_grid = Frame(parent)
        self.right_top_grid.grid(column=2, row=1)