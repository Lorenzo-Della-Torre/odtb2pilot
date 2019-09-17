# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   FJANSSO8 (Fredrik Jansson)
# date:     2019-08-20
# version:  1.0
# reqprod:  76524

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
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    
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


# teststep 1: Change to extended session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Change to Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 2: Verify that ReadDTCInfoSnapshotIdentification are sent. Message contains Snapshot information using subservice (03)
def step_2(stub, s, r, ns):
    global testresult
    global service_19_message
    
    stepno = 2
    purpose = "Verify that ReadDTCInfoSnapshotIdentification are sent"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "ReadDTCInfoSnapshotIdentification", b'' , b'')
    can_mr_extra = ''
  
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], '5903')
    
    # Save message for use in next steps 
    service_19_message = SC.can_messages[r][0][2]
    
    time.sleep(1)
    

# teststep 3: Verify that message contains information of DTC for specific Snapshot record Number selected from service 19 subservice ReadDTCInfoSnapshotIdentification
def step_3(stub, s, r, ns):
    global testresult
    global dtcBytes

    stepno = 3
    purpose = "Verify that message contains information of DTC for specific Snapshot record Number selected from service 19 subservice ReadDTCInfoSnapshotIdentification"
    timeout = 1 # wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    # Checking if the message is long enough to contain a DTC
    if (len(service_19_message) >= 16):
        # Pick first DTC
        dtc = service_19_message[8:14]
    else:
        testresult = False

    # Make it a byte string
    dtcBytes = bytearray.fromhex(dtc)
    print ('------------------\ndtc: ' , dtc, ' \ndtcBytes: ', dtcBytes, '\n------------------')

    can_m_send = SC.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber", dtcBytes, b'\xFF')
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], 'EF04')


# teststep 4: Request report Generic Snapshot By DTC Number
def step_4(stub, s, r, ns):
    global testresult

    stepno = 4
    purpose = "Empty reply using service AF with suppressPosRspMsgIndicationBit = True"
    timeout = 1 # wait a second for reply to be send

    # No reply expected
    min_no_messages = 0
    max_no_messages = 0

    # Using response from step 1 as input
    can_m_send = SC.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber(84)", dtcBytes, b'\xFF')
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 5: verify Extended session
def step_5(stub, s, r, ns):
    global testresult
    stepno = 5
    purpose = "Verify Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send =SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
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

    #start logging
    # to be implemented
    
    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")
    
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
    # action: Change to extended session
    # result: BECM report mode
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step 2:
    # action: Verify that ReadDTCInfoSnapshotIdentification are sent. Message contains Snapshot information using subservice (03)
    # result: BECM reply positively
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3:
    # action: Verify that message contains information of DTC for specific Snapshot record Number selected from service 19 subservice ReadDTCInfoSnapshotIdentification
    # result: BECM reply positively
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4:
    # action: Verify empty reply using service AF with suppressPosRspMsgIndicationBit = True
    # result: BECM replies with empty reply
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step 5:
    # action: Verify Extended session active
    # result: BECM sends active mode
    step_5(network_stub, can_send, can_receive, can_namespace)

    # step 6:
    # action: Change BECM to default
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
    print ("Stop heartbeat sent")
    SC.stop_heartbeat()
    #time.sleep(5)
    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them 
    SC.thread_stop()
            
    print ("Test cleanup end: ", datetime.now())
    print ()
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
