"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/usr/bin/env python3

""" Create statistics on number of REQPRODs covered per day """

import argparse
import logging
import sys
import re
import datetime
import os
from os.path import isfile, join
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
    req_set = set()
    RE_REQPROD_ID = re.compile(r'\s*BSW_REQPROD_(?P<reqprod>\d+)_', flags=re.IGNORECASE)
    RE_REQPROD_ID_NEW = re.compile(
        r'\s*e_(?P<reqprod>\d+)_(?P<var>[a-zA-Z]*|-)_(?P<rev>\d+)', 
        flags=re.IGNORECASE)
    files = [file_name for file_name in os.listdir(folder_path)
             if (isfile(join(folder_path, file_name)) and file_name.endswith(LOG_FILE_EXT))]
    for file in files:
        re_match_e = RE_REQPROD_ID_NEW.match(file)
        if re_match_e:
            req_set.add(re_match_e.group('reqprod'))
            continue
        re_match = RE_REQPROD_ID.match(file)
        if re_match:
            req_set.add(re_match.group('reqprod'))
    return req_set


def get_all_req_set(folder_path):
    """ Gather all stats fot the different days """
    RE_DATE = re.compile(r'Testrun_(?P<rundate>\d+)_', flags=re.IGNORECASE)
    day_run_dict = defaultdict(set)
    log_folders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
    for log_folder in log_folders:
        logging.debug('In the {%s}!!', log_folder)
        re_match_date = RE_DATE.search(log_folder)
        if re_match_date:
            testrun_set = get_req_cnt(log_folder)
            key_name = "A_" + str(re_match_date.group('rundate'))
            day_run_dict[key_name].update(testrun_set)
    logging.debug(day_run_dict)
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
    # Setup the axis to not be clogged, small ticks for months
    years = mdates.YearLocator()
    months = mdates.MonthLocator()
    fmyear = mdates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(fmyear)
    ax.xaxis.set_minor_locator(months)
    ax.set(title="Number of REQPRODs covered during a day")
    plt.savefig(f"{plt_name}.svg", format="svg")

def main(margs):
    """ Call the other functions from here """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    day_sets = get_all_req_set(margs.resfolder)
    create_stats_plot(margs.outplt, day_sets)

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
