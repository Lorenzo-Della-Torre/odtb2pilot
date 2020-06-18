# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-05-06
# version:  1.1
# reqprod:  76502

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

import ODTB_conf
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
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

def step_2(can_par):
    """
    Teststep 2: verify ReadDTCInfoSnapshotIdentification reply positively
    """
    stepno = 2
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification", b'', b''),
        extra=''
        )
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=2,
        purpose="verify ReadDTCInfoSnapshotIdentification reply positively",
        timeout=1,
        min_no_messages=-1,
        max_no_messages=-1
        )
    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],
                                          teststring='5903')

    return result

def step_3(can_par):
    """
    Teststep 3: verify ReadDTCInfoSnapshotIdentification reply empty message
    """
    stepno = 3
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification(83)", b'', b''),
        extra=''
        )
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=3,
        purpose="verify ReadDTCInfoSnapshotIdentification reply empty message",
        timeout=1,
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and not SC.can_messages[can_par["receive"]]

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
    # action: # Change to extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_par, 1)

    # step2:
    # action:
    # result: BECM sends positive reply
        result = result and step_2(can_par)

    # step3:
    # action:
    # result: BECM sends positive reply
        result = result and step_3(can_par)

    # step4:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x03')#, 4)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
