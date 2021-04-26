# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-20
# version:  1.1
# reqprod:  74147

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-17
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
    Teststep 2: verify ReadDataByIdentifier reply positively
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x21',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify ReadDataByIdentifier reply positively",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    return result

def step_3(can_p, p4_server_max, jitter_testenv):
    """
    Teststep 3: Verify (time receive message – time sending request) < P4_server_max
    """
    step_no = 3
    purpose = "Verify (time receive message – time sending request) less than P4_server_max"
    SUTE.print_test_purpose(step_no, purpose)
    # remove the flow control frame response: frame starting with '3'
    if int(SC.can_frames[can_p["send"]][-1][2][0:1]) == 3:
        logging.info("Remove FC frame")
        SC.can_frames[can_p["send"]].pop(-1)
    logging.info("Last Can_frame sent: %s", SC.can_frames[can_p["send"]][-1])
    logging.info("First CAN_frame received %s", SC.can_frames[can_p["receive"]][0])

    t_rec = 1000 * SC.can_frames[can_p["send"]][-1][0]
    t_send = 1000 * SC.can_frames[can_p["receive"]][0][0]

    logging.info("Time P4_s_max + jitter %s", p4_server_max + jitter_testenv)
    logging.info("Tdiff: T_send-T_rec  : %s", (t_send-t_rec))
    logging.info("T difference(s): %s", (p4_server_max + jitter_testenv) - (t_send - t_rec))

    result = ((t_rec - t_send) < ((p4_server_max + jitter_testenv)/1000))
    logging.info("Step %s teststatus: %s \n", step_no, result)
    return result

def step_4(can_p):
    """
    Teststep 4: Complete ECU Part/Serial Number(s)
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xED\xA0',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Complete ECU Part/Serial Number(s)",
        "timeout": 3,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    return result

def step_5(can_p, p4_server_max, jitter_testenv):
    """
    Teststep 5: Verify (time receive message – time sending request) < P4_server_max
    """
    step_no = 5
    purpose = "Verify (time receive message – time sending request) less than P4_server_max"
    SUTE.print_test_purpose(step_no, purpose)
    # remove the flow control frame response: frame starting with '3'
    if int(SC.can_frames[can_p["send"]][-1][2][0:1]) == 3:
        logging.info("Remove FC frame")
        SC.can_frames[can_p["send"]].pop(-1)
    logging.info("Last Can_frame sent: %s", SC.can_frames[can_p["send"]][-1])
    logging.info("First CAN_frame received %s", SC.can_frames[can_p["receive"]][0])

    t_rec = 1000 * SC.can_frames[can_p["send"]][-1][0]

    t_send = 1000 * SC.can_frames[can_p["receive"]][0][0]

    logging.info("Time P4_s_max + jitter %s", p4_server_max + jitter_testenv)
    logging.info("Tdiff: T_send-T_rec  : %s", (t_send-t_rec))
    logging.info("T difference(s): %s", (p4_server_max + jitter_testenv) - (t_send - t_rec))

    result = ((t_rec - t_send) < ((p4_server_max + jitter_testenv)/1000))
    logging.info("Step %s teststatus: %s \n", step_no, result)
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

    p4_server_max = 200 # milliseconds
    jitter_testenv = 10

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
    # action: change BECM to Programming
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=1)

    # step 2:
    # action: send ReadDataByIdentifier signal in extended mode
    # result: BECM sends positive reply
        result = result and step_2(can_p)

    # step 3:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
        result = result and step_3(can_p, p4_server_max, jitter_testenv)

    # step 4:
    # action: send ReadDataByIdentifier signal in extended mode (complete ECU numbers)
    # result: BECM sends positive reply
        result = result and step_4(can_p)

    # step 5:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
        result = result and step_5(can_p, p4_server_max, jitter_testenv)

    # step 6:
    # action: verify Programming session active
    # result: BECM send active mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02', stepno=6)

    # step 7:
    # action: # Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=7)
        time.sleep(1)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
