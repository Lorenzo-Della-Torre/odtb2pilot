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
import threading
from threading import Thread

import random
import time

import grpc
import string

import logging
import os
import sys

sys.path.append('generated')

import volvo_grpc_network_api_pb2
import volvo_grpc_network_api_pb2_grpc
import volvo_grpc_functional_api_pb2
import volvo_grpc_functional_api_pb2_grpc
import common_pb2

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
    
        #clear old messages
        if clear_old_mess: 
            SC.clear_all_can_frames()
            SC.clear_all_can_messages()
    
            self.print_test_purpose(step_no, purpose)
    
        # wait for messages
        # define answer to expect
        can_answer = SC.can_receive(m_send, m_receive_extra)
        #print ("can_frames to receive", can_answer)
        # message to send
        print ("To send:   [", time.time(), ", ", can_send, ", ", m_send.hex().upper(),"]")
        #print ("test send CAN_MF: ")
        #SC.t_send_signal_CAN_MF(stub, can_send, can_rec, can_nspace, m_send)
        SC.t_send_signal_CAN_MF(stub, can_send, can_rec, can_nspace, m_send, True, 0x00)
        #wait timeout for getting subscribed data
        time.sleep(timeout)
       
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
            #error andling for messages without space between 4 BCD and 2 ascii
            elif y != 14 or str(i[8:10]) != "20":
                raise ValueError("That is not a part number")
            else:
                #error andling for message without ascii valid 
                j=int(i[10:12],16)
                x=int(i[12:14],16)
                if (j < 65 | j > 90) | (x < 65 | x > 90):
                    raise ValueError("That is not a valid ascii")
                else:
                    #fascii = str(binascii.unhexlify(i[8:14]).upper())
                    #fascii = str(i[0:8]) + fascii[2:5]
                    #return "{} is: {}".format(title, fascii)
                    #fascii = i[0:8] + bytes.fromhex(i[8:14]).decode('utf-8')
                    return title + i[0:8] + bytes.fromhex(i[8:14]).decode('utf-8')
        except ValueError as ve:
            print("{} Error: {}".format(title, ve))   

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

     #Pretty Print function support for Real Time DID
    def P_DID(self, message, title,length):
        pos = message.find(title)
        return "{}".format(message[pos + 4: pos + 4 +(length*2)])
    
    #Pretty Print function support for Real Time DID
    def PP_DID(self, message, title, length):
        retval = ""
        if title=='Global Real Time':
            retval = "Global Real Time'" + self.P_DID(message,'DD00', length) + "'\n" 
            
        elif title=='Total Distance':
            retval = "Total Distance'" + self.P_DID(message,'DD01', length) + "'\n"

        elif title=='Vehicle Battery Voltage':
            retval = "Vehicle Battery Voltage'" + self.P_DID(message,'DD02', length) + "'\n"

        elif title=='Usage Mode':
            retval = "Usage Mode'" + self.P_DID(message,'DD0A', length) + "'\n"

        elif title=='PNC':
            retval = "PNC'" + self.P_DID(message,'DD0B', length) + "'\n"
        
        else:
            print('not supported DID PP')
        return retval
