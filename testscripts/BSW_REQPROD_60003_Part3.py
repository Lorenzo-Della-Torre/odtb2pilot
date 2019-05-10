# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-02
# version:  1.0
# reqprod:  60003

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

import ODTB_conf

from support_can import Support_CAN
SC = Support_CAN()

from support_test_odtb2 import Support_test_ODTB2
SuTe = Support_test_ODTB2()

# Global variable:
testresult = True


    
# precondition for test running:
#  BECM has to be kept alive: start heartbeat
def precondition(stub, s, r, ns):
    global testresult
    
    # start heartbeat, repeat every 0.8 second
    SC._heartbeat = True
    t = Thread (target=SC.send_heartbeat, args = (stub, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00',0.8))
    t.daemon = True
    t.start()
    # wait for BECM to wake up
    time.sleep(5)
    # Register signals
    
    #messages = list()
    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_rec = "BecmToVcu1Front1DiagResFrame"
    can_nspace = "Front1CANCfg1"
    

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    timeout = 300   #seconds
    #timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)
    
    print()
    step_0(stub, s, r, ns)
    
    print ("precondition testok:", testresult, "\n")

    
# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult
    
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xED\xA0', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))
    

# teststep 1: verify session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    
# teststep 2: request EDA0 - complete ECU part/serial number default session
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "request EDA0 - complete ECU part/serial number to get MF reply"
    timeout = 0.0 #Don't wait - need to send FC frames
    min_no_messages = -1
    max_no_messages = -1
    
    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xED\xA0', "")
    can_mr_extra = ''
    
    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 970 #wait max 1000ms before sending FC frame back
    FC_flag = 49 #Wait
    FC_auto = False
    
    SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 3: wait maxtime to send reply for first frame, send reply
def step_3(stub, s, r, ns):

    stepno = 3
    purpose = "Verify FC with max number of WAIT frames"

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 970 # requirement: wait max 1000ms before sending FC frame back
    FC_flag = 49 #Wait
    FC_auto = False
    
    max_delay = 254   #number of delays wanted
    #max_delay = 4   #number of delays wanted
    
    print ("Step ", stepno, ":")
    print ("Purpose: ", purpose)

    SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    # do a loop:
    # send intended number of FC Wait frames
    #
    # controll number of frames sent from ECU

    
    # delay for TS in ms: if TS_delay < 127, if TS_delay between 0xF1 and 0xF9 then 100-900 usec
    # this one will allow delay bigger than 127 ms as needed for testing purposes
    #if ((TS_delay > 0xF1) & (TS_delay < 0xFA)):
    #    TSdelay = (TS_delay & 0x0F) / 10000
    #else:
    #    TSdelay = TS_delay / 1000

    for count in range(max_delay):
        time.sleep(FC_delay/1000)
        #print ("Step3 loop: messages received ", len(SC.can_messages))
        #print ("Step3 loop: messages: ", SC.can_messages, "\n")
        #SC.send_FC_frame(stub,s,ns,FC_flag,BS,ST)
        #print ("step3 FC to send:  FC_flag ", SC.can_subscribes[r][4]," BS: ",  SC.can_subscribes[r][1]," ST: ", SC.can_subscribes[r][2])
        SC.send_FC_frame(stub, s, ns, SC.can_subscribes[r][4], SC.can_subscribes[r][1], SC.can_subscribes[r][2])
        SC.can_subscribes[r][5] += 1
        print ("DelayNo.: ", SC.can_subscribes[r][5]-1, ", Number of can_frames received: ", len(SC.can_frames[r]))

        
# teststep 4: send flow control with continue flag (0x30), BS=0, ST=0
def step_4(stub, s, r, ns):
   
    stepno = 4
    purpose = "Change FC to continue (0x30)"

    BS = 0          # b'\x00'
    ST = 0          # b'\x00'
    FC_delay = 0
    FC_flag = 48    # b'\x30'
    FC_auto = True
    
    SuTe.print_test_purpose(stepno, purpose)
    #    
    time.sleep( SC.can_subscribes[r][3] / 1000)
    SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    #SC.send_FC_frame(stub,s,ns,FC_flag,BS,ST)
    SC.send_FC_frame(stub, s, ns, SC.can_subscribes[r][4], SC.can_subscribes[r][1], SC.can_subscribes[r][2])


# teststep 5: update received messages and frames, display
def step_5(stub, s, r, ns):
    global testresult
    #
    stepno = 5
    purpose = "update received messages and frames, display"

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    SuTe.print_test_purpose(stepno, purpose)
    
    time.sleep(1)
    SC.clear_all_can_messages()
    SC.update_can_messages(r)
    print()
    print ("Step5: messages received ", len(SC.can_messages))
    print ("Step5: messages: ", SC.can_messages, "\n")
    print ("Step5: frames received ", len(SC.can_frames))
    print ("Step5: frames: ", SC.can_frames, "\n")
    print("Test if string contains all IDs expected:")
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='62EDA0')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F120')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12B')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12E')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')
    

def run():
    global testresult

    #start logging
    # to be implemented
    
    # where to connect to signal_broker
    channel = grpc.insecure_channel(ODTB_conf.ODTB2_DUT + ':' + ODTB_conf.ODTB2_PORT)
    functional_stub = volvo_grpc_functional_api_pb2_grpc.FunctionalServiceStub(channel)
    network_stub = volvo_grpc_network_api_pb2_grpc.NetworkServiceStub(channel)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = "Front1CANCfg1"

    # Test PreCondition
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    root.info('BEGIN:  %s' % os.path.basename(__file__))
    
    
    print ("Testcase start: ", datetime.now())
    starttime = time.time()
    print ("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)
    
    # step2:
    # action: check current session
    # result: BECM reports programmin session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send 'hard_reset' to BECM
    # result: BECM acknowledges message
    step_3(network_stub, can_send, can_receive, can_namespace)
    
    # step4:
    # action: check current session
    # result: BECM reports default session
    step_4(network_stub, can_send, can_receive, can_namespace)
   
    # step5:
    # action: update received can messages
    # result: verify whole message received
    step_5(network_stub, can_send, can_receive, can_namespace)
    
    ############################################
    # postCondition
    ############################################
            
    print ()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))

    
    print ("Do cleanup now...")
    print ("Stop heartbeat sent")
    SC._heartbeat = False
    #time.sleep(5)

    #print ("Signals to unsubscribe")
    #print ("Number of signals subscribed ", len(SC.can_subscribes))
    #print ("Can signals subscribed to: ", SC.can_subscribes)
    for unsubsc in SC.can_subscribes:
        print ("unsubscribe signal: ", unsubsc)
        SC.can_subscribes[unsubsc][0].cancel()
        #print ("can_subscribes obj ", SC.can_subscribes[unsubsc][0])

        print ("waiting for threads to finish")
    time.sleep(5)
    
    print ("active threads remaining: " , threading.active_count())
    #cleanup
    #postcondition(network_stub)
    while threading.active_count() > 1:
        item =(threading.enumerate())[-1]
        print ("thread to join ", item)
        item.join(5)
        time.sleep(5)
        print ("active thread after join ", threading.active_count() )
        print ("thread enumerate ", threading.enumerate())
            
    print ("Test cleanup end: ", datetime.now())
    print ()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
