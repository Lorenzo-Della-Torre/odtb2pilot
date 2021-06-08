"""
Rig handling routines
"""
import sys
import logging
from pathlib import Path

from paramiko import SSHClient

from hilding.settings import initialize_settings
from hilding import get_settings


log = logging.getLogger('rig')

def handle_rigs(args):
    """ rig management command handler """
    settings = get_settings()
    if args.list:
        print(settings)
    if args.update:
        get_rig_delivery_files()
    if args.update_all:
        for rig in settings.rigs.keys():
            initialize_settings(rig, force=True)
            get_rig_delivery_files()


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
    settings = get_settings()
    user = settings.rig.user
    hostname = settings.rig.hostname
    log.info("Connecting to: %s@%s", user, hostname)
    ssh.connect(hostname, username=user)
    sftp = ssh.open_sftp()
    remote_delivery_path = Path('/home/pi/delivery')
    delivery_files = sftp.listdir(remote_delivery_path.as_posix())
    log.info("Copy remote %s/*.{vbf,sddb,dbc} files to this host",
             remote_delivery_path)

    for filename in delivery_files:
        remote_file = remote_delivery_path.joinpath(filename)
        if filename.endswith('.vbf'):
            local_file = settings.rig.vbf_path.joinpath(filename)
            sftp_copy(sftp, remote_file, local_file)
        if filename.endswith('.sddb'):
            local_file = settings.rig.sddb_path.joinpath(filename)
            sftp_copy(sftp, remote_file, local_file)
        if filename.endswith('.dbc'):
            local_file = settings.rig.dbc_path.joinpath(filename)
            sftp_copy(sftp, remote_file, local_file)

# check md5sum for ~/delivery/*.{vbf,sddb}
