"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-10-22
# version:  2.1
# reqprod:  53841

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

from build.did import pbl_did_dict
from supportfunctions.support_can import SupportCAN, CanParam
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


def step_3(can_p):
    '''
    Test service #22:
    Verify diagnostic service complies to SDDB
    Request all PBL DIDs in SDDB for ECU
    '''
    stepno = 3
    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 0
    stepresult = len(pbl_did_dict) > 0
    logging.info("Step %s: DID:s in dictionary: %s", stepno, len(pbl_did_dict))

    for did_id, did_info in pbl_did_dict.items():
        did_counter += 1
        if did_counter > MAX_NO_OF_DIDS:
            logging.info("MAX_NO_OF_DIDS reached: %s", MAX_NO_OF_DIDS)
            break
        logging.debug('DID counter: %s', str(did_counter))


        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict_from_service_22 = SE22.get_did_info(can_p, did_id, RESPONSE_TIMEOUT)
        logging.debug("did_dict_from_service_22: %s", did_dict_from_service_22)

        # Copy info to the did_info dictionary from the did_dict
        did_info = SE22.adding_info(did_dict_from_service_22, did_info)
        logging.debug("did_info: %s", did_info)

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

    logging.debug("Step %s: DID:s checked: %s", stepno, did_counter)
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

    #result = result and len(pbl_did_dict) > 0
    logging.info("Result: %s", result)
    if result:

        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Change to programming session (02) - enter PBL
        # result: ECU reports session
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=1)

        # step 2:
        # action: Request DID EDA0
        # result: ECU responds with DID EDA0
        result = result and SE22.read_did_eda0(can_p, stepno=2)

        # step 3:
        # action: Request all DID:s in dictionary (or until limit is reached)
        # result: ECU responds with DID:s
        result = result and step_3(can_p)

        # step 4:
        # action: Change to default session
        # result: ECU reports session
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=4)
        time.sleep(1)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
