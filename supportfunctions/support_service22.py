"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# project:  Hilding testenvironment using SignalBroker
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

The Python implementation of the gRPC route guide client.
"""

import logging
import inspect
import time
from collections import namedtuple
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUPPORT_TEST = SupportTestODTB2()
SIO = SupportFileIO

Infoentry = namedtuple('Infoentry', 'did name c_sid c_did c_size scal_val_list err_msg payload')

class SupportService22:
    # These will take some more time to get rid of.
    # pylint: disable=eval-used,too-many-branches,too-many-locals,too-many-nested-blocks,undefined-variable,too-many-statements,too-many-arguments
    """
    class for supporting Service#22
    """

    @staticmethod
    def read_did_eda0(can_p: CanParam,\
                      pn_sn_list=None, stepno=220):
        """
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

        #pn_sn_list=[['F120', 'PN'],\
        #            ['F12A', 'PN'],\
        #            ['F12B', 'PN'],\
        #            ['F18C', 'SN'],\
        #            ['F12E', 'PN'],\
        #            ['F126', 'VIDCV']]
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'pn_sn_list')

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        if SC.can_messages[can_p["receive"]]:
            rec_message = SC.can_messages[can_p["receive"]][0][2]
            if pn_sn_list != []:
                logging.debug("S220: validate reply contains PN/SN: %s", pn_sn_list)
                result = result and\
                     SUPPORT_TEST.validate_combined_did_eda0(rec_message,
                                                             pn_sn_list,
                                                            )
            logging.info('%s',
                         SUPPORT_TEST.pp_combined_did_eda0(rec_message,
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
    def read_did_pressure_sensor(can_p: CanParam, did=b'\xFD\x35', dsession=b'', stepno=222):
        """
        Read DID FD35: pressure sensor

        return:
        result: True/False
        pressure: pressure value as int
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             did, b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Read Pressure Sensor " + did.hex().upper(),
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        pressure = 0
        if SC.can_messages[can_p["receive"]] and\
           SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]],
                                     teststring='62' + did.hex().upper()):
            #SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]],
            #                          teststring='0662' + did.hex().upper()):
            #position 6-9: 2bytes for pressure value (uint)
            press = SC.can_messages[can_p["receive"]][0][2][6:10]
            pressure = int(press, 16)
            logging.info('Read Pressure Sensor (raw): 0x%s', press)
            logging.info('Read Pressure Sensor (kPa): %s', pressure)
        else:
            logging.info("Could not read pressure sensor (DID %s)", did.hex().upper())

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

    @staticmethod
    def read_did_appl_dbpn(can_p: CanParam, stepno=220):
        """
        Read applicaytion database part numbert
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x20', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Application Diagnostic Database Part Number",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        if SC.can_messages[can_p["receive"]]:
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            message = SC.can_messages[can_p["receive"]][0][2]
            pos1 = message.find('F120')
            logging.info('Part number (F120) %s',
                         SUPPORT_TEST.pp_partnumber(message[pos1+4: pos1+18],\
                                                    message[pos1:pos1+4] + ' '))
        else:
            logging.info('%s', "No messages received for request Read DID F125")
            logging.info("Frames received: %s", SC.can_frames[can_p["receive"]])
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            result = False
        return result

    @staticmethod
    def read_did_pbl_pn(can_p: CanParam, stepno=220):
        """
        Read primary bootloader part number
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x25', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Primary Bootloader Software Part Number",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        if SC.can_messages[can_p["receive"]]:
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            message = SC.can_messages[can_p["receive"]][0][2]
            pos1 = message.find('F125')
            logging.info('Part number (F125) %s',
                         SUPPORT_TEST.pp_partnumber(message[pos1+4: pos1+18],\
                                                    message[pos1:pos1+4] + ' '))
        else:
            logging.info('%s', "No messages received for request Read DID F125")
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
                             "purpose" : "verify current session is PBL",
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

    def get_ecu_mode(self, can_p: CanParam,\
                            stepno='226',\
                            purpose="get ECU mode (DEF/PBL/SBL/EXT)"):
        """
        Function used determine ECU mode using EDA0 reply
        return: ECU_mode (DEF/PBL/SBL/EXT)
        """
        logging.debug("Step_no: %s", stepno)
        logging.debug("Purpose: %s", purpose)
        self.read_did_eda0(can_p)

        message = SC.can_messages[can_p["receive"]][0][2]
        ecu_mode = 'unknown'
        pos = message.find('EDA0')
        if (not message.find('F121', pos) == -1) and (not message.find('F125', pos) == -1):
            # Security Access Request SID
            ecu_mode = 'PBL'
        elif (not message.find('F122', pos) == -1) and (not message.find('F123', pos) == -1):
            ecu_mode = 'SBL'
        elif (not message.find('F120', pos) == -1) and (not message.find('F12E', pos) == -1):
            self.read_did_f186(can_p, dsession=b'')

            if SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]],
                                         teststring='62F18601'):
                ecu_mode = 'DEF'
            elif SUPPORT_TEST.test_message(SC.can_messages[can_p["receive"]],
                                           teststring='62F18603'):
                ecu_mode = 'EXT'
        return ecu_mode

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
    def adding_info(cls, source_dict, target_dict):
        '''
        Copies some information from one dictionary to another
        Returns the dictionary
        '''
        if 'payload' in source_dict:
            target_dict['payload'] = source_dict['payload']
            target_dict['payload_length'] = source_dict['payload_length']
        if 'error_message' in source_dict:
            target_dict['error_message'] = source_dict['error_message']
        if 'sid_test' in source_dict:
            target_dict['sid_test'] = source_dict['sid_test']
        if 'did_in_response_test' in source_dict:
            target_dict['did_in_response_test'] = source_dict['did_in_response_test']
        if 'did' in source_dict:
            target_dict['did'] = source_dict['did']
        return target_dict


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
            if ('payload_length' in did_dict and int(did_dict['size']) ==
                    did_dict['payload_length']):
                pass_or_fail_counter_dict['Passed'] += 1
                c_size = True
            # Wrong payload length
            else:
                if 'payload_length' in did_dict:
                    did_dict['error_message'] = 'Size wrong. Expected %s but was %s' % (
                        did_dict['size'], str(did_dict['payload_length']))
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

        name = did_dict['name']
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
        if 'formula' in did_dict:
            formula = did_dict['formula']

        data = 'Formula = [' + formula + '] ' + pp_payload

        info_entry = Infoentry(did=did_id, name=name, c_sid=c_sid, c_did=c_did, c_size=c_size,
                               scal_val_list=scal_val_list, err_msg=err_msg, payload=data)
        return info_entry, pass_or_fail_counter_dict
