#!/usr/bin/env python3

# Date: 2019-11-19
# Authors: Anton Svensson (asvens37), Fredrik Jansson (fjansso8)

"""
Create html table from log files.
Usage: python3 visualize_logs.py --logfolder <path_to_logs>
Output: html file with the results in a table
"""

import traceback
import argparse
import logging
import sys
from sys import path
import os
from os.path import dirname as dir # pylint: disable=redefined-builtin
import subprocess
import socket
from os import listdir # pylint: disable=ungrouped-imports
from os.path import isfile, join, isdir # pylint: disable=ungrouped-imports
from datetime import datetime
import re
import collections
import csv
from yattag import Doc

from hilding import get_settings
from supportfunctions.support_test_odtb2 import SupportTestODTB2 # pylint: disable=wrong-import-position
from supportfunctions.logs_to_html_css import STYLE as CSS # pylint: disable=wrong-import-position
# Ugly hack to allow absolute import from the root folder
# whatever its name is. Please forgive the heresy.
if __name__ == "__main__" and __package__ is None:
    path.append(dir(path[0]))
    __package__ = "autotest" # pylint: disable=redefined-builtin

td = get_settings().rig.get_testrun_data()


SUPPORT_TEST = SupportTestODTB2()

RE_DATE_START = re.compile(r'\s*Testcase\s+start:\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+:\d+:\d+)')
RE_RESULT = re.compile(r'.*(?P<result>FAILED|PASSED|To be inspected|tested implicitly|'\
                       'Tested implicitly|Not applicable).*')
RE_FOLDER_TIME = re.compile(r'.*Testrun_(?P<date>\d+_\d+)')
RE_REQPROD_ID = re.compile(r'\s*e_(?P<reqprod>\d+)_', flags=re.IGNORECASE)
# case insensetive

# When calculating per cent, how many decimals do we want
AMOUNT_OF_DECIMALS = 1

# Report statuses
NA_STATUS = 'NA'
NO_RES_STATUS = 'NO RESULT'
INSPECTION_STATUS = 'INSPECTION'
IMPLICIT_STATUS = 'IMPLICITLY'
PASSED_STATUS = 'PASSED'
FAILED_STATUS = 'FAILED'
MISSING_STATUS = 'MISSING'
UNKNOWN_STATUS = 'UNKNOWN'

# Use the keys when regex-matching in log-files
MATCH_DICT = {'Not applicable': NA_STATUS,
              'NO RESULT': NO_RES_STATUS,
              'To be inspected': INSPECTION_STATUS,
              'tested implicitly': IMPLICIT_STATUS,
              'Tested implicitly': IMPLICIT_STATUS,
              'PASSED': PASSED_STATUS,
              'FAILED': FAILED_STATUS,
              'MISSING': MISSING_STATUS,
              'UNKNOWN': UNKNOWN_STATUS}

# Which color to use for the status
COLOR_DICT = {PASSED_STATUS:'#94f7a2', FAILED_STATUS:'#f54949', NA_STATUS:'DarkSeaGreen',
              MISSING_STATUS:'WHITE', NO_RES_STATUS:'#94c4f7', INSPECTION_STATUS:'Wheat',
              IMPLICIT_STATUS:'PaleGreen', UNKNOWN_STATUS: 'BurlyWood'}

DESC_DICT = {PASSED_STATUS:'Passed',
             FAILED_STATUS:'Failed',
             NA_STATUS:'Not applicable',
             MISSING_STATUS:'No log-file found. Either a new test or removed',
             NO_RES_STATUS:'Did not reach the end of the script. No status found.',
             INSPECTION_STATUS:'Test by inspection',
             IMPLICIT_STATUS:'Implicitly tested by another testscript',
             UNKNOWN_STATUS: 'Unknown error or status'}

BROKEN_URL_COLOR = 'BlanchedAlmond'
SUM_COLOR = 'DarkGoldenRod'
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

# Adding some style to this page ;)
# Example:  Making every other row in a different colour
#           Customizing padding
#           Customizing links



### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Create html table from generated test reports')
    parser.add_argument("--logfolder", help="path to log reports", type=str, action='store',
                        dest='report_folder', nargs='+',)
    parser.add_argument("--reqcsv", help="csv with the REQPROD keys from Elektra", type=str,
                        action='store', dest='req_csv', default='req_bsw.csv',)
    parser.add_argument("--outfile", help="name of outfile html", type=str, action='store',
                        dest='html_file', default='report.html',)
    parser.add_argument("--logs", help="Get the X last testruns from the logfolders",
                        type=str, action='store', dest='logs', default='testruns',)
    parser.add_argument("--script_folder", help="Path to testscript folders",
                        type=str, action='store', dest='script_folder', default='./',)
    parser.add_argument("--graphfile", help="Filename of the local_stats_plot generated file",
                        type=str, action='store', dest='graph_file', default='stats_plot.svg',)
    ret_args = parser.parse_args()
    return ret_args


def get_file_names_and_results(folder_path):
    """Return list with all filenames in logfolder"""
    res_dict = {}
    # Will take time and date from last file. OK for now.
    f_date = None
    f_time = None
    files = [file_name for file_name in listdir(folder_path)
             if (isfile(join(folder_path, file_name))
                 and file_name.endswith(LOG_FILE_EXT)
                 and not file_name.endswith('progress.log'))]

    for file in files:
        file_path = os.path.join(folder_path, file)
        with open(file_path, encoding='utf-8') as file_name:
            # Default is NO_RES_STATUS, incase there is no match
            result = NO_RES_STATUS
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
            logging.debug('%s : %s', test_name, result)

            # Use the key and not the string we are matching with.
            # Match with 'Tested implicitly by', but show 'IMPLICITLY'
            if result in MATCH_DICT:
                res_dict[test_name] = MATCH_DICT[result]
            else:
                res_dict[test_name] = UNKNOWN_STATUS
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


def amount_per_status(status, res_counter):
    """
    Given a status, example: PASSED
    And a list of testrun results.
    This function will return the amount for that particular status.
    """
    result = 0
    for item in res_counter:
        if item == status:
            result += res_counter[item]
    return result


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


def get_key_and_url_comb(my_path, folder):
    """
    Creates a key and URL dictionary based on the files in the folders
    """
    ret_dict = {}
    gitlab_url_root = "https://gitlab.cm.volvocars.biz/HWEILER/odtb2pilot/blob/master/" + folder
    for root, _, files in os.walk(my_path):
        for file in files:
            if file.endswith(PY_FILE_EXT):
                temp_path = os.path.join(root, file)
                temp_path_fix = temp_path.replace('\\', '/')
                # Split at first tests_folder in case that name is reused later in the path
                temp_url = gitlab_url_root + temp_path_fix.split(folder, 1)[1]
                key_name = file.lower().split(PY_FILE_EXT)[:-1]
                ret_dict[key_name[0]] = temp_url
    return ret_dict


def get_url_dict(script_folder):
    '''
    Create and return a dict with the urls to the different scripts.
    '''
    url_dict = get_key_and_url_comb(os.path.join(script_folder, 'test_folder'), 'test_folder')
    return url_dict


def get_git_revision_hash():
    ''' Returns git revision hash '''
    message = ''

    try:
        # This part is for RPi
        repo_path = os.path.join('..', 'Repos', 'odtb2pilot') # Not in repo, try to find repo
        message = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                          cwd=repo_path).decode('ascii').strip()
    except Exception as _: # pylint: disable=broad-except
        try:
            # This is when run locally
            message = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
        except Exception as _: # pylint: disable=broad-except
            logging.warning('Not able to get git hash')
            message = ''
    return message
# Will break this into smaller functions later, but it is not easy to split the html generation.


def generate_error_page(err_msg, outfile):
    """
    Create html error page
    """
    doc, tag, text, _ = Doc().ttl()

    with tag('html'):
        with tag('head'):
            with tag('style'):
                text(CSS)
        with tag('body'):
            with tag('div', id='header_box'): # Header box
                text('Log report')
            with tag('div', id='btn_container'):
                with tag('button', klass="btn btn-primary"):
                    with tag("a", href='did_report.html', target='_blank'):
                        text('DID report')
            with tag('div', id='error_msg'):
                with tag('div', id='error_msg_header'):
                    text('Error occured when creating Log report:')
                with tag('div', id='error_msg_body'):
                    text(err_msg)
            try:
                text(SUPPORT_TEST.get_current_time())
            except Exception as _: # pylint: disable=broad-except
                logging.error(traceback.format_exc())
    write_to_file(doc.getvalue(), outfile)


# Will break this into smaller functions later, but it is not easy to split the html generation.
def generate_html(folderinfo_result_tuple_list, outfile, verif_d,  # pylint: disable=too-many-locals, too-many-branches, too-many-statements, too-many-arguments
                  elektra_d, script_folder, log_folders, graph_file):
    """
    Create html table based on the dict
    """
    doc, tag, text, line = Doc().ttl()

    # Create the urls for the different files in GitLab
    url_dict = get_url_dict(script_folder)
    dvm_url_service_level = 'https://c1.confluence.cm.volvocars.biz/display/BSD/VCC+-+UDS+services'

    res_counter_list = list()
    key_set = set()

    # Creating set with only "keys", using a set to not get duplicates.
    # The testscript names are the keys
    for testres_tuple in folderinfo_result_tuple_list:
        # The second argument in tuple is the result dict
        # And the result dict is the key and the result of the test (FAILED/PASSED/NA)
        result_dict = testres_tuple[TESTRES_DICT_IDX]
        for key in result_dict:
            key_set.add(key)

    # Sorting the keys
    sorted_key_list = sorted(key_set)
    amount_of_testruns = str(len(folderinfo_result_tuple_list))

    req_set = set()

    with tag('html'):
        with tag('head'):
            with tag('style'):
                text(CSS)
        with tag('body'):
            with tag('div', id='header_box'): # Header box
                text('Log report')
            with tag('div', id='btn_container'):
                with tag('button', klass="btn btn-primary"):
                    with tag("a", href='did_report.html', target='_blank'):
                        text('DID report')

            doc.stag('br') # Line break for some space

            # One counter for each test suite
            for _ in folderinfo_result_tuple_list:
                res_counter_list.append(collections.Counter())

            # For the legend (explanation) and the summarization
            for key in sorted_key_list:
                index = 0
                for folderinfo_and_result_tuple in folderinfo_result_tuple_list:
                    testres_dict = folderinfo_and_result_tuple[TESTRES_DICT_IDX]
                    result = MISSING_STATUS # Default
                    if key in testres_dict:
                        result = testres_dict[key]
                        res_counter_list[index][result] += 1
                    index += 1

            doc.stag('br') # Line break for some space

            # Get the counter for the last testrun
            res_counter = res_counter_list[0]

            # A separate table for metadata
            git_revision_hash = get_git_revision_hash()
            hostname = socket.gethostname()
            current_time = get_current_time()

            with tag('div', klass='flex-container'):
                with tag('div', klass='metadata_box'):
                    with tag('div', klass='metadata_header'):
                        with tag('h1', klass='metadata'):
                            text('Testrun info')
                        with tag('table', klass='metadata_table'):
                            with tag('tr'):
                                with tag('td'):
                                    text('Report Generator Hostname')
                                with tag('td', klass='number'):
                                    text(hostname)
                            with tag('tr'):
                                with tag('td'):
                                    text('Report generated')
                                with tag('td', klass='number'):
                                    text(current_time)
                    with tag('table', klass='metadata_table'):
                        with tag('tr'):
                            with tag('td', klass='thin-row'):
                                text('logs_to_html GIT Hash')
                            with tag('td', klass='thin-row number'):
                                text(git_revision_hash)
                        with tag('tr'):
                            with tag('td', klass='thick-row'):
                                text('ECU GIT Hash')
                            with tag('td', klass='ecu_git_hash thick-row number'):
                                text(td.git_hash)

                    with tag('table', klass='metadata_table'):
                        for name in td.eda0_dict:
                            with tag('tr'):
                                with tag('td', klass='thin-row'):
                                    text(name)
                                with tag('td', klass='number thin-row'):
                                    text(td.eda0_dict.get(name, ''))

                # A separate table for the legend (explanation) and the summarization
                with tag('div', klass='legend'):
                    with tag('table', klass='legend'):
                        with tag('tr'): # Heading
                            with tag('th', klass='legend'):
                                text("Category")
                            with tag('th', klass='legend'):
                                text("# of scripts")
                            with tag('th', klass='legend'):
                                text("Explanation")
                        # Using the description dict to get the different categories
                        for category in DESC_DICT:
                            with tag('tr', klass='stripe'):
                                with tag('td', klass='legend', bgcolor=COLOR_DICT[category]):
                                    text(category)
                                with tag('td', klass='number legend'):
                                    text(amount_per_status(category, res_counter))
                                with tag('td', klass='legend'):
                                    text(DESC_DICT[category])

                with tag('div', klass='pic'):
                    doc.stag('img', src=graph_file)

            doc.stag('br') # Line break for some space

            with tag('table', id='main'):
                with tag('tr'):
                    # Heading - First row
                    with tag('th', klass="main", colspan='3'):
                        text('')
                    with tag('th', klass="main", colspan=amount_of_testruns):
                        text('TestResult-Hilding')
                with tag('tr'):
                    # Heading - Second row
                    for heading in HEADING_LIST:
                        with tag('th', klass="main"):
                            text(heading)
                    for folderinfo_and_result_tuple in folderinfo_result_tuple_list:
                        with tag('th', klass="main"):
                            text(folderinfo_and_result_tuple[FOLDER_TIME_IDX])

                # Iterating over the set of keys (rows) matching it with the dicts representing
                # the testrun result. Creating the body of the table.
                # The testcript names are the keys
                for key in sorted_key_list:
                    with tag('tr', klass='stripe'):
                        # First column - DVM
                        with tag('td', klass="main"):
                            with tag("a", href=dvm_url_service_level, target='_blank'):
                                text('DVM')

                        # Second column - REQPROD
                        e_match = RE_REQPROD_ID.match(key)
                        if e_match:
                            e_key = str(e_match.group('reqprod'))
                            req_set.add(e_key)
                            with tag('td', klass="main number"):
                                if e_key in elektra_d:
                                    with tag("a", href=elektra_d[e_key], target='_blank'):
                                        text(e_key)
                                else:
                                    text(e_key)

                        # Third column - Script name
                        if key.lower() in url_dict:
                            with tag('td', klass="main"):
                                with tag("a", href=url_dict[key.lower()], target='_blank'):
                                    text(key)
                        else:
                            # Highlight with blue if we don't find the matching URL
                            #with tag('td', bgcolor=BROKEN_URL_COLOR):
                            with tag('td', klass="main"):
                                text(key)

                        # Fourth (fifth, sixth) - Result columns
                        # Look up in dicts
                        for folderinfo_and_result_tuple in folderinfo_result_tuple_list:
                            folder_name = folderinfo_and_result_tuple[FOLDER_NAME_IDX]
                            testres_dict = folderinfo_and_result_tuple[TESTRES_DICT_IDX]
                            result = MISSING_STATUS
                            if key in testres_dict:
                                result = testres_dict[key]

                            # Creating URL string
                            href_string = (log_folders + '\\' + folder_name + '\\' + key
                                           + LOG_FILE_EXT)
                            color = COLOR_DICT[MISSING_STATUS]
                            if result in COLOR_DICT:
                                color = COLOR_DICT.get(result)
                            with tag('td', klass="main", bgcolor=color):
                                with tag("a", href=href_string, target='_blank'):
                                    text(result)

                # Sum row
                with tag('tr'):
                    with tag('td', klass="main", colspan='3'):
                        text('')
                    for res_counter in res_counter_list:
                        with tag('td', klass="main"):
                            text(calculate_sum_string(res_counter))

            doc.stag('br') # Line break for some space

            # A separate table for the coverage
            with tag('table', id='coverage'):
                with tag('tr'):
                    # Heading
                    with tag('th', klass='coverage'):
                        text("Verification method")
                    with tag('th', klass='coverage'):
                        text("Available")
                    with tag('th', klass='coverage'):
                        text("Covered")
                    with tag('th', klass='coverage'):
                        text("% covered")

                    # Counting how many requirements there are of each verification method
                    req_counter = collections.Counter()
                    for req in verif_d:
                        req_counter[verif_d[req]] += 1

                    # Counting how many unique requirements we have verified of each
                    # verification method
                    tested_counter = collections.Counter()
                    for req in req_set:
                        if req in verif_d:
                            tested_counter[verif_d[req]] += 1
                        else:
                            logging.warning('Req: %s not in verif_dict', req)

                for each in req_counter:
                    with tag('tr', klass='stripe'):
                        with tag('td', klass='number coverage'):
                            text(each)                      # First column

                        with tag('td', klass='number coverage'): # Second column
                            text(str(req_counter[each]))

                        tested_str = ''                     # Third column
                        if tested_counter[each] > 0:
                            tested_str = str(tested_counter[each])
                        with tag('td', klass='number coverage'):
                            text(tested_str)

                        # Fourth column
                        # Calculating the per cent
                        percent = (tested_counter[each] / req_counter[each]) * 100
                        coverage = ''
                        if percent > 0:
                            coverage = str(round(percent, AMOUNT_OF_DECIMALS)) + '%'
                        with tag('td', klass='number coverage'):
                            text(coverage)

                # The total row
                with tag(f'tr style="background-color:{SUM_COLOR}"'):
                    tot_req = sum(req_counter.values())
                    tot_test = sum(tested_counter.values())
                    if tot_req == 0:
                        tot_cov = 0
                    else:
                        tot_cov = (tot_test / tot_req) * 100
                    line('td', 'Total')

                    with tag('td', klass='number'):         # Second column
                        text(str(tot_req))
                    with tag('td', klass='number'):         # Third column
                        text(str(tot_test))
                    with tag('td', klass='number'):         # Fourth column
                        text(str(round(tot_cov, AMOUNT_OF_DECIMALS)) + '%')

            doc.stag('br') # Line break for some space

    write_to_file(doc.getvalue(), outfile)


def get_current_time():
    '''
    Returns current time
    This also exist in support_test_odtb2. Should use that one instead when the python path
    issue is solved.
    '''
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time


def write_to_file(content, outfile):
    '''
    Write content to outfile
    This also exist in support_file_io. Should use that one instead when the python path
    issue is solved.
    '''
    with open(outfile, 'w') as file:
        file.write(str(content))


def main(margs):
    """Call other functions from here"""
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    try:
        folderinfo_result_tuple_list = []
        verif_dict = {}
        e_link_dict = {}
        log_folders = ''

        # For selected folders
        if margs.report_folder:
            logging.debug('Input: %s', margs.report_folder)
            folders = margs.report_folder
            folders.sort(reverse=True)
        elif margs.logs: # No selected folder. Pick 5 latest folders
            logging.debug('Input: %s', margs.logs)
            log_folders = margs.logs

            # Get all testfolders
            all_test_folders = [file_name for file_name in listdir(log_folders)
                                if isdir(file_name) and RE_FOLDER_TIME.match(file_name)]
            all_test_folders.sort(reverse=True)
            # Pick the 5 newest
            folders = all_test_folders[:5]

        # For each folder
        for folder_name in folders:
            res_dict, _, _ = get_file_names_and_results(folder_name)
            folder_time = get_folder_time(folder_name)
            logging.debug('Folder time: %s', folder_time)
            # Put all data in a tuple
            folderinfo_and_result_tuple = (folder_time, res_dict, folder_name)
            # And put the tuple in a list
            folderinfo_result_tuple_list.append(folderinfo_and_result_tuple)

        if margs.req_csv:
            logging.debug("CSV-file found: %s", margs.req_csv)
            verif_dict, e_link_dict = get_reqprod_links(margs.req_csv)
        generate_html(folderinfo_result_tuple_list, margs.html_file, verif_dict, e_link_dict,
                      margs.script_folder, log_folders, margs.graph_file)
        logging.info("Script finished")

    except Exception as _: # pylint: disable=broad-except
        logging.error(traceback.format_exc())
        generate_error_page(str(traceback.format_exc()), margs.html_file)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
