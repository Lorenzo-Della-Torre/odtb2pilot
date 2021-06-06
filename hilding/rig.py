# download vbf and sddb file to rigs/pX/vbf and /rigs/pX/sddb

# check md5sum for ~/delivery/*.{vbf,sddb}

from paramiko import SSHClient
from scp import SCPClient

from hilding.settings import Settings

settings = Settings()

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect(settings.hostname, username=settings.user)
scp = SCPClient(ssh.get_transport())

scp.get('~/delivery/*.vbf', settings.vbf_path, preserve_times=True)
scp.get('~/delivery/*.sddb', settings.sddb_path, preserve_times=True)
