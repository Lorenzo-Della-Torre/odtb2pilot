# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO
# date:     2020-01-20
# reqprod:  53843
# version:  1.0

# author:   LDELLATO
# date:     2020-09-25
# reqprod:  53843
# version:  1.1

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
import argparse

import odtb_conf

from build.did import pbl_did_dict
from build.did import pbl_diag_part_num

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_rpi_gpio import SupportRpiGpio

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31


# For each each DID, wait this time for the response. If you wait to short time you might not get
# the full message (payload). The unit is seconds. 2s should cover even the biggest payloads.
RESPONSE_TIMEOUT = 2

# Test this amount of DIDs. Example: If equal to 10, the program will only test the first 10 DIDs.
# This is to speed up during testing.
# 500 should cover all DIDs
MAX_NO_OF_DIDS = 500

# Reserve this time for the full script (seconds)
SCRIPT_TIMEOUT = MAX_NO_OF_DIDS * RESPONSE_TIMEOUT + 15

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SGPIO = SupportRpiGpio()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Check format of DID file')
    parser.add_argument("--did_file", help="DID-File", type=str, action='store',
                        dest='did_file', required=False,)
    ret_args = parser.parse_args()
    return ret_args

def step_4(can_p):
    '''
    Teststep 4: Extract DB Part Number for PBL
    '''
    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xF1\x21', b''),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 4,
                         "purpose" : "Extract DB Part Number for PBL",
                         "timeout" : 5,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("PBL DB part number: %s", SC.can_messages[can_p["receive"]])
    logging.info("Step 4: %s", SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:]))
    pbl_part_number = SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:])
    return result, pbl_part_number

def step_5(pbl_part_number):
    """
    Teststep 5: Compare PBL DB Part Numbers from Data Base and PBL
    """
    stepno = 5
    purpose = "Compare PBL DB Part Numbers from Data Base and PBL"
    SUTE.print_test_purpose(stepno, purpose)

    pbl_part_number = pbl_part_number.replace(" ", "_")
    logging.info("pbl_diag_part_num: %s", pbl_diag_part_num)
    logging.info("pbl_part_number: %s", pbl_part_number)
    result = bool(pbl_diag_part_num == pbl_part_number)
    if result:
        logging.info('PBL DB Part Numbers are equal! Continue')
    else:
        logging.info('PBL DB Part Numbers are NOT equal! Test FAILS')

    return result

def step_6(can_p):
    '''
    Teststep 6: Test if all DIDs in DB are present in SW PBL
                Test service #22:
                Verify diagnostic service complies to SDDB
                Request all PBL DIDs in SDDB for ECU
    '''
    stepno = 6
    purpose = "Test if all DIDs in DB are present in SW SBL"
    SUTE.print_test_purpose(stepno, purpose)

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

        logging.debug("did_id: %s", did_id)
        logging.debug("did_info: %s", did_info)

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
            #if not logging.getLogger("master").isEnabledFor(logging.DEBUG):
            #    return False

    logging.info("Step %s: DID:s checked: %s", stepno, did_counter)

    for result in result_list:
        logging.debug('DID: %s, c_did: %s, c_sid: %s, c_size: %s, err_msg: %s',
                      result.did, result.c_did, result.c_sid, result.c_size,
                      result.err_msg)
        stepresult = stepresult and result.c_did and result.c_sid and result.c_size \
                                and not result.err_msg

    logging.info("Step %s: Result teststep: %s\n", stepno, stepresult)

    return stepresult

def step_7(can_p):
    '''
    Teststep 7: Test if DIDs not in DB return Error message
    '''

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xF1\x02', b''),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 7,
                         "purpose" : "Test if DIDs not in DB return Error message",
                         "timeout" : 1, # wait for message to arrive, but don't test (-1)
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F2231')
    #logging.info('%s', SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
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
    timeout = 500
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################


        # step 1:
        # action: Verify programming preconditions
        # result: ECU sends positive reply
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)
        time.sleep(1)

        # step 2:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)
        time.sleep(1)

        # step 3:
        # action: Security Access Request SID
        # result: ECU sends positive reply
        result = result and SE27.activate_security_access(can_p, 3)

        # step 4:
        # action: Extract SWP Number for PBL
        # result: ECU sends positive reply
        result_step4, pbl_part_number = step_4(can_p)
        result = result and result_step4

        # step 5:
        # action: Compare the PBL Part Numbers from Data Base and PBL
        # result: The Part Numbers shall be equal
        result = result and step_5(pbl_part_number)

        # step 6:
        # action: Test if all DIDs in DB are present in SW PBL
        # result: All DIDs shall be implemented as described in SDDB
        #         The test will fail if not correct response
        #         but keep the result separate and reset/end Testcase
        result = result and step_6(can_p)

        # step 7:
        # action: Test if DIDs not in DB return Error message
        # result: ECU sends negative reply
        #         The test will fail if not negative response
        #         but keep the result separate and reset/end Testcase
        result = result and step_7(can_p)

        # step 8:
        # action: Hard Reset
        # result: ECU sends positive reply
        result_8 = SE11.ecu_hardreset(can_p, stepno=8)
        time.sleep(5)
        result = result and result_8

        # step 9:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=9)


    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
