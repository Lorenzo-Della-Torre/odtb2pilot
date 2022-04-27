"""shall contain big functions to keep the GUI file clean(er)
"""
from socket import gaierror
from paramiko import SSHClient
from paramiko import AuthenticationException
from paramiko.ssh_exception import SSHException
from pathlib import Path
import yaml
import shutil
import os

from hilding.conf import get_conf

CONF = get_conf()

def add_ssh_key(selected_rig, ssh_passwords, console_content, local_auth_key):
    """Add a key to the remote rigs authorized keys list. Giving future access without
    using password

    Args:
        selected_rig (string): A rig, as writtern in conf_local
        ssh_passwords (dict): Dictionary containing passwords used when sshing
        console_content (StringVar): Anything written here will be put in console tab
        local_auth_key (string): The key that should be added to remote host

    Returns:
        Bool: Result
    """
    CONF.__init__()
    ssh = SSHClient()
    ssh.load_system_host_keys()
    user = CONF.rigs.get(selected_rig).get("user")
    hostname = CONF.rigs.get(selected_rig).get("hostname")

    # Connect to hilding
    try:
        # first try to connect using pre-authorized_keys
        ssh.connect(hostname, username=user)
    except (AuthenticationException, SSHException, gaierror):
        # if that doesn't work see if password in configured
        console_content.set(console_content.get() + " Password dict: " +str(ssh_passwords) + "\n")
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
    authorized_keys_path = Path(f'/home/{user}/.ssh/authorized_keys')
    try:
        with sftp.open(authorized_keys_path.as_posix(), 'a') as remote_auth_keys:
            remote_auth_keys.write("\n" + local_auth_key + "\n")
    except FileNotFoundError:
        console_content.set(console_content.get() + " Unable to open remote auth keys \n")
    return True

def get_filenames_from_rig(selected_rig, ssh_passwords, console_content):
    """Get paths to VBFs and SDDb files on a certain rig

    Args:
        selected_rig (string): Name of rig as written in yml config files
        ssh_passwords (dict): A dictionary containing ssh passwords for rigs.
        Used of ssh kays are not configured

    Returns:
        bool, list, list, SFTPClient: Result, list with vbf paths, list with sddb paths, SFTPClient
    """
    # Read from file in case of updates
    CONF.__init__()
    ssh = SSHClient()
    ssh.load_system_host_keys()
    user = CONF.rigs.get(selected_rig).get("user")
    hostname = CONF.rigs.get(selected_rig).get("hostname")
    remote_vbf_paths = []
    remote_sddbs_paths = []
    remote_rig = ""

    # Connect to hilding
    try:
        # first try to connect using pre-authorized_keys
        ssh.connect(hostname, username=user)
    except (AuthenticationException, SSHException, gaierror):
        # if that doesn't work see if password in configured
        console_content.set(console_content.get() + " Password dict: " +str(ssh_passwords) + "\n")
        potential_password = ssh_passwords.get(selected_rig)
        if potential_password:
            try:
                ssh.connect(hostname, username=user, password=potential_password)
            except(AuthenticationException, SSHException, gaierror):
                return False, remote_vbf_paths, remote_sddbs_paths, None
        else:
            print(f"password for {selected_rig} not found in {ssh_passwords}"
                " or password incorrect")
            return False, remote_vbf_paths, remote_sddbs_paths, None
    sftp = ssh.open_sftp()

    # Get config from hilding
    remote_config_path = Path(f'/home/{user}/Repos/odtb2pilot/conf_local.yml')
    try:
        with sftp.open(remote_config_path.as_posix()) as remote_config_yml:
            remote_config_dict = yaml.safe_load(remote_config_yml)
            remote_rig = remote_config_dict.get("default_rig")
    except FileNotFoundError:
        print("Unable to open remote config")

    # Get VBF paths
    remote_vbf_path = Path(f'/home/{user}/Repos/odtb2pilot/rigs/{remote_rig}/vbf')
    try:
        remote_files = sftp.listdir(remote_vbf_path.as_posix())
        remote_vbf_paths = [remote_vbf_path.joinpath(remote_file) for remote_file in remote_files]
    except FileNotFoundError:
        print(f"No VBF files found in {remote_vbf_path.as_posix()}")

    # Get sddb paths
    remote_sddb_path = Path(f'/home/{user}/Repos/odtb2pilot/rigs/{remote_rig}/sddb')
    try:
        remote_files = sftp.listdir(remote_sddb_path.as_posix())
        remote_sddbs_paths = [remote_sddb_path.joinpath(remote_file) for remote_file in remote_files]
    except FileNotFoundError:
        print(f"No sddb found in {remote_sddb_path.as_posix()}")
        pass

    return True, remote_vbf_paths, remote_sddbs_paths, sftp

def get_rig_files(ssh_passwords, selected_rig, remote_paths=[]):
    """Download vbf and sddb files to rigs/X/vbf and /rigs/X/sddb

    Args:
        selected_rig (string): Name of rig as written in yml config files
        ssh_passwords (dict): A dictionary containing ssh passwords for rigs.
        remote_paths (list, optional): Paths to remote files. Defaults to [].

    Returns:
        boolean: Result from file download
    """
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
    sftp = ssh.open_sftp()

    local_rig_path = CONF.hilding_root.joinpath(f"rigs/{selected_rig}/")
    shutil.rmtree(local_rig_path, ignore_errors=True)
    os.makedirs(local_rig_path.joinpath("vbf"), exist_ok=True)
    os.makedirs(local_rig_path.joinpath("sddb"), exist_ok=True)
    os.makedirs(local_rig_path.joinpath("build"), exist_ok=True)
    for remote_file in remote_paths:
        #remote_file = remote_delivery_paths.joinpath(filename)
        if remote_file.as_posix().endswith('.vbf'):
            local_file = local_rig_path.joinpath("vbf", remote_file.name)
            sftp.get(remote_file.as_posix(), local_file)
        if remote_file.as_posix().endswith('.sddb'):
            local_file = local_rig_path.joinpath("sddb", remote_file.name)
            sftp.get(remote_file.as_posix(), local_file)
            # We get the parsed sddb files as well to make sure we have an exact replica
            remote_python_sddbs = sftp.listdir(remote_file.parent.parent.joinpath("build").as_posix())
            for build_file in [f for f in remote_python_sddbs if f.endswith("py")]:
                local_file = local_rig_path.joinpath("build", build_file)
                sftp.get(remote_file.parent.parent.joinpath("build", build_file).as_posix(), local_file)
        if remote_file.as_posix().endswith('.dbc'):
            local_file = local_rig_path.joinpath("dbc/", remote_file.name)
            sftp.get(remote_file.as_posix(), local_file)

    ssh.close()
    return True
