/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


#!/usr/bin/env python3

""" Compare REQPROD id from SWRS for MEP2 BaseTech and the FIP from Confluence.
    Date: 2019-11-21
    Author: Anton Svensson (asvens37)
"""

import argparse
import csv
import openpyxl # pylint: disable=import-error

OUTPUT_FILE = "req_bsw.csv"

# FIP constants
REQPROD_IDX = 1
VERIF_IDX = 6
# SWRS constants
REQPROD_IDX_SWRS = 1
VERIF_IDX_SWRS = 7
LINK_IDX_SWRS = 11

### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Create csv with requirement ID')
    parser.add_argument("--fip", help="Analyzed FIP.", type=str, action='store',
                        dest='fip', required=True,)
    parser.add_argument("--swrs", help="Set of requirements from Elektra", type=str,
                        action='store', dest='swrs',)
    ret_args = parser.parse_args()
    return ret_args

def parse_xlsx(file_path):
    """Get info from the fip"""
    ret_dict = {}
    workbook = openpyxl.load_workbook(file_path)
    workspace = workbook.active
    firstline = True
    for line in workspace:
        if firstline:
            firstline = False
        else:
            temp_reqprod = line[REQPROD_IDX].value
            temp_verif = line[VERIF_IDX].value
            ret_dict[temp_reqprod] = temp_verif
    return ret_dict

def parse_csv(file_path):
    """Get info from the csv"""
    ret_dict_meth = {}
    ret_dict_link = {}
    with open(file_path) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        firstline = True
        for line in csvreader:
            if len(line) > 1:
                if firstline:
                    firstline = False
                else:
                    temp_reqprod = line[REQPROD_IDX_SWRS]
                    temp_verif = line[VERIF_IDX_SWRS]
                    temp_link = line[LINK_IDX_SWRS]
                    ret_dict_meth[temp_reqprod] = temp_verif
                    ret_dict_link[temp_reqprod] = temp_link
    return ret_dict_meth, ret_dict_link

def create_csv(fip_d, swrs_d, swrs_d2):
    """Combine the fip and swrs to one file"""
    all_keys = set()
    # Note that swrs_d, swrs_d2 have the same keys
    for key in fip_d:
        all_keys.add(key)
    for key2 in swrs_d:
        all_keys.add(key2)
    #all_keys.add(list(fip_d))
    #all_keys.add(swrs_d.keys())
    sort_keys = sorted(filter(None, all_keys))
    print(sort_keys)
    write_to_file(sort_keys, fip_d, swrs_d, swrs_d2)

def write_to_file(keys, fip, swrs, swrs_links):
    """Write output to file"""
    with open(OUTPUT_FILE, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', lineterminator='\n')
        writer.writerow(["REQPROD", "TEST_METHOD", "ELEKTRA", "LINK"])
        for key in keys:
            writer.writerow([key, fip.get(key, '-'), swrs.get(key, '-'), swrs_links.get(key, '-')])
    csvfile.close()

def main(margs):
    """Call functions from here"""
    fip_dict = parse_xlsx(margs.fip)
    if margs.swrs:
        swrs_meth_dict, swrs_link_dict = parse_csv(margs.swrs)

    else:
        swrs_meth_dict = {}
        swrs_link_dict = {}
    create_csv(fip_dict, swrs_meth_dict, swrs_link_dict)

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
