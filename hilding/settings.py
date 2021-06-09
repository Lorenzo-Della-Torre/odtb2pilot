"""
Hilding settings module

usage example:

from hilding import get_settings
get_settings().rig.hostname

"""
import sys
import logging
import pprint
import importlib
from pathlib import Path
import yaml


log = logging.getLogger('settings')


def get_settings():
    """
    get the hilding settings

    this is the main way to access the settings
    """
    # pylint: disable=global-statement
    global _SETTINGS
    if _SETTINGS:
        return _SETTINGS
    return Settings()


def initialize_settings(rig, force=False):
    """ initialize the settings with a given rig """
    # pylint: disable=global-statement
    global _SETTINGS
    if _SETTINGS and not force:
        raise ReferenceError("The settings module has already been initialized")
    _SETTINGS = Settings(select_rig=rig)

_SETTINGS = None



class Settings:
    """ Hilding settings """
    def __init__(self, select_rig=None, settings_file_name="settings.yml"):
        self.selected_rig_dict = {}
        if settings_file_name:
            settings_file_name_path = self.get_settings_file_path(
                settings_file_name)
            with open(settings_file_name_path) as settings_file:
                self.read_settings_file(settings_file, select_rig)
        self.rig = Rig(self)

    def read_settings_file(self, settings_file, select_rig):
        """ read settings from file-like object """
        self.settings = yaml.safe_load(settings_file)
        if not 'default_rig' in self.settings:
            sys.exit(f"No default_rig in {settings_file.name}")
        if not 'rigs' in self.settings:
            sys.exit(f"No rigs configured in {settings_file.name}")
        rigs = self.settings['rigs']
        if not select_rig:
            if not self.default_rig:
                sys.exit(f"The default_rig has not been configured "
                         f"in {settings_file.name}")
            select_rig = self.default_rig
        if not select_rig in rigs:
            sys.exit(f"Could not find the requested rig {select_rig} "
                     f"in the rigs configuration")
        self.selected_rig_dict = rigs[select_rig]

    def get_settings_file_path(self, settings_file_name):
        """ get or create a new setting file from template """
        settings_file_path = self.hilding_root.joinpath(settings_file_name)
        if not settings_file_path.exists():
            log.info("No %s file found. Creating a new one...",
                     settings_file_name)
            with open(settings_file_path) as f:
                f.write(SETTINGS_YML_TEMPLATE)
        return settings_file_path

    @property
    def default_rig(self):
        """ settings default rig """
        return self.settings.get('default_rig')

    @property
    def rigs(self):
        """ settings default rig """
        return self.settings.get('rigs', {})

    @property
    def hilding_root(self):
        """ get the root directory of the hilding instance """
        return Path(__file__).parent.parent

    def __str__(self):
        return pprint.pformat(self.settings)


class Rig:
    """ hilding rig management """
    def __init__(self, settings):
        self.settings = settings

    @property
    def hostname(self):
        """ settings hostname """
        return self.settings.selected_rig_dict.get('hostname')

    @property
    def user(self):
        """ settings user """
        return self.settings.selected_rig_dict.get('user', 'pi')

    @property
    def platform(self):
        """ settings platform """
        return self.settings.selected_rig_dict.get('platform')

    @property
    def signal_broker_port(self):
        """ settings signal broker port number """
        return str(self.settings.selected_rig_dict.get('signal_broker_port', 50051))

    @property
    def default_signal_send(self):
        """ settings platform """
        platform_data = self.settings.settings.get(self.platform)
        return platform_data.get("default_signal_send")

    @property
    def default_signal_receive(self):
        """ settings platform """
        platform_data = self.settings.settings.get(self.platform)
        return platform_data.get("default_signal_receive")

    @property
    def rig_path(self):
        """ get the path to the default rig """
        rigs = self.settings.hilding_root.joinpath("rigs")
        return ensure_exists(rigs.joinpath(self.settings.default_rig))

    @property
    def vbf_path(self):
        """ get the path to the vbf dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("vbf"))

    @property
    def sddb_path(self):
        """ get the path to the sddb dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("sddb"))

    @property
    def dbc_path(self):
        """ get the path to the dbc dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("dbc"))

    @property
    def build_path(self):
        """ get the path to the build dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("build"))

    def get_sddb(self, content: str):
        """
        accessor method to get one of the generated sddb modules
        (e.g.  "dids", "dtcs", "services")
        """

        # needs caching

        sddb_file = self.build_path.joinpath(f"sddb_{content}.py")
        if not sddb_file.exists():
            raise ModuleNotFoundError(f"The {sddb_file} file does not exist")
        spec = importlib.util.spec_from_file_location("sddb", sddb_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def ensure_exists(path):
    """ create directory if it does not exists """
    path.mkdir(exist_ok=True)
    return path



SETTINGS_YML_TEMPLATE = b"""
default_rig: piX
rigs:
  - piX:
      hostname: art-piX.dhcp.nordic.volvocars.net
      user: pi #optional
      platform: spa2
      signal_broker_port: 50051 #optional
"""
