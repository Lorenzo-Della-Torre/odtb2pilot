# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-03-24
# version:  1.0
# reqprod:  411891

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

import ODTB_conf as ODTB_config
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
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0",
                       b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)

    SC.start_periodic(stub, "Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame",
                      "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)

    # timeout = more than maxtime script takes
    timeout = 950   #seconds"

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

    logging.info('%s', SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
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
    Teststep 2: ESS Software Part Download older version
    """
    stepno = 2
    purpose = "ESS Software Part Download older version"
    ess_vbf_old = "./VBF_Reqprod/REQ_411891_ess_32263151_AA_6M_old_version_file.vbf"
    result = SSBL.sw_part_download(stub, ess_vbf_old, can_send, can_receive,
                                   can_namespace, stepno, purpose)
    return result

def step_3(stub, can_send, can_receive, can_namespace):
    """
    Teststep 3: Updated ESS Software Part Download
    """
    stepno = 3
    purpose = "Updated ESS Software Part Download"
    ess_vbf_up = SSBL.get_ess_filename()
    result = SSBL.sw_part_download(stub, ess_vbf_up, can_send, can_receive,
                                   can_namespace, stepno, purpose)
    return result

def step_4(stub, can_send, can_receive, can_namespace):
    """
    Teststep 4: Download EXE, SIGCFG and CARCFG SWPs
    """
    result = True
    stepno = 4
    purpose = "continue Download SW"
    # loop DL for EXE, SIGCFG and CARCFG SWPs

    #for i in range(4, 8):
    #    result = result and SSBL.sw_part_download(stub, can_send, can_receive,
    #                                              can_namespace, stepno, purpose, i)
    for i in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(stub, i, can_send, can_receive,
                                                  can_namespace, stepno, purpose)
    return result

def step_5(stub, can_send, can_receive, can_namespace):
    """
    Teststep 5: Check Complete And Compatible
    """
    stepno = 5
    purpose = "verify RoutineControl start are sent for Type 1"

    result = SSBL.check_complete_compatible_routine(stub, can_send, can_receive,
                                                    can_namespace, stepno, purpose)

    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_receive][0][2]) == 'Complete, Compatible')
    return result

def step_6(stub, can_send, can_receive, can_namespace):
    """
    Teststep 6: Reset
    """
    stepno = 6
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
    #purpose = "ECU Reset"
    #timeout = 1
    #min_no_messages = -1
    #max_no_messages = -1

    #can_m_send = b'\x11\x01'
    #can_mr_extra = ''

    #result = SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
    #                       can_receive, can_namespace, stepno, purpose,
    #                       timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_7(stub, can_send, can_receive, can_namespace):
    """
    Teststep 7: verify session
    """
    stepno = 7
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

    #purpose = "Verify Default session"
    #timeout = 1
    #min_no_messages = 1
    #max_no_messages = 1

    #can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', "")
    #can_mr_extra = b'\x01'

    #result = SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
    #                       can_receive, can_namespace, stepno, purpose,
    #                       timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_config.ODTB2_DUT, ODTB_config.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
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
    result = result and step_1(network_stub, can_send, can_receive, can_namespace)

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

    # step 7:
    # action:
    # result: BECM sends positive reply
    result = result and step_7(network_stub, can_send, can_receive, can_namespace)

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
