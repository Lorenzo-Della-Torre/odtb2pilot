#!/usr/bin/env python3

# Date: 2019-11-19
# Author: Anton Svensson (asvens37)

"""
Create html table from log files.
Usage: python3 visualize_logs.py --logfolder <path_to_logs>
Output: html file with the results in a table
"""

import logging
import argparse
from html import HTML
#import html
import os
from os import listdir
from os.path import isfile, join
import re
import time
import collections

re_date_start = re.compile('\s*Testcase\s+start:\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+:\d+:\d+)')
re_result = re.compile('\s*Testcase\s+result:\s+(?P<result>\w+)')
re_folder_time = re.compile('.*Testrun_(?P<date>\d+_\d+)')

color_dict = {'PASSED':'green', 'FAILED':'red', 'NA':'blue'}

### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Create html table from generated test reports')
    parser.add_argument("--logfolder", help="path to log reports", type=str, action='store', dest='report_folder', nargs='+', required=True,)
    parser.add_argument("--outfile", help="name of outfile html", type=str, action='store', dest='html_file', default='test.html',)
    ret_args = parser.parse_args()
    return ret_args

def get_file_names(folder_path):
    """Return list with all filenames in folder"""
    res_dict = {}
    # will take time and date from last file. OK for now.
    f_date = None
    f_time = None
    files = [f for f in listdir(folder_path) if (isfile(join(folder_path, f)) and f.endswith(".log"))]
    for file in files:
        #print(file)
        with open(folder_path + '\\' + file, encoding='utf-8') as f:
            # default is NA, incase there is no match
            #print(os.path.getctime(folder_path + '\\' + file))
            result = "NA"
            for line in f:
                t = re_date_start.match(line)
                m = re_result.match(line)
                if m:
                    result = m.group('result')
                if t:
                    f_date = t.group('date')
                    f_time = t.group('time')
            res_dict[file] = result
    #print(f_date)
    #print(f_time)
    return res_dict, f_date, f_time

def get_folder_time(folder):
    """Return the date and time on same format based on the folder name"""
    temp_time = re_folder_time.match(folder)
    ret_time = temp_time.group('date')
    return ret_time


def write_table(in_dict, outfile, f_date, f_time):
    """Create html table based on the dict"""
    c = collections.Counter()
    page = HTML()
    page.h('TestResult-ODTB2 run ' + str(f_date) + ' ' + str(f_time))
    table = page.table(border='1')
    sort_key_list = sorted(in_dict.keys())
    for key in sort_key_list:
        table.td(key)
        temp_res = in_dict[key]
        c[temp_res] += 1
        table.td(temp_res, bgcolor=color_dict[temp_res])
        table.tr()
    #print(c)
    temp_str = ""
    for item in c:
        temp_str += item + ':' + str(c[item]) + ' '
        #print(c[item])
    table.td(temp_str, style='font-weight:bold')
    table.tr()
    write_to_file(page, outfile)

def write_to_file(content, outfile):
    """Write content to outfile"""
    with open(outfile, 'w') as f:
        f.write(str(content))

def main(margs):
    """Call other functions from here."""
    for folder in margs.report_folder:
        res_dict, f_date, f_time = get_file_names(folder)
        folder_time = get_folder_time(folder)
        print(folder)
        print(folder_time)
    write_table(res_dict, margs.html_file, f_date, f_time)
    print("working")
    #print(res_dict)

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)