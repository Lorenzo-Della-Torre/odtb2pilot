"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO
# date:     2021-02-19
# version:  1.0
# reqprod:  76169

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
import inspect

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SIO = SupportFileIO

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
SE3E = SupportService3e()


def step_8(can_p: CanParam):
    '''
    Teststep 8: Start sending TesterPresent
    '''
    result = True
    teststep = 8
    #Start testerpresent without reply
    tp_name = "Vcu1ToAllFuncFront1DiagReqFrame"
    #Read current function name from stack:
    new_tp_name = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "tp_name")
    if new_tp_name != '':
        tp_name = new_tp_name
    logging.info("Step %s, Start sending TP again.", teststep)
    SE3E.start_periodic_tp_zero_suppress_prmib(can_p, tp_name)
    return result


def run():# pylint: disable=too-many-statements
    """
    Run
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: Change to Extended Session
    # result:
    logging.info("Step 1: Request change to mode3 (extended session).")
    result = result and SE10.diagnostic_session_control_mode3(can_p, 1)

    # step 2:
    # action: Verify ECU is in Extended Session
    # result:
    logging.info("Step 2: Verify ECU is in Extended Session.")
    result = result and SE22.read_did_f186(can_p, b'\x03', 2)

    # step 3:
    # action: Wait longer than timeout for fallback while sending TP.
    # result:
    logging.info("Step 3: Wait longer than timeout for fallback while sending TP.")
    time.sleep(6)

    # step 4:
    # action: Verify that ECU is still in extended after timeout due to TP sent.
    # result:
    logging.info("Step 4: Verify ECU still in extended due to TP sent.")
    result = result and SE22.read_did_f186(can_p, b'\x03', 4)

    # step 5:
    # action: stop sending tester present
    # result:
    logging.info("Step 5: stop sending tester present.")
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    # step 6:
    # action: Wait longer than timeout for fallback while not sending TP.
    # result:
    logging.info("Step 6: Wait longer than timeout for fallback while not sending TP.")
    time.sleep(6)

    # step 7:
    # action: Verify that ECU did fallback to default.
    # result:
    logging.info("Step 7: Verify ECU fallback to default as no TP sent.")
    result = result and SE22.read_did_f186(can_p, b'\x01', 7)

    # step 8:
    # action: Start sending TesterPresent (TP) again
    result = result and step_8(can_p)
    logging.info("Step 8: Status script:. %s", result)


    # step 9:
    # action: Change to Programming Session
    # result:
    logging.info("Step 9: Request change to mode2 (programming session).")
    result = result and SE10.diagnostic_session_control_mode2(can_p, 9)

    # step 10:
    # action: Wait longer than timeout for fallback while sending TP.
    # result:
    logging.info("Step 10: Wait longer than timeout for fallback while sending TP.")
    time.sleep(6)

    # step 11:
    # action: Verify that ECU is still in programming session after timeout due to TP sent.
    # result:
    logging.info("Step 11: Verify ECU still in programming due to TP sent.")
    result = result and SE22.read_did_f186(can_p, b'\x02', 11)

    # step 12:
    # action: stop sending tester present
    # result:
    logging.info("Step 12: stop sending tester present.")
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    # step 13:
    # action: Wait longer than timeout for fallback while not sending TP.
    # result:
    logging.info("Step 13: Wait longer than timeout for fallback while not sending TP.")
    time.sleep(6)

    # step 14:
    # action: Verify that ECU did fallback to default.
    # result:
    logging.info("Step 14: Verify ECU fallback to default as no TP sent.")
    result = result and SE22.read_did_f186(can_p, b'\x01', 14)


    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
