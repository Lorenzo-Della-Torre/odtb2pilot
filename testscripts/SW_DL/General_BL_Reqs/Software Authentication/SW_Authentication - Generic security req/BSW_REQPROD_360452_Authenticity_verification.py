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
import logging

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
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0", 
                       b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)
    
    SC.start_periodic(stub, "Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame", 
                      "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)
    
    # timeout = more than maxtime script takes
    timeout = 90   #seconds"

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    result = step_0(stub, can_send, can_receive, can_namespace, result)
    logging.info("Precondition testok: %s\n", result)
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
    logging.info('%s', SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result

def step_1(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = result and SSBL.SBL_Activation(stub, can_send, can_receive, can_namespace, 
                                            stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: ESS Software Part Download without Check Routine
    """
    stepno = 2
    purpose = "ESS Software Part Download without Check Routine"
    resultt, sw_signature = SSBL.SW_Part_Download_No_Check(stub, can_send, can_receive, 
                                                           can_namespace, stepno, purpose, 2)
    result = result and resultt
    return result, sw_signature

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: Check Complete And Compatible
    """
    stepno = 3
    purpose = "verify RoutineControl start are sent for Type 1"
    result = result and SSBL.Check_Complete_Compatible_Routine(stub, can_send, can_receive, 
                                                               can_namespace, stepno, purpose) 
    result = result and (SSBL.PP_Decode_Routine_Complete_Compatible
                         (SC.can_messages[can_receive][0][2]) == 'Not Complete, Compatible')                                                                                                                    
    res_before_check_memory = SC.can_messages[can_receive][0][2]
    return result, res_before_check_memory

def step_4(stub, can_send, can_receive, can_namespace, sw_signature, result):
    """
    Check memory
    """
    stepno = 4
    purpose = "Check Memory"
    result = result and SSBL.Check_Memory(stub, can_send, can_receive, can_namespace, 
                                          stepno, purpose, sw_signature)
    return result

def step_5(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 5: Check Complete And Compatible
    """
    stepno = 5
    purpose = "verify RoutineControl start are sent for Type 1"
    result = result and SSBL.Check_Complete_Compatible_Routine(stub, can_send, can_receive, 
                                                               can_namespace, stepno, purpose)
    result = result and (SSBL.PP_Decode_Routine_Complete_Compatible
                         (SC.can_messages[can_receive][0][2]) == 'Not Complete, Compatible')                                                                                                                  
    res_after_check_memory = SC.can_messages[can_receive][0][2]
    return result, res_after_check_memory

def step_6(res_after_check_memory, res_before_check_memory, result): 
    """
    Teststep 6: Check Complete And Compatible messages differ before and after Check Memory 
    """
    stepno = 6
    purpose = "Check Complete And Compatible messages differ before and after Check Memory"
    SUTE.print_test_purpose(stepno, purpose)
    result = result and res_after_check_memory != res_before_check_memory
    return result

def step_7(stub, can_send, can_receive, can_namespace, result):    
    """
    Download other SW Parts
    """
    stepno = 7
    purpose = "continue Download SW"
    for i in range(3, 7):   
        result = result and SSBL.SW_Part_Download(stub, can_send, can_receive, 
                                                  can_namespace, stepno, purpose, i)
    return result

def step_8(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 8: Check Complete And Compatible
    """
    stepno = 8
    purpose = "verify RoutineControl start are sent for Type 1"
    result = result and SSBL.Check_Complete_Compatible_Routine(stub, can_send, can_receive, 
                                                               can_namespace, stepno, purpose)
    result = result and (SSBL.PP_Decode_Routine_Complete_Compatible
                         (SC.can_messages[can_receive][0][2]) == 'Complete, Compatible')
    return result

def step_9(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 9: Reset
    """
    stepno = 9
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

def step_10(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 10: verify session
    """
    stepno = 10
    purpose = "Verify Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1
    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    result = True
    # start logging
    # to be implemented
    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################
    result = precondition(network_stub, can_send, can_receive, can_namespace, result)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    result = step_1(network_stub, can_send, can_receive, can_namespace, result)

    # step 2:
    # action:
    # result: BECM sends positive reply
    result, sw_signature = step_2(network_stub, can_send, can_receive, can_namespace, result)
    
    # step 3:
    # action: 
    # result: BECM sends positive reply
    result, res_before_check_memory = step_3(network_stub, can_send, can_receive, can_namespace, 
                                             result)
    
    # step 4:
    # action: 
    # result: BECM sends positive reply
    result = step_4(network_stub, can_send, can_receive, can_namespace, sw_signature, result)
    
    # step 5:
    # action: 
    # result: BECM sends positive reply
    result, res_after_check_memory = step_5(network_stub, can_send, can_receive, can_namespace, 
                                            result)

    # step 6:
    # action: 
    # result: BECM sends positive reply
    result = step_6(res_before_check_memory, res_after_check_memory, result)

    # step 7:
    # action: 
    # result: BECM sends positive reply
    result = step_7(network_stub, can_send, can_receive, can_namespace, result)

    # step 8:
    # action: 
    # result: BECM sends positive reply
    result = step_8(network_stub, can_send, can_receive, can_namespace, result)

    # step 9:
    # action: 
    # result: BECM sends positive reply
    result = step_9(network_stub, can_send, can_receive, can_namespace, result)

    # step 10:
    # action: 
    # result: BECM sends positive reply
    result = step_10(network_stub, can_send, can_receive, can_namespace, result)

   
    ############################################
    # postCondition
    ############################################
            
    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))
    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()
    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")

if __name__ == '__main__':
    run()
