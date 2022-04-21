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
# date:     2020-03-12
# version:  1.0
# reqprod:  53927

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-18
# version:  1.1
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
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
from hilding.conf import Conf

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
conf = Conf()

WAITING_TIME = 2 #seconds
MAX_DIFF = 20 #max difference allowed for number of frame non-diagnostic received
MIN_NON_DIAG = 10 #min number of non-diagnostic frames received allowed

def step_1(can_p, timeout):
    """
    Teststep 1: register non diagnostic signal
    """
    #same timeout for signal als for whole testscript
    etp: CanTestExtra = {
        'step_no': 1,
        'purpose': "register another signal",
        'timeout': timeout,
        'min_no_messages': -1,
        'max_no_messages': -1
        }

    # fetch any signal sent from BECM when awake
    can_p_ex: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "ECMFront1Fr02",
        'receive': "BECMFront1Fr02",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    SIO.parameter_adopt_teststep(can_p_ex)

    SC.subscribe_signal(can_p_ex, etp["timeout"])
    time.sleep(1)
    SC.clear_all_can_messages()
    #logging.debug("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    #logging.debug("all can messages updated")
    time.sleep(WAITING_TIME)
    #logging.info("Step%s: messages received %s", etp["step_no"],
    #             len(SC.can_messages[can_p_ex["receive"]]))
    #logging.info("Step%s: messages: %s \n", etp["step_no"],
    #             SC.can_messages[can_p_ex["receive"]])
    frames_step1 = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", etp["step_no"], frames_step1)
    logging.info("Step%s: frames: %s \n", etp["step_no"],
                 SC.can_frames[can_p_ex["receive"]])

    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", etp["step_no"], result)
    return result, can_p_ex, frames_step1

def step_3(can_p, can_p_ex):
    """
    Teststep 3: Verify subscribed signal in step 1 is suspended
    """
    stepno = 3
    purpose = "Verify subscribed non-diagnostic signal is suspended"
    SUTE.print_test_purpose(stepno, purpose)
    can_rec = can_p_ex["receive"]
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.info("all can messages updated")
    time.sleep(WAITING_TIME)
    logging.info("Step %s frames received %s", stepno, len(SC.can_frames[can_rec]))
    logging.info("Step %s frames: %s", stepno, SC.can_frames[can_rec])

    result = len(SC.can_frames[can_rec]) == 0

    logging.info("Step %s teststatus: %s", stepno, result)
    time.sleep(2)
    return result

def step_5(can_p, frame_step1, can_p_ex):
    """
    Teststep 5: Verify subscribed signal in step 1 is received
    """
    stepno = 5
    purpose = "Verify subscribed non-diagnostic signal is received"
    SUTE.print_test_purpose(stepno, purpose)
    can_rec = can_p_ex["receive"]
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.info("all can messages updated")
    time.sleep(WAITING_TIME)
    logging.info("Step %s frames received %s", stepno, len(SC.can_frames[can_rec]))
    logging.info("Step %s frames: %s", stepno, SC.can_frames[can_rec])

    result = ((len(SC.can_frames[can_rec]) + MAX_DIFF) > frame_step1 >
              (len(SC.can_frames[can_rec]) - MAX_DIFF))

    logging.info("Step %s teststatus: %s", stepno, result)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT,
                                               odtb_conf.ODTB2_PORT),
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
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 100
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action: register non diagnostic signal
        # result: ECU sends positive reply
        result_step1, can_p_ex, frames_step1 = step_1(can_p, timeout)
        result = result and result_step1

        # step2:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, conf.default_rig_config ,stepno=2,
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step3:
        # action: Verify subscribed signal in step 1 is suspended
        # result: ECU sends positive reply
        result = result and step_3(can_p, can_p_ex)

        # step4:
        # action: Change to default session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=4)

        # step5:
        # action: Verify subscribed signal in step 1 is received
        # result: ECU sends positive reply
        result = result and step_5(can_p, frames_step1, can_p_ex)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
