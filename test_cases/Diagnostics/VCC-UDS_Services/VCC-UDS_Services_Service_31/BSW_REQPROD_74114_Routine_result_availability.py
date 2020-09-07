# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-06-18
# version:  1.1
# reqprod:  74114

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-19
# version:  1.2
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
    Teststep 2: verify Routine Type 3 is not running
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify Routine 3 is not running",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3124')

    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    logging.info("This routine conrol is not active")
    return result

def step_3(can_p):
    """
    Teststep 3: verify routine is in status ‘running’ after ‘start’ request sent
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify Routine Type 3 is in status running after start request is sent",
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


def step_4(can_p):
    """
    Teststep 4: verify Routine is completed after routine control stop is sent
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
        "purpose": "Verify routine is Completed for type 3 after Routine control stop is sent",
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

def step_5(can_p):
    """
    Teststep 5: Verify routine is Completed for type 3 after Routine control result request is sent
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
        "purpose": "Verify routine is Completed for type 3 after Routine control result"\
                   "request is sent",
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

def step_9(can_p):
    """
    Teststep 9: Request Routine result Type 3
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 9,
        "purpose": "request routine result Type 3",
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
    # action: send Result RoutineControl signal
    # result: BECM sends NRC reply
        result = result and step_2(can_p)

    # step3:
    # action: send Start RoutineControl signal
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

    # step 6:
    # action: # action: Verify BECM in Extended session
    # result: BECM reports mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=6)

    # step 7:
    # action: change BECM to default
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=7)

    # step 8:
    # action: change BECM to Extended
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=8)

    # step9:
    # action: send Result RoutineControl signal
    # result: BECM sends positive reply
        result = result and step_9(can_p)

    # step 10:
    # action: change BECM to default
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=10)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
