#!/usr/bin/env python3

# Date: 2019-11-19
# Authors: Anton Svensson (asvens37), Fredrik Jansson (fjansso8)

"""
Create html table from log files.
Usage: python3 visualize_logs.py --logfolder <path_to_logs>
Output: html file with the results in a table
"""

import argparse
import logging
import sys

import os
from os import listdir
from os.path import isfile, join

from datetime import datetime
import re
import collections
import csv

from yattag import Doc

RE_DATE_START = re.compile(r'\s*Testcase\s+start:\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+:\d+:\d+)')
RE_RESULT = re.compile(r'\s*Testcase\s+result:\s+(?P<result>\w+)')
RE_FOLDER_TIME = re.compile(r'.*Testrun_(?P<date>\d+_\d+)')
RE_REQPROD_ID = re.compile(r'\s*BSW_REQPROD_(?P<reqprod>\d+)_', flags=re.IGNORECASE)
# case insensetive

# When calculating per cent, how many decimals do we want
AMOUNT_OF_DECIMALS = 1

# The different status the test run can have
NA_STATUS = 'NA'
PASSED_STATUS = 'PASSED'
FAILED_STATUS = 'FAILED'
MISSING_STATUS = 'MISSING'

# Which color to use for the status
COLOR_DICT = {PASSED_STATUS:'#94f7a2', FAILED_STATUS:'#f54949', NA_STATUS:'#94c4f7',
              MISSING_STATUS:'WHITE'}

HEADING_LIST = ['', 'REQPROD', 'Test Scripts']

LOG_FILE_EXT = '.log'
PY_FILE_EXT = '.py'

REQPROD_IDX = 0
FIP_VERIF_IDX = 1
SWRS_VERIF_IDX = 2
SWRS_LINK_IDX = 3

# For the folderinfo_and_result_tuple
FOLDER_TIME_IDX = 0
TESTRES_DICT_IDX = 1
FOLDER_NAME_IDX = 2

FIRST_PART_IDX = 0


### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Create html table from generated test reports')
    parser.add_argument("--logfolder", help="path to log reports", type=str, action='store',
                        dest='report_folder', nargs='+', required=True,)
    parser.add_argument("--reqcsv", help="csv with the REQPROD keys from Elektra", type=str,
                        action='store', dest='req_csv',)
    parser.add_argument("--outfile", help="name of outfile html", type=str, action='store',
                        dest='html_file', default='test.html',)
    ret_args = parser.parse_args()
    return ret_args


def get_file_names_and_results(folder_path):
    """Return list with all filenames in folder"""
    res_dict = {}
    # Will take time and date from last file. OK for now.
    f_date = None
    f_time = None
    files = [file_name for file_name in listdir(folder_path)
             if (isfile(join(folder_path, file_name)) and file_name.endswith(LOG_FILE_EXT))]
    for file in files:
        with open(folder_path + '\\' + file, encoding='utf-8') as file_name:
            # Default is NA, incase there is no match
            #print(os.path.getctime(folder_path + '\\' + file))
            result = NA_STATUS
            for line in file_name:
                time_match = RE_DATE_START.match(line)
                result_match = RE_RESULT.match(line)
                if result_match:
                    result = result_match.group('result')
                if time_match:
                    f_date = time_match.group('date')
                    f_time = time_match.group('time')
            # Remove '.log' from name
            test_name = file.split(LOG_FILE_EXT)[:-1][FIRST_PART_IDX]
            res_dict[test_name] = result
    return res_dict, f_date, f_time


def get_folder_time(folder):
    """Return the date and time on same format based on the folder name"""
    temp_time = RE_FOLDER_TIME.match(folder)
    ret_time = temp_time.group('date')
    return ret_time


def get_reqprod_links(infile):
    """Return dict of REQPROD number linked to Elektra direct link"""
    ret_verif_dict = {}
    ret_links_dict = {}
    with open(infile) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';')
        firstline = True
        for line in csvreader:
            if firstline:
                firstline = False
            else:
                temp_reqprod = line[REQPROD_IDX]
                temp_verif = get_verif(line[FIP_VERIF_IDX], line[SWRS_VERIF_IDX])
                temp_link = line[SWRS_LINK_IDX]
                ret_verif_dict[temp_reqprod] = temp_verif
                ret_links_dict[temp_reqprod] = temp_link
    return ret_verif_dict, ret_links_dict


def get_verif(fip_val, swrs_val):
    """Helper function that will compare and return verification method"""
    ret_val = None
    if fip_val == swrs_val:
        ret_val = fip_val
    elif fip_val == '-':
        ret_val = swrs_val
    else:
        # default, can be merged with first if we like
        # kept it for debugging possibilities
        ret_val = fip_val
    return ret_val


def calculate_sum_string(res_counter):
    ''' Given a counter as input: Calculating how many tests passed out of the total
        Returning a string '''
    total = 0
    for item in res_counter:
        total += res_counter[item]
    if total == 0:
        # Avoid division with zero
        percent = 0
    else:
        percent = round((res_counter[PASSED_STATUS]/total) * 100, AMOUNT_OF_DECIMALS)
    return str(percent) + '% Passed (' + str(res_counter[PASSED_STATUS]) + '/' + str(total) +')'


def get_url_dict():
    """Create and return a dict with the urls to the different scripts."""
    # Assumption: this file is in odtb2pilot/autotest, and the scripts are in
    #              odtb2pilot/"tests_folder"/*/*.py
    tests_folder = "test_cases_old"
    gitlab_url_root = "https://gitlab.cm.volvocars.biz/HWEILER/odtb2pilot/blob/master/test_cases_old"
    ret_dict = {}
    for root, _, files in os.walk("../" + tests_folder):
        for file in files:
            if file.endswith(PY_FILE_EXT):
                temp_path = os.path.join(root, file)
                temp_path_fix = temp_path.replace('\\', '/')
                # Split at first tests_folder in case that name is reused later in the path
                temp_url = gitlab_url_root + temp_path_fix.split(tests_folder, 1)[1]
                key_name = file.lower().split(PY_FILE_EXT)[:-1]
                ret_dict[key_name[0]] = temp_url
    return ret_dict


def generate_html(folderinfo_and_result_tuple_list, outfile, verif_d, elektra_d): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    """
    Create html table based on the dict
    """
    doc, tag, text, line = Doc().ttl()

    # Adding some style to this page ;)
    # Example:  Making every other row in a different colour
    #           Customizing padding
    #           Customizing links
    style = ("table {border-collapse: collapse;}"
             "table, th, td {border: 1px solid black;}"
             "th, td {text-align: left;}"
             "th {background-color: lightgrey; padding: 8px;}"
             "td {padding: 3px;}"
             "tr:nth-child(even) {background-color: #e3e3e3;}"
             "a {color:black; text-decoration: none;}"
             "#header {background-color: lightgrey; height: 100px; line-height: 100px;"
             "width: 1000px; text-align:center; vertical-align: middle; border:1px black solid;"
             "margin:30px; font-size: 50px;}")

    # Create the urls for the different files in GitLab
    url_dict = get_url_dict()

    dvm_url_service_level = 'https://c1.confluence.cm.volvocars.biz/display/BSD/VCC+-+UDS+services'

    res_counter_list = list()
    key_set = set()

    # Creating set with only "keys", using a set to not get duplicates.
    # The testscript names are the keys
    for testres_tuple in folderinfo_and_result_tuple_list:
        # The second argument in tuple is the result dict
        # And the result dict is the key and the result of the test (FAILED/PASSED/NA)
        result_dict = testres_tuple[TESTRES_DICT_IDX]
        for key in result_dict:
            key_set.add(key)

    # Sorting the keys
    sorted_key_list = sorted(key_set)
    amount_of_testruns = str(len(folderinfo_and_result_tuple_list))

    req_set = set()

    with tag('html'):
        with tag('head'):
            with tag('style'):
                text(style)
        with tag('body'):
            with tag('div', id='header'): # Header box
                text('Test Summary Report')
            with tag('table', id='main'):
                with tag('tr'):
                    # Heading - First row
                    line('th', '', colspan='3')
                    line('th', 'TestResult-ODTB2', colspan=amount_of_testruns)
                with tag('tr'):
                    # Heading - Second row
                    for heading in HEADING_LIST:
                        line('th', heading)
                    for folderinfo_and_result_tuple in folderinfo_and_result_tuple_list:
                        line('th', folderinfo_and_result_tuple[FOLDER_TIME_IDX])
                        # Adding one counter for each testresult folder
                        res_counter_list.append(collections.Counter())

                # Iterating over the set of keys (rows) matching it with the dicts representing
                # the testrun result. Creating the body of the table.
                # The testcript names are the keys
                for key in sorted_key_list:
                    with tag('tr'):
                        # First column - DVM
                        with tag('td'):
                            with tag("a", href=dvm_url_service_level, target='_blank'):
                                text('DVM')

                        # Second column - REQPROD
                        e_match = RE_REQPROD_ID.match(key)
                        if e_match:
                            e_key = str(e_match.group('reqprod'))
                            req_set.add(e_key)
                            with tag('td'):
                                with tag("a", href=elektra_d[e_key], target='_blank'):
                                    text(e_key)

                        # Third column
                        with tag('td'):
                            with tag("a", href=url_dict[key.lower()], target='_blank'):
                                text(key)

                        # Fourth (fifth, sixth) - Result columns
                        # Look up in dicts
                        index = 0
                        for folderinfo_and_result_tuple in folderinfo_and_result_tuple_list:
                            folder_name = folderinfo_and_result_tuple[FOLDER_NAME_IDX]
                            testres_dict = folderinfo_and_result_tuple[TESTRES_DICT_IDX]
                            result = MISSING_STATUS
                            if key in testres_dict:
                                result = testres_dict[key]
                                res_counter_list[index][result] += 1
                            index += 1
                            # Creating URL string
                            href_string = folder_name + '\\' + key + LOG_FILE_EXT

                            with tag('td', bgcolor=COLOR_DICT[result]):
                                with tag("a", href=href_string, target='_blank'):
                                    text(result)

                # Sum row
                with tag('tr'):
                    line('th', '', colspan='3')

                    for res_counter in res_counter_list:
                        line('th', calculate_sum_string(res_counter))

            doc.stag('br') # Line break for some space

            # A separate table for the coverage
            with tag('table', id='main'):
                with tag('tr'):
                    # coverage_table = page.table()

                    # Heading
                    line('th', "Verification method")
                    line('th', "Available")
                    line('th', "Covered")
                    line('th', "% covered")

                    # Counting how many requirements there are of each verification method
                    req_counter = collections.Counter()
                    for req in verif_d:
                        req_counter[verif_d[req]] += 1

                    # Counting how many unique requirements we have verified of each
                    # verification method
                    tested_counter = collections.Counter()
                    for req in req_set:
                        tested_counter[verif_d[req]] += 1

                for each in req_counter:
                    with tag('tr'):
                        line('td', each)                        # First column
                        line('td', str(req_counter[each]))      # Second column

                        tested_str = ''
                        if tested_counter[each] > 0:
                            tested_str = str(tested_counter[each])
                        line('td', tested_str)                  # Third column

                        # Calculating the per cent
                        percent = (tested_counter[each] / req_counter[each]) * 100
                        coverage = ''
                        if percent > 0:
                            coverage = str(round(percent, AMOUNT_OF_DECIMALS)) + '%'
                        line('td', coverage)                    # Fourth column

    doc.stag('br') # Line break for some space
    text(get_current_time())
    write_to_file(doc.getvalue(), outfile)


def get_current_time():
    ''' Returns current time '''
    now = datetime.now()
    current_time = now.strftime("Generated %Y-%m-%d %H:%M:%S")
    return current_time


def write_to_file(content, outfile):
    """Write content to outfile"""
    with open(outfile, 'w') as file:
        file.write(str(content))


def main(margs):
    """Call other functions from here"""

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    folderinfo_and_result_tuple_list = []
    verif_dict = {}
    e_link_dict = {}

    folders = margs.report_folder
    folders.sort(reverse=True)

    for folder_name in folders:
        res_dict, _, _ = get_file_names_and_results(folder_name)
        folder_time = get_folder_time(folder_name)
        # Put all data in a tuple
        folderinfo_and_result_tuple = (folder_time, res_dict, folder_name)
        # And put the tuple in a list
        folderinfo_and_result_tuple_list.append(folderinfo_and_result_tuple)

    if margs.req_csv:
        logging.debug("CSV-file found: %s", margs.req_csv)
        verif_dict, e_link_dict = get_reqprod_links(margs.req_csv)
    generate_html(folderinfo_and_result_tuple_list, margs.html_file, verif_dict, e_link_dict)
    logging.info("Script finished")


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
