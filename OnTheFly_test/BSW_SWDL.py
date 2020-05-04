# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0

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


def precondition(stub, can_send, can_receive, can_namespace):
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
    timeout = 1800   #Normally takes about 1000 seconds, give it some extra time"

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    result = step_0(stub, can_send, can_receive, can_namespace)
    logging.info("Precondition testok: %s\n", result)
    return result

def step_0(stub, can_send, can_receive, can_namespace):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """
    stepno = 0
    #purpose = "Complete ECU Part/Serial Number(s)"
    #timeout = 1
    #min_no_messages = -1
    #max_no_messages = -1

    #ts_param = can_param
    #can_param = Dict[stub, can_send, can_rec, can_nspace, m_send, mr_extra: str]
    #ts_param = Dict()
    ts_param = {"stub": stub,\
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

    print("Step0: ts_param ", ts_param)
    print("Step0: stepno ", stepno)
    print("Step0: extra_param ", extra_param)
    print()
    #can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    #can_mr_extra = ''

    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    #result = SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
    #                       can_receive, can_namespace, stepno, purpose,
    #                       timeout, min_no_messages, max_no_messages)
    logging.info('%s', SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result

def step_1(stub, can_send, can_receive, can_namespace):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(stub, can_send, can_receive, can_namespace,\
                                 stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace):
    """
    Teststep 2: ESS Software Part Download
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    result = SSBL.sw_part_download(stub, SSBL.get_ess_filename(),\
                                   can_send, can_receive, can_namespace,\
                                   stepno, purpose)
    return result

def step_3(stub, can_send, can_receive, can_namespace):
    """
    Teststep 3: Download other SW Parts
    """
    stepno = 3
    result = True
    purpose = "continue Download SW"
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

    return result

def step_5(stub, can_send, can_receive, can_namespace):
    """
    Teststep 5: Reset
    """
    stepno = 5
    #purpose = "ECU Reset"
    #timeout = 1
    #min_no_messages = -1
    #max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''

    #ts_param = Dict()
    ts_param = {"stub" : stub,\
                "m_send" : b'\x11\x01',\
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
    #result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
    #                                  can_receive, can_namespace, stepno, purpose,
    #                                  timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_6(stub, can_send, can_receive, can_namespace):
    """
    Teststep 6: verify session
    """
    stepno = 6
    #purpose = "Verify Default session"
    #timeout = 1
    #min_no_messages = 1
    #max_no_messages = 1

    #can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', "")
    #can_mr_extra = b'\x01'

    #ts_param = Dict()
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', ""),\
                "mr_extra" : b'\x01',\
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
    #result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
    #                                  can_receive, can_namespace, stepno, purpose,
    #                                  timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    #result = True

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")
    #can_namespace = "Front1CANCfg0"

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################

    # read arguments for files to DL:
    f_sbl = ''
    f_ess = ''
    f_df = []
    for f_name in sys.argv:
        if not f_name.find('.vbf') == -1:
            print("Filename to DL: ", f_name)
            if not f_name.find('sbl') == -1:
                f_sbl = f_name
            elif not f_name.find('ess') == -1:
                f_ess = f_name
            else:
                f_df.append(f_name)
    SSBL.__init__(f_sbl, f_ess, f_df)
    SSBL.show_filenames()
    time.sleep(10)

    result = precondition(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    result = result and step_1(network_stub, can_send, can_receive, can_namespace)
    #result = step_4(network_stub, can_send, can_receive, can_namespace)
    # step 2:
    # action:
    # result: BECM sends positive reply
    result = result and step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3:
    # action:
    # result: BECM sends positive reply
    result = result and step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4:
    # action:
    # result: BECM sends positive reply
    result = result and step_4(network_stub, can_send, can_receive, can_namespace)

    # step 5:
    # action:
    # result: BECM sends positive reply
    result = result and step_5(network_stub, can_send, can_receive, can_namespace)

    # step 6:
    # action:
    # result: BECM sends positive reply
    result = result and step_6(network_stub, can_send, can_receive, can_namespace)

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
