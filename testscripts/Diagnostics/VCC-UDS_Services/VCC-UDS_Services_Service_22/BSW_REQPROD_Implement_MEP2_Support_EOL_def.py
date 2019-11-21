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
import ast
from support_test_odtb2 import Support_test_ODTB2
import ODTB_conf

from support_can import Support_CAN
SC = Support_CAN()
SUPPORT_TEST = Support_test_ODTB2()


def pp_frame_info(msg, did_struct, frame, size, sid):
    ''' Pretty print the frame information '''

    frame_info = '\n\n' + msg + '\n' + '----------------------------------------'
    frame_info += '\n  Frame ---> ' + frame
    frame_info += '\n  Size ----> ' + size
    frame_info += '\n  SID -----> ' + sid
    frame_info += '\n  DID -----> ' + did_struct['did']
    frame_info += '\n  Payload -> ' + did_struct['payload']
    frame_info += '\n  Length --> ' + str(did_struct['payload_length'])

    if 'error_message' in did_struct:
        frame_info += '\n  ErrorMsg >' + did_struct['error_message']
        logging.debug('%s%s', '  ErrorMsg >', did_struct['error_message'])

    frame_info += '\n----------------------------------------\n'
    return frame_info


def pp_did_info(did_dict, result_dict):
    ''' Pretty print the DID info (stored in a dictionary) and the result (Passed/failed) '''

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
    logging.info('%s%s', 'can_frames to receive', can_answer)
    # message to send
    logging.info('To send:   [%s, %s, %s]', time.time(), can_send, m_send.upper())
    SC.t_send_signal_CAN_MF(network_stub, can_send, can_rec, can_nspace, m_send, True, 0x00)
    # Wait timeout for getting subscribed data
    timeout = 5 # wait for message to arrive
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
                if sid == '62':
                    sid_test = True
                    did = frame[4:8]
                    index = 8+(int(size)-3)*2
                    payload = frame[8:index]
                else:
                    did_struct['error_message'] = 'Wrong SID. 62 expected, received ' + sid
                    # Error code received
                    if sid == '7F':
                        did = ''
                        index = 8+(int(size)-3)*2
                        payload = frame[6:index]
                        decoded_7f = ", Negative response: " + SUPPORT_TEST.PP_CAN_NRC(payload)
                        did_struct['error_message'] += decoded_7f

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
    ''' Precondition for test running:
        BECM has to be kept alive: start heartbeat '''

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(network_stub, "EcmFront1NMFr", "Front1CANCfg0",
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)

    timeout = 160   #seconds
    SC.subscribe_signal(network_stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(network_stub, can_receive, can_send, can_namespace, timeout)

    step_0(network_stub, can_send, can_receive, can_namespace)


def step_0(network_stub, can_send, can_receive, can_namespace):
    ''' Teststep 0: Complete ECU Part/Serial Number(s) '''
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    SUPPORT_TEST.teststep(network_stub, can_m_send, can_mr_extra, can_send, can_receive,
                          can_namespace, stepno, purpose, timeout, min_no_messages,
                          max_no_messages)
    logging.info(SUPPORT_TEST.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2]))


def service_22(network_stub, can_send, can_receive, can_namespace, did):
    ''' Used for testing the Service 22
        Returns the DID info stored in a dictionary '''

    # Make it a byte string
    hex_did = bytearray.fromhex(did[0:2]) + bytearray.fromhex(did[2:4])

    # Building message
    can_m_send = SC.can_m_send("ReadDataByIdentifier", hex_did, '')
    can_mr_extra = ''

    did_dict = read_response(network_stub, can_m_send, can_mr_extra, did, can_send, can_receive,
                             can_namespace)
    return did_dict


def copy_dict_info(did_dict, data_identifier):
    ''' Copies some information from one dictionary to another
        Returns the dictionary '''
    if 'payload' in did_dict:
        data_identifier['payload'] = did_dict['payload']
        data_identifier['payload_length'] = did_dict['payload_length']
    if 'error_message' in did_dict:
        data_identifier['error_message'] = did_dict['error_message']
    if 'sid_test' in did_dict:
        data_identifier['sid_test'] = did_dict['sid_test']
    if 'did_in_response_test' in did_dict:
        data_identifier['did_in_response_test'] = did_dict['did_in_response_test']
    if 'did' in did_dict:
        data_identifier['did'] = did_dict['did']
    return data_identifier


def test_response(did, result_dict, did_value):
    ''' Comparing the expected size with the actual size and
        compares the received DID value with the expected DID value.
        Adding how the tests went to the did dictionary and adds one 'Failed' or 'Passed'
        to the result dictionary '''
    # Comparing the expected size with the actual size
    if 'error_message' not in did:
        # Verifying DID in response
        if did_value in did['did']:
            did['did_in_response_test'] = True
        else:
            did['did_in_response_test'] = False

        # Verifying payload length
        if ('payload_length' in did and int(did['Size']) ==
                did['payload_length']):
            result_dict['Passed'] += 1
            did['Result'] = True
            did['length_test'] = True
        else:
            if 'payload_length' in did:
                did['error_message'] = ('Size wrong. Expected ' + did['Size'] + ' but was ' +
                                        str(did['payload_length']))
            else:
                did['error_message'] = 'No payload length?'

            did['length_test'] = False
            result_dict['Failed'] += 1
            did['Result'] = False
    else:
        result_dict['Failed'] += 1
        did['Result'] = False

    return did, result_dict


def mark(did, value):
    ''' Creates checked or unchecked checkbox string
        returns string '''
    msg = ''
    if value in did:
        if did[value]:
            msg = '[X]'
        else:
            msg = '[ ]'
    else:
        msg = '[ ]'
    return msg

def pp_result(dictionary, result_dict, diagnostic_part_number_match_message):
    ''' Pretty print the report '''
    result = '\n\n       L'
    result += '\n       E'
    result += '\n       N'
    result += '\n S  D  G'
    result += '\n I  I  T'
    result += '\n D  D  H   DID   Name'
    result += '\n------------------------------------------------------------------------------'

    for data_identifier in dictionary.values():
        sid_mark = mark(data_identifier, 'sid_test')
        did_mark = mark(data_identifier, 'did_in_response_test')
        length_mark = mark(data_identifier, 'length_test')
        did = '  ' + data_identifier['ID']
        name = '  ' + data_identifier['Name']

        payload = ''
        if 'payload' in data_identifier:
            payload = '                 Payload: ' + data_identifier['payload']

        error_message = ''
        if 'error_message' in data_identifier:
            error_message = '                 Error message: ' + data_identifier['error_message']

        result += '\n' + sid_mark + did_mark + length_mark + did + name
        result += '\n' + payload

        if error_message != '':
            result += '\n' + error_message

    result += '\n------------------------------------------------------------------------------'
    result += '\n ' + str(result_dict)
    result += '\n\n ' + diagnostic_part_number_match_message
    result += '\n------------------------------------------------------------------------------'
    return result


def run():
    ''' run '''
    # Where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    logging.debug('%s%s', 'Testcase start: ', datetime.now())
    starttime = time.time()
    logging.debug('%s%s', 'time ', str(time.time()))

    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)

    filename = 'did_from_32290001_AB.py'
    with open(filename, 'r') as data_file:
        content = data_file.read()
        dictionary = ast.literal_eval(content)

    diagnostic_part_number = filename.split('_')[2]

    # Testing so that the Application Diagnostic Database Part Number is correct (matching)
    # It is stored in DID F120 and we match with the ssdb part number
    did = 'F120'
    did_dict = service_22(network_stub, can_send, can_receive, can_namespace, did)

    logging.info('-------------------------------------------------')
    if diagnostic_part_number == did_dict['payload']:
        diagnostic_part_number_match_message = 'Diagnostic part number is matching!'
    else:
        diagnostic_part_number_match_message = (
            'Diagnostic part number is NOT matching! Expected ' +
            diagnostic_part_number + ', but got ' + did_dict['payload'])

    logging.info(diagnostic_part_number_match_message)
    logging.debug(did_dict)
    logging.info('-------------------------------------------------')

    # For each line in dictionary, store result
    result_dict = {"Passed": 0, "Failed": 0}

    for data_identifier in dictionary.values():
        did = data_identifier['ID']

        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict = service_22(network_stub, can_send, can_receive, can_namespace, did)

        # Copy info to the data_identifier dictionary from the did_dict
        data_identifier = copy_dict_info(did_dict, data_identifier)

        # Summarizing the result
        data_identifier, result_dict = test_response(data_identifier, result_dict, did)

        logging.info(pp_did_info(data_identifier, result_dict))

    logging.info(pp_result(dictionary, result_dict, diagnostic_part_number_match_message))


    ############################################
    # postCondition
    ############################################
    logging.info('')
    logging.debug('%s%s', "time ", str(time.time()))
    logging.debug('%s%s', "Testcase end: ", str(datetime.now()))
    logging.info('%s%s', "Time needed for testrun (seconds): ", str(int(time.time() - starttime)))
    logging.debug("Do cleanup now...")
    logging.debug("Stop all periodic signals sent")

    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info('%s%s', 'Test cleanup end: ', str(datetime.now()))


if __name__ == "__main__":
    run()
