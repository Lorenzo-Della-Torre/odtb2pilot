# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-06-18
# version:  1.1
# reqprod:  74116
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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2
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
    Teststep 1: verify RoutineControlRequest is sent for Type 1
    """
    #stepno = 1

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x02\x06', b'\x01'),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 1,
        "purpose" : "verify RoutineControl start(01) is sent in Extended Session",
        "timeout" : 1,
        "min_no_messages" : 1,
        "max_no_messages" : 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)#stepno, param_)
    result = result and SUTE.pp_decode_routine_control_response(
        SC.can_frames[can_p["receive"]][0][2],
        "Type1,Completed")
    return result


def step_3(can_p):
    """
    Teststep 3: verify NRC is sent for Type 1
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x02\x06', b'\x01'),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 3,
        "purpose" : "verify NRC is sent for Type 1 not implemented in Programming session",
        "timeout" : 0.05,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(
        SC.can_messages[can_p["receive"]], teststring='7F3131')

    #logging.info(SUTE.PP_Decode_7F_response(SC.can_frames[can_p["can_rec"]][0][2]))
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

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: request RoutineControlRequestSID in default session
    # result: positive reply, "Type1,Completed"
    result = result and step_1(can_p)

    # step2:
    # action: Change to Programming session
    # result: positive reply, mode2
    result = SE10.diagnostic_session_control_mode2(can_p, stepno=2)

    # step3:
    # action: verify NRC is sent for Type 1 not implemented in Programming session
    # result: NRC, requestOutOfRange
    result = result and step_3(can_p)

    # step 4:
    # action: Verify Programming session
    # result: positive reply, mode2
    result = SE22.read_did_f186(can_p, dsession=b'\x02', stepno=4)

    # step 5:
    # action: Change to default session
    # result: positive reply, mode1
    result = SE10.diagnostic_session_control_mode1(can_p, stepno=5)
    # it takes about one second after mode change from prog to default
    # for BECM/HVBM to take commands again.
    # issue?
    time.sleep(1)


    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
