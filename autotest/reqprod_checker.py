#!/usr/bin/env python3

# Date: 2019-11-21
# Author: Anton Svensson (asvens37)

"""
Compare REQPROD id from SWRS for MEP2 BaseTech and the FIP from Confluence.
"""

import argparse
import openpyxl
import csv

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
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    firstline = True
    for line in ws:
        if firstline:
            firstline = False
        else:
            temp_reqprod = line[REQPROD_IDX].value
            temp_verif = line[VERIF_IDX].value
            ret_dict[temp_reqprod] = temp_verif
    return ret_dict

def parse_csv(file_path):
    """Get info from the csv"""
    ret_dict = {}
    with open(file_path) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        firstline = True
        for line in csvreader:
            if len(line) > 1 :
                if firstline:
                    firstline = False
                else:
                    temp_reqprod = line[REQPROD_IDX_SWRS]
                    temp_verif = line[VERIF_IDX_SWRS]
                    temp_link = line[LINK_IDX_SWRS]
                    ret_dict[temp_reqprod] = (temp_verif, temp_link)
    return ret_dict

def create_csv(fip_d, swrs_d):
    """Combine the fip and swrs to one file"""
    all_keys = set()
    for key in fip_d:
        all_keys.add(key)
    for key2 in swrs_d:
        all_keys.add(key2)
    #all_keys.add(list(fip_d))
    #all_keys.add(swrs_d.keys())
    sort_keys = sorted(filter(None, all_keys))
    print(sort_keys)
    write_to_file(sort_keys, fip_d, swrs_d)

def write_to_file(keys, fip, swrs):
    """Write output to file"""
    with open(OUTPUT_FILE, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["REQPROD", "TEST_METHOD", "ELEKTRA"])
        for key in keys:
            writer.writerow([key, fip.get(key,'-'), swrs.get(key, '-')])
    csvfile.close()

def main(margs):
    """Call functions from here"""
    fip_dict = parse_xlsx(margs.fip)
    if margs.swrs:
        swrs_dict = parse_csv(margs.swrs)
    else:
        swrs_dict = {}
    create_csv(fip_dict, swrs_dict)

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
