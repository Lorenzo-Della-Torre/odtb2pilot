"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-03
# version:  1.1
# reqprod:  74166

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_1(can_p):
    """
    Teststep 1: register another signal
    """
    stepno = 1
    etp: CanTestExtra = {
        "purpose" : "register another signal",
        "timeout" : 15,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.parameter_adopt_teststep(etp)

    can_p_ex: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "ECMFront1Fr02",
        "receive" : "BECMFront1Fr02",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.parameter_adopt_teststep(can_p_ex)

    SC.subscribe_signal(can_p_ex, etp["timeout"])
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.info("all can messages updated")
    time.sleep(1)
    logging.info("Step%s: messages received %s", stepno,
                 len(SC.can_messages[can_p_ex["receive"]]))
    logging.info("Step%s: messages: %s \n", stepno,
                 SC.can_messages[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", stepno,
                 len(SC.can_frames[can_p_ex["receive"]]))
    logging.info("Step%s: frames: %s \n", stepno,
                 SC.can_frames[can_p_ex["receive"]])

    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", stepno, result)
    return result, can_p_ex

def step_3(can_p, can_p_ex):
    """
    Teststep 3: Verify subscribed signal is still sent
    """
    stepno = 3
    purpose = "Verify subscribed signal is still sent"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.info("all can messages updated")
    time.sleep(1)
    logging.info("Step%s: messages received %s", stepno,
                 len(SC.can_messages[can_p_ex["receive"]]))
    logging.info("Step%s: messages: %s \n", stepno,
                 SC.can_messages[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", stepno,
                 len(SC.can_frames[can_p_ex["receive"]]))
    logging.info("Step%s: frames: %s \n", stepno,
                 SC.can_frames[can_p_ex["receive"]])

    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", stepno, result)

    return result

def step_6(can_p, can_p_ex):
    """
    Teststep 6: Verify subscribed signal is still sent
    """
    stepno = 6
    purpose = "Verify subscribed signal is still sent"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.info("all can messages updated")
    time.sleep(1)
    logging.info("Step%s: messages received %s", stepno,
                 len(SC.can_messages[can_p_ex["receive"]]))
    logging.info("Step%s: messages: %s \n", stepno,
                 SC.can_messages[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", stepno,
                 len(SC.can_frames[can_p_ex["receive"]]))
    logging.info("Step%s: frames: %s \n", stepno,
                 SC.can_frames[can_p_ex["receive"]])

    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", stepno, result)

    return result

def run():
    """
    Run - Call other functions from here
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.parameter_adopt_teststep(can_p)
    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: Register not diagnostic message
    # result: BECM send requested signals
        result, can_p_ex = result and step_1(can_p)

    # step2:
    # action: # Change to extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 2)

    # step3:
    # action: Verify signal is still sent
    # result: BECM send requested signals
        result = result and step_3(can_p, can_p_ex)

    # step4:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03')#, 4)

    # step5:
    # action: # Change to default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 5)

    # step6:
    # action: Verify signal is still sent
    # result: BECM send requested signals
        result = result and step_6(can_p, can_p_ex)

    ############################################
    # postCondition
    ############################################

    result = POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
