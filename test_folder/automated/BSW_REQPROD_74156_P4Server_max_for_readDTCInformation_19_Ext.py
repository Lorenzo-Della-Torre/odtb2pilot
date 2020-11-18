# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-05-06
# version:  1.3
# reqprod:  74156

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

import parameters.odtb_conf as odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
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
    Teststep 2: verify ReadDTCInfoSnapshotIdentification reply positively
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification", b'', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify ReadDTCInfoSnapshotIdentification reply positively",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='5903')

    return result

def step_3(can_p):
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

    p4_server_max = 500 # milliseconds
    jitter_testenv = 10

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

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step1:
    # action: # Change to extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 1)

    # step2:
    # action: send ReadDTCInfoSnapshotIdentification signal in Extended mode
    # result: BECM sends positive reply
        result = result and step_2(can_p)

    # step 3:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
        result = result and step_3(can_p)

    # step4:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=4)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
