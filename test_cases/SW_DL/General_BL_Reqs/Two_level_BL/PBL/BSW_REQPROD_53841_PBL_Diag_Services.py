# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   FJANSSO8 (Fredrik Jansson)
# date:     2020-06-23
# version:  1.0
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
import odtb_conf
from support_can import SupportCAN, CanParam
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_service10 import SupportService10
from support_service22 import SupportService22
from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from output.did_dict import sddb_pbl_did_dict

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
MAX_NO_OF_DIDS = 15 #400 #215 #155

# Reserve this time for the full script (seconds)
# 400 DIDs * 2s = 800s should cover all DIDs
SCRIPT_TIMEOUT = MAX_NO_OF_DIDS * RESPONSE_TIMEOUT + 15 #800


def step_1(can_p: CanParam):
    '''
    Change to programming session (02) - enter PBL
    '''
    stepno = 1
    result = SE10.diagnostic_session_control_mode2(can_p, stepno)
    return result


def step_2(can_p: CanParam):
    '''
    Request complete ECU part/serial number: Request Read_Data By Identifier
    '''
    stepno = 2
    result = SE22.read_did_eda0(can_p, stepno)
    return result


def step_3(can_p: CanParam):
    '''
    Test service #22:
    Verify diagnostic service complies to SDDB
    Request all PBL DIDs in SDDB for ECU
    '''
    #stepno = 3
    step3_result = True

    pass_or_fail_counter_dict = {"Passed": 0, "Failed": 0, "conditionsNotCorrect (22)": 0,
                                 "requestOutOfRange (31)": 0}
    result_list = list()
    did_counter = 1 # Used when we don't want to run through all tests

    for did_dict_from_file_values in sddb_pbl_did_dict.values():
        logging.debug('DID counter: %s', str(did_counter))

        did_id = did_dict_from_file_values['ID']
        did_dict_with_result = did_dict_from_file_values

        # Using Service 22 to request a particular DID, returning the result in a dictionary
        did_dict_from_service_22 = SE22.get_did_info(can_p, did_id, RESPONSE_TIMEOUT)

        # Copy info to the did_dict_with_result dictionary from the did_dict
        did_dict_with_result = SE22.adding_info(did_dict_from_service_22, did_dict_with_result)

        # Adding scaled data to the dictionary with the result
        if 'error_message' not in did_dict_with_result:
            did_dict_with_result = SE22.scale_data(did_dict_with_result)

        # Summarizing the result
        info_entry, pass_or_fail_counter_dict = SE22.summarize_result(did_dict_with_result,
                                                                      pass_or_fail_counter_dict,
                                                                      did_id)
        # Add the results
        result_list.append(info_entry)

        # If any of the tests failed. Quit immediately
        if not(info_entry.c_did and info_entry.c_sid and info_entry.c_size):
            logging.info('\n')
            logging.info('----------------------')
            logging.info('Testing DID %s failed.', info_entry.did)
            logging.info('----------------------')
            logging.info('DID correct: %s', info_entry.c_did)
            logging.info('SID correct: %s', info_entry.c_sid)
            logging.info('Size correct: %s', info_entry.c_size)
            logging.info('Error message: %s', info_entry.err_msg)
            logging.info('---------------------------------------')
            logging.info('\n')
            return False

        if did_counter >= MAX_NO_OF_DIDS:
            break

        did_counter += 1

    for result in result_list:
        logging.debug('DID: %s, c_did: %s, c_sid: %s, c_size: %s, err_msg: %s',
                      result.did, result.c_did, result.c_sid, result.c_size,
                      result.err_msg)
        while step3_result:
            step3_result = result.err_msg and result.c_did and result.c_sid and result.c_size
    return step3_result


def run():
    """
    Run - Call other functions from here
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # Where to connect to signal_broker
    # Should get the values from an yml-file instead
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    result = PREC.precondition(can_p, SCRIPT_TIMEOUT)

    ############################################
    # teststeps
    ############################################
    result = result and step_1(can_p)
    result = result and step_2(can_p)
    result = result and step_3(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
