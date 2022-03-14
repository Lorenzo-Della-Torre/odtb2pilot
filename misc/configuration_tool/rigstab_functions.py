"""shall contain big functions to keep the GUI file clean(er)
"""
from socket import gaierror
from paramiko import SSHClient
from paramiko import AuthenticationException
from paramiko.ssh_exception import SSHException
from pathlib import Path
import yaml
import time

from hilding.conf import get_conf
from misc.configuration_tool.overviewtab_functions import get_filenames_from_rig

CONF = get_conf()

def run_command(command, ssh_passwords, selected_rig, timeout=1000):
    ssh = SSHClient()
    ssh.load_system_host_keys()
    user = CONF.rigs.get(selected_rig).get("user")
    hostname = CONF.rigs.get(selected_rig).get("hostname")

    try:
        # first try to connect using pre-authorized_keys
        ssh.connect(hostname, username=user)
    except (AuthenticationException, SSHException, gaierror):
        # if that doesn't work see if password in configured
        potential_password = ssh_passwords.get(selected_rig)
        if potential_password:
            try:
                ssh.connect(hostname, username=user, password=potential_password)
            except(AuthenticationException, SSHException, gaierror):
                return False
        else:
            print(f"password for {selected_rig} not found in {ssh_passwords}"
                " or password incorrect")
            return False
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    stdout_lines = stdout.readlines()
    stderr_lines = stderr.readlines()

    return stdout_lines, stderr_lines


def upload_files(ssh_passwords, selected_rig, local_paths, console_content, files_to_remove = ""):
    """
    download vbf and sddb file to rigs/X/vbf and /rigs/X/sddb
    """
    ssh = SSHClient()
    ssh.load_system_host_keys()
    user = CONF.rigs.get(selected_rig).get("user")
    hostname = CONF.rigs.get(selected_rig).get("hostname")
    remote_rig = ""

    try:
        # first try to connect using pre-authorized_keys
        ssh.connect(hostname, username=user)
    except (AuthenticationException, SSHException, gaierror):
        # if that doesn't work see if password in configured
        potential_password = ssh_passwords.get(selected_rig)
        if potential_password:
            try:
                ssh.connect(hostname, username=user, password=potential_password)
            except(AuthenticationException, SSHException, gaierror):
                return False
        else:
            print(f"password for {selected_rig} not found in {ssh_passwords}"
                " or password incorrect")
            return False
    sftp = ssh.open_sftp()

    # Get config from hilding
    remote_config_path = Path(f'/home/{user}/Repos/odtb2pilot/conf_local.yml')
    try:
        with sftp.open(remote_config_path.as_posix()) as remote_config_yml:
            remote_config_dict = yaml.safe_load(remote_config_yml)
            remote_rig = remote_config_dict.get("default_rig")
    except FileNotFoundError:
        print("Unable to open remote config")

    # Remove files on remote to get clean directory
    _, remote_vbf_paths, remote_sddbs_paths, _ = get_filenames_from_rig(selected_rig, ssh_passwords, console_content)

    if "vbf" in files_to_remove.lower():
        for remote_vbf in remote_vbf_paths:
            sftp.remove(remote_vbf.as_posix())
    if "sddb" in files_to_remove.lower():
        for remote_sddb in remote_sddbs_paths:
            sftp.remove(remote_sddb.as_posix())

    # Create directory if they dont exist
    remote_rig_path = Path(f'/home/{user}/Repos/odtb2pilot/rigs/{remote_rig}/')

    if files_to_remove not in sftp.listdir(remote_rig_path.as_posix()):
        sftp.mkdir(remote_rig_path.joinpath(files_to_remove).as_posix())

    # Transfer new files
    for local_file in local_paths:
        remote_file = remote_rig_path.joinpath(files_to_remove, local_file.split("/")[-1]).as_posix()
        sftp.put(local_file, remote_file)

    ssh.close()

    return True
