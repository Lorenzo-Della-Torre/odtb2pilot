# Testscript ODTB2 MEPII
# project:  ECU basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2021-01-11
# version:  1.0
# reqprod:  129845
# -- UPDATES --
# author:
# date:
# version:
# changes:

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
from supportfunctions.support_service31 import SupportService31

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SSBL = SupportSBL()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
SE31 = SupportService31()

def validate_and_get_pn_f124(message):
    '''
    Validate and pretty print ECU Delivery Assembly Part Number
    '''
    pos = message.find('F124')
    valid = SUTE.validate_part_number_record(message[pos+4:pos+18])
    part_number = SUTE.pp_partnumber(message[pos+4:pos+18])
    return valid, part_number

def check_c_c_routine(can_p: CanParam, stepno):
    """
    Support function for Routine Complete & Compatible
    """

    result = SE31.routinecontrol_requestsid_complete_compatible(can_p, stepno)
    result = result and (
        self.pp_decode_routine_complete_compatible(SC.can_messages[can_p["receive"]][0][2]))
    logging.info(SC.can_messages[can_p["receive"]][0][2])
    return result

def step_3(can_p):
    """
    Teststep 3: send requests DID F124 - in Programming Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x24',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "Request DID F124 - in Programming Session",

        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F124')
    logging.info(SC.can_messages[can_p["receive"]])

    pbl_f124_result = SC.can_messages[can_p["receive"]][0][2]
    result = result and validate_and_get_pn_f124(pbl_f124_result)
    logging.info(pbl_f124_result)
    logging.info("\nTeststep 3_result: %s\n", result)
    return result, pbl_f124_result

def step_5(can_p):
    """
    Teststep 5: send requests DID F124 - with SBL active
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x24',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "Request DID F124 - with SBL Activated",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F124')
    logging.info(SC.can_messages[can_p["receive"]])

    sbl_f124_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info("Step 5: result: %s", sbl_f124_result)
    result = result and validate_and_get_pn_f124(sbl_f124_result)
    logging.info("\nTeststep 5_result: %s\n", result)

    return result, sbl_f124_result

def step_6(pbl_f124_result, sbl_f124_result):
    """
    TestStep 6: Validate F124 Part Number messages
    """
    pbl_valid, pbl_sbl_sw_vn = validate_and_get_pn_f124(pbl_f124_result)
    logging.info("PBL: SBL SW Version Number: %s", pbl_sbl_sw_vn)
    logging.info("pbl_valid: %s", pbl_valid)

    sbl_valid, sbl_sbl_sw_vn = validate_and_get_pn_f124(sbl_f124_result)
    logging.info("SBL: SBL SW Version Number: %s",sbl_sbl_sw_vn)
    logging.info("sbl_valid: %s", sbl_valid)

    result = pbl_valid and sbl_valid

    return result

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
    # result: ECU reports mode
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=1)
        time.sleep(1)

    # step 2:
    # action: Change to Programming session
    # result: ECU reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 2)
        time.sleep(3)
        logging.info("\nStep 2: Result: %s", result)

    # step 3:
    # action: Check Complete and Compatible
    # result: ECU sends "Complete and Compatible" reply
        #result = result and SSBL.check_complete_compatible_routine(can_p, stepno=3)
        result = result and check_c_c_routine(can_p, stepno=3)
        time.sleep(5)

        for frame_type, frames in SC.can_frames.items():
            logging.info("%s:", frame_type)
            for frame in frames:
                #ts, ft, fb = frame
                #logging.info("%s", [round(1000 * (ts - time_stamp[0]), 3), ft, fb])
                logging.info("%s", frame)
        
        logging.info("\nStep 3: Result: %s", result)

    # step 4:
    # action: Change to Programming session
    # result: ECU reports mode
        result = result and SSBL.sbl_activation(can_p,
         fixed_key='FFFFFFFFFF', stepno='4', purpose="DL and activate SBL")
        time.sleep(1)
        logging.info("\nStep 4: Result: %s", result)

    # step 5:
    # action: Check Complete and Compatible
    # result: ECU sends "Complete and Compatible" reply
        result_5 = SSBL.check_complete_compatible_routine(can_p, stepno=5)
        time.sleep(5)

        for frame_type, frames in SC.can_frames.items():
            logging.info("%s:", frame_type)
            for frame in frames:
                #ts, ft, fb = frame
                #logging.info("%s", [round(1000 * (ts - time_stamp[0]), 3), ft, fb])
                logging.info("%s", frame)

        logging.info("\nStep 5: Result: %s", result_5)

    # step 6:
    # action: Complete the testcase
    # result: Merge the results from all steps
    #         The record received Programming Session (PBL and SBL) shall be equal
        step_no = 6
        purpose = "Verify the records received are equal in all modes"
        SUTE.print_test_purpose(step_no, purpose)

        #result = result and result_step_3 and result_step_5
        #logging.info("PBL Result msg: %s", pbl_f124_result)
        #logging.info("SBL Result msg: %s", sbl_f124_result)
        #result = result and step_6(pbl_f124_result, sbl_f124_result)
        
        #result = result and (pbl_f124_result == sbl_f124_result)
        #logging.info("Step 6: Result: %s", result)

    # step7:
    # action: Set to Default session before leaving
    # result: ECU reports modes
        result_end = SE10.diagnostic_session_control_mode1(can_p, 7)
        time.sleep(1)
        result = result and result_end

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
