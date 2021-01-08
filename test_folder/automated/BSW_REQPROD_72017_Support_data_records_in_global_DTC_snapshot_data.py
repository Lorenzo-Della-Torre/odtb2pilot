# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   T-KUMARA (Tanuj Kumar Aluru)
# date:     2020-11-19
# version:  1.0
# reqprod:  72017
#
# inspired by https://grpc.io/docs/tutorials/basic/python.html
#
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

from supportfunctions.support_can import SupportCAN, CanParam,CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE10 = SupportService10()


def step_1(can_p):
    '''
    Verify global DTC snapshot data records contains all data.
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",\
                                            b'\x0B\x4A\x00', b"\xFF"),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Verify global snapshot data ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    did_list = ['DD00', 'DD01', 'DD02', 'DD05', 'DD06', 'DD0A']
    message = SC.can_messages[can_p['receive']][0][2]
    logging.info("Global DTC Snapshot data: %s", message)

    did_check = True
    for i in did_list:
        if not i in message:
            logging.error("The following DID is not in the reply: %s", i)
            did_check = False

    return result and did_check


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
    SSBL.get_vbf_files()
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################

        # step 1:
        # action: Verify global snapshot data contains expected DID's
        # result: Check if expected DiD's are contained in reply
        result = result and step_1(can_p)

   ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
