"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
this module provides an interface to the relevant platform directories

use these access functions instead of directly using the environment variables
as we want to gradually move away from that way of working in favor of defining
all in a single conf.yml for all rigs with their respective platforms
"""
import os
import sys
from pathlib import Path
import yaml


def get_platform_dir():
    """Get the selected platform directory (spa1 or spa2)"""
    platform_dir = os.getenv('ODTBPROJPARAM')
    if not platform_dir:
        sys.exit("You need to set the ODTBPROJPARAM. Exiting...")
    return platform_dir


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
