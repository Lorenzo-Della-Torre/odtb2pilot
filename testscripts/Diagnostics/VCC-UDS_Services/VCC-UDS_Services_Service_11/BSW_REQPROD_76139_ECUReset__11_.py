# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-02
# version:  1.0
# reqprod:  76139 76140

# #inspired by https://grpc.io/docs/tutorials/basic/python.html
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
    t = Thread (target=SC.send_heartbeat, args = (stub, "EcmFront1NMFr", "Front1CANCfg0", b'\x20\x40\x00\xFF\x00\x00\x00\x00',0.8))
    t.daemon = True
    t.start()
    # wait for BECM to wake up
    time.sleep(5)
    # Register signals
    
    #messages = list()
    #can_send = "Vcu1ToBecmFront1DiagReqFrame"
    #can_rec = "BecmToVcu1Front1DiagResFrame"
    #can_nspace = "Front1CANCfg0"
    

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 300   #seconds
    timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)

    # Parameters for FrameControl FC VCU
    time.sleep(1)
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    
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
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))

# teststep 1: Reset
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='025101')
    time.sleep(1)

# teststep 2: verify default session
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 3: Reset
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "ECU Reset no reply"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x81'
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='')
    time.sleep(1)

# teststep 4: verify default session
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
    purpose = "verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 5: Change to Extended session
def step_5(stub, s, r, ns):
    global testresult

    stepno = 5
    purpose = "Change to Extended session"
    time.sleep(1)
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='065003001901F400')

# teststep 6: Reset
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='025101')
    time.sleep(1)

# teststep 7: verify default session
def step_7(stub, s, r, ns):
    global testresult
    
    stepno = 7
    purpose = "verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 8: Change to Extended session
def step_8(stub, s, r, ns):
    global testresult

    stepno = 8
    purpose = "Change to Extended session"
    time.sleep(1)
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='065003001901F400')

# teststep 9: Reset
def step_9(stub, s, r, ns):
    global testresult
    
    stepno = 9
    purpose = "ECU Reset no reply"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x81'
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='')
    time.sleep(1)

# teststep 10: verify default session
def step_10(stub, s, r, ns):
    global testresult
    
    stepno = 10
    purpose = "verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 11: Change to programming session
def step_11(stub, s, r, ns):
    global testresult
    
    stepno = 11
    purpose = "Change to Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)


# teststep 12: verify session
def step_12(stub, s, r, ns):
    global testresult
    
    stepno = 12
    purpose = "Verify programming session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 13: Reset
def step_13(stub, s, r, ns):
    global testresult
    
    stepno = 13
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='025101')
    time.sleep(1)

# teststep 14: verify default session
def step_14(stub, s, r, ns):
    global testresult
    
    stepno = 14
    purpose = "verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 15: Change to programming session
def step_15(stub, s, r, ns):
    global testresult
    
    stepno = 15
    purpose = "Change to Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)


# teststep 16: verify session
def step_16(stub, s, r, ns):
    global testresult
    
    stepno = 16
    purpose = "Verify programming session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1) 

# teststep 17: Reset
def step_17(stub, s, r, ns):
    global testresult
    
    stepno = 17
    purpose = "ECU Reset no reply"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x81'
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='')
    time.sleep(1)

# teststep 18: verify default session
def step_18(stub, s, r, ns):
    global testresult
    
    stepno = 18
    purpose = "verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)   

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
    can_namespace = "Front1CANCfg0"

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
    print ()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: # ECU Reset
    # result: 
    step_1(network_stub, can_send, can_receive, can_namespace)
    
    # step4:
    # action: verify current session
    # result: BECM reports default session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: # ECU Reset(81)
    # result: 
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: verify current session
    # result: BECM reports default session
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step5:
    # action: # Change to Extended session
    # result: BECM reports mode
    step_5(network_stub, can_send, can_receive, can_namespace)

    # step 6:
    # action: # ECU Reset
    # result: 
    step_6(network_stub, can_send, can_receive, can_namespace)
    
    # step7:
    # action: verify current session
    # result: BECM reports default session
    step_7(network_stub, can_send, can_receive, can_namespace)
    
    # step8:
    # action: # Change to Extended session
    # result: BECM reports mode
    step_8(network_stub, can_send, can_receive, can_namespace)

    # step9:
    # action: # ECU Reset(81)
    # result:
    step_9(network_stub, can_send, can_receive, can_namespace)

    # step10:
    # action: verify current session
    # result: BECM reports default session
    step_10(network_stub, can_send, can_receive, can_namespace)

    # step11:
    # action: # Change to Programming session
    # result: BECM reports mode
    step_11(network_stub, can_send, can_receive, can_namespace)

    # step12:
    # action: verify current session
    # result: BECM reports programming session
    step_12(network_stub, can_send, can_receive, can_namespace)

    # step 13:
    # action: # ECU Reset
    # result:
    step_13(network_stub, can_send, can_receive, can_namespace)

    # step14:
    # action: verify current session
    # result: BECM reports default session
    step_14(network_stub, can_send, can_receive, can_namespace)

    # step15:
    # action: # Change to Programming session
    # result: BECM reports mode
    step_15(network_stub, can_send, can_receive, can_namespace)

    # step16:
    # action: verify current session
    # result: BECM reports programming session
    step_16(network_stub, can_send, can_receive, can_namespace)

    # step17:
    # action: # ECU Reset(81)
    # result:
    step_17(network_stub, can_send, can_receive, can_namespace)

    # step18:
    # action: verify current session
    # result: BECM reports default session
    step_18(network_stub, can_send, can_receive, can_namespace)

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
    print ()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
