# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-24
# version:  2.0
# reqprod:  74184

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-24
# version:  2.1
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

WAITING_TIME = 2 #seconds
MAX_DIFF = 50 #max difference allowed for number of frame non-diagnostic received
MIN_NON_DIAG = 10 #min number of non-diagnostic frames received allowed

def step_2(can_p, timeout):
    """
    Teststep 2: register non diagnostic signal
    """
    #same timeout for signal als for whole testscript
    etp: CanTestExtra = {
        'step_no': 2,
        'purpose': "register another signal",
        'timeout': timeout,
        'min_no_messages': -1,
        'max_no_messages': -1
        }

    # fetch any signal sent from BECM when awake
    can_p_ex: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "ECMFront1Fr02",
        'receive': "BECMFront1Fr02",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)

    SC.subscribe_signal(can_p_ex, etp["timeout"])
    time.sleep(1)
    SC.clear_all_can_messages()
    #logging.debug("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    #logging.debug("all can messages updated")
    time.sleep(1)
    #logging.info("Step%s: messages received %s", etp["step_no"],
    #             len(SC.can_messages[can_p_ex["receive"]]))
    #logging.info("Step%s: messages: %s \n", etp["step_no"],
    #             SC.can_messages[can_p_ex["receive"]])
    frames_step2 = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", etp["step_no"], frames_step2)
    logging.info("Step%s: frames: %s \n", etp["step_no"],
                 SC.can_frames[can_p_ex["receive"]])

    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", etp["step_no"], result)
    return result, can_p_ex, frames_step2


def step_3(can_p):
    """
    Teststep 3: verify RoutineControl start(01) reply Currently active
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x00\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify RoutineControl start(01) is sent in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("Step%s: can_m_send %s", etp["step_no"], cpay["payload"])
    logging.info("Step%s: frames received %s", etp["step_no"], SC.can_frames[can_p["receive"]])
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     "Type3,Currently active")
    logging.info("Step %s teststatus:%s \n", etp["step_no"], result)
    return result

def step_4(can_p):
    """
    Teststep 4: verify RoutineControl stop(01) reply Completed
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x00',
                                        b'\x02'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "verify RoutineControl start(01) is sent in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    logging.info("Step%s: can_m_send %s", etp["step_no"], cpay["payload"])
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type3,Completed')
    logging.info("Step %s teststatus:%s \n", etp["step_no"], result)
    return result


def step_5(can_p, can_p_ex, frames_step2):
    """
    Teststep 5: verify that while service 22 is cyclically sent non-diagnostic signal
                is not effected
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x40\x00',
                                        b'\x03'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "verify that while service 31 is cyclically sent non-diagnostic signal"\
                   " is not effected",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    number_of_frames_received = 0
    SC.clear_all_can_messages()
    logging.info("Step%s: all can messages cleared", etp["step_no"])
    SC.clear_all_can_frames()

    now = int(time.time())
    SC.update_can_messages(can_p)

    while now + WAITING_TIME > int(time.time()):
        result = result and SUTE.teststep(can_p, cpay, etp)

    logging.info("Step%s: payload: %s", etp["step_no"], cpay["payload"])
    logging.info("Step%s: frames received: %s", etp["step_no"], number_of_frames_received)
    number_of_frames_received = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step%s: frames received: %s", etp["step_no"], number_of_frames_received)
    result = result and\
             ((number_of_frames_received + MAX_DIFF) > frames_step2 >\
              (number_of_frames_received - MAX_DIFF))
    logging.info("Step %s teststatus: %s\n", etp["step_no"], result)
    return result


def step_6(can_p, can_p_ex, frames_step2):
    """
    Teststep 6: Verify subscribed signal in step 1 is still sent
    """
    step_no = 6
    purpose = "Verify subscribed non-diagnostic signal is still sent as in step 1"
    SUTE.print_test_purpose(step_no, purpose)
    #can_rec = "BECMFront1Fr02"
    SC.clear_all_can_messages()
    logging.info("Step%s: all can messages cleared", step_no)
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.info("Step%s: all can messages updated", step_no)
    time.sleep(WAITING_TIME)

    logging.info("Step%s: frames received %s", step_no, len(SC.can_frames[can_p_ex["receive"]]))
    logging.info("Step%s: frames: %s\n", step_no, SC.can_frames[can_p_ex["receive"]])

    result = ((len(SC.can_frames[can_p_ex["receive"]]) + MAX_DIFF) >\
              frames_step2 >\
              (len(SC.can_frames[can_p_ex["receive"]]) - MAX_DIFF))

    logging.info("Step %s teststatus:%s \n", step_no, result)
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

    # step 2:
    # action: register a non-diagnostic signal
    # result: BECM send requested signals
        result2, can_p_ex, frames_step2 = step_2(can_p, timeout)
        result = result and result2
    # step3:
    # action: send start RoutineControl signal
    # result: BECM sends positive reply
        result = result and step_3(can_p)

    # step4:
    # action: send stop RoutineControl signal in Extended mode
    # result: BECM sends positive reply
        result = result and step_4(can_p)

    # step5:
    # action: send ReadDataByIdentifier cyclically
    # result: BECM reports confirmed message
        result = result and step_5(can_p, can_p_ex, frames_step2)

    # step6:
    # action: Verify signal is still sent
    # result: BECM send requested signals
        result = result and step_6(can_p, can_p_ex, frames_step2)

    # step7:
    # action: Verify Extended session active
    # result: BECM sends active mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=7)

    # step 8:
    # action: change BECM to default
    # result: BECM report mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=8)
        #time.sleep(1)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
