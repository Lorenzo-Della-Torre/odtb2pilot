# project:  ODTB2 testenvironment using SignalBroker
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

"""The Python implementation of the gRPC route guide client."""

from __future__ import print_function
import logging
import time
import fnmatch
import importlib
import os
import argparse
import binascii

#sys.path.append('generated')
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
SC = SupportCAN()


class SupportTestODTB2:
    """
    Class for supporting sending/receiving CAN frames
    """

    @classmethod
    def parse_some_args(cls):
        ''' Get the command line input, using the defined flags. '''
        parser = argparse.ArgumentParser(description='Execute testscript')

        parser.add_argument("--config_file",\
                            help="Input config file which overrides the default one",
                            type=str, action='store', dest='conf_file', required=False,)
        ret_args = parser.parse_args()
        return ret_args


    @classmethod
    def config(cls, margs):
        ''' Determine which config file to use.
            If we have a config file as input parameter, then use it.
            Otherwise use default config file '''
        if margs.conf_file:
            file_name = margs.conf_file
        else:
            # Return first path of the script's name.
            f_name_wo_type = os.path.basename(__file__).split('.')[0]
            # Add .conf at the end, to show that it is a config file.
            file_name = f_name_wo_type + '.conf'
        return file_name


    @classmethod
    def print_test_purpose(cls, stepno, purpose):
        """
        print_test_purpose
        """
        print("\nStep     ", stepno, ":")
        print("Purpose: ", purpose)


    def test_message(self, messagelist, teststring=''):
        """
        test_message
        """
        testresult = True

        #print("Messagelist: ", messagelist)
        if teststring != '' and (messagelist in ('', [])):
            print("Bad: Empty messagelist, teststring '", teststring, "' not found")
            testresult = False
        else:
            for i in messagelist:
            #print("can frame  ", i[2].upper())
            #print("test against ", teststring)
                if teststring == '':
                    print("Nothing expected. Received ", i[2].upper())
                elif teststring in i[2].upper():
                    print("Good: Expected: ", teststring, " received: ", i[2].upper())
                    #continue
                else:
                    testresult = False
                    print("Bad: Expected: ", teststring, " received: ", i[2].upper())
                    print("Try to decode error message (7F): \n",
                          self.pp_decode_7f_response(i[2].upper()))
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
        SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)
        #wait timeout for getting subscribed data
        if (wait_max or (etp["max_no_messages"] == -1)):
            time.sleep(etp["timeout"])
            SC.update_can_messages(can_p["receive"])
        else:
            SC.update_can_messages(can_p["receive"])
            while((time.time()-wait_start <= etp["timeout"])
                  and (len(SC.can_messages[can_p["receive"]]) < etp["max_no_messages"])):
                SC.clear_can_message(can_p["receive"])
                SC.update_can_messages(can_p["receive"])


    def teststep(self, can_p: CanParam, cpay: CanPayload, etp: CanTestExtra):
        """
        teststep for ODTB2 testenvironment

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
        testresult = True

        SC.clear_old_cf_frames()

        clear_old_mess = True
        if "clear_old_mess" in etp:
            clear_old_mess = etp["clear_old_mess"]

        if clear_old_mess:
            logging.debug("Clear old messages")
            SC.clear_all_can_frames()
            SC.clear_all_can_messages()

        self.print_test_purpose(etp["step_no"], etp["purpose"])
        # wait for messages
        # define answer to expect
        logging.debug("Build answer can_frames to receive")
        can_answer = SC.can_receive(cpay['payload'], cpay['extra'])
        logging.debug("CAN frames to receive: %s", can_answer)

        # message to send
        self.__send(can_p, etp, cpay)

        logging.debug("Rec can messages: %s", SC.can_messages[can_p["receive"]])
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
                if etp["min_no_messages"] >= 0:
                    testresult = testresult and\
                        self.test_message(SC.can_messages[can_p["receive"]],\
                                          can_answer.hex().upper())
        logging.info("Step %s: Result teststep: %s", etp["step_no"], testresult)
        return testresult

    @classmethod
    def __pp_partnumber(cls, i, title=''):
        """
        Pretty Print function support for part numbers
        """
        try:
            len_pn = len(i)

            # a message filled with \xFF is not readable
            if str(i[:8]) == "FFFFFFFF":
                #raise ValueError("Not readable")
                return title + i[:8]
            #error handling for messages without space between 4 BCD and 2 ascii
            if len_pn != 14 or str(i[8:10]) != "20":
                raise ValueError("That is not a part number: ", i)
            #error handling for message without ascii valid
            asc_1 = int(i[10:12], 16)
            asc_2 = int(i[12:14], 16)
            if (asc_1 < 65) | (asc_1 > 90) | (asc_2 < 65) | (asc_2 > 90):
                raise ValueError("No valid value to decode: " + i)
            return title + i[0:8] + bytes.fromhex(i[8:14]).decode('utf-8')
        except ValueError as valu_err:
            print("{} Error: {}".format(title, valu_err))
            return title + i


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
            print("Message received: ", message)
        return retval

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
            print("Message received: ", message)
        return retval

    def pp_combined_did_eda0_becm_mode1_mode3(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0:
        """
        pos = message.find('EDA0')
        retval = title
        pos1 = message.find('F120', pos)
        retval = retval + "Application_Diagnostic_Database '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN            '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + "ECU_Delivery_Assembly PN        '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        # Combined DID F12E:
        retval = retval + self.pp_did_f12e(message[(message.find('F12E', pos1+18))
                                                   :(message.find('F12E', pos1+18)+76)])
        ## ECU serial:
        retval = retval + "ECU Serial Number         '" + message[144:152] + "'\n"
        return title + " " + retval


    def pp_combined_did_eda0_pbl(self, message, title=''):
        """
        PrettyPrint Combined_DID EDA0 for PBL
        """
        pos = message.find('EDA0')
        retval = title
        pos1 = message.find('F121', pos)
        retval = retval + "PBL_Diagnostic_Database_Part_Number '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN                '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + "ECU_Delivery_Assembly PN            '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F18C', pos1+18)
        retval = retval + "ECU_Serial_Number                   '"\
                        + message[pos1:pos1+4]\
                        + ' '\
                        + message[pos1+4: pos1+12]\
                        + "'\n"
        pos1 = message.find('F125', pos1+12)
        retval = retval + "PBL_Sw_part_Number                  '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
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
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN                '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        pos1 = message.find('F18C', pos1+18)
        retval = retval + "ECU_Serial_Number                   '"\
                        + message[pos1:pos1+4]\
                        + ' '\
                        + message[pos1+4: pos1+12]\
                        + "'\n"
        pos1 = message.find('F124', pos1+12)
        retval = retval + "SBL_Sw_version_Number               '"\
                        + self.__pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]\
                        + ' ')\
                        + "'\n"
        return title + " " + retval


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
                        + self.__pp_partnumber(message[pos+6:pos+20])\
                        + "'\n"
        retval = retval + "Software Application SWP1 '"\
                        + self.__pp_partnumber(message[pos+20:pos+34])\
                        + "'\n"
        retval = retval + "Software Application SWP2 '"\
                        + self.__pp_partnumber(message[pos+34:pos+48])\
                        + "'\n"
        retval = retval + "Software Application SWCE '"\
                        + self.__pp_partnumber(message[pos+48:pos+62])\
                        + "'\n"
        retval = retval + "ECU SW Structure PartNumb '"\
                        + self.__pp_partnumber(message[pos+62:pos+76])\
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
            print("PP_Decode_Routine_Control_response: missing message")
        else:
            pos = message.find('71')
            if pos == -1:
                testresult = False
                print("no routine control message: '71' not found in message ")

            else:
                routine = message[pos+4:pos+8]
                r_type = self.__routine_type(message[pos+8:pos+9])
                r_status = self.__routine_status(message[pos+9:pos+10])
                print(r_type + " Routine'" + routine + "' " + r_status + "\n")
        if (r_type + ',' + r_status) == rtrs:
            print("The response is as expected"+"\n")
        else:
            print("error: received " + r_type + ',' + r_status + " expected Type" + rtrs + "\n")
            testresult = False
            print("teststatus:", testresult, "\n")
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
        print("read_f: File to read: ", f_path_name)
        with open(f_path_name, 'rb') as f_name:
            data = f_name.read()
        return data
