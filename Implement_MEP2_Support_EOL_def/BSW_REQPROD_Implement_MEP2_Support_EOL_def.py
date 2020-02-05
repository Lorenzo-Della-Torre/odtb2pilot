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
from html import HTML
from support_test_odtb2 import Support_test_ODTB2
import ODTB_conf
import parameters as parammod
from output.did_dict import sddb_resp_item_dict
from output.did_dict import sddb_app_did_dict
from output.did_dict import app_diag_part_num
from support_can import Support_CAN

SC = Support_CAN()
SUPPORT_TEST = Support_test_ODTB2()

# The different status the test run can have
PASSED_STATUS = 'PASSED'
FAILED_STATUS = 'FAILED'

COLOR_DICT = {PASSED_STATUS:'#94f7a2', FAILED_STATUS:'#ff9ea6'}

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
    timeout = 0.2 #0.5 #5 # wait for message to arrive
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

    timeout = 50   #seconds
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

    #dictionary = dict()
    #if 'Size' in copy_from_dict:
    #    dictionary['Size'] = copy_from_dict['Size']
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

def test_response(did_dict, pass_or_fail_counter_dict, did_id):
    '''
    Comparing the expected size with the actual size and
    compares the received DID value with the expected DID value.
    Adding how the tests went to the did dictionary and adds one 'Failed' or 'Passed'
    to the result dictionary
    '''
    # Comparing the expected size with the actual size
    if 'error_message' not in did_dict:
        # Verifying DID in response
        if 'did' in did_dict and did_id in did_dict['did']:
            did_dict['did_in_response_test'] = True
        else:
            did_dict['did_in_response_test'] = False

        # Verifying payload length
        if ('payload_length' in did_dict and int(did_dict['Size']) ==
                did_dict['payload_length']):
            pass_or_fail_counter_dict['Passed'] += 1
            did_dict['Result'] = True
            did_dict['length_test'] = True
        else:
            if 'payload_length' in did_dict:
                did_dict['error_message'] = 'Size wrong. Expected %s but was %s' % (
                    did_dict['Size'], str(did_dict['payload_length']))
            else:
                did_dict['error_message'] = 'No payload length?'

            did_dict['length_test'] = False
            pass_or_fail_counter_dict['Failed'] += 1
            did_dict['Result'] = False
    else:
        pass_or_fail_counter_dict['Failed'] += 1
        did_dict['Result'] = False

    return did_dict, pass_or_fail_counter_dict


def mark(did, value):
    '''
    Creates checked or unchecked checkbox string
    returns string
    '''
    msg = '[ ]'
    if value in did:
        if did[value]:
            msg = '[X]'
    return msg

def pp_result(dictionary, result_dict, diagnostic_part_number_match_message):
    ''' Pretty print the report '''
    result = '\n\n       L\n       E\n       N\n S  D  G\n I  I  T\n D  D  H   DID   Name'
    result += '\n------------------------------------------------------------------------------'

    for data_identifier_object in dictionary.values():
        sid_mark = mark(data_identifier_object, 'sid_test')
        did_mark = mark(data_identifier_object, 'did_in_response_test')
        length_mark = mark(data_identifier_object, 'length_test')
        did = '  ' + data_identifier_object['ID']
        name = '  ' + data_identifier_object['Name']

        payload = ''
        if 'payload' in data_identifier_object:
            payload = '                 Payload: ' + data_identifier_object['payload']

        error_message = ''
        if 'error_message' in data_identifier_object:
            error_message = '                 Error message: %s' % (
                data_identifier_object['error_message'])

        result += '\n' + sid_mark + did_mark + length_mark + did + name
        result += '\n' + payload

        if error_message != '':
            result += '\n' + error_message

        if 'formatted_result_value' in data_identifier_object:
            for formatted_result_value in data_identifier_object['formatted_result_value']:
                result += '\n                 ' + formatted_result_value

    result += '\n------------------------------------------------------------------------------'
    result += '\n %s\n\n %s' % (str(result_dict), diagnostic_part_number_match_message)
    result += '\n------------------------------------------------------------------------------'
    return result

def compare_part_numbers(network_stub, can_send, can_receive, can_namespace,
                         diagnostic_part_number):
    '''
    Testing so that the Application Diagnostic Database Part Number is correct (matching)
    It is stored in DID F120 and we match with the ssdb part number
    '''
    PART_NUMBER_STRING_LENGTH = 14

    # Get diagnostic part number from ECU (using service 22)
    did_dict = service_22(network_stub, can_send, can_receive, can_namespace,
                          parammod.DID_TO_GET_PART_NUMBER)
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

    # Clean underscore (Replace with whitespace) from SDDB file part number
    sddb_cleaned_part_number = diagnostic_part_number.replace('_', ' ')

    # Comparing part numbers
    if sddb_cleaned_part_number == ecu_diag_part_num_full:
        diagnostic_part_number_match_message = 'Diagnostic part number is matching!'
    else:
        diagnostic_part_number_match_message = (
            'Diagnostic part number is NOT matching! Expected ' +
            sddb_cleaned_part_number + ', but got ' + ecu_diag_part_num_full)

    logging.debug('-------------------------------------------------')
    logging.debug(diagnostic_part_number_match_message)
    logging.debug(did_dict)
    logging.debug('-------------------------------------------------')
    return diagnostic_part_number_match_message

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
    formula = formula.replace('&amp;0x', '&')
    formula = formula.replace('&0x', '&')
    and_pos = formula.find('&')
    if and_pos != -1:
        logging.debug('Formula = %s and_pos = %s', formula, and_pos)
        hex_value = formula[and_pos + 1:and_pos + 1 + int(size) * 2]
        formula = formula.replace(hex_value, str(int(hex_value, 16)) + ')')
        populated_formula = formula.replace('X', '(' +str(value))
    else:
        logging.debug('Value = %s', value)
        populated_formula = formula.replace('X', str(value))
    return populated_formula


def clean_compare_value(compare_value):
    '''
    Removing '=0x' from compare value
    '''
    cleaned_compare_value = compare_value.replace('=0x', '')
    return cleaned_compare_value


def get_scaled_value(resp_item, value):
    '''
    Input - Response Item with at least formula
            Value which should converted from raw data
    Returns the string with converted data
    '''
    int_value = int(value, 16)

    unit = str()
    # Extracts the unit value (if it exists)
    if 'Unit' in resp_item:
        unit = resp_item['Unit']

    if 'Formula' in resp_item:
        size = resp_item['Size']
        formula = resp_item['Formula']
        logging.debug('Formula = %s', formula)
        populated_formula = populate_formula(formula, int_value, size)
        logging.debug('Populated formula = %s', populated_formula)
        result = str(eval(populated_formula))
        logging.debug('Formula = %s => %s = [%s %s]', formula, result, result, unit)
        return result + ' ' + unit

    # If we reach this, then there is no formula. That is an issue, formula should be mandatory
    logging.debug('No formula!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    return 'No formula'

def scale_data(did_dict_with_result):
    '''
    Input  - Takes a dictionary where we store the results from previous test runs
    Output - Same dictionary as in input. Now with added scaled data.

    For each DID which were tested, look up response items. Scale payload using formula in
    Response Item.
    '''

    payload = did_dict_with_result['payload']
    did_id = did_dict_with_result['ID']
    key = '22' + did_id
    logging.debug('Payload = %s (Length = %s)', payload, did_dict_with_result['payload_length'])

    # For each response item for the dict
    formatted_result_value_list = list()
    for resp_item in sddb_resp_item_dict[key]:
        try:
            sub_payload = get_sub_payload(payload, resp_item['Offset'], resp_item['Size'])
            logging.debug('=================================================================')
            logging.debug('Name = %s', resp_item['Name'])
            logging.debug('--------------------')
            logging.debug('Payload = %s (Sub payload = %s (Offset = %s Size = %s))', payload,
                          sub_payload, resp_item['Offset'], resp_item['Size'])

            if 'CompareValue' in resp_item:
                compare_value = resp_item['CompareValue']
                compare_value = clean_compare_value(compare_value)
                if sub_payload != compare_value:
                    logging.debug('--------------------')
                    logging.debug('Has compare value! But no match. Comparing %s with %s',
                                  compare_value, sub_payload)
                    logging.debug('--------------------')
                else:
                    logging.debug('Equal! Comparing %s with %s', compare_value, sub_payload)
                    # Adding name for easier readability
                    formatted_result_value = resp_item['Name'] + ' = '
                    # Adding converted raw data
                    formatted_result_value += get_scaled_value(resp_item, sub_payload)
                    formatted_result_value_list.append(formatted_result_value)
            else:
                logging.debug('No compare value!')
                # Adding name for easier readability
                formatted_result_value = resp_item['Name'] + ' = '
                # Adding converted raw data
                formatted_result_value += get_scaled_value(resp_item, sub_payload)
                formatted_result_value_list.append(formatted_result_value)
        except RuntimeError as runtime_error:
            logging.fatal(runtime_error)

    if formatted_result_value_list:
        did_dict_with_result['formatted_result_value'] = formatted_result_value_list
    return did_dict_with_result

def add_ws_every_nth_char(payload_in, nth):
    '''
    Adds whitespace every n:th character to the supplied string
    '''
    result = " ".join(payload_in[i:i+nth] for i in range(0, len(payload_in), nth))
    return result

def generate_html(outfile, dictionary, pass_or_fail_counter_dict,
                  diagnostic_part_number_match_message):
    """Create html table based on the dict"""
    page = HTML()

    # Adding some style to this page ;)
    # Example:  Making every other row in a different colour
    #           Customizing padding
    #           Customizing links
    page.style("table#main {border-collapse: collapse;}"
               "table#main, th, td {border: 1px solid black;}"
               "th, td {text-align: left;}"
               "th {background-color: lightgrey; padding: 8px;}"
               "td {padding: 3px;}"
               "tr:nth-child(even) {background-color: #e3e3e3;}"
               "a {color:black; text-decoration: none;}"
               "#header, #match, #passed_fail{height: 100px;"
               "line-height: 100px; width: 1000px; text-align:center; vertical-align: middle;"
               "border:1px black solid; margin:30px;}"
               "#header {font-size: 50px; background-color: lightgrey;}"
               "#match {font-size: 25px; background-color: #ffdea6}"
               "#passed_fail {font-size: 25px; background-color: #ffdea6}"
               "")

    page.div('Summary Report: Sending all DIDs Test', id='header')
    page.div(diagnostic_part_number_match_message, id='match')
    page.div(str(pass_or_fail_counter_dict), id='passed_fail')

    table = page.table(id='main')
    # First row in table
    table_row = table.tr()
    # First column
    did_th = table_row.th()
    did_th('DID')
    # Next column
    table_row.th('Name')
    # Next column
    table_row.th('Correct SID')
    # Next column
    table_row.th('Correct DID')
    # Next column
    table_row.th('Correct size')
    # Next column
    table_row.th('Scaled values')
    # Next column
    table_row.th('Error Message')
    # Next column
    payload_th = table_row.th()
    payload_th('Payload')


    for data_identifier_object in dictionary.values():
        sid_test = False
        if 'sid_test' in data_identifier_object:
            sid_test = data_identifier_object['sid_test']

        did_in_response_test = False
        if 'did_in_response_test' in data_identifier_object:
            did_in_response_test = data_identifier_object['did_in_response_test']

        length_test = False
        if 'length_test' in data_identifier_object:
            length_test = data_identifier_object['length_test']

        did = data_identifier_object['ID']
        name = data_identifier_object['Name']

        table_row = table.tr()

        # First column
        table_row.td(did)

        # Second column (Name)
        name_td = table_row.td(style='white-space: nowrap;')
        name_td(name)

        # column (Result)
        result_td = table_row.td(style='white-space: nowrap;')
        if sid_test:
            result_td(style='background-color: ' + COLOR_DICT[PASSED_STATUS])
        else:
            result_td(style='background-color: ' + COLOR_DICT[FAILED_STATUS])

        # column (Result)
        result_td = table_row.td(style='white-space: nowrap;')
        if did_in_response_test:
            result_td(style='background-color: ' + COLOR_DICT[PASSED_STATUS])
        else:
            result_td(style='background-color: ' + COLOR_DICT[FAILED_STATUS])

        # column (Result)
        result_td = table_row.td(style='white-space: nowrap;')
        if length_test:
            result_td(style='background-color: ' + COLOR_DICT[PASSED_STATUS])
        else:
            result_td(style='background-color: ' + COLOR_DICT[FAILED_STATUS])

        table_cell = table_row.td()
        inner_table = table_cell.table(style='border-style: none; border: 0px;')
        if 'formatted_result_value' in data_identifier_object:
            for formatted_result_value in data_identifier_object['formatted_result_value']:
                inner_tr = inner_table.tr()
                inner_td = inner_tr.td(style='border-style: none; white-space: nowrap;')
                inner_td(formatted_result_value)
        else:
            inner_tr = inner_table.tr()
            inner_tr.td(style='border-style: none;')

        error_message = str()
        if 'error_message' in data_identifier_object:
            error_message = data_identifier_object['error_message']
            error_msg_td = table_row.td(style='white-space: nowrap; background-color:' +
                                        COLOR_DICT[FAILED_STATUS])
            error_msg_td(error_message)
        else:
            table_row.td()

        # Column - Payload
        payload = ''
        if 'payload' in data_identifier_object:
            payload = data_identifier_object['payload']
            payload = add_ws_every_nth_char(payload, 16)
        table_row.td(payload)

    now = datetime.now()
    current_time = now.strftime("Generated %Y-%m-%d %H:%M:%S")
    page.p(current_time)
    write_to_file(page, outfile)

def write_to_file(content, outfile):
    """Write content to outfile"""
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

    # Testing so that the Application Diagnostic Database Part Number is correct (matching)
    # It is stored in DID F120 and we match with the ssdb part number
    diagnostic_part_number_match_message = str()
    try:
        diagnostic_part_number_match_message = compare_part_numbers(network_stub, can_send,
                                                                    can_receive, can_namespace,
                                                                    app_diag_part_num)
    except RuntimeError as runtime_error:
        diagnostic_part_number_match_message = runtime_error

    # For each line in dictionary_from_file, store result
    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0}

    all_results_dict = dict()

    for did_dict_from_file_values in sddb_app_did_dict.values():
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
        did_dict_with_result, pass_or_fail_counter_dict = test_response(did_dict_with_result,
                                                                        pass_or_fail_counter_dict,
                                                                        did_id)
        # Add the results
        all_results_dict[did_id] = did_dict_with_result

    logging.info(pp_result(all_results_dict, pass_or_fail_counter_dict,
                           diagnostic_part_number_match_message))

    generate_html("result_report.html", all_results_dict, pass_or_fail_counter_dict,
                  diagnostic_part_number_match_message)

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
