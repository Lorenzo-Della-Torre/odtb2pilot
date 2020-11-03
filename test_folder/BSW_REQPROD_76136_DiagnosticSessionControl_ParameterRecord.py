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
import inspect

import parameters.odtb_conf
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

def step_1(can_p):
    """
    Teststep 1: Change to extended session + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose" : "Request session change to Mode3 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    p2_server_timing = "065003001901F400"
    #logging.info("Step%s: P2Server_timing before YML: %s",etp["step_no"], p2_server_timing)
    p2_server_timing_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'p2_server_timing')
    # don't set empty value if no replacement was found:
    if p2_server_timing_new:
        p2_server_timing = p2_server_timing_new
    else:
        logging.info("Step%s P2Server_timing_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: P2Server_timing after YML: %s", etp["step_no"], p2_server_timing)
    result = SE10.diagnostic_session_control_mode3(can_p, etp["step_no"])
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
             teststring=p2_server_timing)
    logging.info("Step%s: compare P2_server_max against: %s", etp["step_no"], p2_server_timing)
    logging.info("Step%s: result of compare: %s", etp["step_no"], result)
    return result

def step_2(can_p):
    """
    Teststep 2: Change to extended session + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose" : "Request session change to Mode3 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    p2_server_timing = "065003001901F400"
    #logging.info("Step%s: P2Server_timing before YML: %s",etp["step_no"], p2_server_timing)
    p2_server_timing_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'p2_server_timing')
    # don't set empty value if no replacement was found:
    if p2_server_timing_new:
        p2_server_timing = p2_server_timing_new
    else:
        logging.info("Step%s P2Server_timing_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: P2Server_timing after YML: %s", etp["step_no"], p2_server_timing)
    result = SE10.diagnostic_session_control_mode3(can_p, etp["step_no"])
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
             teststring=p2_server_timing)
    logging.info("Step%s: compare P2_server_max against: %s", etp["step_no"], p2_server_timing)
    logging.info("Step%s: result of compare: %s", etp["step_no"], result)
    return result

def step_3(can_p):
    """
    Teststep 3: Change to default session from extended + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose" : "Change to default session from extended + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    p2_server_timing = "065001001901F400"
    #logging.info("Step%s: P2Server_timing before YML: %s",etp["step_no"], p2_server_timing)
    p2_server_timing_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'p2_server_timing')
    # don't set empty value if no replacement was found:
    if p2_server_timing_new:
        p2_server_timing = p2_server_timing_new
    else:
        logging.info("Step%s P2Server_timing_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: P2Server_timing after YML: %s", etp["step_no"], p2_server_timing)
    result = SE10.diagnostic_session_control_mode1(can_p, etp["step_no"])
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
             teststring=p2_server_timing)
    logging.info("Step%s: compare P2_server_max against: %s", etp["step_no"], p2_server_timing)
    logging.info("Step%s: result of compare: %s", etp["step_no"], result)
    return result

def step_4(can_p):
    """
    Teststep 4: Request session change to Mode3 + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose" : "Request session change to Mode3 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x03\x00\x19\x01\xF4')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F1013')

    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))

    return result

def step_6(can_p):
    """
    Teststep 6: Request session change to Mode2 + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 6,
        "purpose" : "Request session change to Mode2 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x02\x10\x02\x10\x02')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F1013')

    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))

    return result


def step_7(can_p):
    """
    Teststep 3: Change to default session from extended + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 7,
        "purpose" : "Change to default session from extended + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    p2_server_timing = "065002001901F400"
    #logging.info("Step%s: P2Server_timing before YML: %s",etp["step_no"], p2_server_timing)
    p2_server_timing_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'p2_server_timing')
    # don't set empty value if no replacement was found:
    if p2_server_timing_new:
        p2_server_timing = p2_server_timing_new
    else:
        logging.info("Step%s P2Server_timing_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: P2Server_timing after YML: %s", etp["step_no"], p2_server_timing)
    result = SE10.diagnostic_session_control_mode2(can_p, etp["step_no"])
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
             teststring=p2_server_timing)
    logging.info("Step%s: compare P2_server_max against: %s", etp["step_no"], p2_server_timing)
    logging.info("Step%s: result of compare: %s", etp["step_no"], result)
    return result

def step_10(can_p):
    """
    Teststep 10: Request session change to Mode2 + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 10,
        "purpose" : "Request session change to Mode2 + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x02\x10\x02\x10\x02')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F1013')

    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))

    return result

def step_11(can_p):
    """
    Teststep 11: Change to default session from programming + P2Server_max parameter
    """
    etp: CanTestExtra = {
        "step_no": 11,
        "purpose" : "Change to default session from programming + P2Server_max parameter",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    p2_server_timing = "065001001901F400"
    #logging.info("Step%s: P2Server_timing before YML: %s",etp["step_no"], p2_server_timing)
    p2_server_timing_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'p2_server_timing')
    # don't set empty value if no replacement was found:
    if p2_server_timing_new:
        p2_server_timing = p2_server_timing_new
    else:
        logging.info("Step%s P2Server_timing_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: P2Server_timing after YML: %s", etp["step_no"], p2_server_timing)
    result = SE10.diagnostic_session_control_mode1(can_p, etp["step_no"])
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
             teststring=p2_server_timing)
    logging.info("Step%s: compare P2_server_max against: %s", etp["step_no"], p2_server_timing)
    logging.info("Step%s: result of compare: %s", etp["step_no"], result)
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
    # action: Change to extended session
    # result: BECM reports mode
        result = result and step_1(can_p)

    # step2:
    # action: Change to extended session from extended
    # result: BECM reports mode
        result = result and step_2(can_p)

    # step3:
    # action: Change to default session from extended
    # result: BECM reports mode
        result = result and step_3(can_p)

    # step4:
    # action: Change to extended session + P2Server_max param
    # result: BECM reports NRC
        result = result and step_4(can_p)

    # step5:
    # action: verify current session
    # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=5)

    # step6:
    # action: # Change to programming session + P2Server_max param
    # result: BECM reports NRC
        result = result and step_6(can_p)

    # step7:
    # action: # Change to programming mode
    # result: BECM reports mode
        SE10.diagnostic_session_control_mode2(can_p, 7)
        result = result and step_7(can_p)

    # step8:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02', stepno=8)

    # step9:
    # action: # Change to programming mode from programming
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 9)
        result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
             teststring='065002001901F400')

    # step10:
    # action: # Change to Programming session + P2Server_max paremeter
    # result: BECM reports NRC
        result = result and step_10(can_p)

    # step11:
    # action: # Change to default session from programming
    # result: BECM reports mode
        #result = result and SE10.diagnostic_session_control_mode1(can_p, 11)
        #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
        #     teststring='065001001901F400')
        result = result and step_11(can_p)
        time.sleep(1)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
