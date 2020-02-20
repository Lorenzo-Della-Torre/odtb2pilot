# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-13
# version:  1.0
# reqprod:  74166

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

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 300   #seconds
    timeout = 60   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)

    # Parameters for FrameControl FC VCU
    time.sleep(1)
    block_size=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    SC.change_MF_FC(s, block_size, ST, FC_delay, FC_flag, FC_auto)

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
    stepno = 1
    purpose = "register another signal"
    SuTe.print_test_purpose(stepno, purpose)
    timeout = 15
    min_no_messages = -1
    max_no_messages = -1

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
    time.sleep(1)
    print ()
    print ("Step1: frames received ", len(SC.can_frames[can_rec]))
    print ("Step1: frames: ", SC.can_frames[can_rec], "\n")

    testresult = testresult and (len(SC.can_frames[can_rec]) > 10)

    print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 2: Change to Extended session
def step_2(stub, s, r, ns):
    global testresult

    stepno = 2
    purpose = "Change to Extended session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='065003001901F400')




# teststep 2: check for number of frames/messages for signal step1 within 10 sec
# teststep 3: change to programming, wait 1 second...
# teststep 4: clear messages/frames
# teststep 5: wait 10 sec, check for number of frames received for signal in step1
# teststep 6: check session
# teststep 7: change to default
# teststep 8: check how many frames/messages received within 10 sec

def step_3(stub, s, r, ns):
    global testresult

    stepno = 3
    purpose = "Verify subscribed signal in step 1 is sent"
    SuTe.print_test_purpose(stepno, purpose)
    can_rec = "BECMFront1Fr02"
    #SC.update_can_messages(r)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(r)
    print ("all can messages updated")
    time.sleep(1)
    print ()
    print ("Step3: frames received ", len(SC.can_frames[can_rec]))
    print ("Step3: frames: ", SC.can_frames[can_rec], "\n")

    testresult = testresult and (len(SC.can_frames[can_rec]) > 10)

    print ("Step ", stepno, " teststatus:", testresult, "\n")

# teststep 5: Change to default session
def step_4(stub, s, r, ns):
    global testresult

    stepno = 4
    purpose = "Change to default session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='065001')



def step_5(stub, s, r, ns):
    global testresult
    stepno = 5
    purpose = "Verify subscribed signal is still sent"
    SuTe.print_test_purpose(stepno, purpose)
    time.sleep(1)
    can_rec = "BECMFront1Fr02"
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(r)
    print ("all can messages updated")
    time.sleep(1)
    print ()
    print ("Step5: frames received ", len(SC.can_frames[can_rec]))
    print ("Step5: frames: ", SC.can_frames[can_rec], "\n")

    testresult = testresult and (len(SC.can_frames[can_rec]) > 10)

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
    # action: # Change to Programming session
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)

    # step2:
    # action: verify current session
    # result: BECM reports programming session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send single requests
    # result:
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step4:
    # action: update received messages, verify if DID contained"
    # result: verify if DID contained
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step5:
    # action: request another DID
    # result:
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
    SC.stop_heartbeat()
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
