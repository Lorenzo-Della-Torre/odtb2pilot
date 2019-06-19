# project:  ODTB2 testenvironment using SignalBroker
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-06-18
# version:  1.2

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

from __future__ import print_function
from datetime import datetime
import time

import logging
import os
import sys

#import threading
#from threading import Thread
#
#import random
#
#import grpc
#import string

#sys.path.append('generated')

#import network_api_pb2
#import network_api_pb2_grpc
#import functional_api_pb2
#import functional_api_pb2_grpc
#import system_api_pb2
#import system_api_pb2_grpc
#import common_pb2

from support_can import Support_CAN
SC = Support_CAN()


#class for supporting sending/receiving CAN frames
class Support_test_ODTB2:


    def print_test_purpose(self, stepno, purpose):
        print ("\nStep     ", stepno, ":")
        print ("Purpose: ", purpose)

    
    def test_message(self, messagelist, teststring=''):
        testresult = True
    
        #print ("Messagelist: ", messagelist)
        if teststring != '' and (messagelist == '' or messagelist == []):
            print ("Bad: Empty messagelist, teststring '", teststring, "' not found")
            testresult = False
        else:
            for i in messagelist:
            #print ("can frame  ", i[2].upper())
            #print ("test against ", teststring)
                if (teststring == ''):
                    print ("Nothing expected. Received ", i[2].upper())
                elif teststring in i[2].upper():
                    print ("Good: Expected: ", teststring, " received: ", i[2].upper())
                    #continue
                else:
                    testresult = False
                    print ("Bad: Expected: ", teststring, " received: ", i[2].upper())
        return testresult

        
    def teststep(self, stub, m_send, m_receive_extra, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose="", timeout = 5, min_no_messages = -1, max_no_messages = -1, clear_old_mess= True):
        testresult = True
    
        #print ("teststep called")
        SC.clear_old_CF_frames()
        
        if clear_old_mess: 
            print ("clear old messages")
            SC.clear_all_can_frames()
            SC.clear_all_can_messages()
    
        self.print_test_purpose(step_no, purpose)
    
        # wait for messages
        # define answer to expect
        print ("build answer can_frames to receive")
        can_answer = SC.can_receive(m_send, m_receive_extra)
        print ("can_frames to receive", can_answer)
        # message to send
        print ("To send:   [", time.time(), ", ", can_send, ", ", m_send.hex().upper(),"]")
        #print ("test send CAN_MF: ")
        #SC.t_send_signal_CAN_MF(stub, can_send, can_rec, can_nspace, m_send)
        SC.t_send_signal_CAN_MF(stub, can_send, can_rec, can_nspace, m_send, True, 0x00)
        #wait timeout for getting subscribed data
        time.sleep(timeout)
       
        #print ("all can frames : ", SC.can_frames)
        #print ("all can frames for receiver : ", SC.can_frames[can_rec])
        SC.clear_all_can_messages()
        SC.update_can_messages(can_rec)
        #print ("all can messages : ", SC.can_messages)
        print ("rec can messages : ", SC.can_messages[can_rec])
        if (len(SC.can_messages[can_rec]) < min_no_messages):
            print ("Bad: min_no_messages not reached: ", len(SC.can_messages[can_rec]))
            testresult = False
        elif (not max_no_messages < 0) and (len(SC.can_messages[can_rec]) > max_no_messages):
            print ("Bad: max_no_messages ", len(SC.can_messages[can_rec]))
            testresult = False
        else:
            print ("number messages ", len(SC.can_messages[can_rec]))
            if (len(SC.can_messages[can_rec]) > 0):
                if (not min_no_messages < 0):
                    testresult = testresult and self.test_message(SC.can_messages[can_rec], can_answer.hex().upper())
        print ("Step ", step_no, " teststatus:", testresult, "\n")
        return testresult
        
#Pretty Print function support for part numbers
    def PP_PartNumber(self, i, title=''):
        try:
            y=len(i)
            # a message filled with \xFF is not readable
            if str(i[:8]) == "FFFFFFFF":
                #raise ValueError("Not readable")
                return title + i[:8]
            #error handling for messages without space between 4 BCD and 2 ascii
            elif y != 14 or str(i[8:10]) != "20":
                raise ValueError("That is not a part number: ", i)
            else:
                #error handling for message without ascii valid 
                j=int(i[10:12],16)
                x=int(i[12:14],16)
                if (j < 65) | (j > 90) | (x < 65) | (x > 90):
                    raise ValueError("No valid value to decode: " + i )
                else:
                    #fascii = str(binascii.unhexlify(i[8:14]).upper())
                    #fascii = str(i[0:8]) + fascii[2:5]
                    #return "{} {}".format(title, fascii)
                    #fascii = i[0:8] + bytes.fromhex(i[8:14]).decode('utf-8')
                    return title + i[0:8] + bytes.fromhex(i[8:14]).decode('utf-8')
        except ValueError as ve:
            print("{} Error: {}".format(title, ve))  
            return title + i 

# PrettyPrint Combined_DID EDA0:
    def PP_CombinedDID_EDA0(self, message, title=''):        
        pos = message.find('EDA0')
        retval = ""
        pos1 = message.find('F120', pos)
        retval = retval + "Application_Diagnostic_Database '" + self.PP_PartNumber (message[ pos1+4: pos1+18], message[ pos1:pos1+4] + ' ')+ "'\n"
        pos1 = message.find('F12A', pos1+18)
        retval = retval + "ECU_Core_Assembly PN            '" + self.PP_PartNumber (message[ pos1+4: pos1+18], message[ pos1:pos1+4] + ' ')+ "'\n"
        pos1 = message.find('F12B', pos1+18)
        retval = retval + "ECU_Delivery_Assembly PN        '" + self.PP_PartNumber (message[ pos1+4: pos1+18], message[ pos1:pos1+4] + ' ')+ "'\n"
        # Combined DID F12E:
        retval = retval + self.PP_DID_F12E(message[(message.find('F12E',pos1+18)):(message.find('F12E',pos1+18)+76)] )
        ## ECU serial:
        retval = retval + "ECU Serial Number         '" + message[144:152] + "'\n"
        return retval

        
# PrettyPrint DID F12E:
    def PP_DID_F12E(self, message, title=''):        
        retval = ""
        pos = message.find('F12E')
        # Combined DID F12E:
        retval = retval + "Number of SW part numbers '" + message[pos+4:pos+6] + "'\n"
        retval = retval + "Software Application SWLM '" + self.PP_PartNumber (message[pos+6:pos+20]) + "'\n"
        retval = retval + "Software Application SWP1 '" + self.PP_PartNumber (message[pos+20:pos+34]) + "'\n"
        retval = retval + "Software Application SWP2 '" + self.PP_PartNumber (message[pos+34:pos+48]) + "'\n"
        retval = retval + "Software Application SWCE '" + self.PP_PartNumber (message[pos+48:pos+62]) + "'\n"
        retval = retval + "ECU SW Structure PartNumb '" + self.PP_PartNumber (message[pos+62:pos+76]) + "'\n"
        return retval

    def PP_CAN_NRC(self, message):
        mess_len = len(message)
        if (mess_len == 0):
            return ("No NRC found")
        else:
            NRC = {
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
            return NRC.get(message[0:2], "invalid message: ") + " (" + message + ")"
                
                
        
    def PP_Decode_7F_response (self, message):
        retval = ""
        mess_len = len(message)
        if (mess_len == 0):
            return ("PP_Decode_7F_response: missing message")
        else:
            pos = message.find ('7F')
            if pos == -1:
                return ("no error message: '7F' not found in message ")
            else:
                service = "Service: " + message[pos+2:pos+4] 
                rc = self.PP_CAN_NRC(message[pos+4:])
                return "Negative response: " + service + ", " + rc

    def PP_Decode_Routine_Control_response (self, message, RTRS=''):
        testresult=True
        RType = ""
        RStatus = ""
        mess_len = len(message)
        if (mess_len == 0):
            testresult = False
            print("PP_Decode_Routine_Control_response: missing message")
        else:
            pos = message.find ('71')
            if pos == -1:
                testresult = False
                print("no routine control message: '71' not found in message ")
        
            else: 
                routine = message[pos+4:pos+8]
                if message[pos+8:pos+9] == '1':
                    RType = "Type1"
                elif message[pos+8:pos+9] == '2':
                    RType = "Type2"
                elif message[pos+8:pos+9] == '3':
                    RType = "Type3"
                else:
                    RType = "Not supported Routine Type"
                    
                if message[pos+9:pos+10] == '0':
                    RStatus = "Completed"
                elif message[pos+9:pos+10] == '1':
                    RStatus = "Aborted"
                elif message[pos+9:pos+10] == '2':
                    RStatus = "Currently active"
                else:
                    RStatus = "Not supported Routine Status"

                print(RType + " Routine'" + routine + "' " + RStatus + "\n") 
        if (RType + ',' + RStatus) == RTRS:
            print("The response is as expected"+"\n")
        else:
            print("error: received " + RType + ',' + RStatus + " expected Type" + RTRS + "\n")
            testresult = False
            print ("teststatus:", testresult, "\n")

        return testresult  


            



                
        