# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-02
# version:  1.1
# reqprod:  74143

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
SE11 = SupportService11()
SE10 = SupportService10()
SE22 = SupportService22()

JITTER_TESTENV = 10

def step_1(can_par):
    """
    Teststep 1: Read out P2_server_max programming session
    """
    stepno = 1
    purpose = "Read out P2_server_max programming session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    t_1 = time.time()
    result = SE10.diagnostic_session_control_mode2(can_par, stepno)
    result = result and SE10.diagnostic_session_control_mode2(can_par, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_par["receive"]])
    p2_server_max = int(SC.can_messages[can_par["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    t_2 = SC.can_messages[can_par["receive"]][0][0]
    time.sleep(1)
    return t_1, t_2, p2_server_max, result

def step_2(t_1, t_2, p2_server_max):
    """
    Teststep 2: Verify (time receive message – time sending request) less than P2_server_max
    """
    stepno = 2
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    result = ((p2_server_max + JITTER_TESTENV)/1000 > (t_2 - t_1))

    logging.info("T difference(s): %s", (p2_server_max + JITTER_TESTENV)/1000 - (t_2 - t_1))
    logging.info("Step %s teststatus:%s \n", stepno, result)
    return result

def step_3(can_par):
    """
    Teststep 3: Read out P2_server_max default session
    """
    stepno = 3
    purpose = "Read out P2_server_max default session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    t_1 = time.time()
    result = SE10.diagnostic_session_control_mode1(can_par, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_par["receive"]])
    p2_server_max = int(SC.can_messages[can_par["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    t_2 = SC.can_messages[can_par["receive"]][0][0]
    time.sleep(1)
    return t_1, t_2, p2_server_max, result

def step_4(t_1, t_2, p2_server_max):
    """
    Teststep 4: Verify (time receive message – time sending request) less than P2_server_max
    """
    stepno = 4
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    result = ((p2_server_max + JITTER_TESTENV)/1000 > (t_2 - t_1))

    logging.info("T difference(s): %s", (p2_server_max + JITTER_TESTENV)/1000 - (t_2 - t_1))
    logging.info("Step %s teststatus:%s \n", stepno, result)
    return result

def step_5(can_par):
    """
    Teststep 5: Read out P2_server_max extended session
    """
    stepno = 5
    purpose = "Read out P2_server_max extended session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    t_1 = time.time()
    result = SE10.diagnostic_session_control_mode3(can_par, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_par["receive"]])
    p2_server_max = int(SC.can_messages[can_par["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    t_2 = SC.can_messages[can_par["receive"]][0][0]
    time.sleep(1)
    return t_1, t_2, p2_server_max, result

def step_6(t_1, t_2, p2_server_max):
    """
    Teststep 6: Verify (time receive message – time sending request) less than P2_server_max
    """
    stepno = 6
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    result = ((p2_server_max + JITTER_TESTENV)/1000 > (t_2 - t_1))

    logging.info("T difference(s): %s", (p2_server_max + JITTER_TESTENV)/1000 - (t_2 - t_1))
    logging.info("Step %s teststatus:%s \n", stepno, result)
    return result

def step_7(can_par):
    """
    Teststep 7: Read out P2_server_max default session
    """
    stepno = 7
    purpose = "Read out P2_server_max default session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    t_1 = time.time()
    result = SE10.diagnostic_session_control_mode1(can_par, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_par["receive"]])
    p2_server_max = int(SC.can_messages[can_par["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    t_2 = SC.can_messages[can_par["receive"]][0][0]
    time.sleep(1)
    return t_1, t_2, p2_server_max, result

def step_8(t_1, t_2, p2_server_max):
    """
    Teststep 8: Verify (time receive message – time sending request) less than P2_server_max
    """
    stepno = 8
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    result = ((p2_server_max + JITTER_TESTENV)/1000 > (t_2 - t_1))

    logging.info("T difference(s): %s", (p2_server_max + JITTER_TESTENV)/1000 - (t_2 - t_1))
    logging.info("Step %s teststatus:%s \n", stepno, result)
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
    timeout = 20
    #timeout = 600
    result = PREC.precondition(can_par, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action:
        # result:
        t_1, t_2, p2_server_max, result_step_1 = step_1(can_par)
        result = result and result_step_1

        # step2:
        # action:
        # result:
        result = result and step_2(t_1, t_2, p2_server_max)

        # step3:
        # action:
        # result:
        t_1, t_2, p2_server_max, result_step_3 = step_3(can_par)
        result = result and result_step_3

        # step4:
        # action:
        # result:
        result = result and step_4(t_1, t_2, p2_server_max)

        # step5:
        # action:
        # result:
        t_1, t_2, p2_server_max, result_step_5 = step_5(can_par)
        result = result and result_step_5

        # step6:
        # action:
        # result:
        result = result and step_6(t_1, t_2, p2_server_max)
        time.sleep(1)
        # step7:
        # action:
        # result:
        t_1, t_2, p2_server_max, result_step_7 = step_7(can_par)
        result = result and result_step_7

        # step8:
        # action:
        # result:
        result = result and step_8(t_1, t_2, p2_server_max)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
