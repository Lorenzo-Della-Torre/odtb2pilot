""" project:  ODTB2 testenvironment using SignalBroker
    author:   fjansso8 (Fredrik Jansson)
    date:     2020-05-12
    version:  1.0

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
import yaml # Not installed? pylint: disable=import-error


class SupportFileIO:
    # Disable the too-few-public-methods violation. I'm sure we will have more methods later.
    # pylint: disable=too-few-public-methods
    """
        SupportFileIO
    """


    @classmethod
    def extract_parameter_yml(cls, key, *argv):
        """
        Extract requested data from a Parameter dictionary from yaml.
        """
        param_dir = './parameters_yml'
        #logging.debug("Number file of param: %s", len(sys.argv))
        #logging.debug("regexpr %s", r"\w+_(?P<reqprod>\d{3,})_\w+")
        #logging.debug("sys.argv[0]: %s", sys.argv[0])

        #logging.debug("re.match: %s %s", re.match(r"\w+_(?P<reqprod>\d{3,})_\w+", sys.argv[0]))
        #logging.debug("re.split: %s", re.split(r"(.py)", sys.argv[0])[0] + '.yml')

        if len(sys.argv) > 1:
            f_name = sys.argv[1]
        else:
            # Import Parameters if REQPROD name matches
            # Remove path from filename
            f_name_temp = re.split(r"(BSW_)", sys.argv[0])
            #logging.debug("new f_name: %s", f_name_temp)
            #logging.debug("new arg to split: %s%s", f_name_temp[1], f_name_temp[2])
            f_name = re.split(r"(.py)", f_name_temp[1]+f_name_temp[2])[0] + '.yml'
        #logging.debug("Parameter file: %s", f_name)
        logging.info("Path exists: %s", os.path.exists(param_dir))
        #logging.debug("Path         %s", param_dir)
        logging.info("File exists: %s", os.path.isfile(param_dir + '/' + f_name))
        #logging.info("File         %s", param_dir + '/' + f_name)
        #try to find matching files in catalog holding parameter files
        if os.path.exists(param_dir) and os.path.isfile(param_dir + '/' + f_name):
            dir_file = param_dir + '/' + f_name
        elif os.path.isfile(f_name):
            dir_file = f_name
        #no matching parameter file
        else: dir_file = ''

        # intitialize a tuple
        #value = dict()
        value = ''

        #wanted to have empty file check before try, pylint thinks prog gets to complicated
        #if dir_file != '':
        #    print("open dir_file: ", dir_file)
        try:
            #for entry in files:
            #    #entry_req = re.match(r"\w+_(?P<reqprod>\d{3,})\.\w+", entry)
            #    entry_req = re.match(pattern_req, entry)
            #    if entry_req.group('reqprod') == pattern_req.group('reqprod'):
            #        entry_good = entry

            # extract yaml data from directory
            with open(dir_file) as file:
                data = yaml.safe_load(file)
        except IOError:
            logging.info("Could not open parameter file for testscript\n")
            logging.info("Parameter path: %s", param_dir)
            logging.info("Parameter file: %s", f_name)
            #logging.debug("The pattern {:} is not present in the directory\n"\
            #    .format(pattern_req.group('reqprod')))
            #sys.exit(1)
            #sys.exit is to hard, skip reading parameter, don't exit python
            return value
        #logging.debug("YML key", key)
        for arg in argv:
            #logging.debug("key: %s", key)
            #logging.debug("arg: %s", arg)

            #dict
            if isinstance(arg, dict):
                for dict_key in arg:
                    logging.debug("search data for %s", dict_key)
                    if data[key].get(dict_key) is not None:
                        #logging.debug("New values in dict %s",  data[key].get(dict_key))
                        #logging.debug("used dict_key: %s", dict_key)
                        arg[dict_key] = data[key].get(dict_key)
                        #convert some values to bytes
                        if dict_key in ('mode', 'mask', 'did'):
                            arg[dict_key] = bytes(arg[dict_key], 'utf-8')
                value = arg
            #simple types, normal variables
            ### doesn't work for 'simple' types because of scope
            ### use return value
            elif data[key].get(arg) is not None:
                #logging.debug("Sent new value for %s arg: %s value: %s", key,\
                #      arg, data[key].get(arg))
                value = data[key].get(arg)
                #logging.debug("New values variable %s",  data[key].get(arg))
                logging.debug("new value variable: %s", value)
        return value
