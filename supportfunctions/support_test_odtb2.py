"""
The Python implementation of the gRPC route guide client.

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# project:  Hilding testenvironment using SignalBroker
# author:   FJANSSO8 (Fredrik Jansson)
# date:     2020-05-12
# version:  1.4

# Changes done:
# version 1.3:
#   teststep    Added parameter max_wait. Instead for waiting whole 'timeout',
#               it is now possible to wait until number of expected messages is reached.
#               If number of messages not reached withing timeout you still get an error reported.
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

"""

from __future__ import print_function
import logging
import time
import fnmatch
import importlib
import os
import binascii
from datetime import datetime
import string
import inspect

#sys.path.append('generated')
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO
SC = SupportCAN()

BYTE_SIZE = 2
HEX_BASE = 16
DID_OFFSET = 4

class SupportTestODTB2: # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-branches, too-many-lines
    """
    Class for supporting sending/receiving CAN frames
    """

    @classmethod
    def print_test_purpose(cls, stepno, purpose):
        """
        print_test_purpose
        """
        logging.debug("stepno passed to print_test_purpose: %s", stepno)
        logging.info("Purpose: %s", purpose)


    def test_message(self, messagelist, teststring=''):
        """
        test_message
        """
        testresult = True

        #print("Messagelist: ", messagelist)
        if teststring != '' and (messagelist in ('', [])):
            logging.warning("Bad: Empty messagelist, teststring '%s' not found", teststring)
            testresult = False
        else:
            for i in messagelist:
            #print("can frame  ", i[2].upper())
            #print("test against ", teststring)
                if teststring == '':
                    logging.warning("Nothing expected. Received %s", i[2].upper())
                elif teststring in i[2].upper():
                    logging.debug("Good: Expected: %s received: %s", teststring, i[2].upper())
                    #continue
                else:
                    testresult = False
                    logging.warning("Bad: Expected: %s received: %s", teststring, i[2].upper())
                    logging.warning("Try to decode error message (7F):")
                    logging.warning("%s", self.pp_decode_7f_response(i[2].upper()))
                    #logging.info("test_message: test if 7F38 - "\
                    #             "requestCorrectlyReceived-ResponsePending was received")
                    #if self.check_7f78_response(i):
                    #    logging.info("78 found")
        return testresult


    @classmethod
    def __send(cls, can_p: CanParam, etp: CanTestExtra, cpay: CanPayload):
        """
        Private send method

        can_p["send"]
        can_p["receive"]
        cpay["payload"]
        """
        wait_max = False
        if "wait_max" in etp:
            wait_max = etp["wait_max"]

        wait_start = time.time()
        logging.debug("To send:   [%s, %s, %s]", time.time(), can_p["send"],
                      (cpay["payload"]).hex().upper())
        SC.clear_all_can_messages()
        SC.t_send_signal_can_mf(can_p, cpay, can_p.padding, 0x00)
        #wait timeout for getting subscribed data
        if (wait_max or (etp["max_no_messages"] == -1)):
            time.sleep(etp["timeout"])
            SC.update_can_messages(can_p)
        else:
            SC.update_can_messages(can_p)
            while((time.time()-wait_start <= etp["timeout"])
                  and (len(SC.can_messages[can_p["receive"]]) < etp["max_no_messages"])):
                SC.clear_can_message(can_p["receive"])
                SC.update_can_messages(can_p)
                time.sleep(0.05) #pause a bit to receive frames in background


    def teststep(self,# pylint: disable=too-many-statements
                 can_p: CanParam,
                 cpay: CanPayload, etp: CanTestExtra):# pylint: disable=too-many-statements
        """
        teststep for Hilding testenvironment

        step_no          integer    teststep
        purpose          string     purpose of teststep
        timeout          float      timeout in seconds
        min_no_messages  integer    minimum number of messages to expect
        max_no_messages  integer    maximum number of messages to expect

        Optional parameter:
        step_no          integer teststep
        purpose          string  purpose of teststep
        timeout          float   timeout in seconds
        min_no_messages  integer minimum number of messages to expect
        max_no_messages  integer maximum number of messages to expect
        clear_old_mess   bool    clear old messages before doing teststep
        wait_max         bool    TRUE: wait until timeout for messages
                                  FALSE: wait until max_no_messages reached
        Return:
        testresult       bool    result of teststep is as expected
        """

        # Only log test step number if it is an actual test step in a script calling this function
        # If this function is called from uds.py no print is required since it is handled in dut.py
        try:
            called_from_uds = "uds.py" in inspect.stack()[1][1]
            if int(etp['step_no']) < 100 and not called_from_uds:
                logging.info(
                    "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Step %s started~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
                    etp['step_no'])
        except ValueError:
            pass

        testresult = True

        SC.clear_old_cf_frames()

        clear_old_mess = True
        if "clear_old_mess" in etp:
            clear_old_mess = etp["clear_old_mess"]

        if clear_old_mess:
            logging.debug("Clear old messages")
            SC.clear_all_can_frames()
            SC.clear_all_can_messages()
        self.print_test_purpose(etp['step_no'], etp['purpose'])

        # wait for messages
        # define answer to expect
        logging.debug("Build answer can_frames to receive")
        logging.debug("payload: %s", cpay['payload'])
        logging.debug("pextra:  %s", cpay['extra'])
        can_answer = SC.can_receive(cpay['payload'], cpay['extra'])
        logging.debug("CAN frames to receive: %s", can_answer)

        # message to send
        self.__send(can_p, etp, cpay)
        logging.debug("Teststep: CAN frames: %s", SC.can_frames)
        # currently we don't build messages for frames sent
        #logging.info("Teststep: CAN messages send: %s", SC.can_messages[can_p["send"]])
        logging.debug("Teststep: CAN messages receive: %s", SC.can_messages[can_p["receive"]])

        if SC.can_messages[can_p["receive"]]:
            while self.check_7f78_response(SC.can_messages[can_p["receive"]]):

                # For the following services P4Server_max is equal to P2Server_max.
                # 7F78 response is not an accepted response from the server.
                # Flag with logging error.
                unsupported_services = ['10', '11', '27', '3E', '23', '2F']
                service = SC.can_messages[can_p["receive"]][0][2][4:6]
                if service in unsupported_services:
                    logging.error('Failed: Service %s does not support NRC 78.', service)

                logging.debug("Filter 7Fxx78: requestCorrectlyReceived-ResponsePending")
                logging.debug("Rec can frames: %s", SC.can_frames[can_p["receive"]])
                logging.debug("Rec can messages: %s", SC.can_messages[can_p["receive"]])

                logging.debug("78 - ResponsePending was received")
                logging.debug("7Fxx78 received: remove first frame received")
                SC.remove_first_can_frame(can_p["receive"])
                #wait for next frame to be received
                wait_loop = 0
                max_7fxx78 = 10

                new_max_7fxx78 = SIO.parameter_adopt_teststep('max_7fxx78')
                if new_max_7fxx78 != '':
                    assert isinstance(new_max_7fxx78, int)
                    max_7fxx78 = new_max_7fxx78
                else:
                    logging.debug("teststep: new_max_7Fxx78 is empty. Leave old value.")
                logging.debug("teststep: max_7Fxx78 %s", max_7fxx78)

                while (len(SC.can_frames[can_p['receive']]) == 0) and (wait_loop <= max_7fxx78):
                    time.sleep(1)
                    wait_loop += 1
                    logging.debug("7Fxx78: frames received: %s", SC.can_frames[can_p['receive']])
                    logging.debug("7Fxx78: len frames received: %s",
                                 len(SC.can_frames[can_p['receive']]))
                    logging.info("Waiting for an ECU response for Diag request 0x%s....",
                                cpay['payload'][:len(cpay['payload']) if (len(cpay['payload']) < 8)
                                                                                    else 8].hex())
                    logging.debug("7Fxx78 wait_loop <=%s: %s",
                                 max_7fxx78, (wait_loop <= max_7fxx78))
                logging.info("Received can frames : %s", SC.can_frames[can_p["receive"]])
                SC.clear_can_message(can_p["receive"])
                SC.update_can_messages(can_p)

        if len(SC.can_messages[can_p["receive"]]) < etp["min_no_messages"]:
            logging.warning("Bad: min_no_messages not reached: %s",
                            len(SC.can_messages[can_p["receive"]]))
            testresult = False
        elif etp["max_no_messages"] >= 0 and\
                len(SC.can_messages[can_p["receive"]]) > etp["max_no_messages"]:
            logging.warning("Bad: Max_no_messages %s", len(SC.can_messages[can_p["receive"]]))
            testresult = False
        else:
            if SC.can_messages[can_p["receive"]]:
                logging.debug("teststep test message: %s", SC.can_messages[can_p["receive"]])
                logging.debug("teststep test against len: %s", len(can_answer))
                logging.debug("teststep test against: %s", can_answer)
                if etp["min_no_messages"] >= 0:
                    testresult = testresult and\
                        self.test_message(SC.can_messages[can_p["receive"]],\
                                          can_answer.hex().upper())
        logging.debug("Step %s: Result from teststep method in support_test_odtb2.py: %s",
        etp["step_no"],
        testresult)

        return testresult

    @staticmethod
    def validate_serial_number_record(ecu_serial_number_record: str) -> bool:
        """
        Validate a ECU serial number record

        A ECU serial number record is 4 bytes long

        It contains up to 8 digits coded in BCD, right justified, 0-padded.
        """

        # Validate 4 bytes of data (8 character hex string)
        result = len(ecu_serial_number_record) == 8
        if not result:
            logging.info("validate SN failed - wrong length: %s", len(ecu_serial_number_record))

        # Validate BCD coding in 4 bytes (8 nibbles), right justified, 0 padded
        result = result and all(nibble in string.digits for nibble in ecu_serial_number_record)
        if not result:
            logging.info("validate SN failed - wrong BCD part: %s", ecu_serial_number_record)

        return result

    def validate_serial_number_records(self, sn_records: str) -> bool:
        """
        Validate several serial number records

        A record with several serial numbers starts with
        1 byte containing number of serial numbers to follow
        several serial number records each 4 bytes long
        """

        # Figure out if sn_records contains one ore more serial numbers
        #
        result = True
        sn_len = len(sn_records)
        logging.debug("validate SN records: len sn_records %s", sn_len)
        if sn_len == 8:
        #    4 bytes of data (8 character hex string)
            sn_num = 1
            sn_rec = sn_records
        elif sn_len > 8:
            sn_num = int(sn_records[0:2], 16)
            sn_rec = sn_records[2:]
        else:
            result = False
        if result:
            logging.debug("Validate SN records -  Number of SN: %s", sn_num)
        else:
            logging.debug("Validate SN records -  invalid number of SN")

        if result:
            for sn_count in range(0, sn_num):
                sn_rec2 = sn_rec[sn_count*8:]
                if len(sn_rec2) > 8:
                    sn_rec2 = sn_rec2[0:8]
                result = result and self.validate_serial_number_record(sn_rec2)
                if result:
                    logging.info("Validate SN record ok: %s", sn_rec2)
                else:
                    logging.info("Validate SN record fail: %s", sn_rec2)
        return result

    @staticmethod
    def pp_ecu_serial_number(i, title=''):
        """
        Pretty Print function support for ECU serial numbers
        """
        if not SupportTestODTB2.validate_serial_number_record(i):
            logging.error("Error: Invalid ECU serial number: %s %s", title, i)

        return title + i

    @classmethod
    def validate_part_number_record(cls, part_number_record: str) -> bool:
        """
        Validate a part number record

        A part number record is 7 bytes long

        The first 4 bytes contain the part number:
        Up to 8 digits coded in BCD, right justified, 0-padded.

        Last 3 bytes contain the version suffix:
        3 ASCII encoded uppercase letters or spaces.
        The version suffix can start with 0, 1 or 2 spaces before the letters.
        """
        # Validate 7 bytes of data (14 character hex string)
        result = len(part_number_record) == 14
        if not result:
            logging.info("validate part number failed - wrong length: %s", len(part_number_record))

        if result:
            # First 4 bytes is part number, rest is version suffix
            part_number, version_suffix_hex = part_number_record[:8], part_number_record[8:]

            # Validate BCD coding in first 4 bytes (8 nibbles), right justified, 0 padded
            result = result and all(nibble in string.digits for nibble in part_number)
            if not result:
                logging.info("validate part number failed - part number (first 4 bytes) should\
 only contain digits but is: %s", part_number_record)

            # Validate version suffix
            suffix_chars = [chr(byte) for byte in bytes.fromhex(version_suffix_hex)]
            valid_chars = ' ' + string.ascii_uppercase
            result = result and all((char in valid_chars) for char in suffix_chars)

            # If middle character is space then the first must also be space
            if suffix_chars[1] == ' ':
                result = result and suffix_chars[0] == ' '

            # Last suffix character can not be space
            result = result and suffix_chars[2] != ' '

            if not result:
                logging.info("validate part number failed - suffix part (last 3 chars)\
 have wrong format: %s", part_number_record)
        return result


    def validate_part_number_records(self, pn_records: str) -> bool:
        """
        Validate part number records

        A record with several part numbers starts with
        1 byte containing number of part numbers to follow
        several part number records each 7 bytes long
        """

        # Figure out if sn_records contains one ore more serial numbers
        #
        result = True
        pn_len = len(pn_records)
        logging.debug("validate PN records: len pn_records %s", pn_len)
        if pn_len == 14: #7bytes of data - 14 char hex string
            pn_num = 1
            pn_rec = pn_records
        elif pn_len > 14:
            pn_num = int(pn_records[0:2], 16)
            pn_rec = pn_records[2:]
        else:
            result = False
        if result:
            logging.debug("Validate PN records -  Number of PN: %s", pn_num)
        else:
            logging.debug("Validate PN records -  invalid number of PN")

        if result:
            for pn_count in range(0, pn_num):
                pn_rec2 = pn_rec[pn_count*14:]
                if len(pn_rec2) > 14:
                    pn_rec2 = pn_rec2[0:14]
                result = result and self.validate_part_number_record(pn_rec2)
                if result:
                    logging.info("Validate PN record ok: %s", pn_rec2)
                else:
                    logging.info("Validate PN record fail: %s", pn_rec2)
        return result


    def validate_combined_did_eda0(self, rec_message, pn_sn_list) -> bool:
    # pylint: disable=too-many-statements
        """
        Validate a combined part/serial number

        A combined part/serial number contains several records of part/serial numbers.
        Which records are contained depends on ECU mode and may change for different projects.

        pn_sn_list contains identifiers to check for and which kind of info the contain.
        """

        #iterate through rec_message, find identifiers from pn_sn_list.
        result = True
        pos_list = []
        if pn_sn_list:
            for pn_sn in pn_sn_list:
                logging.debug("Val DID EDA0: looking for %s", pn_sn[0])
                pos_first = rec_message.find(pn_sn[0])
                pos_last = rec_message.rfind(pn_sn[0])
                logging.debug("Val DID EDA0: pos_first %s", pos_first)
                logging.debug("Val DID EDA0: pos_last  %s", pos_last)
                if pos_first == pos_last:
                    pos_list.append(pos_first)
                else:
                    logging.warning("Unclear position of id in combined did response: %s %s",
                                    pos_first,
                                    pos_last)
            logging.info("Validate PN/SN - pos_list generated: %s", pos_list)
            if -1 in pos_list:
                logging.info("Validate PN/SN: Not all IDs found in reply.")
                logging.info("Validate PN/SN: Search for %s", pn_sn_list)
                logging.info("Validate DID EDA0: pos_list %s", pos_list)
                result = False
            else:
                logging.info("Validate PN/SN: All IDs found in reply. Validate format.")
                #is there an index following? -1 if not
                logging.info("Validate DID EDA0: rec_message %s", rec_message)
                logging.info("Validate DID EDA0: pn_sn_list  %s", pn_sn_list)
                for idx, pn_sn in enumerate(pn_sn_list):
                    pos_end = -1
                    logging.debug("Val DID EDA0: idx  %s", idx)
                    pos_start = pos_list[idx]
                    logging.debug("Val DID EDA0: pos_start  %s", pos_start)
                    # -1: index not found
                    if not pos_start == -1:
                        next_pos = sorted(pos_list).index(pos_start) +1
                        logging.debug("Val DID EDA0: next_pos  %s", next_pos)
                        if not next_pos >= len(pos_list):
                            pos_end = sorted(pos_list)[next_pos]
                        else:
                            pos_end = -1
                    logging.debug("rec_message: %s", rec_message)
                    logging.debug("rec_message: pos_start %s", pos_start)
                    logging.debug("rec_message: pos_end   %s", pos_end)
                    if pos_end != -1:
                        record = rec_message[pos_start+4: pos_end]
                    else:
                        record = rec_message[pos_start+4:]

                    logging.debug("rec_message: to check %s", record)
                    if pn_sn[1] == 'PN':
                        result = self.validate_part_number_records(record)
                    elif pn_sn[1] == 'SN':
                        result = self.validate_serial_number_records(record)
                    elif pn_sn[1] == 'VIDCV':
                        logging.info("Vendor ID, cluster version not validated   %s", record)
                    else:
                        result = False
        logging.debug("Validate PN/SN: result %s.", result)
        return result


    @staticmethod
    def pp_partnumber(i, title=''):
        """
        Pretty Print function support for part numbers
        """
        if not SupportTestODTB2.validate_part_number_record(i):
            logging.info("^^^^^^^^^ The previous line is related to DID %s ^^^^^^^^",
                        title)
            return title + i

        return title + i[0:8] + bytes.fromhex(i[8:14]).decode('utf-8')


    def pp_combined_did_eda0(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0:
        """
        pos = message.find('EDA0')
        retval = title
        if (not message.find('F120', pos) == -1) and (not message.find('F12E', pos) == -1):
            retval = self.pp_combined_did_eda0_becm_mode1_mode3(message, "EDA0 for mode1/mode3:\n")
        elif (not message.find('F121', pos) == -1) and (not message.find('F125', pos) == -1):
            retval = self.pp_combined_did_eda0_pbl(message, "EDA0 for PBL:\n")
        elif (not message.find('F122', pos) == -1) and (not message.find('F124', pos) == -1):
            retval = self.pp_combined_did_eda0_sbl(message, "EDA0 for SBL:\n")
        else:
            retval = "Unknown format of EDA0 message'\n"
            logging.warning("Message received: %s", message)
        return retval


    def get_combined_did_eda0(self, message, sddb_dict):
        """
        PrettyPrint Combined_DID EDA0:
        """
        pos = 0
        if (not message.find('F120', pos) == -1) and (not message.find('F12E', pos) == -1):
            retval = self.combined_did_eda0_becm_mode1_mode3(message, sddb_dict)
            return retval

        retval = "Unknown format of EDA0 message'\n"
        logging.warning("%s Message received: %s", retval, message)

        eda0_dict_wo_f12e: dict = {
            'Application Diagnostic Database Part Number': '',
            'ECU Core Assembly Part Number': '',
            'ECU Delivery Assembly Part Number': '',
            'ECU Serial Number': ''
        }
        return eda0_dict_wo_f12e


    def pp_combined_did_eda0_mep2(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0:
        MEP2 has different values
        """
        pos = message.find('EDA0')
        retval = title
        if (not message.find('F120', pos) == -1) and (not message.find('F12E', pos) == -1):
            retval = self.pp_combined_did_eda0_becm_mode1_mode3(message, "EDA0 for mode1/mode3:\n")
        elif (not message.find('F121', pos) == -1) and (not message.find('F125', pos) == -1):
            retval = self.pp_combined_did_eda0_pbl(message, "EDA0 for PBL:\n")
        elif (not message.find('F122', pos) == -1) and (not message.find('F124', pos) == -1):
            retval = self.pp_combined_did_eda0_sbl(message, "EDA0 for SBL:\n")
        else:
            retval = "Unknown format of EDA0 message'\n"
            logging.warning("Message received: %s", message)
        return retval


    def pp_combined_did_eda0_becm_mode1_mode3(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0:
        """
        pos = message.find('EDA0')
        retval = title
        pos1 = message.find('F120', pos)
        retval = retval + "Application_Diagnostic_Database '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN            '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + "ECU_Delivery_Assembly PN        '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        # Combined DID F12E:
        retval = retval + self.pp_did_f12e(message[(message.find('F12E', pos1+18))
                                                   :(message.find('F12E', pos1+18)+76)])
        ## ECU serial:
        retval = retval + "ECU Serial Number         '"\
                        + self.pp_ecu_serial_number(message[144:152]) + "'\n"
        return title + " " + retval


    def combined_did_eda0_becm_mode1_mode3(self, message, sddb_dict):
        """
        Combined_DID EDA0. This function is for returning the actual values.
        Not pretty print them.
        """
        eda0_dict_wo_f12e: dict = {}

        pos1 = message.find('F120')
        eda0_dict_wo_f12e['Application Diagnostic Database Part Number'] =\
            self.pp_partnumber(message[pos1+4: pos1+18])

        pos1 = message.find('F12A', pos1+18)
        eda0_dict_wo_f12e['ECU Core Assembly Part Number'] =\
            self.pp_partnumber(message[pos1+4: pos1+18])

        pos1 = message.find('F12B', pos1+18)
        eda0_dict_wo_f12e['ECU Delivery Assembly Part Number'] =\
            self.pp_partnumber(message[pos1+4: pos1+18])

        # Combined DID F12E:
        f12e_dict = self.get_did_f12e(message[(message.find('F12E', pos1+18))
                                              :(message.find('F12E', pos1+18)+76)], sddb_dict)
        # ECU serial:
        pos1 = message.find('F18C', pos1+18)
        eda0_dict_wo_f12e['ECU Serial Number'] =\
            self.pp_ecu_serial_number(message[pos1+4: pos1+12])

        # Combining the dicts
        eda0_dict = {**eda0_dict_wo_f12e, **f12e_dict}
        return eda0_dict

    def pp_combined_did_eda0_pbl(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0 for PBL
        """
        pos = message.find('EDA0')
        retval = title
        pos1 = message.find('F121', pos)
        retval = retval + "PBL_Diagnostic_Database_Part_Number '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN                '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + "ECU_Delivery_Assembly PN            '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F18C', pos1+18)
        retval = retval + "ECU_Serial_Number                   '"\
                        + self.pp_ecu_serial_number(message[pos1+4: pos1+12], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F125', pos1+12)
        retval = retval + "PBL_Sw_part_Number                  '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        return title + " " + retval


    def pp_combined_did_eda0_sbl(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0 for SBL
        """
        pos = message.find('EDA0')
        retval = title
        pos1 = message.find('F122', pos)
        retval = retval + "SBL_Diagnostic_Database_Part_Number '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN                '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F18C', pos1+18)
        retval = retval + "ECU_Serial_Number                   '"\
                        + self.pp_ecu_serial_number(message[pos1+4: pos1+12], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F124', pos1+12)
        retval = retval + "SBL_Sw_version_Number               '"\
                        + self.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        return title + " " + retval


    def get_did_f12e(self, payload, sddb_dict):
        """
        Returns DID F12E content in a dict.
        """

        f12e_dict: dict = {}

        for resp_item in sddb_dict['F12E']:
            name = resp_item.get('name')
            offset = resp_item.get('offset')
            size = resp_item.get('size')

            start = int(offset, HEX_BASE)*BYTE_SIZE
            end = start+(int(size, HEX_BASE)*BYTE_SIZE)

            if len(payload) >= end:
                part_number = self.pp_partnumber(payload[start + DID_OFFSET:end + DID_OFFSET])
                f12e_dict[name] = part_number
            else:
                raise RuntimeError('Payload is to short!')
        return f12e_dict


    def pp_did_f12e(self, message, title=''):
        """
        PrettyPrint DID F12E:
        """
        retval = title
        pos = message.find('F12E')
        # Combined DID F12E:
        retval = retval + "Number of SW part numbers '"\
                        + message[pos+4:pos+6] + "'\n"
        retval = retval + "Software Application SWLM '"\
                        + self.pp_partnumber(message[pos+6:pos+20])\
                        + "'\n"
        retval = retval + "Software Application SWP1 '"\
                        + self.pp_partnumber(message[pos+20:pos+34])\
                        + "'\n"
        retval = retval + "Software Application SWP2 '"\
                        + self.pp_partnumber(message[pos+34:pos+48])\
                        + "'\n"
        retval = retval + "Software Application SWCE '"\
                        + self.pp_partnumber(message[pos+48:pos+62])\
                        + "'\n"
        retval = retval + "ECU SW Structure PartNumb '"\
                        + self.pp_partnumber(message[pos+62:pos+76])\
                        + "'\n"
        return title + " " + retval


    @classmethod
    def extract_db_did_id(cls, d_base_dir, args):
        """
        Extract requested data from a Data Base dictionary.
        """
        message = []
        parse_did_dict = {}
        # Import Data Base if Application Diagnostic Database are compatible
        if args.did_file is not None:
            module = importlib.import_module(args.did_file[:-3])
            parse_did_dict = module.parse_ssdb_dict
        else:
            d_base_dir = d_base_dir.replace(" ", "_")
            listoffiles = os.listdir('./output')
            pattern = 'did_from_{}.py'.format(d_base_dir)
            for entry in listoffiles:
                if fnmatch.fnmatch(entry, pattern):
                    entry = entry[:-3]
                    module = importlib.import_module("output." + entry)
                    parse_did_dict = module.parse_ssdb_dict

            # Extract Service ID from database
        if parse_did_dict != {}:
            for key in parse_did_dict.keys():
                message.append(parse_did_dict[key].get('ID'))
            return message
        raise Exception("Pattern " + pattern + " not found: "
                        "Insert the dict file of DIDs manually by args")


    @classmethod
    def pp_can_nrc(cls, message):
        """
        PrettyPrint to decode negative returncode CAN_NRC
        """
        mess_len = len(message)
        if mess_len == 0:
            return "No NRC found"
        negative_return_code = {
            '00' : 'positiveResponse',
            '01' : 'ISOSAEReserved',
            '02' : 'ISOSAEReserved',
            '03' : 'ISOSAEReserved',
            '04' : 'ISOSAEReserved',
            '05' : 'ISOSAEReserved',
            '06' : 'ISOSAEReserved',
            '07' : 'ISOSAEReserved',
            '08' : 'ISOSAEReserved',
            '09' : 'ISOSAEReserved',
            '0A' : 'ISOSAEReserved',
            '0B' : 'ISOSAEReserved',
            '0C' : 'ISOSAEReserved',
            '0D' : 'ISOSAEReserved',
            '0E' : 'ISOSAEReserved',
            '0F' : 'ISOSAEReserved',
            '10' : 'generalReject',
            '11' : 'serviceNotSupported',
            '12' : 'subFunctionNotSupported',
            '13' : 'incorrectMessageLengthOrInvalidFormat',
            '14' : 'responseTooLong',
            '15' : 'ISOSAEReserved',
            '16' : 'ISOSAEReserved',
            '17' : 'ISOSAEReserved',
            '18' : 'ISOSAEReserved',
            '19' : 'ISOSAEReserved',
            '1A' : 'ISOSAEReserved',
            '1B' : 'ISOSAEReserved',
            '1C' : 'ISOSAEReserved',
            '1D' : 'ISOSAEReserved',
            '1E' : 'ISOSAEReserved',
            '1F' : 'ISOSAEReserved',
            '20' : 'ISOSAEReserved',
            '21' : 'busyRepeatReques',
            '22' : 'conditionsNotCorrect',
            '23' : 'ISOSAEReserved',
            '24' : 'requestSequenceError',
            '25' : 'ISOSAEReserved',
            '26' : 'ISOSAEReserved',
            '27' : 'ISOSAEReserved',
            '28' : 'ISOSAEReserved',
            '29' : 'ISOSAEReserved',
            '2A' : 'ISOSAEReserved',
            '2B' : 'ISOSAEReserved',
            '2C' : 'ISOSAEReserved',
            '2D' : 'ISOSAEReserved',
            '2E' : 'ISOSAEReserved',
            '2F' : 'ISOSAEReserved',
            '30' : 'ISOSAEReserved',
            '31' : 'requestOutOfRange',
            '32' : 'ISOSAEReserved ',
            '33' : 'securityAccessDenied',
            '34' : 'ISOSAEReserved',
            '35' : 'invalidKey',
            '36' : 'exceedNumberOfAttempts',
            '37' : 'requiredTimeDelayNotExpired',
            '38' : 'reservedByExtendedDataLinkSecurityDocument',
            '39' : 'reservedByExtendedDataLinkSecurityDocument',
            '3A' : 'reservedByExtendedDataLinkSecurityDocument',
            '3B' : 'reservedByExtendedDataLinkSecurityDocument',
            '3C' : 'reservedByExtendedDataLinkSecurityDocument',
            '3D' : 'reservedByExtendedDataLinkSecurityDocument',
            '3E' : 'reservedByExtendedDataLinkSecurityDocument',
            '3F' : 'reservedByExtendedDataLinkSecurityDocument',
            '40' : 'reservedByExtendedDataLinkSecurityDocument',
            '41' : 'reservedByExtendedDataLinkSecurityDocument',
            '42' : 'reservedByExtendedDataLinkSecurityDocument',
            '43' : 'reservedByExtendedDataLinkSecurityDocument',
            '44' : 'reservedByExtendedDataLinkSecurityDocument',
            '45' : 'reservedByExtendedDataLinkSecurityDocument',
            '46' : 'reservedByExtendedDataLinkSecurityDocument',
            '47' : 'reservedByExtendedDataLinkSecurityDocument',
            '48' : 'reservedByExtendedDataLinkSecurityDocument',
            '49' : 'reservedByExtendedDataLinkSecurityDocument',
            '4A' : 'reservedByExtendedDataLinkSecurityDocument',
            '4B' : 'reservedByExtendedDataLinkSecurityDocument',
            '4C' : 'reservedByExtendedDataLinkSecurityDocument',
            '4D' : 'reservedByExtendedDataLinkSecurityDocument',
            '4E' : 'reservedByExtendedDataLinkSecurityDocument',
            '4F' : 'reservedByExtendedDataLinkSecurityDocument',
            '50' : 'ISOSAEReserved',
            '51' : 'ISOSAEReserved',
            '52' : 'ISOSAEReserved',
            '53' : 'ISOSAEReserved',
            '54' : 'ISOSAEReserved',
            '55' : 'ISOSAEReserved',
            '56' : 'ISOSAEReserved',
            '57' : 'ISOSAEReserved',
            '58' : 'ISOSAEReserved',
            '59' : 'ISOSAEReserved',
            '5A' : 'ISOSAEReserved',
            '5B' : 'ISOSAEReserved',
            '5C' : 'ISOSAEReserved',
            '5D' : 'ISOSAEReserved',
            '5E' : 'ISOSAEReserved',
            '5F' : 'ISOSAEReserved',
            '60' : 'ISOSAEReserved',
            '61' : 'ISOSAEReserved',
            '62' : 'ISOSAEReserved',
            '63' : 'ISOSAEReserved',
            '64' : 'ISOSAEReserved',
            '65' : 'ISOSAEReserved',
            '66' : 'ISOSAEReserved',
            '67' : 'ISOSAEReserved',
            '68' : 'ISOSAEReserved',
            '69' : 'ISOSAEReserved',
            '6A' : 'ISOSAEReserved',
            '6B' : 'ISOSAEReserved',
            '6C' : 'ISOSAEReserved',
            '6D' : 'ISOSAEReserved',
            '6E' : 'ISOSAEReserved',
            '6F' : 'ISOSAEReserved',
            '70' : 'uploadDownloadNotAccepted',
            '71' : 'transferDataSuspended',
            '72' : 'generalProgrammingFailure',
            '73' : 'wrongBlockSequenceCounter',
            '74' : 'ISOSAEReserved',
            '75' : 'ISOSAEReserved',
            '76' : 'ISOSAEReserved',
            '77' : 'ISOSAEReserved',
            '78' : 'requestCorrectlyReceived-ResponsePending',
            '79' : 'ISOSAEReserved',
            '7A' : 'ISOSAEReserved',
            '7B' : 'ISOSAEReserved',
            '7C' : 'ISOSAEReserved',
            '7D' : 'ISOSAEReserved',
            '7E' : 'subFunctionNotSupportedInActiveSession',
            '7F' : 'serviceNotSupportedInActiveSession',
            '80' : 'ISOSAEReserved',
            '81' : 'rpmTooHigh',
            '82' : 'rpmTooLow',
            '83' : 'engineIsRunning',
            '84' : 'engineIsNotRunning',
            '85' : 'engineRunTimeTooLow',
            '86' : 'temperatureTooHigh',
            '87' : 'temperatureTooLow',
            '88' : 'vehicleSpeedTooHigh',
            '89' : 'vehicleSpeedTooLow',
            '8A' : 'throttle/PedalTooHigh',
            '8B' : 'throttle/PedalTooLow',
            '8C' : 'transmissionRangeNotInNeutral',
            '8D' : 'transmissionRangeNotInGeard',
            '8E' : 'ISOSAEReserved',
            '8F' : 'brakeSwitch(es)NotClosed',
            '90' : 'shifterLeverNotInPark',
            '91' : 'torqueConverterClutchLocked',
            '92' : 'voltageTooHigh',
            '93' : 'voltageTooLow',
            '94' : 'reservedForSpecificConditionsNotCorrect',
            '95' : 'reservedForSpecificConditionsNotCorrect',
            'FD' : 'reservedForSpecificConditionsNotCorrect',
            'FE' : 'reservedForSpecificConditionsNotCorrect',
            'FF' : 'ISOSAEReserved'
            }
        return negative_return_code.get(message[0:2], "invalid message: ") + " (" + message + ")"


    def pp_decode_7f_response(self, message):
        """
        PrettyPrint to decode negative (7F) repsonses
        """
        mess_len = len(message)
        if mess_len == 0:
            return "PP_Decode_7F_response: missing message"

        pos = message.find('7F')
        if pos == -1:
            return "no error message: '7F' not found in message "
        service = "Service: " + message[pos+2:pos+4]
        return_code = self.pp_can_nrc(message[pos+4:])
        return "Negative response: " + service + ", " + return_code


    def check_7f78_response(self, message_el):
        """
        Check if 7F message is 78: requestCorrectlyReceived-ResponsePending
        message: String to check for code 78
        return: bool, True if '78' as returncode in message
        """
        if len(message_el) == 0:
            return False
        message = message_el[0][2]
        result = False
        logging.debug("check_7f78_response message: %s", message)
        mess_len = len(message)
        if mess_len == 0:
            return False

        pos = message.find('7F')
        logging.debug("check_7f78 pos: %s", pos)
        if pos == -1:
            return False
        service = "Service: " + message[pos+2:pos+4]
        return_code = self.pp_can_nrc(message[pos+4:])
        logging.debug("check_7f78 service: %s", service)
        logging.debug("check_7f78 returncode: %s", return_code)
        logging.debug("check_7f78 [6:8] %s", message[6:8])
        if message[6:8] == '78':
            logging.info("negative response (7F) received with event code 78\
                \n (requestCorrectlyReceived-ResponsePending)")
            logging.info("Code 78: ResponsePending")
            result = True
        return result


    @classmethod
    def __routine_type(cls, routine_type):
        """
        __routine_type
        """
        r_type = str()
        if routine_type == '1':
            r_type = "Type1"
        elif routine_type == '2':
            r_type = "Type2"
        elif routine_type == '3':
            r_type = "Type3"
        else:
            r_type = "Not supported Routine Type"
        return r_type


    @classmethod
    def __routine_status(cls, status):
        """
        __routine_status
        """
        r_status = str()
        if status == '0':
            r_status = "Completed"
        elif status == '1':
            r_status = "Aborted"
        elif status == '2':
            r_status = "Currently active"
        else:
            r_status = "Not supported Routine Status"
        return r_status


    def pp_decode_routine_control_response(self, message, rtrs=''):
        """
        support function for Routine Control
        """
        testresult = True
        r_type = ""
        r_status = ""
        mess_len = len(message)
        if mess_len == 0:
            testresult = False
            logging.warning("PP_Decode_Routine_Control_response: Missing message")
        else:
            pos = message.find('71')
            if pos == -1:
                testresult = False
                logging.warning("No routine control message: '71' not found in message ")
            else:
                routine = message[pos+4:pos+8]
                r_type = self.__routine_type(message[pos+8:pos+9])
                r_status = self.__routine_status(message[pos+9:pos+10])
                logging.info("%s Routine'%s' %s", r_type, routine, r_status)
        if (r_type + ',' + r_status) == rtrs:
            logging.debug("The response is as expected")
        else:
            logging.warning("Error: received %s,%s expected Type %s", r_type, r_status, rtrs)
            testresult = False
            logging.info("teststatus:%s\n", testresult)
        return testresult


    @staticmethod
    def set_security_access_pins(sec_id):
        """
        Support function for Security Access
        """
        #iteration variable
        i = int

        #step1: load the challenge bytes, bit by bit, into a 64-bit variable space
        #insert fivefixed bytes and 3 seed
        l_init = 'FFFFFFFFFF'
        l_init = l_init + sec_id[4:6] + sec_id[2:4] + sec_id[0:2]
        # Test Pins
        #l_init = '43BB42AA41'
        #l_init = l_init + '8A' + '96' + '4E'
        l_init = bin(int(l_init, 16))
        l_init = l_init[2:]
        #Extension for Test Pins
        #l_init = '0' + l_init
        #print(hex(int(l_init[:8])))
        l_init = l_init[::-1]

        #step2: Load C541A9 hex into the 24 bit Initial Value variable space
        lista = bin(int('C541A9', 16))
        lista = lista[2:]

        #step3: Perform the Shift Right and Xor operations for 64 times
        for i in l_init:

            lista1 = bin(lista[-1] != i)
            lista1 = lista1[2:]
            # invert position of first bit with the last
            lista = lista1 + lista[:-1]
            # Xor between last reference list and last sec_id arrow
            lista3 = bin(lista[3] != lista1)
            lista3 = lista3[2:]
            #successive Xor between Blast and ....
            lista8 = bin(lista[8] != lista1)
            lista8 = lista8[2:]

            lista11 = bin(lista[11] != lista1)
            lista11 = lista11[2:]

            lista18 = bin(lista[18] != lista1)
            lista18 = lista18[2:]

            lista20 = bin(lista[20] != lista1)
            lista20 = lista20[2:]

            lista = lista [:3] + lista3 + lista[4:8]\
                               + lista8 + lista[9:11]\
                               + lista11 + lista[12:18]\
                               + lista18 + lista[19:20]\
                               + lista20 + lista[21:24]

        #step4: Generate r1, r2, r3
        r_1 = hex(int(lista[12:20], 2))
        r_1 = hex(int(r_1, 16) + int("0x200", 16))
        r_1 = r_1[3:]
        #print(r1)

        r_2 = hex(int((lista[8:12] + lista[0:4]), 2))
        r_2 = hex(int(r_2, 16) + int("0x200", 16))
        r_2 = r_2[3:]
        #print(r_2)

        r_3 = hex(int((lista[20:24] + lista[4:8]), 2))
        r_3 = hex(int(r_3, 16) + int("0x200", 16))
        r_3 = r_3[3:]
        #print(r_3)
        r_123 = hex(int(('0x' + r_1 + r_2 + r_3), 16))
        #print(r_123)
        return bytes.fromhex(r_123[2:])


    @classmethod
    def pp_string_to_bytes(cls, i, num):
        """
        convert DTCstring Number in bytes specifying number of bytes
        """
        #adding trailing 0's
        pad = '0x2'.ljust(num*2 + 3, '0')
        i = hex(int(i, 16) + int(pad, 16))
        return bytes.fromhex(i[3:])


    @classmethod
    def crc16(cls, data):
        """
        crc16
        """
        mask_crc16_citt = 0x1021
        data = bytearray(data)
        # crc initial value
        crc = 0xFFFF
        for bits in data:
            crc ^= bits << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ mask_crc16_citt
                else:
                    crc = crc << 1
            crc &= 0xffff
        return crc


    @classmethod
    def crc32_from_file(cls, filename):
        """
        CRC32_from_file
        """
        buf = (binascii.crc32(filename) & 0xFFFFFFFF)
        return "%08X" % buf


    @staticmethod
    def read_f(f_path_name):
        """
        open file 'filename', read bytewise
        """
        logging.debug("Read_f: File to read: %s", f_path_name)
        with open(f_path_name, 'rb') as f_name:
            data = f_name.read()
        return data


    @staticmethod
    def get_current_time():
        ''' Returns current time '''
        now = datetime.now()
        current_time = now.strftime("Generated %Y-%m-%d %H:%M:%S")
        return current_time


    @classmethod
    def add_ws_every_nth_char(cls, payload_in, nth):
        '''
        Adds whitespace every n:th character to the supplied string
        '''
        result = " ".join(payload_in[i:i+nth] for i in range(0, len(payload_in), nth))
        return result
