# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-02
# version:  1.1
# reqprod:  76139 76140

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
from support_can import SupportCAN, CanParam
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service22 import SupportService22
from support_service11 import SupportService11
from support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()

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
    timeout = 300
    result = PREC.precondition(can_par, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: # ECU Reset
    # result:
        result = result and SE11.ecu_hardreset(can_par, 1)

    # step2:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 2)

    # step3:
    # action: # ECU Reset(81)
    # result:
        result = result and SE11.ecu_hardreset_81(can_par, 3)

    # step4:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 4)

    # step5:
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_par, 5)

    # step 6:
    # action: # ECU Reset
    # result:
        result = result and SE11.ecu_hardreset(can_par, 6)

    # step7:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 7)

    # step8:
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_par)#, 18)

    # step9:
    # action: # ECU Reset(81)
    # result:
        result = result and SE11.ecu_hardreset_81(can_par, 9)

    # step10:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 10)

    # step11:
    # action: # Change to Programming session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_par, 11)

    # step12:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x02')#, 12)

    # step 13:
    # action: # ECU Reset
    # result:
        result = result and SE11.ecu_hardreset(can_par, 13)

    # step14:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 14)

    # step15:
    # action: # Change to Programming session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_par, 15)

    # step16:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x02')#, 16)

    # step17:
    # action: # ECU Reset(81)
    # result:
        result = result and SE11.ecu_hardreset_81(can_par, 17)

    # step18:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 18)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
