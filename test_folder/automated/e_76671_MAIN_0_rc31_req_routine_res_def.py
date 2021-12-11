/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-31
# version:  1.0
# reqprod:  76671

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-09-16
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


def step_1(can_p):
    """
    Teststep 1: send RoutineControlRequest start(81) for Type 1
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
        "purpose": "verify RoutineControl start(01) for Type 1 reply positively",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    payload_reply = '06710102061001'
    routine_response = 'Type1,Completed'

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

    logging.info("Step%s: routine_response: %s", etp["step_no"], SC.can_messages[can_p["receive"]])
    result = result and\
             SUTE.test_message(SC.can_messages[can_p["receive"]], teststring=payload_reply)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     routine_response)
    logging.info("Step %s teststatus:%s \n", etp["step_no"], result)
    return result


def step_2(can_p):
    """
    Teststep 2: verify RoutineControlRequest RoutinheResult is sent for Type 1
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x02\x06',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify RoutineControl Request Routine Resoult(03) reply positively",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    #payload_reply = '06710102061001'
    payload_reply = '037F3110'
    #routine_response = 'Type3,Currently active'

    payload_reply_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'payload_reply')
    # don't set empty value if no replacement was found:
    if payload_reply_new:
        payload_reply = payload_reply_new
    else:
        logging.info("Step%s payload_reply_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: payload_reply after YML: %s", etp["step_no"], payload_reply)

    ### Currently no positive reply expected as no RoutineControl with 'RoutineResults'
    ###     defined in Carcom
    ### for default session
    ### Leave the code in for future changes

    #routine_response_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]),\
    #                                                 'routine_response')
    ## don't set empty value if no replacement was found:
    #if routine_response_new:
    #    routine_response = routine_response_new
    #else:
    #    logging.info("Step%s routine_response_new is empty. Discard.", etp["step_no"])
    #logging.info("Step%s: routine_response after YML: %s", etp["step_no"], routine_response)

    result = SUTE.teststep(can_p, cpay, etp)

    logging.info("Step%s: routine_response: %s", etp["step_no"],\
                 SC.can_messages[can_p["receive"]])
    logging.info("Step%s: negative reply expected due to subservice not defined "\
                 "in default session:", etp["step_no"])
    logging.info("Step%s: expected: Negative response: Service: 31, "\
                 "generalReject (1000000000)", etp["step_no"])

    result = result and\
             SUTE.test_message(SC.can_messages[can_p["receive"]], teststring=payload_reply)
    if result:
        logging.info("Decoded 7F response: %s",
                     SUTE.pp_decode_7f_response(SC.can_messages[can_p["receive"]][0][2].upper()))
    #result = result and\
    #         SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
    #                                                 routine_response)
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
    # step1:
    # action: send start RoutineControl signal for Type 1 (81)
    # result: BECM sends no reply or out of Range or Security Access Denied
        result = result and step_1(can_p)

    # step2:
    # action: send Result RoutineControl signal for Type 1
    # result: BECM sends positive reply
    #         or out of Range or Security Access Denied or Sub-func not supported
        result = result and step_2(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
