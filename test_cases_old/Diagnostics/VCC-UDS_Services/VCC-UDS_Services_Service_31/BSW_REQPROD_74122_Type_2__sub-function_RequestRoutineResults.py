# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-19
# version:  1.0
# reqprod:  74122

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-19
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


def step_2(can_p):
    """
    Teststep 2: verify RoutineControlRequest start reply with Routine active
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x10',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify RoutineControlRequest start reply positively and "\
                   "routine Type 2 is Currently active",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and \
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Currently active')
    return result

def step_3(can_p):
    """
    Teststep 3: verify RoutineControlRequest stop reply with Routine completed
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x10',
                                        b'\x02'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify RoutineControlRequest stop reply positively in Extended Session "\
                   "and routine Type 2 is Completed",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Completed')
    return result


def step_4(can_p):
    """
    Teststep 4: verify RoutineControlRequest result reply with Routine completed
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x10',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "verify RoutineControlRequest result reply positively in Extended Session "\
                   "and routine Type 2 is Completed",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Completed')
    return result

def step_5(can_p):
    """
    Teststep 5: verify RoutineControlRequest start reply with Routine Type 2 long max time active
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x11',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "verify RoutineControlRequest start reply positively in Extended Session "\
                   "and routine Type 2 long max time is Currently active",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Currently active')
    return result

def step_6(can_p):
    """
    Teststep 6: verify RoutineControlRequest Result reply with Routine Type 2 long max time active
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x11',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 6,
        "purpose": "verify RoutineControlRequest result reply positively in Extended Session "\
                   "and routine Type 2 long max time is running",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Currently active')
    return result


def step_7(can_p):
    """
    Teststep 7: verify RoutineControlRequest stop reply with Routine Type 2 long max time Aborted
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x11',
                                        b'\x02'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 7,
        "purpose": "verify RoutineControlRequest stop reply positively and "\
                   "routine Type 2 long max time is Aborted",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Aborted')
    return result

def step_8(can_p):
    """
    Teststep 8: verify RoutineControlRequest result reply with Routine Type 2 long max time Aborted
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x11',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 8,
        "purpose": "verify RoutineControlRequest result reply positively in Extended Session "\
                   "and routine Type 2 long max time is aborted",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Aborted')
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
        result = result and SE10.diagnostic_session_control_mode3(can_p, 1)

    # step2:
    # action: send start RoutineControl signal for Type 2
    # result: BECM sends positive reply
        result = result and step_2(can_p)

     # step3:
    # action: send result RoutineControl signal for Type 2
    # result: BECM sends positive reply
        result = result and step_3(can_p)

    # step4:
    # action: send stop RoutineControl signal for Type 2
    # result: BECM sends positive reply
        result = result and step_4(can_p)

    # step5:
    # action: send start RoutineControl signal for Type 2 long time
    # result: BECM sends positive reply
        result = result and step_5(can_p)

     # step6:
    # action: send result RoutineControl signal for Type 2 long time
    # result: BECM sends positive reply
        result = result and step_6(can_p)

    # step7:
    # action: send stop RoutineControl signal for Type 2 long time
    # result: BECM sends positive reply
        result = result and step_7(can_p)

    # step8:
    # action: send result RoutineControl signal for Type 2 long time
    # result: BECM sends positive reply
        result = result and step_8(can_p)

    # step9:
    # action: verify extended session active
    # result: BECM send active mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=6)

    # step 10:
    # action: # Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 10)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
