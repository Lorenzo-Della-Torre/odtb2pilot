# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-10
# version:  1.2
# reqprod:  52286
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
from support_can import SupportCAN, CanParam #, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service22 import SupportService22
from support_service31 import SupportService31
from support_service3e import SupportService3e

SIO = SupportFileIO
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
SE31 = SupportService31()
SE3E = SupportService3e()

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

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
    timeout = 60
    result = PREC.precondition(can_p, timeout)
    SE3E.stop_periodic_tp_zero_suppress_prmib()
    if result:
    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: Verify programming preconditions
        # result: ECU sends positive reply
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)

        # step2:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)

        # step3:
        # action: Verify ECU in programming session
        # result: ECU sends positive reply
        time.sleep(1)
        result = result and SE22.read_did_f186(can_p, b'\x02', stepno=3)

        # step4:
        # action: don't send a request until timeout occured
        # result:
        logging.info("\n Step 4: Wait shorter than timeout for staying in current mode.")
        logging.info("Step 4: No request to ECU.\n")
        time.sleep(4)

        # step5:
        # action: Verify ECU is still in mode prog session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x02', stepno=5)

        # step6:
        # action: wait longer than timeout
        # result:
        logging.info("\n Step 6: Wait longer than timeout for staying in current mode.")
        logging.info("Step 6: No request to ECU as before.")
        time.sleep(6)

        # step7:
        # action: verify ECU changed to default
        # result: ECU sends positive reply
        time.sleep(1)
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=7)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
