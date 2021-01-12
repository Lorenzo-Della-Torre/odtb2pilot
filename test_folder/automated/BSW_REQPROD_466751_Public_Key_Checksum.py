# Testscript ODTB2 MEPII
# project:  ECU basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2021-01-12
# version:  1.0
# reqprod:  466751
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
    pos = message.find('D03A')
    valid = SUTE.validate_part_number_record(message[pos+4:pos+18])
    ecu_delivery_assembly_pn = SUTE.pp_partnumber(message[pos+4:pos+18])
    return valid, ecu_delivery_assembly_pn

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

    #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='D03A')
    logging.info("TestStep2 Received msg: %s", SC.can_messages[can_p["receive"]])

    default_f12b_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(default_f12b_result)

    return result, default_f12b_result

def step_4(can_p):
    """
    Teststep 3: send requests DID D03A - in Default Session
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
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='D03A')
    logging.info(SC.can_messages[can_p["receive"]])

    extended_f12b_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(extended_f12b_result)

    return result, extended_f12b_result

def step_6(can_p):
    """
    Teststep 6: send requests DID D03A - in Programming Session
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
        "step_no": 6,
        "purpose": "Request DID D03A - in Programming Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='D03A')
    logging.info(SC.can_messages[can_p["receive"]])

    programming_f12b_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(programming_f12b_result)

    return result, programming_f12b_result

def step_8(can_p):
    """
    Teststep 8: send requests DID D03A - with SBL active
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
        "step_no": 8,
        "purpose": "Request DID D03A - with SBL Activated",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='D03A')
    logging.info(SC.can_messages[can_p["receive"]])

    sbl_f12b_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(sbl_f12b_result)

    return result, sbl_f12b_result

def step_9(default_f12b_result, extended_f12b_result, programming_f12b_result, sbl_f12b_result):
    """
    TestStep 9: Validate D03A Part Number messages
    """

    default_valid, default_ecu_da_pn = validate_and_get_pn_f12b(default_f12b_result)
    logging.info("Default ECU Delivery Assembly Part Number: %s  - %s",
                  default_ecu_da_pn, default_valid)

    extended_valid, extended_ecu_da_pn = validate_and_get_pn_f12b(extended_f12b_result)
    logging.info("Extended ECU Delivery Assembly Part Number: %s  - %s",
                  extended_ecu_da_pn, extended_valid)

    programming_valid, programming_ecu_da_pn = validate_and_get_pn_f12b(programming_f12b_result)
    logging.info("Programming ECU Delivery Assembly Part Number: %s  - %s",
                  programming_ecu_da_pn, programming_valid)

    sbl_valid, sbl_ecu_da_pn = validate_and_get_pn_f12b(sbl_f12b_result)
    logging.info("SBL: ECU Delivery Assembly Part Number: %s  - %s",
                  sbl_ecu_da_pn, sbl_valid)

    result = default_valid and extended_valid and programming_valid and sbl_valid

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
    #SSBL.get_vbf_files()
    timeout = 2000
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
        result_step_2, default_f12b_result = step_2(can_p)

    # step 3:
    # action: Change to Extended session
    # result: ECU reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 3)
        time.sleep(1)

    # step 4:
    # action: send requests DID D03A in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        result_step_4, extended_f12b_result = step_4(can_p)
        time.sleep(1)

    # step 5:
    # action: Change to Programming session
    # result: ECU reports mode
        #result = result and SE10.diagnostic_session_control_mode2(can_p, 5)
        #time.sleep(1)

    # step 6:
    # action: send requests DID D03A in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        #result_step_6, programming_f12b_result = step_6(can_p)
        #time.sleep(1)

    # step 7:
    # action: Change to Programming session
    # result: ECU reports mode
        #result = result and SSBL.sbl_activation(can_p, stepno=7, purpose="DL and activate SBL")
        #time.sleep(1)

    # step 8:
    # action: send requests DID D03A in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        #result_step_8, sbl_f12b_result = step_8(can_p)
        #time.sleep(1)

    # step9:
    # action: Complete the testcase
    # result: Merge the results from all steps
    #         The record received in Default, Extended and Programming Session shall be equal
        step_no = 9
        purpose = "Verify the D03A records received are equal in all modes"
        SUTE.print_test_purpose(step_no, purpose)

        #result = result and result_step_2 and result_step_4 and result_step_6 and result_step_8
        #result = result and step_9(default_f12b_result, extended_f12b_result,
        #                            programming_f12b_result, sbl_f12b_result)

        result = result and (default_f12b_result == extended_f12b_result)
        #result = result and (default_f12b_result == programming_f12b_result == sbl_f12b_result)

    # step10:
    # action: Set to Default session before leaving
    # result: ECU reports modes
        result_end = SE10.diagnostic_session_control_mode1(can_p, 10)
        time.sleep(1)
        result = result and result_end

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
