"""
Rig handling routines

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
import sys
import logging
import shutil
from getpass import getpass
from pathlib import Path

from paramiko import SSHClient
from paramiko import AuthenticationException
from paramiko.ssh_exception import SSHException

from hilding.sddb import parse_sddb_file
from hilding.conf import initialize_conf
from hilding import get_conf


log = logging.getLogger('rig')

def handle_rigs(args):
    """ rig management command handler """
    conf = get_conf()

    if args.config:
        print(conf)
        return
    if args.update:
        get_rig_delivery_files()
        return
    if args.update_all:
        for rig in conf.rigs.keys():
            initialize_conf(rig, force=True)
            get_rig_delivery_files()
        return
    for rig in conf.rigs.keys():
        conf = initialize_conf(rig, force=True)
        print(f"{rig:8} {conf.rig.platform:6} "
              f"{conf.rig.user}@{conf.rig.hostname}")


def print_totals(transferred, total):
    """ displays the progress of the file transfer """
    percentage = float(transferred)/float(total)*100
    sys.stdout.write(
        f"Progress: {transferred:,} / {total:,} bytes {percentage:.2f}%\t\r")


def sftp_copy(sftp, remote_file: Path, local_file: Path):
    """ use sftp to copy a remote_file to local_file"""
    log.info("Copying: %s to %s", remote_file, local_file)
    sftp.get(remote_file.as_posix(), local_file, callback=print_totals)


def get_rig_delivery_files():
    """
    download vbf and sddb file to rigs/X/vbf and /rigs/X/sddb
    """
    ssh = SSHClient()
    ssh.load_system_host_keys()
    conf = get_conf()
    user = conf.rig.user
    hostname = conf.rig.hostname
    log.info("Connecting to: %s@%s", user, hostname)
    try:
        # first try to connect using pre-authorized_keys
        ssh.connect(hostname, username=user)
    except (AuthenticationException, SSHException):
        # if that doesn't work prompt the user for a password
        password = getpass()
        ssh.connect(hostname, username=user, password=password)

    sftp = ssh.open_sftp()
    remote_delivery_path = Path(f'/home/{user}/delivery')
    try:
        delivery_files = sftp.listdir(remote_delivery_path.as_posix())
    except FileNotFoundError:
        log.info("%s does not exist on HILding. If this folder exists, all vbf, sddb and dbc \
files within it will be transferred to your local computer", str(remote_delivery_path))
    else:
        log.info("Copy remote %s/*.{vbf,sddb,dbc} files to this host",
             remote_delivery_path)

        # remove previous file for this rig to keep things clean
        shutil.rmtree(conf.rig.rig_path)
        sddb_file_downloaded = False
        for filename in delivery_files:
            remote_file = remote_delivery_path.joinpath(filename)
            if filename.endswith('.vbf'):
                local_file = conf.rig.vbf_path.joinpath(filename)
                sftp_copy(sftp, remote_file, local_file)
            if filename.endswith('.sddb'):
                local_file = conf.rig.sddb_path.joinpath(filename)
                sftp_copy(sftp, remote_file, local_file)
                sddb_file_downloaded = True
            if filename.endswith('.dbc'):
                local_file = conf.rig.dbc_path.joinpath(filename)
                sftp_copy(sftp, remote_file, local_file)

        if sddb_file_downloaded:
            # automatically run the sddb parsing after downloading a new sddb file
            parse_sddb_file()

# check md5sum for ~/delivery/*.{vbf,sddb}
