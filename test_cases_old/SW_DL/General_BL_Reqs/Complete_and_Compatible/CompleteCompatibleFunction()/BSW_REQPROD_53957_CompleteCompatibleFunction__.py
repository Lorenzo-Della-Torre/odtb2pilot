# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0
# reqprod:  53957

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
import glob

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
from support_SBL import Support_SBL
from support_SecAcc import Support_Security_Access

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSBL = Support_SBL()
SSA = Support_Security_Access()

def precondition(stub, can_send, can_receive, can_namespace):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0",\
                       b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)

    SC.start_periodic(stub, "Networkeptalive", True,\
                      "Vcu1ToAllFuncFront1DiagReqFrame", "Front1CANCfg0",\
                      b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)

    # timeout = more than maxtime script takes
    timeout = 2000  #seconds"


    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    print()
    result = step_0(stub, can_send, can_receive, can_namespace)

    print("precondition testok:", result, "\n")
    return result

def step_0(stub, can_send, can_receive, can_namespace):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """
    stepno = 0
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', ""),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Complete ECU Part/Serial Number(s)",\
                   "timeout" : 1,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1
                  }

    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    print(SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    time.sleep(1)
    return result

def step_1(stub, can_send, can_receive, can_namespace):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(stub, can_send,
                                 can_receive, can_namespace, stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace):
    """
    Teststep 2: ESS Software Part Download
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    result = SSBL.sw_part_download(stub, SSBL.get_ess_filename(),
                                   can_send, can_receive, can_namespace,
                                   stepno, purpose)
    return result

def step_3(stub, can_send, can_receive, can_namespace):
    """
    Teststep 3: Download other SW Parts
    """
    stepno = 3
    purpose = "continue Download SW"
    result = True
    for i in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(stub, i, can_send, can_receive,
                                                  can_namespace, stepno, purpose)
    return result

def step_4(stub, can_send, can_receive, can_namespace):
    """
    Teststep 4: Check Complete And Compatible
    """
    stepno = 4
    purpose = "verify RoutineControl start are sent for Type 1"

    result = SSBL.check_complete_compatible_routine(stub, can_send, can_receive,
                                                    can_namespace, stepno, purpose)
    result = result and SUTE.test_message(SC.can_messages[can_receive], 'Complete, Compatible')
    return result

def step_5(stub, can_send, can_receive, can_namespace):
    """
    Teststep 5: Reset
    """
    stepno = 5
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ECUResetHardReset", b'', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "ECU Reset",\
                   "timeout" : 1,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1
                  }

    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_6(stub, can_send, can_receive, can_namespace):
    """
    Teststep 6: Activate SBL
    """
    stepno = 6
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(stub, can_send,
                                 can_receive, can_namespace, stepno, purpose)
    return result

def step_7(stub, can_send, can_receive, can_namespace):
    """
    Teststep 7: Download Different SW Parts variant
    """
    stepno = 7
    purpose = "Download SWP1 variant"
    result = True
    #REQ_53957_32325411XC_SWP1variant.vbf
    if len(glob.glob("./VBF_Reqprod/REQ_53057*.vbf")) == 0:
        result = False
    else:
        for f_name in glob.glob("./VBF_Reqprod/REQ_53057*.vbf"):
            result = result and SSBL.sw_part_download(stub, f_name,
                                                      can_send, can_receive, can_namespace,
                                                     stepno, purpose)
    return result

def step_8(stub, can_send, can_receive, can_namespace):
    """
    Teststep 8: Check Complete And Compatible
    """
    stepno = 8
    purpose = "verify RoutineControl start are sent for Type 1"

    result = SSBL.check_complete_compatible_routine(stub, can_send, can_receive,
                                                    can_namespace, stepno, purpose)
    result = result and SUTE.test_message(SC.can_messages[can_receive], 'Complete, Compatible')
    return result

def step_9(stub, can_send, can_receive, can_namespace):
    """
    Teststep 9: Reset
    """
    stepno = 9
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ECUResetHardReset", b'', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "ECU Reset",\
                   "timeout" : 1,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1
                  }
    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_10(stub, can_send, can_receive, can_namespace):
    """
    Teststep 10: verify session
    """
    stepno = 10
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', ""),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Verify Default session",\
                   "timeout" : 1,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1
                  }
    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    time.sleep(1)
    return result

def run():
    """
    Run
    """

    #test_result = True

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
    result = precondition(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = result and step_1(network_stub, can_send, can_receive, can_namespace)

    # step 2:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_4(network_stub, can_send, can_receive, can_namespace)

    # step 5:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_5(network_stub, can_send, can_receive, can_namespace)

    # step 6:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_6(network_stub, can_send, can_receive, can_namespace)

    # step 7:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_7(network_stub, can_send, can_receive, can_namespace)

    # step 8:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_8(network_stub, can_send, can_receive, can_namespace)

    # step 9:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_9(network_stub, can_send, can_receive, can_namespace)

    # step 10:
    # action:
    # result: BECM sends positive reply
    test_result = result and step_10(network_stub, can_send, can_receive, can_namespace)

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
