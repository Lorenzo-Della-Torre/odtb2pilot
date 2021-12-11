"""
Interface to configuration files.

The config parser read several different configuration files. The later files
will override values from the earlier ones.

This is the suggested setup:

    epshil/framework/etc/default.cfg   [Should contain reasonable defaults (for HIL)]
    epshil/framework/etc/*             [Various settings]
    c:\HIL.cfg                         [Override settings for particular HIL]

Iterations:
    cfg = config('git')                                    # Settings from ...\etc\git.cfg + HIL.cfg
    for section in cfg:                                    # Iterate sections
        print(section.name)
        for option in section:                             # Iterate options
            print(option.name, 'value is', option.value)

For section names or option names with spaces:
    [blinker]                                              # Contents of blinker.cfg
    ...                                                    #
    monitor port = 5557                                    # Option with spaces

    Code sample
    -----------
    cfg = config('blinker')                                # Read from ...\etc\blinker.cfg + HIL.cfg
    portnum = cfg.blinker.monitor_port                     # Coerced to integer

    # alternatively
    portnum = config('blinker')['blinker']['monitor port']

Sections and options are accessible as lowercase:
    cfg = config('HIL')
    print(cfg.hil.ipaddress)

If default ConfigParser behaviour is wanted:
    c = configparser.ConfigParser()
    c.read(locations('blinker'))                           # locations(<name>) will return list of config files
"""

import configparser as cpm
import os
import logging
import logging.config
import re


log = logging.getLogger('epsconfig')


#
# NOTE: Paths are relative to the location of THIS file.
#
ROOT = os.path.dirname(__file__)
WORKSTATION_CONFIG = os.path.join('c:\\', 'HIL.cfg')
CONFIG_DIRECTORIES = [
    os.path.abspath(ROOT),
    os.path.abspath(os.path.join(ROOT, '..', '..', 'etc')),  # c:\epshil\framework\etc
    os.path.join(os.path.expanduser('~'), '.epsconfig')
]


class Config(object):
    """
    Wrapper around ConfigParser that makes it possible
    to iterate and access sections and options of sections
    as attributes (or items).
    """
    def __init__(self, config, name, files):
        """
        'config' is a ConfigParser, 
        'name is a symbolic name,
        'files' is a list of file names that were read.
        """
        self.config = config
        self.name = name
        self.files = files

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.name, self.files)

    def __str__(self):
        return self.name

    def is_valid(self):
        """Return True if any INI files were read."""
        return len(self.files) > 0

    def __iter__(self):
        """Return Section object for each iteration."""
        for s in self.config.sections():
            yield Section(self.config, s)

    def __getattr__(self, section):
        """Return Section object that matches the argument. Names are mangled
        to allow for attribute access."""
        for s in self.config.sections():
            if section.lower() == mangle(s):
                return Section(self.config, s)
        return NullSection(section)

    def __getitem__(self, section):
        """Return Section object that matches the argument. Item access will
        not change case."""
        for s in self.config.sections():
            if mangle(section) == mangle(s):
                return Section(self.config, s)
        return NullSection(section)


class Section(object):
    """Add attribute and item access as well as the iteration protocol."""
    def __init__(self, config, section):
        """The argument 'config' is a ConfigParser, 'section' is the name of a
        section."""
        self.config = config
        self.section = section

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.section)

    def __str__(self):
        return self.name

    @property
    def name(self):
        """Return the name of the section."""
        return self.section

    def get_value(self, option):
        """Return option value. Try to return booleans for
        yes/no/true/false/...  and try to return numeric values for strings
        that (probably) are numbers."""
        try:
            return self.config.getboolean(self.section, option)
        except ValueError:
            try:
                value = self.config.getfloat(self.section, option)
                if '.' in self.config.get(self.section, option):
                    return value
                else:
                    return self.config.getint(self.section, option)
            except ValueError:
                return self.config.get(self.section, option)

    def __iter__(self):
        """Return Option object for each iteration."""
        for option in self.config.options(self.section):
            yield Option(self.config, self.section, option, self.get_value(option))

    def __getattr__(self, option):
        """Return option that matches the mangled value."""
        for opt in self.config.options(self.section):
            if option.lower() == mangle(opt):
                return self.get_value(opt)
        return None

    def __getitem__(self, option):
        """Return option, for item access the correct case must be given."""
        for opt in self.config.options(self.section):
            if mangle(option) == mangle(opt):
                return self.get_value(opt)


class NullSection(object):
    """Dummy object that will return the value 'None'."""
    def __init__(self, section):
        self.section = section
        log.debug("Section '%s' not found.", section)

    def __getattr__(self, value):
        log.debug("Option '%s' not found in section '%s'.", value, self.section)

    __getitem__ = __getattr__


class Option(object):
    """Add attribute and item access as well as the iteration protocol."""
    def __init__(self, config, section, option, value):
        """'config' is a ConfigParser object, 'section' is the section name and
        'option' is the option name. The value is the value as read from the
        configuration files."""
        self.config = config
        self.section = section
        self.option = option
        self.value = value

    def __repr__(self):
        return '{}({}, {})={}'.format(self.__class__.__name__, self.section,
                self.option, self.value)

    def __str__(self):
        return self.option

    @property
    def name(self):
        return self.option


def config(name, inifiles=None):
    """Return a 'Config' option from 'name' which is a configuration file
    without file extension. The 'locations()' function will make sure that the
    file is found in the standard places."""
    files = []
    c = cpm.ConfigParser()
    files.extend(c.read(locations(name)) if inifiles is None else inifiles)
    log.debug("Using these configuration files: %s."  % str(files))
    return Config(c, name, files)


def mangle(s):
    """Mangle aattribute names to allow for Python attribute access (replace
    all whitepace with '_' (underscore)."""
    return re.sub('\s+', '_', s.lower())


def locations(name):
    """Return list of absolute path names to configuratino files that match
    'name'."""
    L = []
    for c in CONFIG_DIRECTORIES:
        L.append(os.path.join(c, f'{name}.cfg'))
        L.append(os.path.join(c, f'{name}.ini'))
    L.append(WORKSTATION_CONFIG)
    return L

# eof
