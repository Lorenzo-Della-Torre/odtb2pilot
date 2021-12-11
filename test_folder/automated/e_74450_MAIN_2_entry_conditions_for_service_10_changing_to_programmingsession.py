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

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-05
# version:  1.1
# reqprod:  74450

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
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, PerParam
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
    Teststep 1: send signal vehicle velocity < 3km/h
    """
    stepno = 1
    purpose = "send signal vehicle velocity < 3km/h"
    SUTE.print_test_purpose(stepno, purpose)

    # where to connect to signal_broker
    can_p_ex: PerParam = {
        "name" : 'VehSpdLgtSafe',
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "frame" : b'\x80\xd5\x00\x00\x00\x00\x00\x00',
        "nspace" : can_p["namespace"].name,
        "intervall" : 0.015,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)
    SC.start_periodic(can_p["netstub"], can_p_ex)

def step_4(can_p):
    """
    Teststep 4: send signal vehicle velocity > 3km/h
    """
    stepno = 4
    purpose = "send signal vehicle velocity > 3km/h"
    SUTE.print_test_purpose(stepno, purpose)

    # where to connect to signal_broker
    can_p_ex_2: PerParam = {
        "name" : 'VehSpdLgtSafe',
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "frame" : b'\x80\xd6\x00\x00\x00\x00\x00\x00',
        "nspace" : can_p["namespace"].name,
        "intervall" : 0.015,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex_2)
    SC.set_periodic(can_p_ex_2)

def step_5(can_p):
    """
    Teststep 5: Request session change to Mode2 while car moving
    """
    etp: CanTestExtra = {
        "step_no" : 5,
        "purpose" : "Request session change to Mode2 while car moving",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    #SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    SE10.diagnostic_session_control(can_p, etp, b'\x02')
    result = SE10.diagnostic_session_control(can_p, etp, b'\x02')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F1022')
    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))

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
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step1:
    # action:
    # result: BECM reports mode
        step_1(can_p)

    # step2:
    # action: Change to programming session
    # result: BECM reports mode
        SE10.diagnostic_session_control_mode2(can_p, 2)
        result = result and SE10.diagnostic_session_control_mode2(can_p, 2)

    # step3:
    # action: Change to default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 3)

    # step4:
    # action: send signal vehicle velocity > 3km/h
    # result:
        step_4(can_p)
        time.sleep(2)

    # step5:
    # action: Request session change to Mode2 while car moving
    # result: BECM reports mode
        result = result and step_5(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
