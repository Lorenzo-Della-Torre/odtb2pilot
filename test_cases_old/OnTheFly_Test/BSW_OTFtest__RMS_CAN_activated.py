# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-04
# version:  1.0
# reqprod:  none


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

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2

SC = Support_CAN()
SUTE = Support_test_ODTB2()


# Global variable:


def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0",
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    time.sleep(4) #wait for ECU startup

    timeout = 60   #seconds
    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    print()
    result = step_0(stub, can_send, can_receive, can_namespace, result)

    print("precondition testok:", result, "\n")
    return result


def step_0(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 0: Complete ECU Part/Serial Number(can_send)
    """

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(can_send)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra,
                                      can_send, can_receive, can_namespace,
                                      stepno, purpose, timeout,
                                      min_no_messages, max_no_messages)
    print(SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result


def step_1(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 1: register RMS signal
    """

    stepno = 1
    purpose = "register RMS signal"
    SUTE.print_test_purpose(stepno, purpose)
    timeout = 60
    #min_no_messages = -1
    #max_no_messages = -1

    #can_receive = "BecmRmsCanFr03"
    #can_nspace = SC.nspace_lookup(can_namespace)
    #can_nspace = SC.nspace_lookup("BecmRmsCanFr1")

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    time.sleep(1)
    #SC.clear_all_can_messages()
    print("all can messages cleared")
    #SC.clear_all_can_frames()
    SC.update_can_messages(can_receive)
    print("all can messages updated")
    time.sleep(10)
    print()
    print("Step1: messages received ", len(SC.can_messages[can_receive]))
    print("Step1: messages: ", SC.can_messages[can_receive], "\n")
    print("Step1: frames received ", len(SC.can_frames[can_receive]))
    print("Step1: frames: ", SC.can_frames[can_receive], "\n")

    result = result and (len(SC.can_frames[can_receive]) > 10)

    print("Step ", stepno, " teststatus:", result, "\n")
    return result



def run():
    """
    Run
    """

    test_result = True

    #start logging
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
    # action: Register RMS message
    # result: BECM send requested signals
    #test_result = step_1(network_stub, can_send, can_receive, can_namespace, test_result)
    test_result = step_1(network_stub, can_send,
                         "BecmRmsCanFr03", SC.nspace_lookup("BecmRmsCanFr1"),
                         test_result)


    ############################################
    # postCondition
    ############################################
    print()
    print("time ", time.time())
    print("Testcase end: ", datetime.now())
    print("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print("Do cleanup now...")
    print("Stop all periodic signals sent")
    #SC.stop_heartbeat()
    SC.stop_periodic_all()
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
