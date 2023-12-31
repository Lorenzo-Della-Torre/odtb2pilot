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
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-10
# version:  1.0
# reqprod:  76512

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
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
    Teststep 2: vverify that Read DTC Extent Info reply positively
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoExtDataRecordByDTCNumber",
                                        b'\x0B\xE1\x23', b'\xFF'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "verify that Read DTC Extent Info reply positively",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],
                                          teststring='5906')
    #extract the dtc number from the first frame received '0'
    # second value '2' on specific position (8:14)
    dtc_number = SUTE.pp_string_to_bytes(SC.can_frames[can_p["receive"]][0][2][8:14], 3)
    #extract the dtc extended record number from the second frame received '1'
    #second value '2' on specific position (2:4)
    dtc_ext_data_record_number = SUTE.pp_string_to_bytes(
        SC.can_frames[can_p["receive"]][1][2][2:4], 1)
    return result, dtc_number, dtc_ext_data_record_number

def step_3(can_p, dtc_number, dtc_ext_data_record_number):
    """
    Teststep 3: verify that ExtDataRecordByDTCNumber for specific number reply positively
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoExtDataRecordByDTCNumber",\
                                        dtc_number, dtc_ext_data_record_number),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "verify that ExtDataRecordByDTCNumber for specific number reply positively",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],
                                          teststring='5906')
    return result

def step_4(can_p, dtc_number, dtc_ext_data_record_number):
    """
    Teststep 4: verify that ExtDataRecordByDTCNumber reply with empty message
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoExtDataRecordByDTCNumber(86)",
                                        dtc_number, dtc_ext_data_record_number),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "verify that ExtDataRecordByDTCNumber reply with empty message",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and not SC.can_messages[can_p["receive"]]
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

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
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step1:
    # action: # Change to extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 1)

    # step2:
    # action:
    # result: BECM sends positive reply
        resultt, dtc_number, dtc_ext_data_record_number = step_2(can_p)
        result = result and resultt

    # step3:
    # action:
    # result: BECM sends positive reply
        result = result and step_3(can_p, dtc_number, dtc_ext_data_record_number)

    # step4:
    # action:
    # result: BECM sends positive reply
        result = result and step_4(can_p, dtc_number, dtc_ext_data_record_number)

    # step5:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=5)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
