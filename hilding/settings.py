"""
Hilding settings module
"""
import sys
import logging
import pprint
import yaml

from hilding.platform import get_hilding_root

log = logging.getLogger('settings')


class Settings:
    """ Hilding settings """
    def __init__(self, settings_file_name="settings.yml"):
        self.selected_rig = {}
        self.settings_file_name = settings_file_name
        if self.settings_file_name:
            with open(self.settings_file_name) as settings_file:
                self.read_settings_file(settings_file)

    def read_settings_file(self, settings_file):
        """ read settings from file like object """
        self.settings = yaml.safe_load(settings_file)
        if not 'default_rig' in self.settings:
            sys.exit(f"No default_rig in {self.settings_file_name}")
        self.default_rig = self.settings['default_rig']
        if not 'rigs' in self.settings:
            sys.exit(f"No rigs configured in {self.settings_file_name}")
        rigs = self.settings['rigs']
        for rig in rigs:
            if self.default_rig in rig:
                self.selected_rig = rig[self.default_rig]
        if not self.selected_rig:
            sys.exit(f"The default_rig has not been configured "
                     f"in {self.settings_file_name}")

    @property
    def hostname(self):
        """ settings hostname """
        return self.selected_rig.get('hostname')

    @property
    def signal_broker_port(self):
        """ settings signal broker port number """
        return self.selected_rig.get('signal_broker_port')

    @property
    def user(self):
        """ settings user """
        return self.selected_rig.get('user')

    def __str__(self):
        return pprint.pformat(self.settings)

    @property
    def rig_path(self):
        root = get_hilding_root()
        return root.joinpath("rigs").joinpath(self.default_rig)

    @property
    def vbf_path(self):
        return self.rig_path.joinpath("vbf")

    @property
    def sddb_path(self):
        return self.rig_path.joinpath("sddb")

    def create_settings_yml(self):
        root = get_hilding_root()
        settings_yml = root.joinpath("settings.yml")
        if not settings_yml.exists():
            log.info("No settings.yml file found. Creating a new one...")
            with open(settings_yml) as f:
                f.write(SETTINGS_YML_TEMPLATE)

SETTINGS_YML_TEMPLATE = b"""
default_rig: pX
rigs:
  - pX:
      hostname: bsw-pX.dhcp.nordic.volvocars.net
      user: pi #optional
      platform: spa2
      signal_broker_port: 50051 #optional
"""
