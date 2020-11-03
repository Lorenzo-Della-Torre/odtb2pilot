# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-03
# version:  1.1
# reqprod:  74144

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-07-09
# version:  1.2
# reqprod:  74144
# changes:  YML fixed, some timing fixed

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-06
# version:  1.3
# reqprod:  74144
# changes:  Copied snippet from 74143 for better calculation of response time

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
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()

JITTER_TESTENV = 10

def step_time_measure(can_p, stepno, p2_server_max):
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
    #p2_server_max = int(SC.can_messages[can_p["receive"]][0][2][8:10], 16)
    #logging.info("Step %s: P2_server_max: %s",
    #             stepno,
    #             int(SC.can_messages[can_p["receive"]][0][2][8:10], 16))

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
    Request session change to Mode1
    """
    cpay: CanPayload = {
        'payload': SC_CARCOM.can_m_send("DiagnosticSessionControl", b'\x01', b''),
        'extra': ''
        }
    etp: CanTestExtra = {
        'step_no': 1,
        'purpose': "get P2_server_max",
        'timeout': 1,
        'min_no_messages': 1,
        'max_no_messages': 1
        }
    result = SUTE.teststep(can_p, cpay, etp)
    p2_server_max = int(SC.can_messages[can_p["receive"]][0][2][8:10], 16)
    return result, p2_server_max

def step_2(can_p):
    """
    ecu_hardreset
    """
    cpay: CanPayload = {
        'payload': SC_CARCOM.can_m_send("ECUResetHardReset", b'', b''),
        'extra': ''
        }
    etp: CanTestExtra = {
        'step_no': 2,
        'purpose': "ECU Reset",
        'timeout': 1,
        'min_no_messages': -1,
        'max_no_messages': -1
        }
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='025101')
    time.sleep(1)
    return result

def run():
    """
    Run - Call other functions from here
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    logging.info("Connecting to: %s", odtb_conf.ODTB2_DUT)
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
        # action:Change to default session
        # result: positive reply with Parameters P2_server_max and P2*_server_max
        result, p2_server_max = result and step_1(can_p)

        # step 2:
        # action: ECU Reset
        # result:
        #result, t_1, t_2 = result and step_2(can_p)
        result = result and step_2(can_p)

        # step 3:
        # action: Wait for the response message
        # result: (time receive message – time sending request) less than P2_server_max
        #result = result and step_3(t_1, t_2, p2_server_max)
        result = result and step_time_measure(can_p, stepno=3, p2_server_max=p2_server_max)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
