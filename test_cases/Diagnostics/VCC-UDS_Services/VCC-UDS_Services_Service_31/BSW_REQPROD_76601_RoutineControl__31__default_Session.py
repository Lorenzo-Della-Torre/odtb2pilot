# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-31
# version:  1.0
# reqprod:  76601

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-26
# version:  1.1
# changes:  update for YML support

# inspired by https://grpc.io/docs/tutorials/basic/python.html
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
from support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service22 import SupportService22
from support_service10 import SupportService10
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
    Teststep 1: verify RoutineControlRequest is sent for Type 1
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x02\x06',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "verify RoutineControl start are sent for Type 1",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type1,Completed')
    logging.info("Step %s teststatus:%s \n", etp["step_no"], result)
    return result


def step_2(can_p):
    """
    Teststep 2: verify RoutineControlRequest is not applicable for Type 2
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x50',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify RoutineControl is not applicable for Type 2",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    time.sleep(1)
    return result


def step_3(can_p):
    """
    Teststep 3: verify RoutineControlRequest is not applicable for Type 3
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify RoutineControl is not applicable for Type 3",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    return result

def run():
    """
    Run - Call other functions from here
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
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
        result = result and step_1(can_p)

    # step2:
    # action: send start RoutineControl signal for Type 2
    # result: BECM sends NRC (requestOutOfRange)
        result = result and step_2(can_p)

    # step3:
    # action: send start RoutineControl signal for Type 3
    # result: BECM sends NRC (requestOutOfRange)
        result = result and step_3(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()