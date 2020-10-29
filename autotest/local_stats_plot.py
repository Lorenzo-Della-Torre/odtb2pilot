#!/usr/bin/env python3

""" Create statistics on number of REQPRODs covered per day """

import argparse
import re
import datetime
import os
from os.path import isfile, join
from collections import defaultdict
import matplotlib.pyplot as plt

# Take the folder with test logs, and then have set per day, which is later put into a pole plot

RE_FOLDER_TIME = re.compile(r'.*Testrun_(?P<date>\d+_\d+)')

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(
        description='Create plot with local test case coverage over time')
    parser.add_argument("--resultfolder", help="path to parent of log reports folders", type=str,
        action='store', dest='resfolder', default="fake_test_result",)
    parser.add_argument("--outplot", help="name of the output file without extension", type=str,
        action='store', dest='outplt', default="mysvggraph2")
    ret_args = parser.parse_args()
    return ret_args

def get_req_cnt(folder_path):
    """ Return how many reqprods that has been tested per day """
    # For future: consider to merge this with parts from logs_to_html.py
    LOG_FILE_EXT = ".log"
    req_set= set()
    RE_REQPROD_ID = re.compile(r'\s*BSW_REQPROD_(?P<reqprod>\d+)_', flags=re.IGNORECASE)
    files = [file_name for file_name in os.listdir(folder_path)
            if (isfile(join(folder_path, file_name)) and file_name.endswith(LOG_FILE_EXT))]
    for file in files:
        #print(file)
        re_match = RE_REQPROD_ID.match(file)
        if re_match:
            #print(re_match.group('reqprod'))
            req_set.add(re_match.group('reqprod'))
    return req_set


def get_all_req_set(folder_path):
    """ Gather all stats fot the different days """
    RE_DATE = re.compile(r'Testrun_(?P<rundate>\d+)_', flags=re.IGNORECASE)
    day_run_dict = defaultdict(set)
    log_folders = [ f.path for f in os.scandir(folder_path) if f.is_dir() ]
    for log_folder in log_folders:
        print(f'In the {log_folder}!!')
        re_match_date = RE_DATE.search(log_folder)
        if re_match_date:
            testrun_set = get_req_cnt(log_folder)
            key_name = "A_" + str(re_match_date.group('rundate'))
            day_run_dict[key_name].update(testrun_set)
    print(day_run_dict)
    return day_run_dict

def create_stats_plot(plt_name, stat_sets):
    """ Generate a plot for the set growth """
    bar_xs = []
    bar_ys = []
    RE_DAY = re.compile(
        r'_(?P<runyear>\d{4})(?P<runmonth>\d{2})(?P<runday>\d{2})', flags=re.IGNORECASE)

    for stat_date in stat_sets:
        re_match_day = RE_DAY.search(stat_date)
        if re_match_day:
            x_year = int(re_match_day.group('runyear'))
            x_month = int(re_match_day.group('runmonth'))
            x_day = int(re_match_day.group('runday'))
            x_date = datetime.datetime(x_year, x_month, x_day)
            y_num = len(stat_sets[stat_date])
            bar_xs.append(x_date)
            bar_ys.append(y_num)
    ax = plt.subplot(111)
    ax.bar(bar_xs, bar_ys, width=10)
    ax.xaxis_date()
    ax.set(title="Number of REQPRODs covered during a day")
    plt.savefig(f"{plt_name}.svg", format="svg")

def main(margs):
    """ Call the other functions from here """
    day_sets = get_all_req_set(margs.resfolder)
    create_stats_plot(margs.outplt, day_sets)

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
