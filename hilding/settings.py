"""
Hilding settings module
"""
import sys
import logging
import pprint
import yaml

log = logging.getLogger('settings')

class Settings:
    """ Hilding settings """
    def __init__(self, settings_file_name="settings.yml"):
        if settings_file_name:
            with open(settings_file_name) as settings_file:
                self.read_settings_file(settings_file)
        self.settings_file_name = settings_file_name
        self.selected_rig = None

    def read_settings_file(self, settings_file):
        """ read settings from file like object """
        self.settings = yaml.safe_load(settings_file)
        if not 'default_rig' in self.settings:
            sys.exit(f"No default_rig in {self.settings_file_name}")
        default_rig = self.settings['default_rig']
        if not 'rigs' in self.settings:
            sys.exit(f"No rigs configured in {self.settings_file_name}")
        rigs = self.settings['rigs']
        for rig in rigs:
            if default_rig in rig:
                self.selected_rig = rig[default_rig]
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

    def __str__(self):
        return pprint.pformat(self.settings)
