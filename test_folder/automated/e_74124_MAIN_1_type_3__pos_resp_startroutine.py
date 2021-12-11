/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-23
# version:  1.1
# reqprod:  74124

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-20
# version:  1.2
# changes:  update for YML support

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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload, PerParam
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
    Teststep 1:get initial conditions on speed
    """

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\x4A\x57',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "get initial conditions on speed",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #logging.info("Step%s: speed: %s\n",
    #             etp["step_no"],
    #             str(int(SC.can_frames[can_p["receive"]][0][2][8:12], 16) >> 1))
    init_speed_str = SC.can_frames[can_p["receive"]][0][2][8:12]
    logging.info("Step%s, init_speed: %s", etp["step_no"], init_speed_str)
    return result, init_speed_str


def step_3(can_p):
    """
    Teststep 3: send signal vehicle velocity > 3km/h
    """
    step_no = 3
    purpose = "send signal vehicle velocity > 3km/h"
    SUTE.print_test_purpose(step_no, purpose)

    # start sending velocity
    veloc_param: PerParam = {
        "name" : "VehSpdLgtSafe",
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x80\xd6\x00\x00\x00\x00\x00\x00',
        "intervall" : 0.015
        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), veloc_param)
    SC.start_periodic(can_p["netstub"], veloc_param)

def step_4(can_p):
    """
    Teststep 4: verify RoutineControl start(01) gives correct reply in Extended Session
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x00\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "verify RoutineControl start(01) gives correct reply in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type3,Aborted')
    return result

def step_5(can_p):
    """
    Teststep 5: send signal vehicle velocity < 3km/h
    """
    step_no = 5
    purpose = "send signal vehicle velocity < 3km/h"
    SUTE.print_test_purpose(step_no, purpose)

    veloc_param: PerParam = {
        "name" : "VehSpdLgtSafe",
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x80\xd5\x00\x00\x00\x00\x00\x00',
        "intervall" : 0.015
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), veloc_param)
    SC.start_periodic(can_p["netstub"], veloc_param)

def step_6(can_p):
    """
    Teststep 6: verify RoutineControl start(01) reply Currently active
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x00\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 6,
        "purpose": "verify RoutineControl start(01) gives correct reply in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type3,Currently active')
    return result

def step_7(can_p, init_speed):
    """
    Teststep 7: send signal vehicle velocity = init speed
    """
    #global init_speed
    step_no = 7
    purpose = "send signal vehicle velocity = init speed"
    init_speed_bytes = bytes([int(init_speed, 16) >> 1])

    SUTE.print_test_purpose(step_no, purpose)

    veloc_param: PerParam = {
        "name" : "VehSpdLgtSafe",
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x80' + init_speed_bytes + b'\x00\x00\x00\x00\x00\x00',
        "intervall" : 0.015
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), veloc_param)
    SC.start_periodic(can_p["netstub"], veloc_param)

def step_8(can_p, init_speed):
    """
    Teststep 8:verify initial conditions on speed
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\x4A\x57',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 8,
        "purpose": "verify initial conditions on speed",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], init_speed)
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
    # action:request initial conditions on speed
    # result: BECM reply with speed
        result1, init_speed = step_1(can_p)
        result = result and result1

    # step 2:
    # action:change BECM to Extended session
    # result: BECM reply with mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=2)

    # step3:
    # action: send periodic signal vehicle velocity > 3km/h
    # result:
        step_3(can_p)

    # step4:
    # action: send start RoutineControl signal for Type 3 (01)
    # result: BECM sends positive reply
        result = result and step_4(can_p)

    # step5:
    # action: send periodic signal vehicle velocity < 3km/h
    # result:
        step_5(can_p)

    # step6:
    # action: send start RoutineControl signal for Type 3 (01)
    # result: BECM sends positive reply
        result = result and step_6(can_p)

    # step7:
    # action: send periodic signal vehicle velocity = 0km/h
    # result:
        step_7(can_p, init_speed)

    # step8:
    # action: verify signal vehicle velocity = 0km/h
    # result:
        result = result and step_8(can_p, init_speed)

    # step9:
    # action: Verify Extended session active
    # result: BECM sends active mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=9)

    # step10:
    # action: Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=10)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
