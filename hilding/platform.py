"""
this module provides an interface to the relevant platform directories

use these access functions instead of directly using the environment variables
as we want to gradually move away from that way of working in favor of defining
all in a single settings.yml for all rigs with their respective platforms
"""
import os
import re
import sys
from pathlib import Path
import yaml

def get_platform():
    """ get the currently activated platform """
    platform = os.getenv("ODTBPROJ")
    if not platform:
        raise EnvironmentError("ODTBPROJ is not set")

    match = re.search(r'MEP2_(.+)$', platform)
    if not match:
        raise EnvironmentError(
            "Unknown ODTBPROJ encountered. "
            "get_platform() might need to get updated")

    return match.groups()[0].lower()


def get_platform_dir():
    """Get the selected platform directory (spa1 or spa2)"""
    platform_dir = os.getenv('ODTBPROJPARAM')
    if not platform_dir:
        sys.exit("You need to set the ODTBPROJPARAM. Exiting...")
    return platform_dir


def get_release_dir():
    """Get the release dir for the current platform"""
    dbpath = Path(get_platform_dir()).joinpath('release')
    if not dbpath.exists():
        sys.exit(f"{dbpath} directory is missing. Exiting...")
    return dbpath


def get_build_dir():
    """
    Get the path of the build where we will store the python data structures
    extracted from the sddb xml file
    """
    build_dir = Path(get_platform_dir()).joinpath('build')
    if not build_dir.exists():
        sys.exit(f"{build_dir} directory is missing. Existing...")
    return build_dir


def get_parameters(custom_yml_file=None):
    """
    Get the basic platform parameters from the project_default.yml file for the
    platform
    """
    platform_dir = get_platform_dir()
    parameters_yml_dir = Path(platform_dir).joinpath('parameters_yml')
    project_default = Path(parameters_yml_dir).joinpath("project_default.yml")
    with open(project_default, "r") as f:
        parameters = yaml.safe_load(f)

    if custom_yml_file:
        custom_file = Path(parameters_yml_dir).joinpath(custom_yml_file)
        if not custom_file.exists():
            # raise exception with explicit error message
            raise FileNotFoundError(f"Could not find custom_yml_file in {custom_file}")
        with open(custom_file, "r") as f:
            custom_config = yaml.safe_load(f)
        parameters.update(custom_config)

    return parameters
