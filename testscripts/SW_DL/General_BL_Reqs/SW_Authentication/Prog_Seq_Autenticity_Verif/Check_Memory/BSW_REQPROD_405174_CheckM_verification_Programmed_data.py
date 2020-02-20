# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-02-05
# version:  1.0
# reqprod:  405174

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
    timeout = 920   #seconds"

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    #wait for signals to be registered
    time.sleep(1)
    # Change FC_auto for signal we’re sending
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

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
    result = result and SSBL.sbl_activation(stub, can_send, can_receive, can_namespace,
                                            stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: ESS Software Part Download without Check Routine
    """
    stepno = 2
    purpose = "ESS Software Part Download without Check Routine"
    resultt, sw_signature = SSBL.sw_part_download_no_check(stub, can_send, can_receive,
                                                           can_namespace, stepno, purpose, 2)
    result = result and resultt
    return result, sw_signature

def step_3(stub, can_send, can_receive, can_namespace, sw_signature, result):
    """
    Teststep 3: 1st Check memory with verification failed
    """
    stepno = 3
    purpose = "1st Check Memory with verification failed"
    sw_signature_w = sw_signature[:-1] + b'\x2A'

    result = result and SSBL.check_memory(stub, can_send, can_receive, can_namespace,
                                          stepno, purpose, sw_signature_w)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_receive][0][2])
                         == 'The signed data could not be authenticated')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_receive][0][2]))
    return result

def step_4(stub, can_send, can_receive, can_namespace, sw_signature, result):
    """
    Teststep 4: 2nd Check memory with verification failed
    """
    stepno = 4
    purpose = "2nd Check Memory with verification failed"
    sw_signature_w = sw_signature[:-1] + b'\x2C'

    result = result and SSBL.check_memory(stub, can_send, can_receive, can_namespace,
                                          stepno, purpose, sw_signature_w)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_receive][0][2])
                         == 'The signed data could not be authenticated')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_receive][0][2]))
    return result

def step_5(stub, can_send, can_receive, can_namespace, sw_signature, result):
    """
    Teststep 5: 3rd Check memory with Negative Response
    """
    stepno = 5
    purpose = "3rd Check memory with Negative Response"
    timeout = 2
    min_no_messages = -1
    max_no_messages = -1
    # Parameters for FrameControl FC
    block_size = 0
    separation_time = 0
    frame_control_delay = 0 #no wait
    frame_control_flag = 48 #continue send
    frame_control_auto = False

    SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                    frame_control_auto)

    can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\x02\x12' + sw_signature, b'\x01')
    can_mr_extra = ''
    time.sleep(1)
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='7F31')
    logging.info(SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
    return result

def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: ESS Software Part Download without Check Routine
    """
    stepno = 6
    purpose = "ESS Software Part Download without Check Routine"
    resultt, _ = SSBL.sw_part_download_no_check(stub, can_send, can_receive,
                                                can_namespace, stepno, purpose, 2)
    result = result and resultt
    return result

def step_7(stub, can_send, can_receive, can_namespace, sw_signature, result):
    """
    Teststep 7: 1st Check memory with verification failed
    """
    stepno = 7
    purpose = "1st Check Memory with verification failed"
    sw_signature_w = sw_signature[:-1] + b'\x2A'

    result = result and SSBL.check_memory(stub, can_send, can_receive, can_namespace,
                                          stepno, purpose, sw_signature_w)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_receive][0][2])
                         == 'The signed data could not be authenticated')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_receive][0][2]))
    return result

def step_8(stub, can_send, can_receive, can_namespace, sw_signature, result):
    """
    Teststep 8: 2nd Check memory with verification positive
    """
    stepno = 8
    purpose = "2nd Check memory with verification positive"
    result = result and SSBL.check_memory(stub, can_send, can_receive, can_namespace,
                                          stepno, purpose, sw_signature)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_receive][0][2])
                         == 'The verification is passed')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_receive][0][2]))
    return result

def step_9(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 9: Download other SW Parts
    """
    stepno = 9
    purpose = "continue Download SW"
    for i in range(3, 7):
        result = result and SSBL.sw_part_download(stub, can_send, can_receive,
                                                  can_namespace, stepno, purpose, i)
    return result

def step_10(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 10: Check Complete And Compatible
    """
    stepno = 10
    purpose = "verify RoutineControl start are sent for Type 1"
    result = result and SSBL.check_complete_compatible_routine(stub, can_send, can_receive,
                                                               can_namespace, stepno, purpose)
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_receive][0][2]) == 'Complete, Compatible')
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
    result = step_3(network_stub, can_send, can_receive, can_namespace, sw_signature, result)

    # step 4:
    # action:
    # result: BECM sends positive reply
    result = step_4(network_stub, can_send, can_receive, can_namespace, sw_signature, result)

    # step 5:
    # action:
    # result: BECM sends positive reply
    result = step_5(network_stub, can_send, can_receive, can_namespace, sw_signature, result)

    # step 6:
    # action:
    # result: BECM sends positive reply
    result = step_6(network_stub, can_send, can_receive, can_namespace, result)

    # step 7:
    # action:
    # result: BECM sends positive reply
    result = step_7(network_stub, can_send, can_receive, can_namespace, sw_signature, result)

    # step 8:
    # action:
    # result: BECM sends positive reply
    result = step_8(network_stub, can_send, can_receive, can_namespace, sw_signature, result)

    # step 9:
    # action:
    # result: BECM sends positive reply
    #result = step_9(network_stub, can_send, can_receive, can_namespace, result)

    # step 10:
    # action:
    # result: BECM sends positive reply
    #result = step_10(network_stub, can_send, can_receive, can_namespace, result)

    # step 11:
    # action:
    # result: BECM sends positive reply
    result = step_11(network_stub, can_send, can_receive, can_namespace, result)

    # step 12:
    # action:
    # result: BECM sends positive reply
    result = step_12(network_stub, can_send, can_receive, can_namespace, result)

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
