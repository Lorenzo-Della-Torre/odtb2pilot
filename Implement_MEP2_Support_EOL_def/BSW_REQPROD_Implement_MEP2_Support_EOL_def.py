# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   fjansso8 (Fredrik Jansson)
# date:     2019-10-09
# version:  1.0
# reqprod:

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC route guide client."""

from datetime import datetime
import time
import logging
import sys
from collections import namedtuple
from yattag import Doc
from support_test_odtb2 import Support_test_ODTB2
import ODTB_conf
import parameters as parammod
import BSW_REQPROD_Implement_MEP2_Support_EOL_def_conf as conf
from output.did_dict import sddb_resp_item_dict
from output.did_dict import sddb_app_did_dict
from output.did_dict import app_diag_part_num
from support_can import Support_CAN



SC = Support_CAN()
SUPPORT_TEST = Support_test_ODTB2()

# The different status the test run can have
PASSED_STATUS = 'PASSED'
FAILED_STATUS = 'FAILED'

Infoentry = namedtuple('Infoentry', 'did name c_sid c_did c_size scal_val_list err_msg payload')

def pp_frame_info(msg, did_struct, frame, size, sid):
    ''' Pretty print the frame information '''

    frame_info = '\n\n%s\n----------------------------------------' % (msg)
    frame_info += '\n  Frame ---> ' + frame
    frame_info += '\n  Size ----> ' + size
    frame_info += '\n  SID -----> ' + sid
    frame_info += '\n  DID -----> ' + did_struct['did']
    frame_info += '\n  Payload -> ' + did_struct['payload']
    frame_info += '\n  Length --> ' + str(did_struct['payload_length'])

    if 'error_message' in did_struct:
        frame_info += '\n  ErrorMsg > ' + did_struct['error_message']
        logging.debug('%s%s', '  ErrorMsg > ', did_struct['error_message'])

    frame_info += '\n----------------------------------------\n'
    return frame_info


def pp_did_info(did_dict, result_dict):
    '''
    Pretty print the DID info (stored in a dictionary) and the result (Passed/failed)
    '''

    did_info = '\n-------------------------------------------------'
    did_info += '\n  Name:          ' + did_dict['Name']
    did_info += '\n  ID:            ' + did_dict['ID']
    did_info += '\n  Expected size: ' + did_dict['Size']

    if 'payload' in did_dict:
        did_info += '\n  Actual size:   ' + str(did_dict['payload_length'])
        did_info += '\n  Payload        ' + did_dict['payload']
    if 'error_message' in did_dict:
        did_info += '\n  Error message: ' + did_dict['error_message']
    did_info += '\n  ' + str(result_dict)
    did_info += '\n-------------------------------------------------'
    return did_info


def read_response(network_stub, m_send, m_receive_extra, did, can_send="", can_rec="",
                  can_nspace=""):
    ''' Reads the response from the service 22 request
        Returns the DID info stored in a dictionary '''
    SC.clear_old_CF_frames()

    logging.debug("Clear old messages")
    SC.clear_all_can_frames()
    SC.clear_all_can_messages()

    step_no = 'Test service 22 using DID ' + did
    purpose = 'Send DID and verify response'
    SUPPORT_TEST.print_test_purpose(step_no, purpose)

    # wait for messages
    # define answer to expect
    logging.debug("Build answer can_frames to receive")
    can_answer = SC.can_receive(m_send, m_receive_extra)
    logging.debug('%s%s', 'can_frames to receive', can_answer)
    # message to send
    logging.debug('To send:   [%s, %s, %s]', time.time(), can_send, m_send.upper())
    SC.t_send_signal_CAN_MF(network_stub, can_send, can_rec, can_nspace, m_send, True, 0x00)
    # Wait timeout for getting subscribed data
    timeout = conf.response_timeout #0.5 #5 # wait for message to arrive
    time.sleep(timeout)
    SC.clear_all_can_messages()

    did_struct = {}

    # Default message_status = 0 - single frame message
    message_status = 0
    mf_cf_count = 0
    mf_mess_size = 0
    temp_message = [] #empty list as default

    sid_test = False
    for i in SC.can_frames[can_rec]:
        if message_status == 0:
            det_mf = int(i[2][0:1], 16)
            if det_mf == 0:
                # Single frame message, add frame as message
                frame = i[2]
                size = frame[1:2]
                sid = frame[2:4]

                # Verify SID, should be 62 (Service 22 + 40)
                payload = str()
                if sid in ('62', '7F'):
                    sid_test = True
                    did = frame[4:8]
                    index = 8+(int(size)-3)*2
                    payload = frame[8:index]

                    # Error code received
                    if sid == '7F':
                        did = ''
                        index = 8+(int(size)-3)*2
                        payload = frame[6:index]
                        decoded_7f = "Negative response: " + SUPPORT_TEST.PP_CAN_NRC(payload)
                        did_struct['error_message'] = decoded_7f
                else:
                    did_struct['error_message'] = 'Wrong SID. 62 expected, received %s' % (sid)

                did_struct['did'] = did
                did_struct['payload'] = payload
                did_struct['payload_length'] = int(len(payload)/2)

                temp_message = i
                temp_message[2] = payload

                logging.debug(pp_frame_info('Single frame message received', did_struct, frame,
                                            size, sid))

            elif det_mf == 1:
                # First frame of MF-message, change to status=2 consective frames to follow
                message_status = 2
                mf_cf_count = 32
                # get size of message to receive:
                mf_mess_size = int(i[2][1:4], 16)

                frame = i[2]
                size = frame[1:4]
                sid = frame[4:6]
                did = frame[6:10]
                payload = frame[10:]

                # Verify SID, should be 62 (Service 22 + 40)
                if sid == '62':
                    sid_test = True

                did_struct['did'] = did
                did_struct['payload'] = payload
                did_struct['payload_length'] = int(len(payload)/2)

                logging.debug(pp_frame_info('First multi frame received', did_struct, frame, size,
                                            sid))

                temp_message = i[:]
                temp_message[2] = payload

                mf_size_remain = mf_mess_size - 6
                mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
            elif det_mf == 2:
                logging.warning("Consecutive frame not expected without FC")
            elif det_mf == 3:
                if can_rec not in SC.can_mf_send:
                    logging.warning("Flow control received - not expected")
                    logging.warning('%s%s', "Can-frame:  ", i)
                else:
                    logging.debug('%s%s', "MF sent: ", SC.can_mf_send)
                    logging.debug('%s%s', "FC expected for ", can_rec)
            else:
                logging.warning("Reserved CAN-header")
        elif message_status == 1:
            logging.warning("Message not expected")
        elif message_status == 2:
            if mf_size_remain > 7:
                temp_message[2] = temp_message[2] + i[2][2:16]
                logging.debug('%s%s', 'Consecutive frame received ----->', i[2][2:16])

                did_struct['payload'] += i[2][2:16]
                did_struct['payload_length'] += int(len(i[2][2:16])/2)

                mf_size_remain -= 7
                mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
            else:
                temp_message[2] = temp_message[2] + i[2][2:(2+mf_size_remain*2)]
                logging.debug('%s%s', 'Last frame received ----->', i[2][2:(2+mf_size_remain*2)])
                did_struct['payload'] += i[2][2:(2+mf_size_remain*2)]
                did_struct['payload_length'] += int(len(i[2][2:(2+mf_size_remain*2)])/2)
                mf_size_remain = 0

        else:
            logging.warning("Unexpected message status in can_frames")
    # don't add empty messages
    if not temp_message:
        SC.can_messages[can_rec].append(list(temp_message))

    did_struct['sid_test'] = sid_test
    return did_struct


def precondition(network_stub, can_send, can_receive, can_namespace):
    '''
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    '''

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(network_stub, "EcmFront1NMFr", "Front1CANCfg0",
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)

    timeout = conf.script_timeout
    SC.subscribe_signal(network_stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(network_stub, can_receive, can_send, can_namespace, timeout)

    step_0(network_stub, can_send, can_receive, can_namespace)


def step_0(network_stub, can_send, can_receive, can_namespace):
    ''' Teststep 0: Complete ECU Part/Serial Number(s) '''
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    SUPPORT_TEST.teststep(network_stub, can_m_send, can_mr_extra, can_send, can_receive,
                          can_namespace, stepno, purpose, timeout, min_no_messages,
                          max_no_messages)
    logging.debug(SUPPORT_TEST.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2]))


def service_22(network_stub, can_send, can_receive, can_namespace, did):
    '''
    Used for testing the Service 22
    Returns the DID info stored in a dictionary
    '''

    # Make it a byte string
    hex_did = bytearray.fromhex(did[0:2]) + bytearray.fromhex(did[2:4])

    # Building message
    can_m_send = SC.can_m_send("ReadDataByIdentifier", hex_did, '')
    can_mr_extra = ''

    did_dict = read_response(network_stub, can_m_send, can_mr_extra, did, can_send, can_receive,
                             can_namespace)
    return did_dict


#def copy_dict_info(did_dict, data_identifier):
def adding_info(copy_from_dict, dictionary):
    '''
    Copies some information from one dictionary to another
    Returns the dictionary
    '''
    if 'payload' in copy_from_dict:
        dictionary['payload'] = copy_from_dict['payload']
        dictionary['payload_length'] = copy_from_dict['payload_length']
    if 'error_message' in copy_from_dict:
        dictionary['error_message'] = copy_from_dict['error_message']
    if 'sid_test' in copy_from_dict:
        dictionary['sid_test'] = copy_from_dict['sid_test']
    if 'did_in_response_test' in copy_from_dict:
        dictionary['did_in_response_test'] = copy_from_dict['did_in_response_test']
    if 'did' in copy_from_dict:
        dictionary['did'] = copy_from_dict['did']
    return dictionary

def summarize_result(did_dict, pass_or_fail_counter_dict, did_id):
    '''
    Comparing the expected size with the actual size and
    compares the received DID value with the expected DID value.
    Adding how the tests went to the did dictionary and adds one 'Failed' or 'Passed'
    to the result dictionary.
    '''
    c_did = False
    c_sid = False
    c_size = False

    if 'sid_test' in did_dict and did_dict['sid_test']:
        c_sid = True
    # No error message yet
    if 'error_message' not in did_dict:
        # Verifying DID in response
        if 'did' in did_dict and did_id in did_dict['did']:
            c_did = True
        # Verifying payload length
        if ('payload_length' in did_dict and int(did_dict['Size']) ==
                did_dict['payload_length']):
            pass_or_fail_counter_dict['Passed'] += 1
            c_size = True
        # Wrong payload length
        else:
            if 'payload_length' in did_dict:
                did_dict['error_message'] = 'Size wrong. Expected %s but was %s' % (
                    did_dict['Size'], str(did_dict['payload_length']))
            else:
                did_dict['error_message'] = 'No payload?'
            pass_or_fail_counter_dict['Failed'] += 1

    # Already an error message
    else:
        pass_or_fail_counter_dict['Failed'] += 1
        if 'Negative response: conditionsNotCorrect (22)' in did_dict['error_message']:
            pass_or_fail_counter_dict['conditionsNotCorrect (22)'] += 1
        if 'Negative response: requestOutOfRange (31)' in did_dict['error_message']:
            pass_or_fail_counter_dict['requestOutOfRange (31)'] += 1

    did = did_dict['ID']
    name = did_dict['Name']
    scal_val_list = list()
    if 'formatted_result_value' in did_dict:
        for formatted_result_value in did_dict['formatted_result_value']:
            scal_val_list.append(formatted_result_value)

    err_msg = str()
    if 'error_message' in did_dict:
        err_msg = did_dict['error_message']

    pp_payload = str()
    if 'payload' in did_dict:
        payload = did_dict['payload']
        pp_payload = 'Payload: ' + add_ws_every_nth_char(payload, 16)

    formula = str()
    if 'Formula' in did_dict:
        formula = did_dict['Formula']

    data = 'Formula = [' + formula + '] ' + pp_payload

    info_entry = Infoentry(did=did, name=name, c_sid=c_sid, c_did=c_did, c_size=c_size,
                           scal_val_list=scal_val_list, err_msg=err_msg, payload=data)
    return info_entry, pass_or_fail_counter_dict


def comp_part_nbrs(network_stub, can_send, can_receive, can_namespace,
                   sddb_cleaned_part_number):
    '''
    Testing so that the Application Diagnostic Database Part Number is correct (matching)
    It is stored in DID F120 and we match with the sddb part number
    '''
    message = str()
    match = False
    try:
        PART_NUMBER_STRING_LENGTH = 14

        # Get diagnostic part number from ECU (using service 22)
        did_dict = service_22(network_stub, can_send, can_receive, can_namespace,
                              parammod.DID_TO_GET_PART_NUMBER)
        if 'payload' in did_dict:
            ecu_diag_part_num_full = did_dict['payload']

            # Checking length
            if len(ecu_diag_part_num_full) != PART_NUMBER_STRING_LENGTH:
                raise RuntimeError('ECU Diagnostic Part Number is to short!')

            # Extracting the last part of diagnostic part nummer (AA, AB, ...)
            ecu_diag_part_num_version_hex = ecu_diag_part_num_full[8:PART_NUMBER_STRING_LENGTH]
            # Decoding from hex to ASCII
            ecu_diag_part_num_version = bytearray.fromhex(ecu_diag_part_num_version_hex).decode()
            # Putting it back together to complete string again
            ecu_diag_part_num_full = ecu_diag_part_num_full[0:8] + ecu_diag_part_num_version

            # Comparing part numbers
            if sddb_cleaned_part_number == ecu_diag_part_num_full:
                message = ('Diagnostic part number is matching! Expected ' +
                           sddb_cleaned_part_number + ', and got ' + ecu_diag_part_num_full)
                match = True
            else:
                message = (
                    'Diagnostic part number is NOT matching! Expected ' +
                    sddb_cleaned_part_number + ', but got ' + ecu_diag_part_num_full)

            logging.debug('-------------------------------------------------')
            logging.debug(message)
            logging.debug(did_dict)
            logging.debug('-------------------------------------------------')
    except RuntimeError as runtime_error:
        message = runtime_error
    return match, message

def get_sub_payload(payload, offset, size):
    '''
    Returns the chosen sub part of the payload based on the offset and size
    Payload, offset and size is hexadecimal (16 base)
    Every byte is two characters (multiplying with two)
    '''
    start = int(offset, 16)*2
    end = start+(int(size, 16)*2)

    # Making sure the end is inside the payload
    if len(payload) >= end:
        sub_payload = payload[start:end]
    else:
        raise RuntimeError('Payload is to short!')
    return sub_payload


def populate_formula(formula, value, size):
    '''
    Replaces X in a formula with a value.
    Input:  formula = Example: X*1
            value   = Any value
            size    = size of bitmask/payload when it was in hex

    Output: The formula with X replaced.

    If there is "bitwise AND" in the formula;
    - '&amp;' is replaced with '&'.
    - '0x' is removed from the hex value.
    - The bitmask is translated from hex to decimal

    Example 1:  Input:  Formula: X/100
                        Value: 56
                        Size: 1 (doesn't matter in this example)
                Output: 56/100

    Example 2:  Input:  Formula: X&amp;0xFFFE/2
                        Value: 56
                        Size: 2 (doesn't matter in this example)
                Output: (56 & 65534)/2
    '''

    # Check for "Bitwise AND"
    # Removing characters we don't want
    formula = formula.replace('&amp;0x', '&0x')
    and_pos_hex = formula.find('&0x')
    and_pos_bit = formula.find('&0b')

    # It is a bitwise-and HEX
    if and_pos_hex != -1:
        logging.debug('Formula = %s and_pos_hex = %s', formula, and_pos_hex)
        hex_value = formula[and_pos_hex + 1:and_pos_hex + 3 + int(size) * 2]
        formula = formula.replace(hex_value, str(int(hex_value, 16)) + ')')
        populated_formula = formula.replace('X', '(' +str(value))
    # It is a bitwise-and bit-mapping
    elif and_pos_bit != -1:
        logging.debug('Formula = %s and_pos_bit = %s', formula, and_pos_bit)
        bit_value = bin(value)
        populated_formula = formula.replace('X', '(' +str(bit_value) + ')')
    else:
        logging.debug('Value = %s', value)
        populated_formula = formula.replace('X', str(value))
    return populated_formula


def clean_compare_value_hex(compare_value):
    '''
    Removing '=0x' from compare value or '='
    '''
    cleaned_compare_value = compare_value.replace('=0x', '')
    return cleaned_compare_value


def get_scaled_value(resp_item, sub_payload):
    '''
    Input - Response Item with at least formula
            Value which should converted from raw data
    Returns the string with converted data
    '''
    int_value = int(sub_payload, 16)
    if 'Formula' in resp_item:
        size = resp_item['Size']
        formula = resp_item['Formula']
        logging.debug('Formula = %s', formula)
        populated_formula = populate_formula(formula, int_value, size)
        logging.debug('Populated formula = %s', populated_formula)

        try:
            result = str(eval(populated_formula))
            int_result = int(float(result))
            logging.debug('Formula = %s => %s', formula, result)
            return int_result
        except RuntimeError as runtime_error:
            logging.fatal(runtime_error)
            raise RuntimeError('Failed parsing formula')
        except SyntaxError as syntax_error:
            logging.fatal(syntax_error)
            raise SyntaxError('Failed parsing formula')
    else:
        # If we reach this, then there is no formula. That is an issue, formula should be mandatory
        logging.fatal('No formula!')
        raise RuntimeError('No formula!')


def get_scaled_value_with_unit(resp_item, sub_payload):
    '''
    Input - Response Item with at least formula
            sub_payload which should converted from raw data
    Returns the string with converted data
    '''
    try:
        scaled_value = get_scaled_value(resp_item, sub_payload)
        unit = str()
        # Extracts the unit value (if it exists)
        if 'Unit' in resp_item:
            unit = resp_item['Unit']
        return str(scaled_value) + ' ' + unit
    except RuntimeError as runtime_error:
        logging.fatal(runtime_error)
        return 'Runtime error'
    except SyntaxError as syntax_error:
        logging.fatal(syntax_error)
        return 'Syntax error'


def compare(scaled_value, compare_value):
    '''
    Comparing two values. Returns boolean.
    If the compare value contains '=', then we add an '='
    Example:    Scaled value:    0x40
                Compare value:  =0x40
                Result: eval('0x40==0x40') which gives True
    '''
    improved_compare_value = compare_value
    result = False # If not True, then default is False
    # To be able to compare we need to change '=' to '=='
    if '=' in compare_value:
        improved_compare_value = compare_value.replace('=', '==')
    try:
        result = eval(str(scaled_value) + str(improved_compare_value))
    except NameError as nameError:
        logging.error(nameError)
    return result


def scale_data(did_dict_with_result):
    '''
    Input  - Takes a dictionary where we store the results from previous test runs
    Output - Same dictionary as in input. Now with added scaled data.

    For each DID which were tested, look up response items. Scale payload using formula in
    Response Item.
    '''
    formatted_result_value_list = list()

    try:
        payload = dict()
        if 'payload' in did_dict_with_result:
            payload = did_dict_with_result['payload']
        else:
            logging.fatal('No payload to Scale!!')

        did_id = did_dict_with_result['ID']
        key = '22' + did_id
        logging.debug('Payload = %s (Length = %s)', payload,
                      did_dict_with_result['payload_length'])

        # For each response item for the dict
        for resp_item in sddb_resp_item_dict[key]:
            sub_payload = get_sub_payload(payload, resp_item['Offset'], resp_item['Size'])
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
                    scaled_value = get_scaled_value(resp_item, sub_payload)
                    logging.debug("Scaled_value: %s", str(scaled_value))

                    if compare(scaled_value, compare_value):
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
                formatted_result_value += get_scaled_value_with_unit(resp_item, sub_payload)
                formatted_result_value_list.append(formatted_result_value)
                did_dict_with_result['Formula'] = resp_item['Formula']
    except RuntimeError as runtime_error:
        logging.fatal(runtime_error)
    except KeyError as key_error:
        logging.fatal(key_error)

    if formatted_result_value_list:
        did_dict_with_result['formatted_result_value'] = formatted_result_value_list
    return did_dict_with_result

def add_ws_every_nth_char(payload_in, nth):
    '''
    Adds whitespace every n:th character to the supplied string
    '''
    result = " ".join(payload_in[i:i+nth] for i in range(0, len(payload_in), nth))
    return result


def generate_html2(outfile, result_list, pass_or_fail_counter_dict, part_nbr_match,
                   part_nbr_match_msg):
    """Create html table based on the dict"""
    # Used for for selecting style class
    MATCH_DICT = {True:'match', False:'no_match'}
    ERROR_DICT = {True:'error', False:''}

    HEADING_LIST = ['DID', 'Name', 'Correct SID', 'Correct DID', 'Correct size', 'Scaled values',
                    'Error Message', 'Payload']
    doc, tag, text, line = Doc().ttl()

    style = ("table#main {border-collapse: collapse; width: 100%;}"
             "table#main, th, td {border: 1px solid black;}"
             "th, td {text-align: left;}"
             "th {background-color: lightgrey; padding: 8px;}"
             "td {padding: 3px;}"
             "tr:nth-child(even) {background-color: #e3e3e3;}"
             "a {color:black; text-decoration: none;}"
             "#header, #match, #no_match, #passed_fail {height: 100px;"
             "line-height: 100px; width: 1000px; text-align:center; vertical-align: middle;"
             "border:1px black solid; margin:30px;}"
             "#header {font-size: 50px; background-color: lightgrey;}"
             "#match, .match {background-color: #94f7a2}"
             "#no_match, .no_match, .error {background-color: #ff9ea6}"
             "#no_match, .no_match, #passed_fail, #match, .match {font-size: 25px;}"
             "#passed_fail {background-color: #ffdea6}"
             ".borderless, #scal_val {border-style: none; border: 0px;}"
             ".no_wrap, #scal_val {white-space: nowrap;}"
             "")

    with tag('html'):
        with tag('head'):
            with tag('style'):
                text(style)
        with tag('body'):
            with tag('div', id='header'): # Header box
                text('Summary Report: Sending all DIDs Test')
            with tag('div', id=MATCH_DICT[part_nbr_match]): # Match box
                text(part_nbr_match_msg)
            with tag('div', id='passed_fail'): # Passed/failed counter box
                text(str(pass_or_fail_counter_dict))
            with tag('table', id='main'):
                with tag('tr'):
                    for heading in HEADING_LIST:
                        line('th', heading)
                for elem in result_list:
                    error_exist = False
                    if elem.err_msg:
                        error_exist = True

                    with tag('tr'):
                        line('td', elem.did)
                        line('td', elem.name, klass='no_wrap')
                        line('td', '', klass=MATCH_DICT[elem.c_sid])
                        line('td', '', klass=MATCH_DICT[elem.c_did])
                        line('td', '', klass=MATCH_DICT[elem.c_size])
                        with tag('td'):
                            with tag('table', klass='borderless'):
                                for scal_val in elem.scal_val_list:
                                    with tag('tr'):
                                        line('td', scal_val, id='scal_val')
                        line('td', elem.err_msg, klass=ERROR_DICT[error_exist])
                        line('td', elem.payload)
            text(get_current_time())
    write_to_file(doc.getvalue(), outfile)

def get_current_time():
    ''' Returns current time '''
    now = datetime.now()
    current_time = now.strftime("Generated %Y-%m-%d %H:%M:%S")
    return current_time

def write_to_file(content, outfile):
    '''Write content to outfile'''
    with open(outfile, 'w') as file:
        file.write(str(content))

def run():
    ''' run '''
    # Where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)
    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    # Setup logging
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    logging.info('%s%s', 'Testcase start: ', datetime.now())
    starttime = time.time()
    logging.info('%s%s', 'time ', str(time.time()))

    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)


    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()

    did_counter = 1 # Used when we don't want to run through all tests
    # For each line in dictionary_from_file, store result
    for did_dict_from_file_values in sddb_app_did_dict.values():
        logging.debug('DID counter: %s', str(did_counter))

        did_id = did_dict_from_file_values['ID']

        did_dict_with_result = did_dict_from_file_values

        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict_from_service_22 = service_22(network_stub, can_send, can_receive,
                                              can_namespace, did_id)

        # Copy info to the did_dict_with_result dictionary from the did_dict
        did_dict_with_result = adding_info(did_dict_from_service_22, did_dict_with_result)

        # Adding scaled data to the dictionary with the result
        if 'error_message' not in did_dict_with_result:
            did_dict_with_result = scale_data(did_dict_with_result)

        # Summarizing the result
        info_entry, pass_or_fail_counter_dict = summarize_result(did_dict_with_result,
                                                                 pass_or_fail_counter_dict, did_id)
        # Add the results
        result_list.append(info_entry)

        if did_counter >= conf.max_no_of_dids:
            break

        did_counter += 1

    # Clean underscore (Replace with whitespace) from SDDB file part number
    sddb_cleaned_part_number = app_diag_part_num.replace('_', ' ')

    # Comparing the part numbers
    part_nbr_match, part_nbr_match_msg = comp_part_nbrs(network_stub, can_send, can_receive,
                                                        can_namespace, sddb_cleaned_part_number)

    file_name = "result_report_%s.html" % app_diag_part_num
    generate_html2(file_name, result_list, pass_or_fail_counter_dict, part_nbr_match,
                   part_nbr_match_msg)

    ############################################
    # postCondition
    ############################################
    logging.info('\nTime: %s\n Testcase end: %s', str(time.time()), str(datetime.now()))
    logging.info('%s%s', "Time needed for testrun (seconds): ", str(int(time.time() - starttime)))
    logging.info("Do cleanup now...\n Stop all periodic signals sent")

    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info('%s%s', 'Test cleanup end: ', str(datetime.now()))


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    #ARGS = parse_some_args()
    run()
