"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2020-10-20
# version:  1.0
# reqprod:  68207

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

def validate_partnumbers_f12e(message):
    '''
    Validate ECU Software Part Number
    '''
    valid = False
    pos = message.find('F12E')
    amount = int(message[pos+4:pos+6])
    logging.info("Number of PN in F12E Response: %s", amount)
    if amount > 0:
        valid = SUTE.validate_part_number_record(message[pos+6:pos+20])
        logging.info("_swlm: %s is Valid? %s", message[pos+6:pos+20], valid)
    if amount > 1:
        valid = valid and SUTE.validate_part_number_record(message[pos+20:pos+34])
        logging.info("_swp1: %s is Valid? %s", message[pos+20:pos+34], valid)
    if amount > 2:
        valid = valid and SUTE.validate_part_number_record(message[pos+34:pos+48])
        logging.info("_swp2: %s is Valid? %s", message[pos+34:pos+48], valid)
    if amount > 3:
        valid = valid and SUTE.validate_part_number_record(message[pos+48:pos+62])
        logging.info("_swce: %s is Valid? %s", message[pos+48:pos+62], valid)
    if amount > 4:
        valid = valid and SUTE.validate_part_number_record(message[pos+62:pos+76])
        logging.info("_structure_pn: %s is Valid? %s", message[pos+62:pos+76], valid)

    return valid


def step_2(can_p):
    """
    Teststep 2: send requests DID F12E - in Default Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x2E',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "Request DID F12E - in Default Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)
    default_f12e_result = SC.can_messages[can_p["receive"]][0][2]

    logging.info(default_f12e_result)

    return result, default_f12e_result


def step_5(can_p):
    """
    Teststep 5: send requests DID F12E - in Extended Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x2E',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "Request DID F12E - in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],
                                             teststring='F12E')
    extended_f12e_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(extended_f12e_result)

    return result, extended_f12e_result


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
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

    # step1:
    # action: Check if Default session
    # result: BECM reports modeS
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=1)
        time.sleep(1)

    # step2:
    # action: send requests DID F12E
    # result: Data record with ECU Software Part number is returned
        result_2, default_f12e_result = step_2(can_p)

    # step3:
    # action: Check for valid Part Numbers
    # result: Data record with ECU Software Part number is returned
        step_no = 3
        purpose = "Validate all ECU Part Numbers received"
        SUTE.print_test_purpose(step_no, purpose)

        result = result and result_2 and validate_partnumbers_f12e(default_f12e_result)
        logging.info("Result Step 3: %s", result)

    # step 4:
    # action: Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 4)
        time.sleep(1)

    # step5:
    # action: send requests DID F12E
    # result: Data record with ECU Software Part number is returned
        result_5, extended_f12e_result =  step_5(can_p)
        time.sleep(1)
        result = result and result_5
    # step6:
    # action: Complete the testcase
    # result: The record received in Default and Extended Session shall be equal
        result = result and (default_f12e_result == extended_f12e_result)

    # step7:
    # action: Set to Default session before leaving
    # result: BECM reports modes
        result_end = SE10.diagnostic_session_control_mode1(can_p, 7)
        time.sleep(1)
        result = result and result_end

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
