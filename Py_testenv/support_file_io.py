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
        #print("Number file of param: ", len(sys.argv))
        #print("regexpr ", r"\w+_(?P<reqprod>\d{3,})_\w+")
        #print("sys.argv[0]: ", sys.argv[0])

        #print("re.match: ", re.match(r"\w+_(?P<reqprod>\d{3,})_\w+", sys.argv[0]))
        #print("re.split: ", re.split(r"(.py)", sys.argv[0])[0] + '.yml')

        if len(sys.argv) > 1:
            f_name = sys.argv[1]
        else:
            # Import Parameters if REQPROD name matches
            #pattern_req = re.match(r"\w+_(?P<reqprod>\d{3,})_\w+", sys.argv[0])
            f_name = re.split(r"(.py)", sys.argv[0])[0] + '.yml'
        #print("Parameter file: ", f_name)
        print("Path exists: ", os.path.exists(param_dir))
        #print("Path         ", param_dir)
        print("File exists: ", os.path.isfile(param_dir + '/' + f_name))
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
            print("Could not open parameter file for testscript\n")
            #print("The pattern {} is not present in the directory\n"\
            #    .format(pattern_req.group('reqprod')))
            sys.exit(1)
        #print("YML key", key)
        for arg in argv:
            #print("key: ", key)
            #print("arg: ", arg)

            #dict
            if isinstance(arg, dict):
                for dict_key in arg:
                    print("search data for ", dict_key)
                    if data[key].get(dict_key) is not None:
                        #print("New values in dict",  data[key].get(dict_key))
                        #print("used dict_key: ", dict_key)
                        arg[dict_key] = data[key].get(dict_key)
                        #convert some values to bytes
                        if dict_key in ('mode', 'mask', 'did'):
                            arg[dict_key] = bytes(arg[dict_key], 'utf-8')
                value = arg
            #simple types, normal variables
            ### doesn't work for 'simple' types because of scope
            ### use return value
            elif data[key].get(arg) is not None:
                #print("Sent new value for ", key, "arg: ",\
                #      arg, "value: ", data[key].get(arg))
                value = data[key].get(arg)
                #print("New values variable",  data[key].get(arg))
                print("new value variable: ", value)
        return value
