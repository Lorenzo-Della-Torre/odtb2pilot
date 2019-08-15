# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-07-08
# version:  1.1
# reqprod:  74180

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
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    
    time.sleep(4) #wait for ECU startup

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
    
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1
    
    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))
    
# teststep 1: register another signal
def step_1(stub, s, r, ns):
    global testresult
    global frame_step2
    stepno = 1
    purpose = "register another signal"
    SuTe.print_test_purpose(stepno, purpose)
    timeout = 300

    can_send = "ECMFront1Fr02"
    can_rec = "BECMFront1Fr02"
    can_nspace = SC.nspace_lookup("Front1CANCfg0")

    SC.subscribe_signal(stub, can_send, can_rec, can_nspace, timeout)
    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(r)
    print ("all can messages updated")
    time.sleep(10)
    print ()
    print ("Step1: messages received ", len(SC.can_messages[can_rec]))
    print ("Step1: messages: ", SC.can_messages[can_rec], "\n")
    print ("Step1: frames received ", len(SC.can_frames[can_rec]))
    frame_step2 = len(SC.can_frames[can_rec])
    print ("Step1: frames: ", SC.can_frames[can_rec], "\n")
    
    testresult = testresult and (frame_step2 > 10)
    
    print ("Step ", stepno, " teststatus:", testresult, "\n")
    
# teststep 2: verify that while service 19 is cyclically sent non-diagnostic signal is not affected
def step_2(stub, s, r, ns):
    global testresult
    global frame_step2
    stepno = 2
    purpose = "verify that while service 19 is cyclically sent non-diagnostic signal is not affected"
    timeout = 0.1 #wait a second for reply to be send
    min_no_messages = 1
    max_no_messages = 1
    number_of_frames_received = 0
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.clear_all_can_frames()

    can_rec = "BECMFront1Fr02"
    now = int(time.time())
    print(now)

    while (now + 10 > int(time.time())):
        SC.update_can_messages(r)
        can_m_send = SC.can_m_send( "ReadDTCInfoSnapshotIdentification", b'' ,b'')
        can_mr_extra = ''
        testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages) 
        number_of_frames_received += len(SC.can_frames[can_rec])

    print ("all can messages updated")
    print ("Step2: frames received ", number_of_frames_received)
    testresult = testresult and ((number_of_frames_received + 50) > frame_step2 > (number_of_frames_received - 50))
    print ("Step ", stepno, " teststatus:", testresult, "\n")
      
# Verify subscribed signal in step 1 is still sent
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "Verify subscribed non-diagnostic signal is still sent as in step 1"
    SuTe.print_test_purpose(stepno, purpose)
    can_rec = "BECMFront1Fr02"
    #SC.update_can_messages(r)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(r)
    print ("all can messages updated")
    time.sleep(10)
    print ()
    print ("Step4: frames received ", len(SC.can_frames[can_rec]))
    print ("Step4: frames: ", SC.can_frames[can_rec], "\n")

    testresult = testresult and ((len(SC.can_frames[can_rec]) + 50) > frame_step2 > (len(SC.can_frames[can_rec]) - 50))

    print ("Step ", stepno, " teststatus:", testresult, "\n")

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
    # action: Register not diagnostic message
    # result: BECM send requested signals
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action:send ReadDTCInformation cyclically 
    # result: BECM reports confirmed message
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: Verify signal is still sent
    # result: BECM send requested signals
    step_3(network_stub, can_send, can_receive, can_namespace)
    
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
