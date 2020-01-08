# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0
# reqprod:  53959

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

import time
from datetime import datetime
import sys
import binascii
import intelhex
import struct

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
from support_SBL import Support_SBL
from support_SecAcc import Support_Security_Access

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSBL = Support_SBL()
SSA = Support_Security_Access()

def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """
        
    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0", b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)
    
    SC.start_periodic(stub,"Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame", "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)
    
    # timeout = more than maxtime script takes
    #timeout = 90   #seconds
    timeout = 2000   #seconds"


    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    print()
    result = step_0(stub, can_send, can_receive, can_namespace, result)

    print("precondition testok:", result, "\n")
    return result

def step_0(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    print(SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    time.sleep(1)
    return result

def step_1(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = result and SSBL.SBL_Activation(stub, can_send,
                                            can_receive, can_namespace, stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: ESS Software Part Download
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                              can_namespace, stepno, purpose, 2)
    return result

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: Not Compatible Software Download
    """
    stepno = 3
    purpose = "Not Compatible Software Download"
    
    result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                              can_namespace, stepno, purpose, 3)
    return result

def step_4(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 4: Check Complete And Compatible
    """
    stepno = 4
    purpose = "verify RoutineControl start are sent for Type 1"

    result = result and SSBL.Check_Complete_Compatible_Routine(stub, can_send, can_receive, 
                                                               can_namespace, stepno, purpose)
    result = result and SUTE.test_message(SC.can_messages[can_receive], 'Not Complete, Compatible')
    return result

def step_5(stub, can_send, can_receive, can_namespace, result):    
    """
    Download other SW Parts
    """
    stepno = 5
    purpose = "continue Download SW"
    for i in range(4, 7):
        
        result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                                  can_namespace, stepno, purpose, i)

    return result

def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: Check Complete And Compatible
    """
    stepno = 6
    purpose = "verify RoutineControl start are sent for Type 1"

    result = result and SSBL.Check_Complete_Compatible_Routine(stub, can_send, can_receive, 
                                                               can_namespace, stepno, purpose)
    result = result and SUTE.test_message(SC.can_messages[can_receive], 'Complete, Not Compatible')
    return result

def step_7(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 7: Reset
    """
    
    stepno = 7
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_8(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 8: Activate SBL
    """
    stepno = 8
    purpose = "Download and Activation of SBL"
    result = result and SSBL.SBL_Activation(stub, can_send,
                                            can_receive, can_namespace, stepno, purpose)
    return result

def step_9(stub, can_send, can_receive, can_namespace, result):    
    """
    Teststep 9: Download Compatibles SW Parts
    """
    stepno = 9
    purpose = "Download compatibles SW"
    result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                              can_namespace, stepno, purpose, 2)
    result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                              can_namespace, stepno, purpose, 7)
    for i in range(4, 7):
        
        result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                                  can_namespace, stepno, purpose, i)

    return result

def step_10(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 10: Check Complete And Compatible
    """
    stepno = 10
    purpose = "verify RoutineControl start are sent for Type 1"

    result = result and SSBL.Check_Complete_Compatible_Routine(stub, can_send, can_receive, 
                                                               can_namespace, stepno, purpose)
    result = result and SUTE.test_message(SC.can_messages[can_receive], 'Complete, Compatible')
    return result

def step_11(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 11: Reset
    """ 
    stepno = 11
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_12(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 12: verify session
    """
    stepno = 12
    purpose = "Verify Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    return result

def run():
    """
    Run
    """

    test_result = True

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    print("Testcase start: ", datetime.now())
    starttime = time.time()
    print("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    test_result = precondition(network_stub, can_send, can_receive, can_namespace,test_result)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = step_1(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 2:
    # action:
    # result: BECM sends positive reply
    test_result = step_2(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 3:
    # action: 
    # result: BECM sends positive reply
    #test_result = step_3(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 4:
    # action: 
    # result: BECM sends positive reply
    #test_result = step_4(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 5:
    # action: 
    # result: BECM sends positive reply
    test_result = step_5(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 6:
    # action: 
    # result: BECM sends positive reply
    #test_result = step_6(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 7:
    # action: 
    # result: BECM sends positive reply
    #test_result = step_7(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 8:
    # action: 
    # result: BECM sends positive reply
    #test_result = step_8(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 9:
    # action: 
    # result: BECM sends positive reply
    #test_result = step_9(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 10:
    # action: 
    # result: BECM sends positive reply
    test_result = step_10(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 11:
    # action: 
    # result: BECM sends positive reply
    test_result = step_11(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 12:
    # action: 
    # result: BECM sends positive reply5
    test_result = step_12(network_stub, can_send, can_receive, can_namespace, test_result)
   
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
    if test_result:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
