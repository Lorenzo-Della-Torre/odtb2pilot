# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-19
# version:  1.0
# reqprod:  74130

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
    Teststep 1: Change to extended session
    """
    stepno = 1
    purpose = "Change to Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x03', "")
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)    
    return result
   

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: verify RoutineControlRequest start is sent for Type 3
    """
    stepno = 2
    purpose = "verify RoutineControl start reply positively and routine Type 3 is Currently active "
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x40\x1B\x00', b'\x01')
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_frames[can_receive][0][2],'Type3,Currently active')

    return result

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: verify RoutineControlRequest stop is sent in Extended Session
    """
    stepno = 3
    purpose = "verify RoutineControl result reply positively in Extended Session and routine Type 3 is running"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x40\x1B', b'\x03')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_frames[can_receive][0][2],'Type3,Currently active')

    return result


def step_4(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 4: verify RoutineControlRequest start is sent
    """
    stepno = 4
    purpose = "verify RoutineControl stop reply positively and routine Type 3 is completed"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x40\x1B', b'\x02')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_frames[can_receive][0][2],'Type3,Completed')

    return result
    
def step_5(stub, can_send, can_receive, can_namespace, result):
    """
    # teststep 5: verify Extended session
    """
    
    stepno = 5
    purpose = "Verify Extended session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send =SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x03'
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    return result
    


def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: Change to default session
    """
    stepno = 6
    purpose = "Change to default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

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
    # action: change BECM to Extended
    # result: BECM reports mode
    test_result = step_1(network_stub, can_send, can_receive, can_namespace, test_result)

    # step2:
    # action: send start RoutineControl signal for Type 3
    # result: BECM sends positive reply
    test_result = step_2(network_stub, can_send, can_receive, can_namespace, test_result)
    
     # step3:
    # action: send result RoutineControl signal for Type 3
    # result: BECM sends positive reply
    test_result = step_3(network_stub, can_send, can_receive, can_namespace, test_result)

    # step4:
    # action: send stop RoutineControl signal for Type 3
    # result: BECM sends positive reply
    test_result = step_4(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step5:
    # action: verify extended session active
    # result: BECM send active mode
    test_result = step_5(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 6:
    # action: # Change to Default session
    # result: BECM reports mode
    test_result = step_6(network_stub, can_send, can_receive, can_namespace, test_result)

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

