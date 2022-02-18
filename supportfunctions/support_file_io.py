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
import logging
import inspect
from ast import literal_eval
import yaml

from hilding.conf import Conf

from hilding.predefined_variables import project_default_to_conf_default

dut_configuration = Conf()

def _find_yml_file(directory, file_names):
    """Try to find a yml file matching list of files

    Args:
        dir (str): Root of where the function should look
        file_names (list): List of python files the function should try to match
        with a test specific yml

    Returns:
        str: A path to test specific yml alt. empty string if none was found
    """
    walker = os.walk(directory)

    for root, _, files in walker:
        for file_name in file_names:
            if f"{file_name}.yml" in files:
                return os.path.join(root, f"{file_name}.yml")

    return ""

def _convert_type(var_with_required_type, variable):
    """A funky little function that makes sure we return values with the correct type.
    If we try to replace a value with info from an yml we will make sure it is the same
    type as the original data.

    If the types are different we try to make it into the correct type.

    Args:
        var_with_required_type (any): A arbitrary variable. The type of this
        variable will be the one we want for "variable" as well
        variable (any): We will make sure variable is the same type as
        "var_with_required_type"

    Returns:
        any: "variable" that is of the same type as "var_with_required_type"
    """
    required_type = type(var_with_required_type)
    if not isinstance(variable, required_type):
        try:
            variable_correct_type = literal_eval(variable)
        except ValueError:
            logging.error("Could not convert %s (%s) to %s. Returned type is not the same as "
            "original type!!", variable, type(variable), required_type)
            return variable
        return variable_correct_type
    return variable

def _find_value_in_testspecific_yml(caller, dictionary_to_modify, changed_keys):
    """Try to replace values in input with values from test specific yml

    Args:
        caller (str): Name of step in which values should be replaced. I.e: "run", "step_1"
        input_dictionary (dict, str): A dictionary in which values should be updated,
        might also be string
        changed_keys (list): List containing keys to all values that were updated.

    Returns:
        dict: A dictionary with updated values, or of no values were updated,
        "input_dictionary" will be returned
        list: List containing keys to all values that were updated.
    """
    def __extract_from_subdict(sub_dict):
        """Exchange all values in "dictionary_to_modify" found in
        "sub_dict"

        Args:
            sub_dict (dict): Dictionary is which new values might be found

        Returns:
            boolean: Boolean that indicates if any values where exchanged
        """
        if isinstance(sub_dict, dict):
            for key in dictionary_to_modify:
                value = sub_dict.get(key)

                # The keys in the old yml-files (now removed) sometimes missmatches with
                # the keys in the new ones.
                # Therefore we swap any old keys for the corresponding new key if old key
                # is not found
                if value is None:
                    swapped_key = project_default_to_conf_default.get(key)
                    value = sub_dict.get(swapped_key)

                if value is not None:
                    value_correct_type = _convert_type(dictionary_to_modify[key], value)
                    dictionary_to_modify[key] = value_correct_type
                    changed_keys.append(key)
                    logging.info("Value of ´%s´ changed to ´%s´ found in %s",
                                                                key,
                                                                value_correct_type,
                                                                path_to_test_specific_yml)
        if changed_keys:
            return True
        return False

    file_names_in_callstack = []
    for level in inspect.stack():
        path_to_file = level[1]
        name_of_file = os.path.basename(path_to_file).split(".")[0]
        file_names_in_callstack.append(name_of_file)

    path_to_test_specific_yml = _find_yml_file("test_folder", file_names_in_callstack)

    if path_to_test_specific_yml:

        with open(path_to_test_specific_yml) as yml_file:
            yml_dictionary = yaml.safe_load(yml_file)

        platform = dut_configuration.default_platform
        platform_specific_yml_dict = yml_dictionary.get(platform)

        if platform_specific_yml_dict is not None:
            # If any step or no step at all is okay
            if caller == "*":
                data_modified = __extract_from_subdict(platform_specific_yml_dict)
                if not data_modified:
                    for sub_dict in platform_specific_yml_dict.values():
                        __extract_from_subdict(sub_dict)
            else:
                # Make sure the step is found in the yml i.e: "run", "step_1"
                sub_dict = platform_specific_yml_dict.get(caller)
                __extract_from_subdict(sub_dict)

    return dictionary_to_modify, changed_keys

class SupportFileIO:
    """
        SupportFileIO
    """
    @classmethod
    def _extract_parameters_from_yml(cls, caller, requested_data):
        """Function that tries to update all keys in "input_dictionary" with values
        found in either a test specific yml or conf_default.

        To be backwards compatible "requested_data" might also be a string.
        In that case whatever data is found in a yml with key "requested_data"
        will be returned.

        If any value of caller is okay, use caller="*". This will return the value(s) of
        requested_data that was first found (if found at all). The step could also be skipped
        all together i.e yml could look like this:

        <platform>:
            requested_data:

        note: This function makes sure we return values with the correct type.
        If we try to replace a value with info from an yml we will make sure it is the same
        type as the original data.

        If the types are different we try to make it into the correct type. If this fails
        it might cause a crash.

        Args:
            caller (str): Name of step in which values should be replaced. I.e: "run", "step_1"
            requested_data (dict, str): A dictionary in which values should be updated,
            might also be string - see description above

        Returns:
            dict/any: A dictionary with updated values, or if no values were updated,
            "input_dictionary" will be returned. If "requested_data" is a string
            the data found with key "requested_data" in a yml file will be returned as is.

            list: List containing keys to all values that were updated.
        """

        requested_data_dict = {}
        return_should_be_dict = True

        # Used to make sure that values already changed using test specific yml
        # are not changed again using conf_default
        changed_keys = []

        if not isinstance(requested_data, dict):
            requested_data_dict[requested_data] = ""
            return_should_be_dict = False

        else:
            requested_data_dict = requested_data

        # First we try to find the content of the dictionary in the test specific yml file
        dictionary_to_modify, changed_keys = _find_value_in_testspecific_yml(caller,
                                                                            requested_data_dict,
                                                                            changed_keys)

        # If value was not found in the test specific we try conf_default instead
        default_conf = dut_configuration.default_rig_config

        for key in dictionary_to_modify:
            value = default_conf.get(key)

            # The keys in the old "project_default" (now removed) sometimes missmatches with
            # the keys in conf_default.
            # Therefore we swap any old keys for the corresponding new key if old key is not found
            if value is None:
                swapped_key = project_default_to_conf_default.get(key)
                value = default_conf.get(swapped_key)

            if value is not None and key not in changed_keys:
                value_correct_type = _convert_type(dictionary_to_modify[key], value)
                dictionary_to_modify[key] = value_correct_type
                changed_keys.append(key)
                logging.info("Value of ´%s´ changed to ´%s´ found in conf_default",
                                                                            key,
                                                                            value_correct_type)

        # If input was not a dictionary but a string
        if not return_should_be_dict:
            for key, value in dictionary_to_modify.items():
                return value, changed_keys

        return dictionary_to_modify, changed_keys

    @classmethod
    def extract_parameter_yml(cls, step, *argv):
        """
        If any value of step is okay, use step="*". This will return the value(s) of
        argv that was first found (if found at all). The step could also be skipped
        all together i.e yml could look like this:

        <platform>:
            requested_data:

        This function is kept since some old scripts might use it.
        I doesn't really have any purpose except from calling extract_parameters_from_yml()

        Args:
            step (str): Name of step in which values should be replaced. I.e: "run", "step_1"
            *argv (dict, str): A dictionary in which values should be updated,
            might also be string

        Returns:
            dict/any: A dictionary with updated values, or if no values were updated,
            "argv" will be returned. If "requested_data" is a string
            the data found with key "requested_data" in a yml file will be returned as is.

            list: List containing keys to all values that were updated.
        """

        modified_dictionary, changed_keys = cls._extract_parameters_from_yml(step, argv[0])

        if len(changed_keys) > 0:
            return modified_dictionary

        logging.debug("No value(s) in %s were found in neither conf_default, nor in "
            "a test specific yml file.", argv[0])

        if not isinstance(argv[0], dict):
            return ""
        return argv[0]

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
