# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   FJANSSO8 (Fredrik Jansson)
# date:     2019-09-17
# version:  1.1
# reqprod:  76522

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

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2

SC = Support_CAN()
SUTE = Support_test_ODTB2()


def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0",
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)

    timeout = 40   #seconds
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
    timeout = 5
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
    Teststep 1: Request report Generic Snapshot By DTC Number
    """

    stepno = 1
    purpose = "Request report Generic Snapshot By DTC Number"
    timeout = 1 # wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    # Using 0AA600 for testing
    can_m_send = SC.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber",
                               b'\x0A\xA6\x00', b'\xFF')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='EF04')
    return result


def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: Request report Generic Snapshot By DTC Number for all DTCs
    """

    stepno = 2
    purpose = "Request report Generic Snapshot By DTC Number for all DTCs"
    timeout = 1 # wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber",
                               b'\xFF\xFF\xFF', b'\xFF')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='EF04')
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
    test_result = precondition(network_stub, can_send, can_receive, can_namespace, test_result)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: Request report Generic Snapshot By DTC Number
    # result: BECM reply positively
    test_result = step_1(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 2:
    # action: Request report Generic Snapshot By DTC Number for all DTCs
    # result: BECM reply positively
    test_result = step_2(network_stub, can_send, can_receive, can_namespace, test_result)


    ############################################
    # postCondition
    ############################################

    print()
    print("time ", time.time())
    print("Testcase end: ", datetime.now())
    print("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print("Do cleanup now...")
    print("Stop heartbeat sent")
    SC.stop_heartbeat()
    #time.sleep(5)
    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    print("Test cleanup end: ", datetime.now())
    print()
    if test_result:
        print("Testcase result: PASSED")
    else:
        print("Testcase result: FAILED")


if __name__ == '__main__':
    run()
