#!/usr/bin/env python3

# Date: 2019-11-19
# Author: Anton Svensson (asvens37)

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
import re
import collections

RE_DATE_START = re.compile('\s*Testcase\s+start:\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+:\d+:\d+)')
RE_RESULT = re.compile('\s*Testcase\s+result:\s+(?P<result>\w+)')
RE_FOLDER_TIME = re.compile('.*Testrun_(?P<date>\d+_\d+)')

COLOR_DICT = {'PASSED':'#94f7a2', 'FAILED':'#f54949', 'NA':'#94c4f7'}

### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Create html table from generated test reports')
    parser.add_argument("--logfolder", help="path to log reports", type=str, action='store',
                        dest='report_folder', nargs='+', required=True,)
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


def write_table(column_tuples, outfile):
    """Create html table based on the dict"""
    page = HTML()
    #page.h('TestResult-ODTB2 run ' + str(f_date) + ' ' + str(f_time))
    page.style("table {border-collapse: collapse; width: 100%;} th, td {text-align: left; padding: 8px;} tr:nth-child(even) {background-color: #f2f2f2;}")
    
    table = page.table(border='1', style='border-collapse: collapse')

    key_set = set()
    in_dict = dict()
    
    # Creating set with only "keys"
    for column_tuple in column_tuples:
        # The second argument in tuple is the dict
        in_dict = column_tuple[1]
        for key in in_dict:
            key_set.add(key)

    # Sorting the keys
    sorted_key_list = sorted(key_set)
    amount_of_testruns = str(len(column_tuples))

    # Creating header rows
    table.td("", bgcolor='lightgrey', colspan=amount_of_testruns)
    table.td("TestResult-ODTB2", colspan=amount_of_testruns, bgcolor='lightgrey',
             style='padding: 3px')
    table.tr()
    counters = list()
    table.td('', bgcolor='lightgrey', style='padding: 3px')
    table.td('Test Scripts', bgcolor='lightgrey', style='padding: 3px')
    for column_tuple in column_tuples:
        table.td(column_tuple[0], bgcolor='lightgrey')
        # Adding one counter for each testresult
        counters.append(collections.Counter())
    table.tr()

    # Iterating over the set of keys (rows) matching it with the dicts representing the testrun
    # result. Creating the body of the table.
    for key in sorted_key_list:
        td = table.td('', style='padding: 3px')
        td.a('DVM', href='https://c1.confluence.cm.volvocars.biz/display/BSD/VCC+-+UDS+services', target='_blank')
        table.td(key[:-4], style='padding: 3px')
        #look up in dicts
        index = 0
        for column_tuple in column_tuples:
            folder_name = column_tuple[2]
            in_dict = column_tuple[1]
            temp_res = in_dict[key]
            counters[index][temp_res] += 1
            index += 1
            result_td = table.td(bgcolor=COLOR_DICT[temp_res], style='padding: 3px')
            # Creating URL string
            href_string = folder_name + '\\' + key
            result_td.a(temp_res, href=href_string, target='_blank')
        table.tr()

    # Sum row
    temp_str = ""
    table.td(temp_str, bgcolor='lightgrey', style='padding: 3px', colspan=amount_of_testruns)
    for counter in counters:
        total = 0
        for item in counter:
            total += counter[item]
        percent = round((counter['PASSED']/total) * 100, 1)
        temp_str = str(counter['PASSED']) + '/' + str(total) + ' Passed (' + str(percent) + '%)'
        table.td(temp_str, style='font-weight:bold; padding: 3px', bgcolor='lightgrey')
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
    
    folders = margs.report_folder
    print(folders)
    folders.sort(reverse = True)
    print(folders)
    
    for folder_name in folders:
        print(folder_name)
        res_dict, f_date, f_time = get_file_names(folder_name)
        folder_time = get_folder_time(folder_name)
        folder_tuple = (folder_time, res_dict, folder_name)
        column_tuple.append(folder_tuple)
    #write_table(res_dict, margs.html_file, f_date, f_time)

    write_table(column_tuple, margs.html_file)
    print("working")


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
