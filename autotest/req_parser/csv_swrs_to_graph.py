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

"""
This script shall be used to parse the CarWeaver Requirement Export in 'csv' format.
"""

# imports
import csv

# constants
## to-be-ignored attributes in CW export --> these attributes will be excluded in the parsing outcome
IGNORE_ATTRS = ['Attribute Area', 'Type', 'Req handle', 'Handshaked', 'Implementation']
## to-be-replaced attributes in CW export 
### e.g. replace 'Req id' attr by 'ID' attr, but keep the same value
### {'Req id': '902134', ...} --> {'ID': '902134', ...}
### this modification is intended to keep the hilding compatible with both Elektra and CarWeaver
MODIFY_ATTRS = {'Req id': 'ID', 'Ver': 'Revision', 'Requirement name': 'Name'}
## to-be-added attributes in the parsing outcome with hard-coded values
ADD_ATTRS = {'Class': 'REQPROD', 'Variant': '-', 'State': 'Frozen'}
## CarWeaver requirement prefix, e.g. REQ-902134
CW_REQ_PREFIX = 'REQ-'

# methods
## parse_csv_to_dicts
def parse_csv_to_dicts(csv_path):
    """Parses an input 'CarWeaver Requirement Export' in csv format, 
        and outputs a dictionary with the following structure:
        {
            req_id: {
                'ID': req_id,
                'Revision': req_version,
                'Name', req_name,
                'Class': 'REQPROD',
                'Variant': '-',
                'State': 'Frozen'
            },
            ....
            ....
        }

    Args:
        csv_path (str): String that represents CSV file path.

    Returns:
        reqs_dict (dict): Dictionary that holds the parsing outcome as structured above.
    """
    # init outcome dict
    reqs_dict = {}
    # open CSV file in read-only mode
    with open(csv_path, 'r') as csv_file:
        # parse the CSV file as dict
        dict_reader = csv.DictReader(csv_file)
        # loop on each element/row in the dict
        for row in dict_reader:
            # filter out the to-be-ignored attributes
            for ignore_attr in IGNORE_ATTRS:
                if ignore_attr in row:
                    del row[ignore_attr]
            # modify the to-be-modified attributes
            for key, val in MODIFY_ATTRS.items():
                if key in row:
                    row[val] = row[key]
                    del row[key]
            # insert the to-be-added attributes
            for key, val in ADD_ATTRS.items():
                row[key] = val
            # for compatibility, remove CW requirement prefix
            ## e.g. REQ-902134 --> 902134
            row['ID'] = row['ID'][len(CW_REQ_PREFIX):]
            reqs_dict[row['ID']] = row
    # return the parsing outcome
    return reqs_dict

# this is not a standalone python file
if __name__ == "__main__":
    exit(0)