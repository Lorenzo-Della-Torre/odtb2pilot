"""
    Testscript Hilding MEPII
    project:  BECM basetech MEPII
    author:   fjansso8 (Fredrik Jansson)
    date:     2019-10-09
"""

from datetime import datetime
import traceback
import os
import time
import logging
import sys
import inspect
import socket
import copy
from collections import namedtuple
from yattag import Doc

import odtb_conf

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.logs_to_html_css import STYLE as CSS

import parameters as parammod
import dids_from_sddb_checker_conf as conf
from output.did_dict import sddb_resp_item_dict as sddb_resp_item_dict_imp
from output.did_dict import sddb_app_did_dict as sddb_app_did_dict_imp
from output.did_dict import app_diag_part_num as app_diag_part_num_imp
from output.did_dict import pbl_diag_part_num as pbl_diag_part_num_imp
from output.did_dict import sddb_pbl_did_dict as sddb_pbl_did_dict_imp
from output.did_dict import sbl_diag_part_num as sbl_diag_part_num_imp
from output.did_dict import sddb_sbl_did_dict as sddb_sbl_did_dict_imp

SIO = SupportFileIO
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUPPORT_TEST = SupportTestODTB2()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SSBL = SupportSBL()
SE22 = SupportService22()
SE10 = SupportService10()

# The different status the test run can have
PASSED_STATUS = 'PASSED'
FAILED_STATUS = 'FAILED'
PART_NUMBER_STRING_LENGTH = 14
COMPLETE_ECU_PART_SERIAL_NRS_DID = 'EDA0'
PART_NUMBER_DID = 'F120'
GIT_HASH_DID = 'F1F2'
DEF_VAL = '-'

PART_MATCH_DICT = {True:'part_match', False:'part_no_match'}
MATCH_DICT = {True:'match main', False:'no_match main'}
ERROR_DICT = {True:'error main', False:'main'}
HEADING_LIST = ['DID', 'Name', 'Correct SID', 'Correct DID', 'Correct size', 'Scaled values',
                'Error Message', 'Payload']

Infoentry = namedtuple('Infoentry', 'did name c_sid c_did c_size scal_val_list err_msg payload')


def get_git_hash(can_p):
    '''
    Getting the git hash from the ECU (DID F1F2)
    '''
    ascii_git_hash = ''
    try:
        did_dict = SE22.get_did_info(can_p, GIT_HASH_DID, conf.response_timeout)
        git_hash = did_dict.get('payload', '')
        git_hash_stripped = git_hash.rstrip("0") # Removing trailing zeros
        ascii_git_hash = bytearray.fromhex(git_hash_stripped).decode() # decode from hex to ASCII
    except Exception as _: # pylint: disable=broad-except
        logging.error(traceback.format_exc())
        ascii_git_hash = 'Error'
    return ascii_git_hash


def comp_part_nbrs(can_p, sddb_cleaned_part_number):
    '''
    Testing so that the Application Diagnostic Database Part Number is correct (matching)
    It is stored in DID F120 and we match with the sddb part number
    '''
    message = str()
    match = False
    try:
        # Get diagnostic part number from ECU (using service 22)
        did_dict = SE22.get_did_info(can_p, PART_NUMBER_DID,
                                     conf.response_timeout)
        ecu_diag_part_num_full = ''
        if 'payload' in did_dict:
            ecu_diag_part_num_full = did_dict['payload']

            # Checking length
            if len(ecu_diag_part_num_full) == PART_NUMBER_STRING_LENGTH:
                # Extracting the last part of diagnostic part nummer (AA, AB, ...)
                ecu_diag_part_num_vers_hex = ecu_diag_part_num_full[8:PART_NUMBER_STRING_LENGTH]
                # Decoding from hex to ASCII
                ecu_diag_part_num_version = bytearray.fromhex(ecu_diag_part_num_vers_hex).decode()
                # Putting it back together to complete string again
                ecu_diag_part_num_full = ecu_diag_part_num_full[0:8] + ecu_diag_part_num_version
            else:
                #raise RuntimeError('ECU Diagnostic Part Number is to short!')
                logging.warning('ECU Diagnostic Part Number is to short!')

            # Comparing part numbers
            if sddb_cleaned_part_number == ecu_diag_part_num_full:
                message = ('Diagnostic part number is matching! Expected ' +
                           sddb_cleaned_part_number)
                match = True
            else:
                message = (
                    'Diagnostic part number is NOT matching! Expected ' +
                    sddb_cleaned_part_number)

            logging.debug('-------------------------------------------------')
            logging.debug(message)
            logging.debug(did_dict)
            logging.debug('-------------------------------------------------')
    except RuntimeError as runtime_error:
        message = runtime_error
    return match, message


def generate_error_page(err_msg):
    """ Create html error page """

    # Used for for selecting style class
    doc, tag, text, _ = Doc().ttl()

    with tag('html'):
        with tag('head'):
            with tag('style'):
                text(CSS)
        with tag('body'):
            with tag('div', id='header_box'): # Header box
                text('DID report')
            with tag('div', id='error_msg'):
                with tag('div', id='error_msg_header'):
                    text('Error occured when creating DID report:')
                with tag('div', id='error_msg_body'):
                    text(err_msg)
            try:
                text(SUPPORT_TEST.get_current_time())
            except Exception as _: # pylint: disable=broad-except
                logging.error(traceback.format_exc())
    outfile = "did_report.html"
    write_to_file(doc.getvalue(), outfile)


def generate_html(pbl_list, sbl_list, appl_list, pass_or_fail_counter_dict, part_nbr_match, # pylint: disable=too-many-locals,too-many-statements
                  part_nbr_match_msg, eda0_dict):
    """Create html table based on the dict"""
    # Used for for selecting style class
    doc, tag, text, line = Doc().ttl()
    hostname = socket.gethostname()
    current_time = get_current_time()

    with tag('html'):
        with tag('head'):
            with tag('style'):
                text(CSS)
        with tag('body'):
            with tag('div', id='header_box'): # Header box
                text('DID report')
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
                            with tag('td', klass='thick-row', id=PART_MATCH_DICT[part_nbr_match]):
                                text(part_nbr_match_msg)
                    with tag('table', klass='metadata_table'):
                        for name in eda0_dict:
                            with tag('tr'):
                                with tag('td', klass='thin-row'):
                                    text(name)
                                with tag('td', klass='number thin-row'):
                                    text(eda0_dict.get(name, ''))

                with tag('div', klass='metadata_box'):
                    with tag('div', klass='metadata_header'):
                        with tag('h1', klass='metadata'):
                            text('Summary')
                    with tag('table', klass='metadata_table'):
                        for key in pass_or_fail_counter_dict:
                            with tag('tr'):
                                with tag('td', klass='thin-row'):
                                    text(key)
                                with tag('td', klass='number thin-row'):
                                    text(pass_or_fail_counter_dict.get(key, ''))

            with tag('table', id='main'):
                with tag('tr'):
                    for heading in HEADING_LIST:
                        with tag('th', klass="main"):
                            text(heading)

                __iterate_list(pbl_list, tag, text, line, 'Primary Bootloader')
                __iterate_list(sbl_list, tag, text, line, 'Secondary Bootloader')
                __iterate_list(appl_list, tag, text, line, 'Application')

    outfile = "did_report.html"
    write_to_file(doc.getvalue(), outfile)

def __iterate_list(did_list, tag, text, line, title):
    with tag('tr', klass='stripe'):
        with tag('th', klass="main", colspan='8'):
            text(title)
    for elem in did_list:
        error_exist = False
        if elem.err_msg:
            error_exist = True

        with tag('tr', klass='stripe'):
            with tag('td', klass="main"):
                text(elem.did)
            with tag('td', klass="main no_wrap"):
                text(elem.name)
            with tag('td', klass=MATCH_DICT[elem.c_sid], style='width:25px;'):
                text('')
            with tag('td', klass=MATCH_DICT[elem.c_did], style='width:25px;'):
                text('')
            with tag('td', klass=MATCH_DICT[elem.c_size], style='width:25px;'):
                text('')
            with tag('td', klass="main"):
                with tag('table', klass='borderless'):
                    for scal_val in elem.scal_val_list:
                        with tag('tr'):
                            with tag('td', klass="main", id='scal_val'):
                                text(scal_val)
            with tag('td', klass=ERROR_DICT[error_exist]):
                text(elem.err_msg)
            with tag('td', klass="main"):
                text(elem.payload)


def __extract_payload(did_dict_with_result):
    payload = dict()
    if 'payload' in did_dict_with_result:
        payload = did_dict_with_result['payload']
    else:
        logging.fatal('No payload to Scale!!')
    return payload


def __create_key(did_dict_with_result):
    did_id = did_dict_with_result['ID']
    key = '22' + did_id
    return key


def scale_data(did_dict_with_result, sddb_resp_item_dict_inp): #pylint: disable=too-many-branches
    '''
    Input  - Takes a dictionary where we store the results from previous test runs
    Output - Same dictionary as in input. Now with added scaled data.

    For each DID which were tested, look up response items. Scale payload using formula in
    Response Item.
    '''
    formatted_result_value_list = list()

    try: #pylint: disable=too-many-nested-blocks
        payload = __extract_payload(did_dict_with_result)
        key = __create_key(did_dict_with_result)

        logging.debug('Payload = %s (Length = %s)', payload,
                      did_dict_with_result['payload_length'])

        # For each response item for the dict
        for resp_item in sddb_resp_item_dict_inp[key]:
            sub_payload = SE22.get_sub_payload(payload, resp_item['Offset'], resp_item['Size'])
            logging.debug('==================================')
            logging.debug('Name = %s', resp_item['Name'])
            logging.debug('----------------------------------')
            logging.debug('Payload = %s (Sub payload = %s (Offset = %s Size = %s))', payload,
                          sub_payload, resp_item['Offset'], resp_item['Size'])

            # Has compare value
            if 'CompareValue' in resp_item:
                compare_value = resp_item['CompareValue']
                logging.debug("Compare_value: %s", compare_value)

                try:
                    scaled_value = SE22.get_scaled_value(resp_item, sub_payload)
                    logging.debug("Scaled_value: %s", str(scaled_value))

                    if SE22.compare(scaled_value, compare_value):
                        logging.debug('Equal! Comparing %s with %s', str(compare_value),
                                      scaled_value)
                        # Adding name for easier readability
                        formatted_result_value = resp_item['Name'] + ': '
                        # When comparison value exist, the unit is usually something like:
                        # on/off, open/close, True/False
                        # Then we just add that value and not the comparison value.
                        if 'Unit' in resp_item:
                            formatted_result_value += resp_item['Unit']
                        # Adding scaled value if no Unit value exists
                        else:
                            formatted_result_value += str(scaled_value)
                        formatted_result_value_list.append(formatted_result_value)
                        did_dict_with_result['Formula'] = resp_item['Formula']
                except RuntimeError as runtime_error:
                    logging.fatal(runtime_error)
                except SyntaxError as syntax_error:
                    logging.fatal(syntax_error)
            # Has no compare value
            else:
                logging.debug('No compare value!')
                # Adding name for easier readability
                formatted_result_value = resp_item['Name'] + ' = '
                # Adding scaled data to the result string
                try:
                    formatted_result_value += SE22.get_scaled_value_with_unit(resp_item,
                                                                              sub_payload)
                except OverflowError as overflow_error:
                    logging.error(overflow_error)
                formatted_result_value_list.append(formatted_result_value)
                did_dict_with_result['Formula'] = resp_item['Formula']
    except RuntimeError as runtime_error:
        logging.fatal(runtime_error)
    except KeyError as key_error:
        logging.fatal(key_error)

    if formatted_result_value_list:
        did_dict_with_result['formatted_result_value'] = formatted_result_value_list
    return did_dict_with_result


def write_to_file(content, outfile):
    ''' Write content to outfile '''
    with open(outfile, 'w') as file:
        file.write(str(content))


def create_folder(folder):
    """If folder does not exisists, then it will be created."""
    if not os.path.isdir(folder):
        os.makedirs(folder)


def write_data(head, data, mode, string_bool=True):
    ''' Write content to outfile '''
    output_folder = os.path.join(os.path.abspath(os.getcwd()), parammod.OUTPUT_FOLDER)

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    new_path = os.path.join(output_folder, parammod.OUTPUT_TESTRUN_DATA_FN)
    with open(new_path, mode) as file:
        head = "\n" + head + " = "
        if string_bool:
            data_str = '"' + str(data) + '"'
        else:
            data_str = str(data)
        file.write(head + data_str)


def get_did_eda0(can_p, sddb_resp_item_dict_eda0):
    '''  Returns content from DID EDA0 Request '''
    did_dict = SE22.get_did_info(can_p, COMPLETE_ECU_PART_SERIAL_NRS_DID,
                                 conf.response_timeout)
    message = did_dict.get('payload', '')

    eda0_dict = SUPPORT_TEST.get_combined_did_eda0(message, sddb_resp_item_dict_eda0)
    return eda0_dict


def get_current_time():
    '''
    Returns current time
    This also exist in support_test_odtb2. Should use that one instead when the python path
    issue is solved.
    '''
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time


def write_testrun_data(eda0_dict, can_p):
    '''
    Write data to file
    '''

    # Create output folder if it doesn't exist
    create_folder(parammod.OUTPUT_FOLDER)
    # File used to write the data in. This data is used by the logs_to_html script.
    write_data(parammod.GIT_HASH, get_git_hash(can_p), 'w+')
    write_data('eda0_dict', eda0_dict, 'a+', False)


def did_checker(dids, can_p, response_item_dict, pass_or_fail_counter_dict, max_no_of_dids):
    result_list = list()
    did_counter = 1 # Used when we don't want to run through all tests

    # For each line in dictionary_from_file, store result
    for did_dict_from_file_values in dids:
        logging.debug('DID counter: %s', str(did_counter))

        did_id = did_dict_from_file_values['ID']
        did_dict_with_result = copy.deepcopy(did_dict_from_file_values)

        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict_from_service_22 = SE22.get_did_info(can_p, did_id, conf.response_timeout)

        # Copy info to the did_dict_with_result dictionary from the did_dict
        did_dict_with_result = SE22.adding_info(did_dict_from_service_22, did_dict_with_result)

        # Adding scaled data to the dictionary with the result
        if 'error_message' not in did_dict_with_result:
            did_dict_with_result = scale_data(did_dict_with_result, response_item_dict)

        # Summarizing the result
        info_entry, pass_or_fail_counter_dict = SE22.summarize_result(did_dict_with_result,
                                                                      pass_or_fail_counter_dict,
                                                                      did_id)
        # Add the results
        result_list.append(info_entry)

        if did_counter >= max_no_of_dids and max_no_of_dids != -1:
            break

        did_counter += 1

    return result_list


def run_main_part(parsed_sddb): # pylint: disable=too-many-locals
    '''
    Common part regardless if you execute from main or execute
    '''
    try:
        can_p: CanParam = {
            "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
            "send" : "HvbmdpToHvbmUdsDiagRequestFrame",
            "receive" : "HvbmToHvbmdpUdsDiagResponseFrame",
            "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }

        #Read YML parameter for current function (get it from stack)
        logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

        logging.info("\nTestcase start: %s", datetime.now())
        starttime = time.time()
        logging.info("Time: %s \n", time.time())

        logging.debug('\nPrecondition')
        # read VBF param when testscript is s started, if empty take default param
        SSBL.get_vbf_files_wo_argv()
        result = PREC.precondition(can_p, conf.script_timeout)

        pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                     "requestOutOfRange (31)": 0}

        logging.debug('\nReading eda0')
        eda0_dict = get_did_eda0(can_p, parsed_sddb['response_item_dict'])
        write_testrun_data(eda0_dict, can_p)

        logging.debug('\nTesting application DIDs')
        appl_list = did_checker(parsed_sddb['app_dict'].values(), can_p,
                                parsed_sddb['response_item_dict'],
                                pass_or_fail_counter_dict,
                                conf.max_no_of_dids
                                )

        # Clean underscore (Replace with whitespace) from SDDB file part number
        sddb_cleaned_part_number = parsed_sddb['app_diag_part_num'].replace('_', ' ')

        logging.debug('\nComparing the part numbers')
        part_nbr_match, part_nbr_match_msg = comp_part_nbrs(can_p, sddb_cleaned_part_number)

        #pbl_list = list()
        logging.debug('\nChange to programming session (02) - Enter PBL')
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=1)
        logging.debug('\nTesting PBL DIDs')
        pbl_list = did_checker(parsed_sddb['pbl_dict'].values(), can_p,
                               parsed_sddb['response_item_dict'],
                               pass_or_fail_counter_dict,
                               -1)

        logging.debug('\nDL and activate SBL')
        result = result and SSBL.sbl_dl_activation(can_p, 1, "DL and activate SBL")
        logging.debug('\nTesting SBL DIDs')
        sbl_list = did_checker(parsed_sddb['sbl_dict'].values(), can_p,
                               parsed_sddb['response_item_dict'],
                               pass_or_fail_counter_dict,
                               -1)

        logging.debug('\nGenerating HTML')
        generate_html(pbl_list, sbl_list, appl_list, pass_or_fail_counter_dict, part_nbr_match,
                      part_nbr_match_msg, eda0_dict)

        ############################################
        # postCondition
        ############################################
        logging.debug('\nPostcondition')
        POST.postcondition(can_p, starttime, result, use_analytics=False)
    except Exception as _: # pylint: disable=broad-except
        logging.error(traceback.format_exc())
        generate_error_page(str(traceback.format_exc()))


def execute(parsed_sddb):
    '''
    When executed from other pythonscript
    '''
    run_main_part(parsed_sddb)


def main():
    '''
    Main (run)
    '''

    # Setup logging. We don't want this script to generate to many rows in the log-file
    # so we set it on WARN.
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.WARN)

    parsed_sddb = {'pbl_dict': sddb_pbl_did_dict_imp,
                   'pbl_diag_part_num': pbl_diag_part_num_imp,
                   'sbl_dict': sddb_sbl_did_dict_imp,
                   'sbl_diag_part_num': sbl_diag_part_num_imp,
                   'app_dict': sddb_app_did_dict_imp,
                   'app_diag_part_num': app_diag_part_num_imp,
                   'response_item_dict': sddb_resp_item_dict_imp
                   }
    run_main_part(parsed_sddb)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    #ARGS = parse_some_args()
    main()
