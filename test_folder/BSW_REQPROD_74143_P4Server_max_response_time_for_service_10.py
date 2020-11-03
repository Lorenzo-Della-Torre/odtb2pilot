# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-02
# version:  1.1
# reqprod:  74143

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-05
# version:  1.2
# changes:  Measuring time between function call and reply resulted in too big delay, causing
#           testscript to fail. Changed to taking timestamp from request/reply instead.
#           Further update to comply to latest support function. Tested with SPA/MEP2.

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
SE11 = SupportService11()
SE10 = SupportService10()
SE22 = SupportService22()

JITTER_TESTENV = 10


def step_time_measure(can_p, stepno):
    """
    Teststep time_measure:
    Verify (time receive message – time sending request) less than P2_server_max
    """

    logging.info("Step %s: Collecting data for calculating time:", stepno)
    t_1 = SC.can_frames[can_p["send"]][0][0]
    logging.info("Step %s: Timestamp request sent: %s", stepno, t_1)
    t_2 = SC.can_frames[can_p["receive"]][0][0]
    logging.info("Step %s: Timestamp request sent: %s", stepno, t_2)
    #fetch P2 server max from the received message
    p2_server_max = int(SC.can_messages[can_p["receive"]][0][2][8:10], 16)
    logging.info("Step %s: P2_server_max: %s",
                 stepno,
                 int(SC.can_messages[can_p["receive"]][0][2][8:10], 16))

    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    result = ((p2_server_max + JITTER_TESTENV)/1000 > (t_2 - t_1))
    logging.info("Step%s: t2: %s (sec)", stepno, t_2)
    logging.info("Step%s: t1: %s (sec)", stepno, t_1)
    logging.info("Step%s: t2-t1: %s (sec)", stepno, (t_2 - t_1))
    logging.info("P2_server_max: %s (msec)", p2_server_max)
    logging.info("JITTER_TESTENV: %s (msec)", JITTER_TESTENV)
    logging.info("P2_server_max + JITTER_TESTENV: %s (msec)", p2_server_max + JITTER_TESTENV)
    #logging.info("(p2-jitter) / 1000: %s", (p2_server_max + JITTER_TESTENV)/1000)

    #logging.info("T difference(s): %s", (p2_server_max + JITTER_TESTENV)/1000 - (t_2 - t_1))
    logging.info("Step %s teststatus:%s \n", stepno, result)
    return result

def step_1(can_p):
    """
    Teststep 1: Read out P2_server_max programming session
    """
    stepno = 1
    purpose = "Read out P2_server_max programming session"
    SUTE.print_test_purpose(stepno, purpose)
    result = SE10.diagnostic_session_control_mode2(can_p, stepno)
    result = result and SE10.diagnostic_session_control_mode2(can_p, stepno)
    logging.info(SC.can_frames[can_p["receive"]])
    time.sleep(1)
    return result


def step_3(can_p):
    """
    Teststep 3: Read out P2_server_max default session
    """
    stepno = 3
    purpose = "Read out P2_server_max default session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    #t_1 = time.time()
    result = SE10.diagnostic_session_control_mode1(can_p, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_p["receive"]])
    #p2_server_max = int(SC.can_messages[can_p["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    #t_2 = SC.can_messages[can_p["receive"]][0][0]
    time.sleep(1)
    #return t_1, t_2, p2_server_max, result
    return result


def step_5(can_p):
    """
    Teststep 5: Read out P2_server_max extended session
    """
    stepno = 5
    purpose = "Read out P2_server_max extended session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    #t_1 = time.time()
    result = SE10.diagnostic_session_control_mode3(can_p, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_p["receive"]])
    #p2_server_max = int(SC.can_messages[can_p["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    #t_2 = SC.can_messages[can_p["receive"]][0][0]
    time.sleep(1)
    #return t_1, t_2, p2_server_max, result
    return result


def step_7(can_p):
    """
    Teststep 7: Read out P2_server_max default session
    """
    stepno = 7
    purpose = "Read out P2_server_max default session"
    SUTE.print_test_purpose(stepno, purpose)
    #time start request
    #t_1 = time.time()
    result = SE10.diagnostic_session_control_mode1(can_p, stepno)
    #fetch P2 server max from the received message
    logging.info(SC.can_frames[can_p["receive"]])
    #p2_server_max = int(SC.can_messages[can_p["receive"]][0][2][8:10], 16)
    #fetch time stop request and start reply from ECU reply message
    #t_2 = SC.can_messages[can_p["receive"]][0][0]
    time.sleep(1)
    #return t_1, t_2, p2_server_max, result
    return result


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

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
    timeout = 20
    #timeout = 600
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action:
        # result:
        result = step_1(can_p)

        # step2:
        # action:
        # result:
        result = result and step_time_measure(can_p, 2)

        # step3:
        # action:
        # result:
        result = result and step_3(can_p)

        # step4:
        # action:
        # result:
        result = result and step_time_measure(can_p, 4)

        # step5:
        # action:
        # result:
        result = result and step_5(can_p)
        #result = result and result_step_5

        # step6:
        # action:
        # result:
        result = result and step_time_measure(can_p, 6)
        time.sleep(1)

        # step7:
        # action:
        # result:
        #t_1, t_2, p2_server_max, result_step_7 = step_7(can_p)
        #result = result and result_step_7
        result = result and step_7(can_p)

        # step8:
        # action:
        # result:
        result = result and step_time_measure(can_p, 8)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
