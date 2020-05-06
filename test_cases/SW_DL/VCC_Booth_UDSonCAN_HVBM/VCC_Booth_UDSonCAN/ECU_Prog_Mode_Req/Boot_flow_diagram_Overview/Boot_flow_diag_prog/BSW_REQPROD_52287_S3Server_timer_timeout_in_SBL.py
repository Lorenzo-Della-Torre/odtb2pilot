# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-05-06
# version:  1.0
# reqprod:  52287
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

def precondition(can_param, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """
    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(can_param["stub"], "EcmFront1NMFr", "Front1CANCfg0",
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    timeout = 40   #seconds
    SC.subscribe_signal(can_param["stub"], can_param["can_send"],
                        can_param["can_rec"], can_param["can_nspace"], timeout)
    #record signal we send as well
    SC.subscribe_signal(can_param["stub"], can_param["can_rec"],
                        can_param["can_send"], can_param["can_nspace"], timeout)
    print()
    result = step_0(can_param, result)
    print("precondition testok:", result, "\n")
    return result

def step_0(can_param, result):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """
    stepno = 0
    serv_ = SC.Extract_Parameter_yml(
        "step_{}".format(stepno),
        service="ReadDataByIdentifier",
        did=b'\xED\xA0'
        )

    param_ = SC.Extract_Parameter_yml(
        "step_{}".format(stepno),
        timeout=5,
        purpose="Complete ECU Part/Serial Number(s)",
        min_no_messages=-1,
        max_no_messages=-1)

    can_param["m_send"] = SC.can_m_send(serv_["service"], serv_["did"], "")
    can_param["mr_extra"] = ''
    result = result and SUTE.teststep(can_param, stepno, param_)
    logging.info(SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_param["can_rec"]][0][2], title=''))
    return result

def step_1(can_param, result):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = result and SSBL.sbl_activation(can_param["stub"], can_param["can_send"],
                                            can_param["can_rec"], can_param["can_nspace"],
                                            stepno, purpose)
    return result

def step_2(can_param, result):
    """
    Teststep 2: verify session
    """
    stepno = 2
    serv_ = SC.Extract_Parameter_yml(
        "step_{}".format(stepno),
        service="ReadDataByIdentifier",
        did=b'\xF1\x86')

    param_ = SC.Extract_Parameter_yml(
        "step_{}".format(stepno),
        timeout=1,
        purpose="Verify Programming session",
        min_no_messages=-1,
        max_no_messages=-1,
        time_to_sleep=5)

    can_param["m_send"] = SC.can_m_send(serv_["service"], serv_["did"], "")
    can_param["mr_extra"] = b'\x02'

    result = result and SUTE.teststep(can_param, stepno, param_)
    time.sleep(param_["time_to_sleep"])
    return result

def step_3(can_param, result):
    """
    Teststep 3: verify default session
    """
    stepno = 3
    serv_ = SC.Extract_Parameter_yml(
        "step_{}".format(stepno),
        service="ReadDataByIdentifier",
        did=b'\xF1\x86')

    param_ = SC.Extract_Parameter_yml(
        "step_{}".format(stepno),
        timeout=1,
        purpose="Verify Default session",
        min_no_messages=-1,
        max_no_messages=-1,
        )

    can_param["m_send"] = SC.can_m_send(serv_["service"], serv_["did"], "")
    can_param["mr_extra"] = b'\x01'

    result = result and SUTE.teststep(can_param, stepno, param_)
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

    can_param = SC.Extract_Parameter_yml(
        "main",
        can_send="Vcu1ToBecmFront1DiagReqFrame",
        can_rec="BecmToVcu1Front1DiagResFrame",
        m_send='',
        mr_extra=''
        )
    can_param.update(stub=SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT))
    can_param.update(can_nspace=SC.nspace_lookup("Front1CANCfg0"))
    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################
    result = precondition(can_param, result)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action:
    # result:
    result = step_1(can_param, result)

    # step2:
    # action:
    # result:
    result = step_2(can_param, result)

    # step3:
    # action:
    # result:
    result = step_3(can_param, result)

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
