"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-31
# version:  1.0
# reqprod:  74126

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-21
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
    Teststep 2: verify RoutineControlRequest type3 gives expected reply
    """

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify RoutineControl start reply positively and routine Type 3 is running",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("Step%s: received: %s", etp["step_no"], SC.can_frames[can_p["receive"]])
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     "Type3,Currently active")
    return result

def step_3(can_p):
    """
    Teststep 3: verify Routine Type 3 is still running
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify RoutineControl result reply positively in Extended Session"\
                   " and routine is still running",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     "Type3,Currently active")
    return result

# teststep 4: verify RoutineControlRequest stop result is completed in Extended Session
def step_4(can_p):
    """
    Teststep 4: verify RoutineControlRequest stop result is completed in Extended Session
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x02'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "verify RoutineControl stop reply positively in Extended Session"\
                   " and routine is Completed",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     "Type3,Completed")
    return result

# teststep 5: verify Routine Type 3 is completed
def step_5(can_p):
    """
    Teststep 5: verify Routine Type 3 is completed
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "erify RoutineControl result reply positively in Extended Session"\
                   " and routine is completed",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     "Type3,Completed")
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
        result = result and step_2(can_p)

    # step3:
    # action: send Result RoutineControl signal
    # result: BECM sends positive reply
        result = result and step_3(can_p)

    # step4:
    # action: send stop RoutineControl signal in Extended mode
    # result: BECM sends positive reply
        result = result and step_4(can_p)

    # step5:
    # action: send Result RoutineControl signal
    # result: BECM sends positive reply
        result = result and step_5(can_p)

    # step6:
    # action: # action: Verify BECM in Extended session
    # result: BECM reports mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=6)

    # step7:
    # action: change BECM to default
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=7)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
