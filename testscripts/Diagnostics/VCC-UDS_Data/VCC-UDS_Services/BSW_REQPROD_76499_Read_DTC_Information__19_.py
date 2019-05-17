# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-17
# version:  1.0
# reqprod:  76499

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
    

# teststep 1: verify session
def step_1(stub, s, r, ns):
    global testresult
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
#support function for reading out DTC/DID data:
    #services
    #"DiagnosticSessionControl"=10
    #"ReadDTCInfoExtDataRecordByDTCNumber"=19 06
    #"ReadDTCInfoSnapshotRecordByDTCNumber"= 19 04
    #"ReadDTCByStatusMask" = 19 02 + "confirmedDTC"=03 / "testFailed" = 00
    #"ReadDataByIdentifier" = 22
#def can_m_send_SC():
    #return SC.can_m_send( "ReadDataByIdentifieraa", b'\xF1\x20', "confirmedDTC")
         
# teststep 2: verify that padded bytes in SF contain 0x00
def step_2(stub, s, r, ns):
    global testresult
    #global can_frames
    #global can_messages
    
    
    #SC.can_m_send( "Read counters", b'\x0B\x45\x00') #Request current session
    # b'x\0B\x4A\x00' Hybrid/EV Battery Voltage Sense "D" Circuit--
    # b'x\01'         Operation cycle counter #1
    # b'x\02'         Operation cycle counter #2
    # b'x\03'         Operation cycle counter #3
    # b'x\04'         Operation cycle counter #4
    # b'x\05'         Operation cycle counter #5
    # b'x\06'         Operation cycle counter #6
    # b'x\07'         Operation cycle counter #7
    # b'x\10'         DTC fault detection counter
    # b'x\12'         Max DTC fault detection since last clear
    # b'x\20'         DTC time stamp 20
    # b'x\21'         DTC time stamp 21
    # b'x\30'         DTC Status indicator 30
    # b'x\FF'         return all available values
    
    can_m_send = SC.can_m_send( "ReadDTCInfoExtDataRecordByDTCNumber", b'\x0B\x4A\x00' , b'\xFF')
    # adding can_mr_extra won't work as it get a CAN_MF
    #can_mr_extra = b'\x0B\x4A\x00'
    can_mr_extra = ''
    #print(SC.can_m_send( "Read counters", b'\x0B\x45\x00'))
    stepno = 2
    purpose = "verify that DTC info are sent"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = 1
    max_no_messages = 1
  
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    #SuTe.test_message(SC.can_frames[r], teststring='0462F18601000000')
    #print ("Step ", stepno, " teststatus:", testresult, "\n")
    time.sleep(1)
    
    #SC.clear_all_can_messages()
    #print ("all can messages cleared")
    #SC.update_can_messages(r)
    #print ("all can messages updated")
    print ()
    print ("Step2: frames received ", len(SC.can_frames[r]))
    print ("Step2: frames: ", SC.can_frames[r], "\n")
    print ("Step2: messages received ", len(SC.can_messages[r]))
    print ("Step2: messages: ", SC.can_messages[r], "\n")

    # Did you get a positive or negative reply?
    
    #return(SC.can_frames[r])
    #return(SC.can_messages[r])
    print ("Error  message: ")
    print ("SC.can_messages[r]",SC.can_messages[r][0][2]) 
    print (SuTe.PP_Decode_7F_response(SC.can_messages[r][0][2]))
    print ("Step ", stepno, " teststatus:", testresult, "\n")

def run():
    global testresult

    #start logging
    # to be implemented
    
    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg1")

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
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)
    
    # step2:
    # action: Request battery temp sensor error status
    # result: BECM reports status as MF frame, padded bytes in last frame
    step_2(network_stub, can_send, can_receive, can_namespace)
    

        
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

