# pylint: disable=invalid-name

"""This script should be used to handle requirements that don't need
a test script. This is usually Implicit, Inspection and NA.

"""
import os
import logging
import yaml
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from hilding.conf import Conf

conf = Conf()

IMPLICIT = 'Implicit'
INSPECTION = 'Inspection'
NA = 'NA'
VBF_MOD = 'vbf_modification'
DSPACE = 'dSpace'
SECOC = 'SecOC'

def __split_and_remove_spaces(input_string, delimiter="|"):
    """Splits input string using delimiter. Then removes spaces from first entry in returned tuple

    Args:
        str (str): String that is to be split
        delimiter (str, optional): If custom delimiter is to be used.
        Defaults to "|".

    Returns:
        str: A string without spaces and split using delimiter
    """
    split_input = input_string.split(delimiter)
    ret = split_input
    ret[0] = ret[0].replace(" ", "")
    return ret

def add_to_result(reqprod_dict, directory):
    """Add all the dummy tests to the Result file

    Args:
        reqprod_dict (dict): A dictionary containing all the reqprods covered by the yaml file
        directory (str): Path to the Result file
    """

    with open(directory, mode='a') as result_file_handle:
        for reqprods in reqprod_dict.values():
            for reqprod, info in reqprods.items():
                test_name = __split_and_remove_spaces(info)[0]
                result_file_handle.write(f"{reqprod} PASSED e_{reqprod}_{test_name}.log\n")

def create_logs(reqprod_dict, directory):
    """Create one log for every dummy test

    Args:
        reqprod_dict (dict): A dictionary containing all the reqprods covered by the yaml file
        directory (str): Path to where to logs should be placed
    """

    for category, reqprods in reqprod_dict.items():
        for reqprod, name_and_info in reqprods.items():
            test_name = __split_and_remove_spaces(name_and_info)[0]
            info = __split_and_remove_spaces(name_and_info)[1]
            reqprod = __split_and_remove_spaces(reqprod)[0]
            with open(os.path.join(directory,f"{reqprod}_{test_name}.log"), 'w') as log_file:
                if category == "--NA--":
                    log_file.write(f"Testcase result: Not applicable. Info:{info}")
                if category == "--Inspection--":
                    log_file.write(f"Testcase result: To be inspected. Info:{info}")
                if category == "--dSpace--":
                    log_file.write(f"Testcase result: Tested in dSpace HIL. Info:{info}")
                if category == "--vbf_modification--":
                    log_file.write(f"Testcase result: Modified VBF needed. Info:{info}")
                if category == "--Manual--":
                    log_file.write(f"Testcase result: MANUAL. Info:{info}")
                if category == "--SecOC--":
                    log_file.write(f"Testcase result: SecOC not implemented. Info:{info}")
                if category == "--Excluded--":
                    log_file.write(f"Testcase result: This script is temporarily excluded. Info:{info}")
                #else:
                #    log_file.write(f"Testcase result: {category}. Info: {info}")

def get_dictionary_from_yml(yml_file_dir=""):
    """Extract a dictionary from the yaml file containing black listed requirements.
    This will only include entries for current default platform (set in conf_local.yml)

    Args:
        yml_file_dir (str, optional): Point to yml file containing blacklisted reqprods.
        Default to "". In this case the yml file in the repo root will be used.

    Returns:
        dict: A dictionary from the yaml file containing dummy testsblack listed requirements.
    """

    if yml_file_dir != "":
        yml_file = yml_file_dir
    else:
        yml_file = open(parentdir + "/blacklisted_reqprods.yml", 'r')
    blacklisted_reqs = yaml.safe_load(yml_file)
    relevant_blacklisted_reqs = blacklisted_reqs[conf.default_platform]
    return relevant_blacklisted_reqs

def match_swrs_with_yml(swrs):
    """Finds all tests in swrs that are also present in the yaml file containing dummy tests.
    Will only include tests for default platform (set in conf_default.yml).
    Also returns a copy of swrs where the reqprods covered by the yaml file are removed.

    Args:
        swrs (dict): A dictionary representation of the swrs

    Returns:
        (dict, dict): Returns 2 dictionaries. One that contains all the the reqprods from the
        yaml file that were found in the swrs. The second one is a modified version of swrs
        where all the reqprods found in the yaml file are removed
    """

    reqprods_from_yml = get_dictionary_from_yml()
    matching_reqprods_from_yml = {}
    modified_swrs = dict(swrs)

    for category, yml_reqprods in reqprods_from_yml.items():
        if yml_reqprods is not None:
            matching_reqprods_from_yml[category] = {}
            for reqprod_id, reqprod_data in swrs.items():
                variant = reqprod_data['Variant']
                # We don't use '-' in the blacklist or in scriptnames. replacing with empty.
                if variant == '-':
                    variant = ''
                comparison_variable = f"e_{reqprod_id}_{variant}_{reqprod_data['Revision']}"
                if comparison_variable in yml_reqprods:
                    matching_reqprods_from_yml[category][comparison_variable] = yml_reqprods[comparison_variable]
                    del modified_swrs[reqprod_id]

    return matching_reqprods_from_yml, modified_swrs

def _print_tests(tests_dict):
    """Prints a dictionary containing data from the yaml file
    found in root

    note: This function is not currently used for anything but testing the script.
    It could be removed without altering anything OUTSIDE the main function in this file

    Args:
        tests_dict (Dict): A dictionary created from yaml file in root
    """

    if tests_dict.get(IMPLICIT):
        for implicit_test in tests_dict.get(IMPLICIT):
            logging.info("Testcase result: %s ",
                tests_dict[IMPLICIT].get(implicit_test))

    if tests_dict.get(INSPECTION):
        for _ in tests_dict.get(INSPECTION):
            logging.info("Testcase result: To be inspected")

    if tests_dict.get(NA):
        for _ in tests_dict.get(NA):
            logging.info("Testcase result: Not applicable")

    if tests_dict.get(VBF_MOD):
        for _ in tests_dict.get(VBF_MOD):
            logging.info("Testcase result: Modified VBF needed")

    if tests_dict.get(DSPACE):
        for _ in tests_dict.get(DSPACE):
            logging.info("Testcase result: Tested in dSpace HIL")

    if tests_dict.get(SECOC):
        for _ in tests_dict.get(SECOC):
            logging.info("Testcase result: SecOC not implemented")

def main():
    """Used to test and run functionality found in this file
    """

    tests = get_dictionary_from_yml()
    _print_tests(tests)


if __name__ == "__main__":
    main()
