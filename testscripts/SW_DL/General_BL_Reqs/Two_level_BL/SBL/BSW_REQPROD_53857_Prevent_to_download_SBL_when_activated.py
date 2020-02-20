# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-14
# version:  1.1
# reqprod:  53857
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

import time
from datetime import datetime
import sys

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
    timeout = 120   #seconds"

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
    return result

def step_1(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 1: Download SBL
    """
    stepno = 1
    purpose = "Download of SBL"
    result = result and SSBL.sbl_download(stub, can_send,
                                            can_receive, can_namespace, stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: Re-Download and Activate SBL
    """
    stepno = 2
    purpose = "Re-Download and Activation of SBL"
    result = result and SSBL.sbl_activation(stub, can_send,
                                            can_receive, can_namespace, stepno, purpose)
    return result

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: Read VBF files for SBL
    """
    stepno = 3
    purpose = "SBL files reading"
    global offset, data, data_format

    SUTE.print_test_purpose(stepno, purpose)

    offset, data, _, _, data_format = SSBL.read_vbf_file_sbl(1)

    return result

def step_4(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 4: Extract data for the 1st block from VBF
    """
    stepno = 4
    purpose = "EXtract data for the 1st block from VBF"
    global block_addr_by, block_len_by, offset

    SUTE.print_test_purpose(stepno, purpose)

    _, _, block_addr_by, block_len_by, _, _ = SSBL.block_data_extract(offset, data)

    return result

def step_5(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 5: Request Download the 1st SBL block
    """
    stepno = 5
    purpose = "Request Download the 1st SBL block"

    timeout = 0.05
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x34' + data_format + b'\x44'+ block_addr_by + block_len_by
    can_mr_extra = ''

    # Parameters for FrameControl FC
    block_size=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue sends
    FC_auto = False

    SC.change_MF_FC(can_send, block_size, ST, FC_delay, FC_flag, FC_auto)

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_receive, can_namespace, stepno, purpose,
                                          timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='7F3431')
    print(SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
    return result

def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: Reset
    """
    stepno = 6
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

def step_7(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 7: Download and Activate SBL after Hard Reset
    """
    stepno = 7
    purpose = "Download and Activation of SBL after Hard Reset"
    result = result and SSBL.sbl_activation(stub, can_send,
                                            can_receive, can_namespace, stepno, purpose)
    return result

def step_8(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 8: Reset
    """
    stepno = 8
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

def step_9(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 9: verify session
    """
    stepno = 9
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
    # action: Change to Programming session
    # result: BECM sends positive reply
    test_result = step_2(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 3:
    # action: Request Security Access
    # result: BECM sends positive reply
    test_result = step_3(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 4:
    # action: Send security access key
    # result: BECM sends positive reply
    test_result = step_4(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 5:
    # action: SBL Download
    # result: BECM sends positive reply
    test_result = step_5(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 6:
    # action: SBL Download
    # result: BECM sends positive reply
    test_result = step_6(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 7:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = step_7(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 8:
    # action:
    # result:
    test_result = step_8(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 9:
    # action:
    # result:
    test_result = step_9(network_stub, can_send, can_receive, can_namespace, test_result)

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
