"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2020-10-21
# version:  1.0
# reqprod:  68202

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
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SSBL = SupportSBL()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def validate_and_get_pn_f12b(message):
    '''
    Validate and pretty print ECU Delivery Assembly Part Number
    '''
    pos = message.find('F12B')
    valid = SUTE.validate_part_number_record(message[pos+4:pos+18])
    ecu_delivery_assembly_pn = SUTE.pp_partnumber(message[pos+4:pos+18])
    return valid, ecu_delivery_assembly_pn

def send_request_f12b(can_p, step_no):
    """
    Send requests DID F12B
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x2B',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose": "Request DID F12B",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F12B')
    logging.info(SC.can_messages[can_p["receive"]])

    read_f12b_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(read_f12b_result)

    return result, read_f12b_result


def step_11(default_f12b_result, extended_f12b_result, pbl_f12b_result, sbl_f12b_result):
    """
    Test step 11:
      Validate and compare the ECU Delivery Assembly Part Numbers
    """

    step_no = 11
    purpose = "Verify the F12B records received are equal in all modes"
    SUTE.print_test_purpose(step_no, purpose)

    # validate the part number and format
    result_11, valid_f12b_num = validate_and_get_pn_f12b(default_f12b_result)

    logging.info("\nvalid_f12b_num: %s", valid_f12b_num)
    logging.info("default_f12b_result: %s", default_f12b_result)
    logging.info("extended_f12b_result: %s", extended_f12b_result)
    logging.info("pbl_f12b_result: %s", pbl_f12b_result)
    logging.info("sbl_f12b_result: %s", sbl_f12b_result)

    result = (default_f12b_result == extended_f12b_result)
    logging.info("\nTest_step_11 def==ext: %s\n", result)
    result = result and (pbl_f12b_result == sbl_f12b_result)
    logging.info("\nTest_step_11 pbl==sbl: %s\n", result)
    result = result and (default_f12b_result == pbl_f12b_result)
    logging.info("\nTest_step_11 def==pbl: %s\n", result)
    result = result and result_11
    logging.info("\nTest_step_11 Def Valid: %s\n", result)
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
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 2000
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

    # step 1:
    # action: Check if Default session
    # result: BECM reports modeS
        #result = result and SE22.read_did_f186(can_p, b'\x01', stepno=1)
        result = result and SE10.diagnostic_session_control_mode1(can_p, 1)
        time.sleep(5)

    # step 2:
    # action: send requests DID F12B in Default Session
    # result: Data record with Autosar BSW cluster version is returned
        step_result, default_f12b_result = send_request_f12b(can_p, 2)
        result = step_result and result
        logging.info("\nTest_step_2 Result: %s\n", result)

    # step 3:
    # action: Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 3)
        time.sleep(2)
        logging.info("\nTest_step_3 Result: %s\n", result)

    # step 4:
    # action: send requests DID F12B in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        step_result, extended_f12b_result = send_request_f12b(can_p, 4)
        time.sleep(1)
        result = step_result and result
        logging.info("\nTest_step_4 Result: %s\n", result)

    # step 5:
    # action: Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 5)
        time.sleep(5)
        logging.info("\nTest_step_5 Result: %s\n", result)

    # step 6:
    # action: Change to Program session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 6)
        time.sleep(2)
        logging.info("\nTest_step_6 Result: %s\n", result)

    # step 7:
    # action: send requests DID F12B in Program Session
    # result: Data record with Autosar BSW cluster version is returned
        step_result, pbl_f12b_result = send_request_f12b(can_p, 7)
        time.sleep(1)
        result = step_result and result
        logging.info("\nTest_step_7 Result: %s\n", result)

    # step 8:
    # action: Download and Activate SBL
    # result:
        result = result and SSBL.sbl_activation(can_p,
         fixed_key='FFFFFFFFFF', stepno='8', purpose="DL and activate SBL")
        time.sleep(3)
        logging.info("\nTest_step_8 Result: %s\n", result)

    # step 9:
    # action: send requests DID F12B in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        step_result, sbl_f12b_result = send_request_f12b(can_p, 9)
        time.sleep(1)
        result = step_result and result
        logging.info("\nTest_step_9 Result: %s\n", result)

    # step 10:
    # action: Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 10)
        time.sleep(5)
        logging.info("\nTest_step_10 Result: %s\n", result)

    # step 11:
    # action: Complete the testcase
    # result: Merge the results from all steps
    #         The record received in Default, Extended and Programming Session shall be equal
        result = result and step_11(default_f12b_result, extended_f12b_result,
                                    pbl_f12b_result, sbl_f12b_result)


    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
