/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-16
# version:  1.0
# reqprod:  76622

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-09-01
# version:  1.1
# changes:  update for YML support

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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_2(can_p):
    """
    Teststep 2: verify RoutineControlRequest start is sent
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x11\x08\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify RoutineControl start reply positively",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    payload_reply = '057101401132'
    routine_response = 'Type3,Currently active'

    payload_reply_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'payload_reply')
    # don't set empty value if no replacement was found:
    if payload_reply_new:
        payload_reply = payload_reply_new
    else:
        logging.info("Step%s payload_reply_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: payload_reply after YML: %s", etp["step_no"], payload_reply)

    routine_response_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'routine_response')
    # don't set empty value if no replacement was found:
    if routine_response_new:
        routine_response = routine_response_new
    else:
        logging.info("Step%s routine_response_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: routine_response after YML: %s", etp["step_no"], routine_response)

    result = SUTE.teststep(can_p, cpay, etp)

    result = result and\
             SUTE.test_message(SC.can_messages[can_p["receive"]], teststring=payload_reply)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     routine_response)
    logging.info("Step %s teststatus:%s \n", etp["step_no"], result)
    return result

def step_3(can_p):
    """
    Teststep 3: verify RoutineControlRequest stop is sent in Extended Session
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x11',
                                        b'\x02'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify RoutineControl stop reply positively in Extended Session",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    payload_reply = '057102401130'
    routine_response = 'Type3,Completed'

    payload_reply_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'payload_reply')
    # don't set empty value if no replacement was found:
    if payload_reply_new:
        payload_reply = payload_reply_new
    else:
        logging.info("Step%s payload_reply_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: payload_reply after YML: %s", etp["step_no"], payload_reply)

    routine_response_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'routine_response')
    # don't set empty value if no replacement was found:
    if routine_response_new:
        routine_response = routine_response_new
    else:
        logging.info("Step%s routine_response_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: routine_response after YML: %s", etp["step_no"], routine_response)

    logging.info("Step%s: routine_response: %s", etp["step_no"], SC.can_messages[can_p["receive"]])
    result = result and\
             SUTE.test_message(SC.can_messages[can_p["receive"]], teststring=payload_reply)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     routine_response)
    logging.info("Step %s teststatus:%s \n", etp["step_no"], result)
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
    # action: change BECM to Extended
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=1)

    # step2:
    # action: send start RoutineControl signal
    # result: BECM sends positive reply
    #step_2a(network_stub, can_send, can_receive, can_namespace)

        result = result and step_2(can_p)

    # step3:
    # action: send stop RoutineControl signal in Extended mode
    # result: BECM sends positive reply
        result = result and step_3(can_p)

    # step4:
    # action: # action: Verify BECM in Extended session
    # result: BECM reports mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=4)

    # step5:
    # action: change BECM to default
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=5)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
