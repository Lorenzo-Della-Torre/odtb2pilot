#!/usr/bin/env python3

""" Module containing the constant parameters used in the project"""
# Date: 2020-01-23 Parameters for Validating diagnostic configuration
# Author: Fredrik Jansson (fjansso8)


# Output information
OUTPUT_FILE_NAME = 'did_dict'
OUTPUT_FOLDER = 'output/'

# Names for dict variables in OUTPUT_FILE_NAME
PBL_DICT_NAME = 'sddb_pbl_did_dict'
SBL_DICT_NAME = 'sddb_sbl_did_dict'
APP_DICT_NAME = 'sddb_app_did_dict'
RESP_ITEM_DICT_NAME = 'sddb_resp_item_dict'

# Names for part number variables in OUTPUT_FILE_NAME
PBL_PART_NUM_NAME = 'pbl_diag_part_num'
SBL_PART_NUM_NAME= 'sbl_diag_part_num'
APP_PART_NUM_NAME= 'app_diag_part_num'

DID_TO_GET_PART_NUMBER = 'F120'

SDDB_INDATA_TYPE = {
    '01' : 'UnSigned',
    '02' : 'Signed',
    '03' : 'Hex',
    '04' : 'BCD + Ascii ( DID : F12x)',
    '05' : 'BCD (DID F18C)',
    '06' : 'Ascii',
    '07' : '4 Byte float'
}

SDDB_OUTDATA_TYPE = {
    '01' : 'Oct.',
    '02' : 'Hex',
    '03' : 'Dec',
    '04' : 'Bin',
    '05' : 'BCD (DID F18C)',
    '06' : 'Ascii',
    '07' : '5 BCD + 3 Ascii',
    '08' : '4 BCD + 3 Ascii ( DID: F12x)'
}
