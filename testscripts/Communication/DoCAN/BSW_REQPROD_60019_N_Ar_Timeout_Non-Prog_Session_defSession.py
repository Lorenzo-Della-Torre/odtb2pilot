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
    #timeout = 300   #seconds
    timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)
    
    print()
    step_0(stub, s, r, ns)
    
    print ("precondition testok:", testresult, "\n")

    
# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult
    can_m_send = b'\x22\xED\xA0'
    #can_mr_extra = b'\x01'
    can_mr_extra = ''
    
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))
    
# teststep 1: verify session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)
    
# teststep 2: request EDA0 - with FC delay < timeout 1000 ms
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "request EDA0 - with FC delay < timeout 1000 ms"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    BS1 = 11
    BS=0
    ST=0
    FC_flag =   48 #continue to send
    FC_delay = 950 #wait 800ms before sending FC frame back
    FC_auto = True

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xED\xA0', "")
    can_mr_extra = ''
    
    #clear_all_can_frames()
    SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    if len(SC.can_frames[r]) == BS1:
        print ("Timeout due to FC delay: ")
        print ("number of frames received as expected: ", len(SC.can_frames[r]))
    else:
        testresult = False
        print("FAIL: Wrong number of frames received. Expeced", BS1, "Received:", len(SC.can_frames[r]))
    print ("Step3: frames received ", len(SC.can_frames[r]), "\n")
    
# teststep 3: request EDA0 - with FC delay > timeout 1000 ms
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "request EDA0 - with FC delay > timeout 1000 ms"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    BS1 = 1
    BS=0
    ST=0
    FC_flag =   48 #continue to send
    FC_delay = 1050 #wait 800ms before sending FC frame back
    FC_auto = True

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xED\xA0', "")
    can_mr_extra = ''
    
    #clear_all_can_frames()
    SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    if len(SC.can_frames[r]) == BS1:
        print ("Timeout due to FC delay: ")
        print ("number of frames received as expected: ", len(SC.can_frames[r]))
    else:
        testresult = False
        print("FAIL: Wrong number of frames received. Expeced", BS1, "Received:", len(SC.can_frames[r]))
    print ("Step4: frames received ", len(SC.can_frames[r]), "\n")

 
# teststep 4: set back FC_delay to default
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
    purpose = "set back FC_delay to default"
    timeout = 5 
    min_no_messages = -1
    max_no_messages = -1

    BS1 = 1
    BS=0
    ST=0
    FC_flag =   48 #continue to send
    FC_delay =  0 
    FC_auto = True
    
    SuTe.print_test_purpose(stepno, purpose)
    #update_can_messages_2(stub, r)
    #print(can_frames, "\n")
    SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)



    # teststep 5: verify session
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
    purpose = "Verify Default session"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

def run():
    global testresult

    #start logging
    # to be implemented
    
    # where to connect to signal_broker
    #channel = grpc.insecure_channel('localhost:50051')
    
    # old Raspberry board Rpi 3B#channel
    #channel = grpc.insecure_channel('10.247.249.204:50051')
    
    # new Raspberry-board Rpi 3B+
    # ToDo: get IP via DNS
    channel = grpc.insecure_channel('10.246.47.27:50051')
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
    #print ("after precond active threads ", threading.active_count())
    #print ("after precond thread enumerate ", threading.enumerate())

    #subscribe_to_BecmFront1NMFr(network_stub)
    
    ############################################
    # teststeps
    ############################################
    # step1:
    # action: check current session
    # result: BECM reports programmin session
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: send request with FC_delay < timeout
    # result: whole message received
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send request with FC_delay > timeout
    # result: only first frame received
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: restore FC_delay again
    # result: 
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step5:
    # action: check current session
    # result: BECM reports default session
    step_5(network_stub, can_send, can_receive, can_namespace)

    
    ############################################
    # postCondition
    ############################################
            
    print()
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
    print()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()