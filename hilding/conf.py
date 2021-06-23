"""
Hilding conf module

usage example:
> from hilding import get_conf
> get_conf().rig.hostname

in tests you could use:
> dut.conf.rig.hostname

"""
import sys
import logging
import pprint
from pathlib import Path
import yaml

from hilding.conf_rig import Rig

log = logging.getLogger('conf')

def get_conf():
    """ get the hilding conf """
    # pylint: disable=global-statement
    global _CONF
    if _CONF:
        return _CONF
    return Conf()


def initialize_conf(rig, force=False):
    """
    initialize the conf with a given rig

    reinitialize of the force parameter is True

    note: you will have to run another conf = get_conf() for any existing
    instances of conf or use the return value from this function
    """
    # pylint: disable=global-statement
    global _CONF
    if _CONF and not force:
        raise ReferenceError("The conf module has already been initialized")
    _CONF = Conf(select_rig=rig)
    return _CONF

_CONF = None


class Conf:
    """ Hilding configuration """
    def __init__(self, select_rig=None):
        self.__conf = self.get_default_conf()
        self.selected_rig_dict = {}
        self.add_local_conf(select_rig)
        self.rig = Rig(self)

    def get_default_conf(self):
        """ returns a dictionary with the default conf """
        conf_default_yml = self.hilding_root.joinpath("conf_default.yml")
        with open(conf_default_yml) as conf_default_file:
            conf_default = yaml.safe_load(conf_default_file)
        return conf_default

    def add_local_conf(self, select_rig):
        """ add conf_local.yml values over conf_default.yml settings """
        conf_local_yml = self.hilding_root.joinpath("conf_local.yml")
        if not conf_local_yml.exists():
            log.info("No %s file found. Creating a new one...", conf_local_yml)
            with open(conf_local_yml, "w") as f:
                f.write(CONF_LOCAL_YML_TEMPLATE)

        with open(conf_local_yml) as conf_local_file:
            self.__conf.update(yaml.safe_load(conf_local_file))
            if not 'default_rig' in self.__conf:
                sys.exit(f"No default_rig in {conf_local_file.name}")
            if not 'rigs' in self.__conf:
                sys.exit(f"No rigs configured in {conf_local_file.name}")
            rigs = self.__conf['rigs']
            if not select_rig:
                if not self.default_rig:
                    sys.exit(f"The default_rig has not been configured "
                             f"in {conf_local_file.name}")
                select_rig = self.default_rig
            if not select_rig in rigs:
                sys.exit(f"Could not find the requested rig {select_rig} "
                         f"in the rigs configuration")
            self.selected_rig_dict = rigs[select_rig]

    @property
    def default_rig(self):
        """ conf default rig """
        return self.__conf.get('default_rig')

    @property
    def rigs(self):
        """ conf default rig """
        return self.__conf.get('rigs', {})

    @property
    def platforms(self):
        """ conf default rig """
        return self.__conf.get('platforms', {})

    @property
    def hilding_root(self):
        """ get the root directory of the hilding instance """
        return Path(__file__).parent.parent

    def __str__(self):
        return pprint.pformat(self.__conf)



CONF_LOCAL_YML_TEMPLATE = \
"""# note: conf_local.yml should never be committed to the repo
default_rig: piX
rigs:
    piX:
        hostname: bsw-piX.dhcp.nordic.volvocars.net
        user: pi #optional
        platform: hvbm
        signal_broker_port: 50051 #optional
"""
