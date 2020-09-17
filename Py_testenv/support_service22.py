# project:  ODTB2 testenvironment using SignalBroker
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-05-29
# version:  1.0

# Initial version:
# version 1.0:
#   teststep    Common teststeps moved into support for dedicated service
#   pep8        coding is changed to confirm to pep8 (some code left, though)

# inspired by https://grpc.io/docs/tutorials/basic/python.html

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

import logging
import time
from collections import namedtuple
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUPPORT_TEST = SupportTestODTB2()

Infoentry = namedtuple('Infoentry', 'did name c_sid c_did c_size scal_val_list err_msg payload')

class SupportService22:
    # These will take some more time to get rid of.
    # pylint: disable=eval-used,too-many-branches,too-many-locals,too-many-nested-blocks,undefined-variable,too-many-statements,too-many-arguments
    """
    class for supporting Service#22
    """

    @staticmethod
    def read_did_eda0(can_p: CanParam, stepno=220):
        """
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        if SC.can_messages[can_p["receive"]]:
            logging.info('%s',
                         SUPPORT_TEST.pp_combined_did_eda0(SC.can_messages[can_p["receive"]][0][2],
                                                           title=''))
        else:
            logging.info('%s', "No messages received for request Read DID EDA0")
            logging.info("Frames received: %s", SC.can_frames[can_p["receive"]])
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            result = False
        return result


    @staticmethod
    def read_did_f186(can_p: CanParam, dsession=b'', stepno=221):
        """
        Read DID F186: Active Diagnostic Session
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x86', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Active Diagnostic Session",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        #time.sleep(1)
        return result


    @staticmethod
    def read_did_fd35_pressure_sensor(can_p: CanParam, dsession=b'', stepno=222):
        """
        Read DID FD35: pressure sensor

        return:
        result: True/False
        pressure: pressure value as int
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xFD\x35', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Read Pressure Sensor FD35",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        pressure = 0
        if SC.can_messages[can_p["receive"]] and\
           SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]], teststring='0662FD35'):
            #position 6-9: 2bytes for pressure value (uint)
            press = SC.can_messages[can_p["receive"]][0][2][6:10]
            pressure = int(press, 16)
            logging.info('Read Pressure Sensor (raw): 0x%s', press)
            logging.info('Read Pressure Sensor (kPa): %s', pressure)
        else:
            logging.info("Could not read pressure sensor (DID FD35)")

        #time.sleep(1)
        return result, pressure

    #@classmethod
    @staticmethod
    def read_did_4a28_pressure_sensor(can_p: CanParam, dsession=b'', stepno=223):
        """
        Read DID 4A28: pressure sensor

        return:
        result: True/False
        pressure: pressure value as int
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\x4A\x28', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Read Pressure Sensor 4A28",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        pressure = 0
        if SC.can_messages[can_p["receive"]] and\
            SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]], teststring='07624A28'):
            #position 26 bits for pressure value, temperature and flags
            raw4a28 = SC.can_messages[can_p["receive"]][0][2][6:14]
            #position 12 bits for pressure value (uint)
            pressure = int(raw4a28[0:4], 16)
            logging.info('Read 4A28 return value (raw): 0x%s', raw4a28)
            logging.info('Read Pressure Sensor (kPa): %s', pressure)
        else:
            logging.info("Could not read pressure sensor (DID 4A28)")

        #time.sleep(1)
        return result, pressure

    #@classmethod
    @staticmethod
    def read_did_eda0_mep2(can_p: CanParam, stepno=220):
        """
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        if SC.can_messages[can_p["receive"]] == 0:
            logging.info('%s', SUPPORT_TEST.pp_combined_did_eda0_mep2(\
                         SC.can_messages[can_p["receive"]][0][2], title=''))
        else:
            logging.info('%s', "No messages received for request Read DID EDA0")
            logging.info("Frames received: %s", SC.can_frames[can_p["receive"]])
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            result = False
        return result

    #@classmethod
    @staticmethod
    def verify_pbl_session(can_p: CanParam, stepno=224):
        """
        Verify ECU in Primary Bootloader Session
        """

        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        #verify Primary Bootloader Diagnostic Database Part number
        #is included in the response message from EDA0 request
        result = not (SC.can_messages[can_p["receive"]][0][2]).find('F121') == -1

        return result

    #@classmethod
    @staticmethod
    def verify_sbl_session(can_p: CanParam, stepno=225):
        """
        Verify ECU in Secondary Bootloader Session
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x22', b''),
                            "extra":''
                           }

        etp: CanTestExtra = {"step_no" : stepno,
                             "purpose" : "Verify Programming session in SBL",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        result = result and SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]],
                                                      teststring='F122')

        return result

    @classmethod
    def __pp_frame_info(cls, msg, did_struct, frame, size, sid):
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


    #private
    @classmethod
    def __read_response(cls, can_par: CanParam, m_send, m_receive_extra, did, timeout):
        ''' Reads the response from the service 22 request
            Returns the DID info stored in a dictionary '''
        can_send = can_par["send"]
        can_rec = can_par["receive"]

        cpay = {
            "payload" : m_send,
            "extra" : m_receive_extra
        }

        SC.clear_old_cf_frames()

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
        SC.t_send_signal_can_mf(can_par, cpay, True, 0x00)
        # Wait timeout for getting subscribed data
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
                            decoded_7f = "Negative response: " + SUPPORT_TEST.pp_can_nrc(payload)
                            did_struct['error_message'] = decoded_7f
                    else:
                        did_struct['error_message'] = 'Wrong SID. 62 expected, received %s' % (sid)

                    did_struct['did'] = did
                    did_struct['payload'] = payload
                    did_struct['payload_length'] = int(len(payload)/2)

                    temp_message = i
                    temp_message[2] = payload

                    logging.debug(cls.__pp_frame_info('Single frame message received',
                                                      did_struct, frame, size, sid))

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

                    logging.debug(cls.__pp_frame_info('First multi frame received', did_struct,
                                                      frame, size, sid))

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
                    logging.debug('Last frame received -----> %s', i[2][2:(2+mf_size_remain*2)])
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


    @classmethod
    def get_did_info(cls, can_par: CanParam, did, timeout):
        '''
        Used for testing the Service 22
        Returns the DID info stored in a dictionary
        '''

        # Make it a byte string
        hex_did = bytearray.fromhex(did[0:2]) + bytearray.fromhex(did[2:4])

        # Building message
        can_m_send = SC_CARCOM.can_m_send("ReadDataByIdentifier", hex_did, b'')
        can_mr_extra = ''

        did_dict = cls.__read_response(can_par, can_m_send, can_mr_extra, did, timeout)
        return did_dict


    @classmethod
    def adding_info(cls, copy_from_dict, dictionary):
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


    @classmethod
    def summarize_result(cls, did_dict, pass_or_fail_counter_dict, did_id):
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
            pp_payload = 'Payload: ' + SUPPORT_TEST.add_ws_every_nth_char(payload, 16)

        formula = str()
        if 'Formula' in did_dict:
            formula = did_dict['Formula']

        data = 'Formula = [' + formula + '] ' + pp_payload

        info_entry = Infoentry(did=did, name=name, c_sid=c_sid, c_did=c_did, c_size=c_size,
                               scal_val_list=scal_val_list, err_msg=err_msg, payload=data)
        return info_entry, pass_or_fail_counter_dict


    @classmethod
    def get_sub_payload(cls, payload, offset, size):
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


    @classmethod
    def get_scaled_value(cls, resp_item, sub_payload):
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
            populated_formula = cls.__populate_formula(formula, int_value, size)
            logging.debug('Populated formula = %s', populated_formula)

            try:
                result = str(eval(populated_formula))
                int_result = int(float(result))
                logging.debug('Formula = %s => %s', formula, result)
                return int_result
            except RuntimeError as runtime_error:
                logging.fatal(runtime_error)
                raise RuntimeError('Failed parsing formula') from runtime_error
            except SyntaxError as syntax_error:
                logging.fatal(syntax_error)
                raise SyntaxError('Failed parsing formula') from syntax_error
        else:
            # If we reach this, then there is no formula.
            # That is an issue, formula should be mandatory
            logging.fatal('No formula!')
            raise RuntimeError('No formula!')


    @classmethod
    def get_scaled_value_with_unit(cls, resp_item, sub_payload):
        '''
        Input - Response Item with at least formula
                sub_payload which should converted from raw data
        Returns the string with converted data
        '''
        try:
            scaled_value = cls.get_scaled_value(resp_item, sub_payload)
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


    @classmethod
    def __populate_formula(cls, formula, value, size):
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


    @classmethod
    def clean_compare_value_hex(cls, compare_value):
        '''
        Removing '=0x' from compare value or '='
        '''
        cleaned_compare_value = compare_value.replace('=0x', '')
        return cleaned_compare_value


    @classmethod
    def compare(cls, scaled_value, compare_value):
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
        except NameError as name_error:
            logging.error(name_error)
        return result
