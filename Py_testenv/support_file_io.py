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
    def extract_parameter_yml(cls, *argv, **kwargs):
        """
        Extract requested data from a Parameter dictionary from yaml.
        """
        # Import Parameters if REQPROD name are compatible
        #pattern_req = re.match(r"\w+_(?P<reqprod>\d{3,})\.\w+", sys.argv[0])
        FILE_NAME_IDX = 0
        pattern_req = re.search(r'(?<=BSW_)\w+', sys.argv[FILE_NAME_IDX])
        files = os.listdir('./parameters_yml')
        # intitialize a tuple
        value = dict()
        try:
            for entry in files:
                #entry_req = re.match(r"\w+_(?P<reqprod>\d{3,})\.\w+", entry)
                entry_req = re.search(r'(?<=^)\w+', entry)
                #if entry_req.group('reqprod') == pattern_req.group('reqprod'):
                if entry_req.group(0) == pattern_req.group(0):
                    entry_good = entry
            # extract yaml data from directory
            with open('./parameters_yml/' + entry_good) as file:
                data = yaml.safe_load(file)
        except IOError:
            print("The pattern {} is not present in the directory\n"\
                  .format(pattern_req.group('reqprod')))
            sys.exit(1)
        for key, arg in kwargs.items():
            # if yaml key return value from yaml file
            if data[str(argv[FILE_NAME_IDX])].get(key) is not None:
                value[key] = data[str(argv[FILE_NAME_IDX])].get(key)
                #convert some values to bytes
                if key in ('mode', 'mask', 'did'):
                    value[key] = bytes(value[key], 'utf-8')
            else:
                value[key] = arg
        return value
