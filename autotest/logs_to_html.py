#!/usr/bin/env python3

# Date: 2019-11-19
# Authors: Anton Svensson (asvens37), Fredrik Jansson (fjansso8)

"""
Create html table from log files.
Usage: python3 visualize_logs.py --logfolder <path_to_logs>
Output: html file with the results in a table
"""

#import logging
import argparse
from html import HTML
from os import listdir
from os.path import isfile, join
import os
import re
import collections
import csv

RE_DATE_START = re.compile('\s*Testcase\s+start:\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+:\d+:\d+)')
RE_RESULT = re.compile('\s*Testcase\s+result:\s+(?P<result>\w+)')
RE_FOLDER_TIME = re.compile('.*Testrun_(?P<date>\d+_\d+)')
RE_REQPROD_ID = re.compile('\s*BSW_REQPROD_(?P<reqprod>\d+)_', flags=re.IGNORECASE)
# case insensetive

COLOR_DICT = {'PASSED':'#94f7a2', 'FAILED':'#f54949', 'NA':'#94c4f7'}

REQPROD_IDX = 0
FIP_VERIF_IDX = 1
SWRS_VERIF_IDX = 2
SWRS_LINK_IDX = 3


### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Create html table from generated test reports')
    parser.add_argument("--logfolder", help="path to log reports", type=str, action='store',
                        dest='report_folder', nargs='+', required=True,)
    parser.add_argument("--reqcsv", help="csv with the REQPROD keys from Elektra", type=str, action='store',
                        dest='req_csv',)
    parser.add_argument("--outfile", help="name of outfile html", type=str, action='store',
                        dest='html_file', default='test.html',)
    ret_args = parser.parse_args()
    return ret_args

def get_file_names(folder_path):
    """Return list with all filenames in folder"""
    res_dict = {}
    # Will take time and date from last file. OK for now.
    f_date = None
    f_time = None
    files = [file_name for file_name in listdir(folder_path)
             if (isfile(join(folder_path, file_name)) and file_name.endswith(".log"))]
    for file in files:
        with open(folder_path + '\\' + file, encoding='utf-8') as file_name:
            # Default is NA, incase there is no match
            #print(os.path.getctime(folder_path + '\\' + file))
            result = "NA"
            for line in file_name:
                time_match = RE_DATE_START.match(line)
                result_match = RE_RESULT.match(line)
                if result_match:
                    result = result_match.group('result')
                if time_match:
                    f_date = time_match.group('date')
                    f_time = time_match.group('time')
            res_dict[file] = result
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
        #print("same %s" % fip_val)
    elif fip_val == '-':
        ret_val = swrs_val
        #print("SWRS rulez!!!")
    else:
        # default, can be merged with first if we like
        # kept it for debugging possibilities
        ret_val = fip_val
    return ret_val

def get_url_dict():
    """Create and return a dict with the urls to the different scripts."""
    # Assumption: this file is in odtb2pilot/autotest, and the scripts are in
    #              odtb2pilot/testscripts/*/*.py
    TESTS_FOLDER = "testscripts"
    GITLAB_URL_ROOT = "https://gitlab.cm.volvocars.biz/HWEILER/odtb2pilot/blob/master/testscripts"
    ret_dict = {}
    for root, dirs, files in os.walk("../" + TESTS_FOLDER):
        for file in files:
            if file.endswith(".py"):
                temp_path = os.path.join(root, file)
                temp_path_fix = temp_path.replace('\\', '/')
                # Split at first TESTS_FOLDER in case that name is reused later in the path
                temp_url = GITLAB_URL_ROOT + temp_path_fix.split(TESTS_FOLDER, 1)[1]
                key_name = file.lower().split(".py")[:-1]
                ret_dict[key_name[0]] = temp_url
    return ret_dict

def write_table(column_tuples, outfile, verif_d, elektra_d):
    """Create html table based on the dict"""
    page = HTML()

    # Adding some style to this page ;) Making it every other row in a different colour
    page.style("th, td {text-align: left; padding: 8px;} tr:nth-child(even) {background-color: #e3e3e3;}")
    
    table = page.table(border='1', style='border-collapse: collapse')

    key_set = set()
    in_dict = dict()
    
    # Creating set with only "keys"
    for column_tuple in column_tuples:
        # The second argument in tuple is the dict
        in_dict = column_tuple[1]
        for key in in_dict:
            key_name = key.split(".log")[:-1]
            key_set.add(key_name[0])

    # Sorting the keys
    sorted_key_list = sorted(key_set)
    amount_of_testruns = str(len(column_tuples))

    # Create the urls for the different files in GitLab
    url_dict = get_url_dict()

    # Creating header rows
    table.td("", bgcolor='lightgrey', colspan='3')
    table.td("TestResult-ODTB2", colspan=amount_of_testruns, bgcolor='lightgrey', style='font-weight:bold')
    table.tr()
    counters = list()
    table.td('', bgcolor='lightgrey')
    table.td('REQPROD', bgcolor='lightgrey')
    table.td('Test Scripts', bgcolor='lightgrey', style='font-weight:bold')
    for column_tuple in column_tuples:
        table.td(column_tuple[0], bgcolor='lightgrey', style='font-weight:bold')
        # Adding one counter for each testresult
        counters.append(collections.Counter())
    table.tr()

    # Iterating over the set of keys (rows) matching it with the dicts representing the testrun
    # result. Creating the body of the table.
    for key in sorted_key_list:
        # First column
        td = table.td(style='padding: 3px')
        td.a('DVM', href='https://c1.confluence.cm.volvocars.biz/display/BSD/VCC+-+UDS+services', target='_blank', style='color:black; text-decoration: none;' )
        
        # Second column
        # Elektra link
        elektra_td = table.td(style='padding: 3px')
        e_match = RE_REQPROD_ID.match(key)

        if e_match:
            e_key = str(e_match.group('reqprod'))
            elektra_td.a(e_key, href=elektra_d[e_key], target='_blank', style='color:black; text-decoration: none;')
        
        # Third column
        # Creating script URL
        script_url = url_dict[key.lower()]

        script_td = table.td(style='padding: 3px')
        script_td.a(key, href=script_url, target='_blank', style='color:blue; text-decoration: none;')

        # Result columns
        # Look up in dicts
        index = 0
        for column_tuple in column_tuples:
            folder_name = column_tuple[2]
            in_dict = column_tuple[1]
            # add file extension to get log
            temp_res = in_dict[key + ".log"]
            counters[index][temp_res] += 1
            index += 1
            result_td = table.td(bgcolor=COLOR_DICT[temp_res], style='padding: 3px')
            # Creating URL string
            href_string = folder_name + '\\' + key
            result_td.a(temp_res, href=href_string, target='_blank', style='color:black; text-decoration: none;')
        table.tr()

    # Sum row
    temp_str = ""
    table.td(temp_str, bgcolor='lightgrey', style='padding: 3px', colspan='3')
    for counter in counters:
        total = 0
        for item in counter:
            total += counter[item]
        percent = round((counter['PASSED']/total) * 100, 1)
        temp_str = str(counter['PASSED']) + '/' + str(total) + ' Passed (' + str(percent) + '%)'
        table.td(temp_str, style='font-weight:bold', bgcolor='lightgrey')
    table.tr()
    #print(table)
    write_to_file(page, outfile)

def write_to_file(content, outfile):
    """Write content to outfile"""
    with open(outfile, 'w') as file:
        file.write(str(content))

def main(margs):
    """Call other functions from here."""
    column_tuple = []
    verif_dict = {}
    e_link_dict = {}
    
    folders = margs.report_folder
    folders.sort(reverse = True)
    
    for folder_name in folders:
        res_dict, f_date, f_time = get_file_names(folder_name)
        folder_time = get_folder_time(folder_name)
        folder_tuple = (folder_time, res_dict, folder_name)
        column_tuple.append(folder_tuple)
    #write_table(res_dict, margs.html_file, f_date, f_time)
    if margs.req_csv:
        verif_dict, e_link_dict = get_reqprod_links(margs.req_csv)
    write_table(column_tuple, margs.html_file, verif_dict, e_link_dict)
    print("working")


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
