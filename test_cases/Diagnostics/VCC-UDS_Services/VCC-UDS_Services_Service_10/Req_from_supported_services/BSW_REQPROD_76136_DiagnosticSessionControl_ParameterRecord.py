# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-03
# version:  1.1
# reqprod:  76136

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
from support_can import SupportCAN, CanParam, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_4(can_par):
    """
    Teststep 4: Request session change to Mode3 + P2Server_max parameter
    """
    stepno = 4
    etp: CanTestExtra = {
        "purpose" : "Request session change to Mode3 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml("step_{}".format(stepno), etp)
    result = SE10.diagnostic_session_control(can_par, etp, b'\x03\x00\x19\x01\xF4')
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='7F1013')

    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_par["receive"]][0][2]))

    return result

def step_6(can_par):
    """
    Teststep 6: Request session change to Mode2 + P2Server_max parameter
    """
    stepno = 6
    etp: CanTestExtra = {
        "purpose" : "Request session change to Mode2 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml("step_{}".format(stepno), etp)
    result = SE10.diagnostic_session_control(can_par, etp, b'\x02\x10\x02\x10\x02')
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='7F1013')

    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_par["receive"]][0][2]))

    return result

def step_10(can_par):
    """
    Teststep 10: Request session change to Mode2 + P2Server_max parameter
    """
    stepno = 10
    etp: CanTestExtra = {
        "purpose" : "Request session change to Mode2 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml("step_{}".format(stepno), etp)
    result = SE10.diagnostic_session_control(can_par, etp, b'\x02\x10\x02\x10\x02')
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='7F1013')

    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_par["receive"]][0][2]))

    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_par: CanParam = {
        "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml("main", can_par)
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
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
             teststring='065003001901F400')

    # step2:
    # action: # Change to extended session from extended
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_par, 2)
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
             teststring='065003001901F400')

    # step3:
    # action: # Change to default session from extended
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_par, 3)
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
             teststring='065001001901F400')

    # step4:
    # action: # Change to extended session + P2Server_max param
    # result: BECM reports NRC
        result = result and step_4(can_par)

    # step5:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 5)

    # step6:
    # action: # Change to programming session + P2Server_max param
    # result: BECM reports NRC
        result = result and step_6(can_par)

    # step7:
    # action: # Change to programming mode
    # result: BECM reports mode
        SE10.diagnostic_session_control_mode2(can_par, 7)
        result = result and SE10.diagnostic_session_control_mode2(can_par, 7)
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
             teststring='065002001901F400')

    # step8:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x02')#, 8)

    # step9:
    # action: # Change to programming mode from programming
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_par, 9)
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
             teststring='065002001901F400')

    # step10:
    # action: # Change to Programming session + P2Server_max paremeter
    # result: BECM reports NRC
        result = result and step_10(can_par)

    # step11:
    # action: # Change to default session from programming
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_par, 11)
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
             teststring='065001001901F400')

    ############################################
    # postCondition
    ############################################

    result = POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
