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
        if (messagelist == ''):
            print ("Empty messagelist")
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
        else:
            print ("number messages ", len(SC.can_messages[can_rec]))
            if (len(SC.can_messages[can_rec]) > 0):
                if (not min_no_messages < 0):
                    testresult = testresult and self.test_message(SC.can_messages[can_rec], can_answer.hex().upper())
        print ("Step ", step_no, " teststatus:", testresult, "\n")
        return testresult
