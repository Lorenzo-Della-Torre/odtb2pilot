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
    
    can_m_send = b'\x22\xED\xA0'
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    

# teststep 1: verify session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = b'\x10\x03'
    can_mr_extra = b'\x03'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

    # teststep 1: verify session
def step_1a(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = b'\x22\xF1\x86'
    can_mr_extra = b'\x03'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

    
# teststep 2: send several requests at one time - requires SF to send, MF for reply
def step_2(stub, s, r, ns):
    global testresult
    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    stepno = 2
    purpose = "send several requests at one time - requires SF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1
    
    can_m_send = b'\x22\xF1\x20\xF1\x2A'
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    #SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #print ("Step2: frames received ", len(SC.can_frames))
    #print ("Step2: frames: ", SC.can_frames, "\n")


# teststep 3: update received messages and frames, display
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "update received messages and frames, display"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    SuTe.print_test_purpose(stepno, purpose)
    
    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.update_can_messages(r)
    print ("all can messages updated")
    print()
    print ("Step3: messages received ", len(SC.can_messages[r]))
    print ("Step3: messages: ", SC.can_messages[r], "\n")
    print ("Step3: frames received ", len(SC.can_frames[r]))
    print ("Step3: frames: ", SC.can_frames[r], "\n")
    print("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F120')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')

    
# teststep 4: request 10 DID in one request - those with shortest reply
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
    purpose = "request 10 DID in one request - those with shortest reply (MF send, MF reply)"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    #can_m_send = b'\x22\xF1\x20\xF1\x2A\xF1\x2B\xF1\x2E\xF1\x8C\xF1\x86\xF1\x26\xF2\x00\xF2\x01\xF2\x02\xF2\x03'
    #can_m_send = b'\x22\xDD\x01'
    #can_m_send = b'\x22\xDD\x02\xDD\x0A\xDD\x0B\xDD\x0C'
    #can_m_send = b'\x22\xDC\x81\xDC\x82\xDC\x80\xDB\x80'
    
    can_m_send = b'\x22\x48\x02' #02
    can_m_send = b'\x22\x48\x03' #02
    
    can_m_send = b'\x22\x49\x1A' #01
    can_m_send = b'\x22\x49\x45' #03
    can_m_send = b'\x22\x49\x47' #02
    can_m_send = b'\x22\x49\x50' #02
    
    can_m_send = b'\x22\xDA\x80' #04
    can_m_send = b'\x22\xDA\x81' #02
    can_m_send = b'\x22\xDA\xD0' #02
    can_m_send = b'\x22\xDA\xD1' #02
    can_m_send = b'\x22\xDB\x72' #03
    #...
    can_m_send = b'\x22\xDB\x80' #03

    can_m_send = b'\x22\xDD\x01'
    #can_m_send = b'\x22\xDD\x02\xDD\x0A\xDD\x0B\xDD\x0C'
    can_m_send = b'\x22\xDD\x0C'

    can_m_send = b'\x22\xF1\x20'
    can_m_send = b'\x22\xF1\x26' #long number...036
    can_m_send = b'\x22\xF1\x2A' #07
    can_m_send = b'\x22\xF1\x2B' #07
    can_m_send = b'\x22\xF1\x2E' #long number...036
    can_m_send = b'\x22\xF1\x8C'
    can_m_send = b'\x22\xF1\x86'

    can_m_send = b'\x22\xDB\x91'

    can_m_send = b'\x22\xDD\x00' #04
    can_m_send = b'\x22\xDD\x01' #03
    can_m_send = b'\x22\xDD\x02' #01
    can_m_send = b'\x22\xDD\x0A' #01
    can_m_send = b'\x22\xDD\x0B' #03
    can_m_send = b'\x22\xDD\x0C' #01
    
    
    ##error 7F2231#
    #can_m_send = b'\x22\x00\x01'
    #...
    #can_m_send = b'\x22\x00\x0F'
    #can_m_send = b'\x22\x20\x20'
    #...
    #can_m_send = b'\x22\x20\x28'
    #can_m_send = b'\x22\x20\x30'

    #can_m_send = b'\x22\x48\x04'
    #can_m_send = b'\x22\x49\x1C'
    #can_m_send = b'\x22\xDA\x50'
    #can_m_send = b'\x22\xDA\x51'
    #can_m_send = b'\x22\xDA\x82' #02
    #can_m_send = b'\x22\xDC\x80'
    #can_m_send = b'\x22\xDC\x81'
    #can_m_send = b'\x22\xDC\x82'
    #can_m_send = b'\x22\xED\xC0'
    #...
    #can_m_send = b'\x22\xED\xC3'
    #can_m_send = b'\x22\xED\xD1'
    
    #can_m_send = b'\x22\xF1\x2C'
    #can_m_send = b'\x22\xF2\x00'
    #...
    #can_m_send = b'\x22\xF2\x1F'
    
    #\x49\x1A
    can_m_send = b'\x22\xDD\x02\xDD\x0A\xDD\x0C\x49\x47\x49\x50\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45'
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    #SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #print ("Step2: frames received ", len(SC.can_frames))
    #print ("Step2: frames: ", SC.can_frames, "\n")


# teststep 5: update received messages and frames, display
def step_5(stub, s, r, ns):
    global testresult
    
    stepno = 5
    purpose = "update received messages and frames, display"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    SuTe.print_test_purpose(stepno, purpose)
    
    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.update_can_messages(r)
    print ("all can messages updated")
    print()
    print ("Step5: messages received ", len(SC.can_messages[r]))
    print ("Step5: messages: ", SC.can_messages[r], "\n")
    print ("Step5: frames received ", len(SC.can_frames[r]))
    print ("Step5: frames: ", SC.can_frames[r], "\n")
    print("Test if string contains all IDs expected:")
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F120')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12B')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12E')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F186')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12C')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F126')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F200')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F201')
    ##testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD02')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0A')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0B')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0C')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DC80')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DC81')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DC82')

    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DA1A')

    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD02')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0C')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4947')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4950')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DAD0')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DAD1')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4802')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4803')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4945')

    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DB80')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4929')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4930')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4945')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4947')
    #testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4950')

    
# teststep 6: request 11 DID at once
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "send 11 requests at one time - fails in current version (max10)"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    can_m_send = b'\x22\x49\x1A\xDD\x02\xDD\x0A\xDD\x0C\x49\x47\x49\x50\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45'
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    #SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #print ("Step2: frames received ", len(SC.can_frames))
    #print ("Step2: frames: ", SC.can_frames, "\n")


# teststep 7: update received messages and frames, display
def step_7(stub, s, r, ns):
    global testresult
    #
    stepno = 7
    purpose = "update received messages and frames, display"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    SuTe.print_test_purpose(stepno, purpose)
    
    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.update_can_messages(r)
    print ("all can messages updated")
    print()
    print ("Step7: messages received ", len(SC.can_messages[r]))
    print ("Step7: messages: ", SC.can_messages[r], "\n")
    print ("Step7: frames received ", len(SC.can_frames[r]))
    print ("Step7: frames: ", SC.can_frames[r], "\n")
    print("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='037F223100000000')

    
# teststep 8: send 10 requests at one time - those with most bytes in return
def step_8(stub, s, r, ns):
    global testresult
    
    stepno = 8
    purpose = "send several requests at one time - requires MF to send"
    timeout = 5 # wait for message to arrive, but don't test (-1)
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    #can_m_send = b'\x22\xF1\x20\xF1\x2A\xF1\x2B\xF1\x2E\xF1\x8C\xF1\x86\xF1\x26\xF2\x00\xF2\x01\xF2\x02\xF2\x03'
    #can_m_send = b'\x22\xDD\x01'
    #can_m_send = b'\x22\xDD\x02\xDD\x0A\xDD\x0B\xDD\x0C'
    #can_m_send = b'\x22\xDC\x81\xDC\x82\xDC\x80\xDB\x80'
    
    can_m_send = b'\x22\x48\x02' #02
    can_m_send = b'\x22\x48\x03' #02
    
    can_m_send = b'\x22\x49\x1A' #01
    can_m_send = b'\x22\x49\x45' #03
    can_m_send = b'\x22\x49\x47' #02
    can_m_send = b'\x22\x49\x50' #02
    
    can_m_send = b'\x22\xDA\x80' #04
    can_m_send = b'\x22\xDA\x81' #02
    can_m_send = b'\x22\xDA\xD0' #02
    can_m_send = b'\x22\xDA\xD1' #02
    can_m_send = b'\x22\xDB\x72' #03
    #...
    can_m_send = b'\x22\xDB\x80' #03

    can_m_send = b'\x22\xDD\x01'
    #can_m_send = b'\x22\xDD\x02\xDD\x0A\xDD\x0B\xDD\x0C'
    can_m_send = b'\x22\xDD\x0C'

    can_m_send = b'\x22\xF1\x20'
    can_m_send = b'\x22\xF1\x26' #long number...036
    can_m_send = b'\x22\xF1\x2A' #07
    can_m_send = b'\x22\xF1\x2B' #07
    can_m_send = b'\x22\xF1\x2E' #long number...036
    can_m_send = b'\x22\xF1\x8C' #04
    can_m_send = b'\x22\xF1\x86' #01

    can_m_send = b'\x22\xDB\x91'

    can_m_send = b'\x22\xDD\x00' #04
    can_m_send = b'\x22\xDD\x01' #03
    can_m_send = b'\x22\xDD\x02' #01
    can_m_send = b'\x22\xDD\x0A' #01
    can_m_send = b'\x22\xDD\x0B' #03
    can_m_send = b'\x22\xDD\x0C' #01
    
    
    ##error 7F2231#
    #can_m_send = b'\x22\x00\x01'
    #...
    #can_m_send = b'\x22\x00\x0F'
    #can_m_send = b'\x22\x20\x20'
    #...
    #can_m_send = b'\x22\x20\x28'
    #can_m_send = b'\x22\x20\x30'

    #can_m_send = b'\x22\x48\x04'
    #can_m_send = b'\x22\x49\x1C'
    #can_m_send = b'\x22\xDA\x50'
    #can_m_send = b'\x22\xDA\x51'
    #can_m_send = b'\x22\xDA\x82' #02
    #can_m_send = b'\x22\xDC\x80'
    #can_m_send = b'\x22\xDC\x81'
    #can_m_send = b'\x22\xDC\x82'
    #can_m_send = b'\x22\xED\xC0'
    #...
    #can_m_send = b'\x22\xED\xC3'
    #can_m_send = b'\x22\xED\xD1'
    
    #can_m_send = b'\x22\xF1\x2C'
    #can_m_send = b'\x22\xF2\x00'
    #...
    #can_m_send = b'\x22\xF2\x1F'
    
    # send 11 requests now
    can_m_send = b'\x22\xED\xA0\xF1\x26\xF1\x2E\xDA\x80\xF1\x8C\xDD\x00\xDD\x0B\xDD\x01\x49\x45\xDB\x72'
    can_mr_extra = ''
    
    SC.change_MF_FC(s, BS, ST, FC_delay, FC_flag, FC_auto)
    #SC.change_MF_FC(r, BS, ST, FC_delay, FC_flag, FC_auto)
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 9: update received messages and frames, display
def step_9(stub, s, r, ns):
    global testresult
    #
    stepno = 9
    purpose = "update received messages and frames, display"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received (by checking ID for each serial-number)
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    SuTe.print_test_purpose(stepno, purpose)
    
    time.sleep(1)
    SC.clear_all_can_messages()
    print ("all can messages cleared")
    SC.update_can_messages(r)
    print ("all can messages updated")
    print()
    print ("Step9: messages received ", len(SC.can_messages[r]))
    print ("Step9: messages: ", SC.can_messages[r], "\n")
    print ("Step9: frames received ", len(SC.can_frames[r]))
    print ("Step9: frames: ", SC.can_frames[r], "\n")
    print("Test if string contains all IDs expected:")

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='EDA0')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F120')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12A')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12B')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12E')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')

    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F126')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F12E')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DA80')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='F18C')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD00')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD0B')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DD01')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='4945')
    testresult = testresult and SuTe.test_message(SC.can_messages[r], teststring='DB72')


    

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
    # action: update received can messages
    # result: verify whole message received
    step_3(network_stub, can_send, can_receive, can_namespace)
    
    # step4:
    # action: check current session
    # result: BECM reports default session
    step_4(network_stub, can_send, can_receive, can_namespace)
   
    step_5(network_stub, can_send, can_receive, can_namespace)
    step_6(network_stub, can_send, can_receive, can_namespace)
    step_7(network_stub, can_send, can_receive, can_namespace)
    step_8(network_stub, can_send, can_receive, can_namespace)
    # step5:
    # action: send 'hard_reset' to BECM
    # result: BECM acknowledges message
    #step_5(network_stub, can_send, can_receive, can_namespace)
    
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
