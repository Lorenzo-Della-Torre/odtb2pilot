"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO
# date:     2020-11-09
# version:  1.1
# reqprod:  67761
# title:    Vehicle manufacture specific data records defined in GMRDB
# mode:     Extended

#inspired by https://grpc.io/docs/tutorials/basic/python.html

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

from build.did import app_did_dict
from build.did import app_diag_part_num

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

# For each each DID, wait this time for the response. If you wait to short time you might not get
# the full message (payload). The unit is seconds. 2s should cover even the biggest payloads.
RESPONSE_TIMEOUT = 2

# Test this amount of DIDs. Example: If equal to 10, the program will only test the first 10 DIDs.
# This is to speed up during testing.
# 500 should cover all DIDs
MAX_NO_OF_DIDS = 500

# Reserve this time for the full script (seconds)
SCRIPT_TIMEOUT = MAX_NO_OF_DIDS * RESPONSE_TIMEOUT + 15

def step_2(can_p):
    """
    Read DID F120: Application Diagnostic Database Part Number
    """
    stepno = 2
    etp: CanTestExtra = {
        "step_no": stepno,
        "purpose" : "Service22: Application Diagnostic Database Part Number",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1}
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    cpay: CanPayload = {
        "payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x20',
                                        b''),
        "extra": b''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)
    part_number = SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:])
    part_number = part_number.replace(" ", "_")
    logging.info("Step 2: %s", part_number)
    return result, part_number

def step_4(can_p):
    '''
    Test service #22:
    Verify diagnostic service complies to SDDB
    Request all APP DIDs in SDDB for ECU
    '''
    stepno = 4
    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 0
    stepresult = len(app_did_dict) > 0
    logging.info("Step %s: DID:s in dictionary: %s", stepno, len(app_did_dict))

    for did_id, did_info in app_did_dict.items():

        if ((0x0100 <= int(did_id, base=16) <= 0xDBFF) or
            (0xDE00 <= int(did_id, base=16) <= 0xE2FF) or
            (0xE600 <= int(did_id, base=16) <= 0xED1F) or
            (0xED80 <= int(did_id, base=16) <= 0xED9F) or
            (0xF010 <= int(did_id, base=16) <= 0xF0FF)):

            did_counter += 1
            if did_counter > MAX_NO_OF_DIDS:
                logging.info("MAX_NO_OF_DIDS reached: %s", MAX_NO_OF_DIDS)
                break
            logging.info('DID counter: %s', str(did_counter))

            logging.info("Testing DID: %s", did_id)
            logging.info(did_info)

            # Using Service 22 to request a particular DID, returning the result in a dictionary
            did_dict_from_service_22 = SE22.get_did_info(can_p, did_id, RESPONSE_TIMEOUT)

            # Copy info to the did_info dictionary from the did_dict
            did_info = SE22.adding_info(did_dict_from_service_22, did_info)

            # Summarizing the result
            info_entry, pass_or_fail_counter_dict = SE22.summarize_result(
                did_info, pass_or_fail_counter_dict, did_id)

            # Add the results
            result_list.append(info_entry)

            # If any of the tests failed. Quit immediately unless debugging.
            if not(info_entry.c_did and info_entry.c_sid and info_entry.c_size):
                logging.info('----------------------')
                logging.info('Testing DID %s failed.', info_entry.did)
                logging.info('----------------------')
                logging.info('DID correct: %s', info_entry.c_did)
                logging.info('SID correct: %s', info_entry.c_sid)
                logging.info('Size correct: %s', info_entry.c_size)
                logging.info('Error message: %s', info_entry.err_msg)
                logging.info('---------------------------------------')
                if not logging.getLogger("master").isEnabledFor(logging.DEBUG):
                    return False

    logging.info("Step %s: DID:s checked: %s", stepno, did_counter)
    logging.info(pass_or_fail_counter_dict)

    for result in result_list:
        logging.debug('DID: %s, c_did: %s, c_sid: %s, c_size: %s, err_msg: %s',
                      result.did, result.c_did, result.c_sid, result.c_size,
                      result.err_msg)
        stepresult = stepresult and result.c_did and result.c_sid and result.c_size \
                                and not result.err_msg

    logging.info("Step %s: Result teststep: %s\n", stepno, stepresult)
    return stepresult


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # Where to connect to signal_broker
    # Should get the values from an yml-file instead
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
    result = PREC.precondition(can_p, SCRIPT_TIMEOUT)

    #result = result and len(app_did_dict) > 0
    logging.info("Result: %s", result)
    if result:

        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Change to Extended session (03)
        # result: ECU reports session
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=1)

        # step 2:
        # action: Request DID F120
        # result: ECU responds with Application Diagnostic Database Part Number
        result_2, app_diag_part_num_response = step_2(can_p)
        result = result and result_2

        # step 3:
        # action: Check the app_diag_part_num in SDDB and Application
        # result: The part numbers should be equal
        SUTE.print_test_purpose(3, "Compare APP Diagnostic Part Numbers from Data Base and APP")
        logging.info("APP Diagnostic Part numbers are equal: %s",
                     (app_diag_part_num == app_diag_part_num_response))
        result = result and (app_diag_part_num == app_diag_part_num_response)

        # step 4:
        # action: Test all DID:s in dictionary within interval
        #         [0100, DBFF] or [DE00, E2FF] or [E600, ED1F] or [F010, F0FF]
        #         (or until limit is reached)
        # result: ECU responds with DID and size
        result = result and step_4(can_p)

        # step 5:
        # action: Change to default session
        # result: ECU reports session
        result_5 = SE10.diagnostic_session_control_mode1(can_p, stepno=5)
        time.sleep(1)
        result = result and result_5

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
