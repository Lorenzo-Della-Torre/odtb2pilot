# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-02
# version:  1.1
# reqprod:  76139 76140

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-07-08
# version:  1.2
# reqprod:  76139 76140
# changes:  YML fixed, some timing fixed

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
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service10 import SupportService10

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
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "Vcu1ToBecmFront1DiagReqFrame",
        'receive': "BecmToVcu1Front1DiagResFrame",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    #Read YML parameter for current function (get it from stack)
    logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
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
    # step 1:
    # action: # ECU Reset
    # result:
        result = result and SE11.ecu_hardreset(can_p, 1)

    # step2:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=2)

    # step3:
    # action: # ECU Reset(1181)
    # result:
        result = result and SE11.ecu_hardreset_noreply(can_p, 3)

    # step4:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=4)

    # step5:
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 5)

    # step 6:
    # action: # ECU Reset
    # result:
        result = result and SE11.ecu_hardreset(can_p, 6)

    # step7:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=7)

    # step8:
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=8)

    # step9:
    # action: # ECU Reset(1181)
    # result:
        result = result and SE11.ecu_hardreset_noreply(can_p, 9)

    # step10:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=10)

    # step11:
    # action: # Change to Programming session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 11)

    # step12:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02', stepno=12)

    # step 13:
    # action: # ECU Reset
    # result:
        result = result and SE11.ecu_hardreset(can_p, 13)

    # step14:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01')#, 14)

    # step15:
    # action: # Change to Programming session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 15)

    # step16:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02')#, 16)

    # step17:
    # action: # ECU Reset(1181)
    # result:
        result = result and SE11.ecu_hardreset_noreply(can_p, 17)

    # step18:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01')#, 18)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
