"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

    project:  Hilding testenvironment using SignalBroker
    author:   fjansso8 (Fredrik Jansson)
    date:     2020-05-12
    version:  1.0

    author:   hweiler (Hans-Klaus Weiler)
    date:     2020-07-30
    version:  1.1
    changes:  YML parameter uses default dir, YML project default
              YML handles parameters in dict

    author:   hweiler (Hans-Klaus Weiler)
    date:     2020-08-05
    version:  1.2
    changes:  fixed issue when dict key not found

    Inspired by https://grpc.io/docs/tutorials/basic/python.html

    Copyright 2015 gRPC authors.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    The Python implementation of the gRPC route guide client.
"""

import os
import sys
import re
import logging
import inspect
import yaml # Not installed? pylint: disable=import-error

class SupportFileIO:
    """
        SupportFileIO
    """

    @classmethod
    def __argv_to_string(cls, argv):
        """Transforms a list of strings to a print friendly string
            If argv is already a string it will be returned as is.

            Example:
            argv = ({'name': 'Heartbeat', 'send': True, 'id': 'HvbmdpNmFrame'},)

            as input would generate
            ´name, send, id´

            as output
        Args:
            argv (str, list): argv that is input to extract_parameter_yml

        Returns:
            str: a printer friendly representation of argv
        """
        ret = "´"
        entries = argv[0]
        if not isinstance(entries, str):
            for entry in entries:
                ret += entry + ", "
            ret = ret[0:-2] #to remove the last ","
            ret += "´"
        else:
            ret = "´" + entries + "´"
        return ret

    @classmethod
    def extract_parameter_yml(cls, key, *argv):
        # pylint: disable=too-many-locals
        # pylint: disable=deprecated-method
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """
        Extract requested data from a parameter dictionary from yaml.
        There may be two dictionary for parameters:
        - a project specific default one
        - a file specific one
        If parameters exist in both, the file specific overrides the project specific
        """
        odtb_proj_param = os.environ.get('ODTBPROJPARAM')
        if odtb_proj_param is None:
            odtb_proj_param = '.'
        param_dir = 'parameters_yml'
        proj_default = "project_default.yml"
        #logging.debug("Number file of param: %s", len(sys.argv))
        #logging.debug("regexpr %s", r"\w+_(?P<reqprod>\d{3,})_\w+")
        #logging.debug("sys.argv[0]: %s", sys.argv[0])

        if len(sys.argv) > 1:
            f_name = sys.argv[1]
        else:
            # Import Parameters if REQPROD name matches
            # Remove path from filename

            #f_name_temp = re.split(r"(BSW_)", sys.argv[0])
            #logging.debug("SIO Split part1:  %s", f_name_temp)
            f_name_temp = (re.split(r"/", sys.argv[0]))[-1]
            logging.debug("SIO arg to split: %s", sys.argv[0])
            logging.debug("SIO split1 '/': %s", f_name_temp)
            f_name_temp = (re.split(r"\\", f_name_temp))[-1]
            logging.debug("SIO split2 '\\': %s", f_name_temp)

            f_name = re.split(r"(.py)", f_name_temp)[0] + '.yml'
            #logging.info("SIO Split part2:  %s", f_name_temp)
        if os.path.exists(odtb_proj_param):
            logging.debug("Path to project: %s", odtb_proj_param)
        logging.debug("Path exists: %s", os.path.exists(odtb_proj_param + '/' + param_dir))
        if os.path.exists(odtb_proj_param + '/' + param_dir):
            logging.debug("Path: %s", odtb_proj_param + '/' + param_dir)
        #logging.debug("Path         %s", odtb_proj_param + '/' + param_dir)
        #logging.debug("Project default: %s", odtb_proj_param + '/' param_dir + '/' + proj_default)
        logging.debug("Project default exists: %s",\
                      os.path.isfile(odtb_proj_param + '/' + param_dir + '/' + proj_default))
        if os.path.isfile(odtb_proj_param + '/' + param_dir + '/' + proj_default):
            logging.debug("Default: %s", (odtb_proj_param + '/' + param_dir + '/' + proj_default))
        logging.debug("File exists: %s",\
                      os.path.isfile(odtb_proj_param + '/' + param_dir + '/' + f_name))
        if os.path.isfile(odtb_proj_param + '/' + param_dir + '/' + f_name):
            logging.debug("Parameter file : %s", (odtb_proj_param + '/' + param_dir + '/' + f_name))

        #try to find matching files in catalog holding parameter files
        logging.debug("dir_file_default: %s",
                      odtb_proj_param + '/' + param_dir + '/' + proj_default)
        if os.path.exists(odtb_proj_param + '/' + param_dir)\
            and os.path.isfile(odtb_proj_param + '/' + param_dir + '/' + proj_default):
            dir_file_default = odtb_proj_param + '/' + param_dir + '/' + proj_default
        elif os.path.isfile(proj_default):
            dir_file_default = proj_default
        #no matching parameter file
        else: dir_file_default = ''

        if os.path.exists(odtb_proj_param + '/' + param_dir)\
            and os.path.isfile(odtb_proj_param + '/' + param_dir + '/' + f_name):
            dir_file = odtb_proj_param + '/' + param_dir + '/' + f_name
        elif os.path.isfile(f_name):
            dir_file = f_name
        #no matching parameter file
        else: dir_file = ''
        #logging.info("File dir_file         %s", dir_file)

        value = ''
        default_par_open = False
        file_par_open = False

        #wanted to have empty file check before try, pylint thinks prog gets to complicated
        #if dir_file != '':
        #    print("open dir_file: ", dir_file)
        try:
            # extract yaml data from directory
            with open(dir_file_default) as file:
                data_default = yaml.safe_load(file)
                default_par_open = True
        except IOError:
            #sys.exit(1)
            #sys.exit is to hard, skip reading parameter, don't exit python
            default_par_open = False

        try:
            #for entry in files:
            #    #entry_req = re.match(r"\w+_(?P<reqprod>\d{3,})\.\w+", entry)
            #    entry_req = re.match(pattern_req, entry)
            #    if entry_req.group('reqprod') == pattern_req.group('reqprod'):
            #        entry_good = entry

            # extract yaml data from directory
            with open(dir_file) as file:
                data = yaml.safe_load(file)
                file_par_open = True
        except IOError:
            #sys.exit(1)
            #sys.exit is to hard, skip reading parameter, don't exit python
            file_par_open = False
        if not (default_par_open or file_par_open):
            logging.info("Config file used for extracting %s: %s",
                cls.__argv_to_string(argv),
                dir_file + dir_file_default)
            return value

        #logging.debug("YML key", key)
        for arg in argv:
            #logging.debug("key: %s", key)
            #logging.debug("arg: %s", arg)

            #dict
            logging.debug("Dict to modify: %s", arg)
            if isinstance(arg, dict):
                for dict_key in arg:
                    logging.debug("search project parameter data for %s %s", key, dict_key)

                    #search in default parameters
                    if default_par_open and\
                        key in data_default and\
                        (data_default[key].get(dict_key) is not None):
                        #logging.debug("Default data for newarg %s",\
                        #              data_default[key].get(dict_key))
                        newarg = data_default[key].get(dict_key)
                        logging.debug("Default-par: New values for %s: %s",
                                      dict_key, newarg)
                        logging.debug("type before replace: %s", type(arg[dict_key]))
                        logging.debug("type after replace: %s", type(newarg))

                        if not isinstance(newarg, type(arg[dict_key])):
                            logging.debug("Try to get same type via EVAL:")
                            logging.debug("EVAL changes type: %s",
                                          type(eval(newarg))) # pylint: disable=eval-used
                            newarg = eval(newarg) # pylint: disable=eval-used

                        #arg[dict_key] = data_default[key].get(dict_key)
                        arg[dict_key] = newarg

                        #convert some values to bytes
                        if dict_key in ('mode', 'mask', 'did'):
                            logging.debug("type before convert: %s", arg[dict_key])
                            arg[dict_key] = bytes(arg[dict_key], 'utf-8')
                            logging.debug("type after convert type: %s", arg[dict_key])

                    #search in file specific parameters
                    logging.debug("search file parameter data for %s %s", key, dict_key)
                    if file_par_open and\
                        key in data and\
                        (data[key].get(dict_key) is not None):
                        newarg = data[key].get(dict_key)
                        logging.debug("File-par: Old values in dict %s = %s",
                                      dict_key, arg[dict_key])
                        logging.debug("File-par: New values in dict %s = %s",
                                      dict_key, newarg)
                        logging.debug("type arg before: %s", type(arg[dict_key]))
                        logging.debug("type arg read: %s", type(newarg))
                        if not isinstance(newarg, type(arg[dict_key])):
                            logging.debug("Try to get same type via EVAL:")
                            logging.debug("EVAL changes type: %s",
                                          type(eval(newarg))) # pylint: disable=eval-used
                            newarg = eval(newarg) # pylint: disable=eval-used
                        #logging.debug("type arg after:  %s", type(newarg))
                        arg[dict_key] = newarg
                        #convert some values to bytes
                        if dict_key in ('mode', 'mask', 'did'):
                            arg[dict_key] = bytes(arg[dict_key], 'utf-8')
                value = arg
            #simple types, normal variables
            ### doesn't work for 'simple' types because of scope
            ### use return value
            elif default_par_open and\
                key in data_default and\
                (data_default[key].get(arg) is not None):
                #logging.debug("Sent new value for %s arg: %s value: %s", key,\
                #      arg, data_default[key].get(arg))
                value = data_default[key].get(arg)
                #logging.debug("New values variable %s",  data[key].get(arg))
                logging.debug("new value variable: %s", value)
            elif file_par_open and\
                key in data and\
                (data[key].get(arg) is not None):
                #logging.debug("Sent new value for %s arg: %s value: %s", key,\
                #      arg, data[key].get(arg))
                value = data[key].get(arg)
                logging.debug("new value variable: %s", value)
        logging.info("Config file used for extracting %s: %s",
            cls.__argv_to_string(argv),
            dir_file + dir_file_default)
        return value



    @classmethod
    def parameter_adopt_teststep(cls, dict_name):
        """
            parameter_adopt_teststep
            allows you to change variable values in a specific teststep

            parameters:
            inspect.stack()[1][3]   contains name of calling function
            dict_name               dict which values should be replaced
        """
        return cls.extract_parameter_yml(str(inspect.stack()[1][3]), dict_name)
