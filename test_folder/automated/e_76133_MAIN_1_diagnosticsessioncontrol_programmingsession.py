# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-03
# version:  1.1
# reqprod:  76133

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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_3(can_p):
    """
    Teststep 3: Request session change to Mode2 without reply
    """
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose" : "Request session change to Mode2 without reply",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x82')\
         and not SC.can_messages[can_p["receive"]]
    return result

def step_10(can_p):
    """
    Teststep 10: Request session change to Mode2 without reply
    """
    etp: CanTestExtra = {
        "step_no": 10,
        "purpose" : "Request session change to Mode2 without reply",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x82')\
         and not SC.can_messages[can_p["receive"]]
    return result

def step_13(can_p):
    """
    Teststep 13: Request session change to Mode2 without reply
    """
    etp: CanTestExtra = {
        "step_no": 13,
        "purpose" : "Request session change to Mode2 without reply",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x82')\
         and not SC.can_messages[can_p["receive"]]
    return result

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
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step1:
    # action: # Change to programming session
    # result: BECM reports mode
        SE10.diagnostic_session_control_mode2(can_p, 1)
        result = result and SE10.diagnostic_session_control_mode2(can_p, 1)

    # step2:
    # action: # Change to default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 2)
        time.sleep(1)
    # step3:
    # action: # Change to programming session without reply
    # result: BECM reports mode
        result = result and step_3(can_p)

    # step4:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02')#, 4)

    # step5:
    # action: # Change to default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 5)
        time.sleep(1)
    # step6:
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 6)

    # step7:
    # action: # Change to Programming session from extended
    # result: BECM reports mode
        SE10.diagnostic_session_control_mode2(can_p, 7)
        result = result and SE10.diagnostic_session_control_mode2(can_p, 7)

    # step8:
    # action: # Change to default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 8)
        time.sleep(1)

    # step9:
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 9)

    # step10:
    # action: # Change to Programming session from extended without reply
    # result: BECM reports mode
        result = result and step_10(can_p)

    # step11:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02')#, 11)

    # step12:
    # action: # Change to Programming session from programming
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 12)

    # step13:
    # action: # Change to programming session from programming without reply
    # result: BECM reports mode
        result = result and step_13(can_p)

    # step14:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02')#, 14)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
