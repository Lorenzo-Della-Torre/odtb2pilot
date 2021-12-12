"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  ECU basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2021-01-12
# version:  1.0
# reqprod:  466751

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

The Python implementation of the gRPC route guide client.
"""

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


def step_2(can_p):
    """
    Teststep 2: send requests DID D03A - in Default Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xD0\x3A',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "Read Public Key Checksum - in Default Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(3)

    logging.info("TestStep2 Received msg: %s", SC.can_messages[can_p["receive"]])
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='D03A')

    default_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(default_result)

    return result, default_result

def step_4(can_p):
    """
    Teststep 3: send requests DID D03A - in Extended Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xD0\x3A',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Request DID D03A - in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(3)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='D03A')
    logging.info(SC.can_messages[can_p["receive"]])

    extended_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(extended_result)

    return result, extended_result


def run():
    """
    Run - Call other functions from here
    """

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToECUFront1DiagReqFrame",
        "receive" : "ECUToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 500
    result = PREC.precondition(can_p, timeout)
    result = True

    if result:
    ############################################
    # teststeps
    ############################################

    # step 1:
    # action: Check if Default session
    # result: ECU reports modeS
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=1)
        time.sleep(1)

    # step 2:
    # action: send requests DID D03A in Default Session
    # result: Data record with Autosar BSW cluster version is returned
        result_step_2, default_result = step_2(can_p)

    # step 3:
    # action: Change to Extended session
    # result: ECU reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 3)
        time.sleep(1)

    # step 4:
    # action: send requests DID D03A in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        result_step_4, extended_result = step_4(can_p)
        time.sleep(1)

    # step 5:
    # action: Complete the testcase
    # result: Merge the results from all steps
    #         The record received in Default and Extended Session shall be equal
        step_no = 5
        purpose = "Verify the D03A records received are equal in all modes"
        SUTE.print_test_purpose(step_no, purpose)
        logging.info("D03A read in Default: %s  Valid: %s", default_result, result_step_2)
        logging.info("D03A read in Extended: %s Valid: %s",extended_result, result_step_4)
        result = result and result_step_2 and result_step_4
        result = result and (default_result == extended_result)

    # step 6:
    # action: Set to Default session before leaving
    # result: ECU reports modes
        result_end = SE10.diagnostic_session_control_mode1(can_p, 6)
        time.sleep(1)
        result = result and result_end

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
