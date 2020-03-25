# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-03-12
# version:  1.0
# reqprod:  53927

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

WAITING_TIME = 2 #seconds
MAX_DIFF = 20 #max difference allowed for number of frame non-diagnostic received
MIN_NON_DIAG = 10 #min number of non-diagnostic frames received allowed
def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0",
                       b'\x2F\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.5)

    SC.start_periodic(stub, "Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame",
                      "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 2.0)

    # timeout = more than maxtime script takes (seconds)
    timeout = 80
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

    step_no = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', b'')
    can_mr_extra = b''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    logging.info('%s', SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result

def step_1(stub, can_receive, result):
    """
    Teststep 1: register not diagnostic signal
    """
    stepno = 1
    purpose = "register another signal"
    SUTE.print_test_purpose(stepno, purpose)
    timeout = 80

    can_send = "ECMFront1Fr02"
    can_rec = "BECMFront1Fr02"
    can_nspace = SC.nspace_lookup("Front1CANCfg0")

    SC.subscribe_signal(stub, can_send, can_rec, can_nspace, timeout)
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_receive)
    logging.info("all can messages updated")
    time.sleep(WAITING_TIME)
    logging.info("Step %s messages received %s", stepno, len(SC.can_messages[can_rec]))
    logging.info("Step %s messages: %s", stepno, SC.can_messages[can_rec])
    logging.info("Step %s frames received %s", stepno, len(SC.can_frames[can_rec]))
    frame_step1 = len(SC.can_frames[can_rec])
    logging.info("Step %s frames: %s", stepno, SC.can_frames[can_rec])

    result = result and (frame_step1 > MIN_NON_DIAG)

    logging.info("Step %s teststatus: %s", stepno, result)
    return result, frame_step1

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: Activate SBL
    """
    stepno = 2
    purpose = "Download and Activation of SBL"
    result = result and SSBL.sbl_activation(stub, can_send,
                                            can_receive, can_namespace, stepno, purpose)
    return result

def step_3(can_receive, result):
    """
    Teststep 3: Verify subscribed signal in step 1 is suspended
    """
    stepno = 3
    purpose = "Verify subscribed non-diagnostic signal is suspended"
    SUTE.print_test_purpose(stepno, purpose)
    can_rec = "BECMFront1Fr02"
    #SC.update_can_messages(r)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_receive)
    logging.info("all can messages updated")
    time.sleep(WAITING_TIME)
    logging.info("Step %s frames received %s", stepno, len(SC.can_frames[can_rec]))
    logging.info("Step %s frames: %s", stepno, SC.can_frames[can_rec])

    result = result and len(SC.can_frames[can_rec]) == 0

    logging.info("Step %s teststatus: %s", stepno, result)
    time.sleep(2)
    return result

def step_4(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 4: Change to default session
    """
    stepno = 4
    purpose = "Change to default session"
    timeout = 2
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send("DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    time.sleep(2)
    return result

def step_5(can_receive, result, frame_step1):
    """
    Teststep 5: Verify subscribed signal in step 1 is received
    """
    stepno = 5
    purpose = "Verify subscribed non-diagnostic signal is received"
    SUTE.print_test_purpose(stepno, purpose)
    can_rec = "BECMFront1Fr02"
    #SC.update_can_messages(r)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_receive)
    logging.info("all can messages updated")
    time.sleep(WAITING_TIME)
    logging.info("Step %s frames received %s", stepno, len(SC.can_frames[can_rec]))
    logging.info("Step %s frames: %s", stepno, SC.can_frames[can_rec])

    result = result and ((len(SC.can_frames[can_rec]) + MAX_DIFF) > frame_step1 >
                         (len(SC.can_frames[can_rec]) - MAX_DIFF))

    logging.info("Step %s teststatus: %s", stepno, result)
    return result

def run():
    """
    Run
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
    # action:
    # result:
    result, frame_step1 = step_1(network_stub, can_receive, result)

    # step 2:
    # action:
    # result:
    result = step_2(network_stub, can_send, can_receive, can_namespace, result)

    # step3:
    # action:
    # result:
    result = step_3(can_receive, result)

    # step4:
    # action:
    # result:
    result = step_4(network_stub, can_send, can_receive, can_namespace, result)

    # step5:
    # action:
    # result:
    result = step_5(can_receive, result, frame_step1)

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
