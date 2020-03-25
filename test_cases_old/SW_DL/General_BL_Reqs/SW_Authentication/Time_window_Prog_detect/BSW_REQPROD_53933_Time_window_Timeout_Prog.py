# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-30
# version:  1.0
# reqprod:  53933

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
    timeout = 60   #seconds"

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

def step_1(stub):
    """
    Teststep 1: Switch the ECU off and on
    """
    stepno = 1
    purpose = "Switch the ECU off and on"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    logging.info("Relais1 on")
    SC.t_send_GPIO_signal_hex(stub, "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x00')
    time.sleep(3)
    logging.info("Relais1 off")
    SC.t_send_GPIO_signal_hex(stub, "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x01')

def step_2(stub, can_namespace):
    """
    Teststep 2: Send burst Diagnostic Session Control Programming Session with 
    periodicity of 10ms for 40 ms window
    """
    stepno = 2
    purpose = """Send burst Diagnostic Session Control Programming Session with 
                 periodicity of 10ms for 40 ms window"""
    SUTE.print_test_purpose(stepno, purpose)
    # Send NM burst (20 frames):
    # t_send_signal_hex(self, stub, signal_name, namespace, payload_value)
    # SC.send_burst(self, stub, burst_id, burst_nspace, burst_frame, 
    # burst_intervall, burst_quantity)
    SC.send_burst(stub, "Vcu1ToAllFuncFront1DiagReqFrame", can_namespace, 
                  b'\x02\x10\x82\x00\x00\x00\x00\x00', 0.010, 4)
    time.sleep(2)

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: verify session
    """
    stepno = 3
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

def step_4(stub):
    """
    Teststep 4: Switch the ECU off and on
    """
    stepno = 4
    purpose = "Switch the ECU off and on"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    logging.info("Relais1 on")
    SC.t_send_GPIO_signal_hex(stub, "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x00')
    time.sleep(3)
    logging.info("Relais1 off")
    SC.t_send_GPIO_signal_hex(stub, "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x01')

def step_5(stub, can_namespace):
    """
    Teststep 5: Send burst Diagnostic Session Control Programming Session with 
    periodicity of 2ms for 40 ms window
    """
    stepno = 5
    purpose = """Send burst Diagnostic Session Control Programming Session with 
                 periodicity of 2ms for 40 ms window"""
    SUTE.print_test_purpose(stepno, purpose)
    # Send NM burst (20 frames):
    # t_send_signal_hex(self, stub, signal_name, namespace, payload_value)
    # SC.send_burst(self, stub, burst_id, burst_nspace, burst_frame, 
    # burst_intervall, burst_quantity)
    SC.send_burst(stub, "Vcu1ToAllFuncFront1DiagReqFrame", can_namespace, 
                  b'\x02\x10\x82\x00\x00\x00\x00\x00', 0.002, 20)
    time.sleep(2)

def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: verify session
    """
    stepno = 6
    purpose = "Verify Programming session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    time.sleep(1)
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

    result = result and SUTE.test_message(SC.can_messages[can_receive], 
                                          teststring='025101')
    time.sleep(1)
    return result

def step_8(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 8: verify session
    """
    stepno = 8
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
    step_1(network_stub)

    # step 2:
    # action:
    # result: BECM sends positive reply
    step_2(network_stub, can_namespace)
    
    # step 3:
    # action: 
    # result: BECM sends positive reply
    result = step_3(network_stub, can_send, can_receive, can_namespace, result)

    # step 4:
    # action: 
    # result: BECM sends positive reply
    step_4(network_stub)

    # step 5:
    # action: 
    # result: BECM sends positive reply
    step_5(network_stub, can_namespace)
    
    # step 6:
    # action: 
    # result: BECM sends positive reply
    result = step_6(network_stub, can_send, can_receive, can_namespace, result)

    # step 7:
    # action: 
    # result: BECM sends positive reply
    result = step_7(network_stub, can_send, can_receive, can_namespace, result)

    # step 8:
    # action: 
    # result: BECM sends positive reply
    result = step_8(network_stub, can_send, can_receive, can_namespace, result)

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

