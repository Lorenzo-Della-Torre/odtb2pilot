"""
Hilding conf module

usage example:
> from hilding import get_conf
> get_conf().rig.hostname

in tests you could use:
> dut.conf.rig.hostname


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
    _CONF = Conf(selected_rig=rig)
    return _CONF

_CONF = None


class Conf:
    """ Hilding configuration """
    def __init__(self, selected_rig=None):
        self.__conf = self.get_default_conf()
        self.__selected_rig = selected_rig
        self.selected_rig_dict = {}
        self.add_local_conf()
        self.rig = Rig(self)

    def get_default_conf(self):
        """ returns a dictionary with the default conf """
        conf_default_yml = self.hilding_root.joinpath("conf_default.yml")
        with open(conf_default_yml) as conf_default_file:
            conf_default = yaml.safe_load(conf_default_file)
        return conf_default

    def add_local_conf(self):
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
            if not self.selected_rig in rigs:
                sys.exit(f"Could not find the requested rig {self.selected_rig} "
                         f"in the rigs configuration")
            self.selected_rig_dict = rigs[self.selected_rig]

    @property
    def default_rig(self):
        """ conf default rig """
        return self.__conf.get('default_rig')

    @property
    def default_platform(self):
        """ conf default platform (the default rigs platform type) """
        return self.rigs.get(self.default_rig).get('platform')

    @property
    def selected_rig(self):
        """ conf selected rig """
        return self.__selected_rig or self.default_rig

    @property
    def rigs(self):
        """ conf rigs """
        return self.__conf.get('rigs', {})

    @property
    def platforms(self):
        """ conf platforms """
        return self.__conf.get('platforms', {})

    @property
    def hilding_root(self):
        """ get the root directory of the hilding instance """
        return Path(__file__).parent.parent

    @property
    def default_rig_config(self):
        """ get conf for default rig """
        return self.platforms.get(self.default_platform)

    def __str__(self):
        return pprint.pformat(self.__conf)



CONF_LOCAL_YML_TEMPLATE = \
"""# note: conf_local.yml should never be committed to the repo
default_rig: piX
rigs:
    piX:
        hostname: bsw-piX.dhcp.nordic.volvocars.net
        user: pi #optional
        platform: hvbm_p519_sa1
        signal_broker_port: 50051 #optional
        relay_connected : None
"""
