# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   FJANSSO8 (Fredrik Jansson)
# date:     2019-12-16
# version:  1.0

# author:   J-ADSJO
# date:     2020-10-23
# version:  1.1

# #inspired by https://grpc.io/docs/tutorials/basic/python.html
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
from support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess
from support_rpi_gpio import SupportRpiGpio

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service11 import SupportService11
from support_service22 import SupportService22
from support_service31 import SupportService31

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
SE31 = SupportService31()

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Check format of DID file')
    parser.add_argument("--did_file", help="DID-File", type=str, action='store',
                        dest='did_file', required=False,)
    ret_args = parser.parse_args()
    return ret_args

def step_2(can_p):
    '''
    Teststep 2: Extract SWP Number for SBL
    '''

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xF1\x22', b''),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 2,
                         "purpose" : "Extract SWP Number for SBL",
                         "timeout" : 5,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("SBL part number: %s", SC.can_messages[can_p["receive"]])
    logging.info("Step 2: %s", SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:]))
    db_number = SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:])
    return result, db_number

def step_3(margs, db_number):
    """
    Teststep 3: Extract all DID from Data Base
    """
    stepno = 3
    purpose = "Extract all DID from Data Base"
    SUTE.print_test_purpose(stepno, purpose)
    did_list = SUTE.extract_db_did_id(db_number, margs)
    return did_list

def step_4(can_p, did_list):
    '''
    Teststep 4: Test if all DIDs in DB are present in SW SBL
    '''

    etp: CanTestExtra = {"step_no": 4,
                         "purpose" : "Test if all DIDs in DB are present in SW SBL",
                         "timeout" : 1, # wait for message to arrive, but don't test (-1)
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    for did in did_list:
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                            bytes.fromhex(did), b''),
                            "extra" : ''
                           }

        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

        result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_5(can_p):
    '''
    Teststep 5: Test if DIDs not in DB return Error message
    '''

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xF1\x02', b''),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 5,
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

def run(margs):
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
    timeout = 100
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=1,
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step 2:
        # action: Extract SWP Number for SBL
        # result: ECU sends positive reply
        result_step2, db_number = result and step_2(can_p)
        result = result and result_step2

        # step 3:
        # action: Extract all DID from Data Base
        # result:
        did_list = step_3(margs, db_number)

        # step 4:
        # action: Test if all DIDs in DB are present in SW SBL
        # result: ECU sends positive reply
        result = result and step_4(can_p, did_list)

        # step 5:
        # action: Test if DIDs not in DB return Error message
        # result: ECU sends positive reply
        result = step_5(can_p)

        # step 6:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=6)
        time.sleep(1)

        # step 7:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=7)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    ARGS = parse_some_args()
    run(ARGS)
