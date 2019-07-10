# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-07-04
# version:  1.0
# reqprod:  76512

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

from datetime import datetime
import time
import logging
import os
import sys

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
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    
    timeout = 40   #seconds
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
    min_no_messages = -1
    max_no_messages = -1
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))
    

# teststep 1: Change to Extended session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Change to Extended session(03) from default"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
         
# teststep 2: verify that Read DTC Extent Info are sent
def step_2(stub, s, r, ns):
    global testresult
    global DTCnumber
    global DTC_ExtDataRecordNumber

    stepno = 2
    purpose = "verify that Read DTC Extent Info are sent"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send(  "ReadDTCInfoExtDataRecordByDTCNumber", b'\x0B\x4A\x00' , b'\xFF')
    can_mr_extra = ''
  
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], '5906')
    time.sleep(1)

    print ()
    print ("Step2: frames received ", len(SC.can_frames[r]))
    print ("Step2: frames: ", SC.can_frames[r], "\n")
    print ("Step2: messages received ", len(SC.can_messages[r]))
    print ("Step2: messages: ", SC.can_messages[r], "\n")

    
    DTCnumber = SuTe.PP_StringTobytes(SC.can_frames[r][0][2][8:14],3)
    print(DTCnumber)
    DTC_ExtDataRecordNumber = SuTe.PP_StringTobytes(SC.can_frames[r][1][2][2:4],1)
    print(DTC_ExtDataRecordNumber)

# teststep 3: verify that ExtDataRecordByDTCNumber are sent for specific number
def step_3(stub, s, r, ns):
    global testresult
    global DTCnumber
    global DTC_ExtDataRecordNumber

    stepno = 3
    purpose = "verify that ExtDataRecordByDTCNumber are sent for specific number"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDTCInfoExtDataRecordByDTCNumber", DTCnumber ,DTC_ExtDataRecordNumber)
    can_mr_extra = ''
  
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], '5906')
    time.sleep(1)
    
    print ()
    print ("Step3: frames received ", len(SC.can_frames[r]))
    print ("Step3: frames: ", SC.can_frames[r], "\n")
    print ("Step3: messages received ", len(SC.can_messages[r]))
    print ("Step3: messages: ", SC.can_messages[r], "\n")

# teststep 4: verify that ExtDataRecordByDTCNumber reply with empty message
def step_4(stub, s, r, ns):
    global testresult
    global DTCnumber
    global DTC_ExtDataRecordNumber

    stepno = 4
    purpose = "verify that ExtDataRecordByDTCNumber reply with empty message"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDTCInfoExtDataRecordByDTCNumber(86)", DTCnumber ,DTC_ExtDataRecordNumber)
    can_mr_extra = ''
  
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and not SC.can_messages[r]
    time.sleep(1)
    
    print ()
    print ("Step4: frames received ", len(SC.can_frames[r]))
    print ("Step4: frames: ", SC.can_frames[r], "\n")
    print ("Step4: messages received ", len(SC.can_messages[r]))
    print ("Step4: messages: ", SC.can_messages[r], "\n")

    # teststep 5: verify extended session
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
    purpose = "Verify extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x03'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

# teststep 6: Change to default session
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "Change to default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

def run():
    global testresult
    
    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg1")

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
    # action: change BECM to Extended
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: send signal SnapshotIdentification
    # result: BECM respond positively
    step_2(network_stub, can_send, can_receive, can_namespace)
    
    # step3:
    # action: send signal ExtDataRecordByDTCNumber with specific data record numbers
    # result: BECM respond positively
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: send signal ExtDataRecordByDTCNumber with specific data record numbers (86)
    # result: BECM send empty frame
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step5:
    # action: Verify Extended session active
    # result: BECM sends active mode
    step_5(network_stub, can_send, can_receive, can_namespace)
    
    # step 6:
    # action: change BECM to default
    # result: BECM report mode
    step_6(network_stub, can_send, can_receive, can_namespace)
    

        
    ############################################
    # postCondition
    ############################################
            
    print()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print ("Do cleanup now...")
    print ("Stop all periodic signals sent")
    #SC.stop_heartbeat()
    SC.stop_periodic_all()
    #time.sleep(5)

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them 
    SC.thread_stop()
            
    print ("Test cleanup end: ", datetime.now())
    print()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()

