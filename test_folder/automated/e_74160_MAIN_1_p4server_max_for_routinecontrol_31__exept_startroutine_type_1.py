"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-06-17
# version:  1.0
# reqprod:  74160

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-24
# version:  1.1
# changes:  update for YML support

# inspired by https://grpc.io/docs/tutorials/basic/python.html
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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

JITTER_TESTENV = 10
P4_SERVER_MAX = 200 # mseconds

def step_time_measure(can_p, stepno, p_server_max):
    """
    Teststep time_measure:
    Verify (time receive message – time sending request) less than P_server_max
    """

    logging.info("Step %s: Collecting data for calculating time:", stepno)
    t_1 = SC.can_frames[can_p["send"]][0][0]
    logging.info("Step %s: Timestamp request sent: %s", stepno, t_1)
    t_2 = SC.can_frames[can_p["receive"]][0][0]
    logging.info("Step %s: Timestamp request sent: %s", stepno, t_2)
    purpose = "Verify (time receive message – time sending request) less than P_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    result = ((p_server_max + JITTER_TESTENV)/1000 > (t_2 - t_1))
    logging.info("Step%s: t2: %s (sec)", stepno, t_2)
    logging.info("Step%s: t1: %s (sec)", stepno, t_1)
    logging.info("Step%s: t2-t1: %s (sec)", stepno, (t_2 - t_1))
    logging.info("P_server_max: %s (msec)", p_server_max)
    logging.info("JITTER_TESTENV: %s (msec)", JITTER_TESTENV)
    logging.info("P_server_max + JITTER_TESTENV: %s (msec)", p_server_max + JITTER_TESTENV)
    logging.info("Step %s teststatus:%s \n", stepno, result)
    return result


# teststep 2: verify RoutineControl start reply positively and routine Type 3 is running
def step_2(can_p):
    """
    Teststep 2: verify RoutineControl start reply positively and routine Type 3 is running
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x00',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify RoutineControl start reply positively and routine Type 3 is running",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    #T1=time.time()
    result = SUTE.teststep(can_p, cpay, etp)
    #T2 = SC.can_messages[r][0][0]
    return result


# teststep 4: verify RoutineControl start reply positively and routine Type 2 is completed
def step_4(can_p):
    """
    Teststep 4: verify RoutineControl start reply positively and routine Type 2 is completed
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xDC\x10',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "verify RoutineControl start reply positively and routine Type 3 is completed",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    #T1=time.time()
    result = SUTE.teststep(can_p, cpay, etp)

    #T2 = SC.can_messages[r][0][0]
    result = result and\
             SUTE.pp_decode_routine_control_response(SC.can_frames[can_p["receive"]][0][2],
                                                     'Type2,Completed')
    return result


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
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action:Change to extended session
    # result: BECM report mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=1)

    # step 2:
    # action:
    # result:
        result = result and step_2(can_p)

    # step 3:
    # Verify (time receive message – time sending request) less than P4_server_max
    # action: Wait for the response message
    # result: (time receive message – time sending request) less than P4_server_max
        result = result and step_time_measure(can_p, stepno=3, p_server_max=P4_SERVER_MAX)

    # step 2:
    # action:
    # result:
        result = result and step_4(can_p)

    # step 5:
    # action: Wait for the response message
    # result: (time receive message – time sending request) less than P4_server_max
        result = result and step_time_measure(can_p, stepno=5, p_server_max=P4_SERVER_MAX)

    # step6:
    # action: Verify Extended session active
    # result: BECM sends active mode
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=6)

    # step 7:
    # action: change BECM to default
    # result: BECM report mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=7)
        #time.sleep(1)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
