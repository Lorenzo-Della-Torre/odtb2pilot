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

import ODTB_conf
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()

def step_1(can_par):
    """
    Teststep 1: verify ReadDTCInfoSnapshotIdentification reply positively
    """
    stepno = 1
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification", b'', b''),
        extra=''
        )
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=1,
        purpose="verify ReadDTCInfoSnapshotIdentification reply positively",
        timeout=1,
        min_no_messages=1,
        max_no_messages=1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='5903')

    return result

def step_2(can_par):
    """
    Teststep 2: Verify (time receive message – time sending request) < P4_server_max
    """
    stepno = 2
    purpose = "Verify (time receive message – time sending request) less than P4_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    # remove the flow control frame response: frame starting with '3'
    if int(SC.can_frames[can_par["send"]][-1][2][0:1]) == 3:
        logging.info("Remove FC frame")
        SC.can_frames[can_par["send"]].pop(-1)
    logging.info("Last Can_frame sent: %s", SC.can_frames[can_par["send"]][-1])
    logging.info("First CAN_frame received %s", SC.can_frames[can_par["receive"]][0])

    p4_server_max = 500 # milliseconds
    jitter_testenv = 10

    t_rec = 1000 * SC.can_frames[can_par["send"]][-1][0]
    t_send = 1000 * SC.can_frames[can_par["receive"]][0][0]

    logging.info("Time P4_s_max + jitter %s", p4_server_max + jitter_testenv)
    logging.info("Tdiff: T_send-T_rec  : %s", (t_send-t_rec))
    logging.info("T difference(s): %s", (p4_server_max + jitter_testenv) - (t_send - t_rec))

    result = ((t_rec - t_send) < ((p4_server_max + jitter_testenv)/1000))
    logging.info("Step %s teststatus: %s \n", stepno, result)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_par: CanParam = SIO.extract_parameter_yml(
        "main",
        netstub=SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        send="Vcu1ToBecmFront1DiagReqFrame",
        receive="BecmToVcu1Front1DiagResFrame",
        namespace=SC.nspace_lookup("Front1CANCfg0")
        )

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_par, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

    # step1:
    # action: send ReadDTCInfoSnapshotIdentification signal in default mode
    # result: BECM sends positive reply
        result = result and step_1(can_par)

    # step 2:
    # action: Verify (time receive message – time sending request) < P4_server_max
    # result: positive result
        result = result and step_2(can_par)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
