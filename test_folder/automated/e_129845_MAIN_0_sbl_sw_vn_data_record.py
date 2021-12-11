"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  ECU basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2021-01-11
# version:  1.0
# reqprod:  129845

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

def validate_and_get_pn_f124(message):
    '''
    Validate and pretty print ECU Delivery Assembly Part Number
    '''
    pos = message.find('F124')
    valid = SUTE.validate_part_number_record(message[pos+4:pos+18])
    part_number = SUTE.pp_partnumber(message[pos+4:pos+18])
    logging.info("SBL Software Version Number: %s", part_number)
    return valid

def step_3(can_p):
    """
    Teststep 3: send requests DID F124 - in Programming Session
      Expect: Negative response: Service: 22, requestOutOfRange (3100000000)
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
    # Negative response: Service: 22, requestOutOfRange (3100000000)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F2231')

    pbl_f124_result = SC.can_messages[can_p["receive"]][0][2]
    #result = result and validate_and_get_pn_f124(pbl_f124_result)

    logging.info(pbl_f124_result)
    logging.debug("\nTeststep 3_result: %s\n", result)

    return result

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
    result = result and validate_and_get_pn_f124(sbl_f124_result)

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
        time.sleep(1)

    # step 3:
    # action: read DID F124 from PBL
    # result: Negative response: Service: 22, requestOutOfRange (3100000000)
        result = result and step_3(can_p)
        time.sleep(1)

    # step 4:
    # action: DL and activate SBL
    # result: ECU reports mode
        result = result and SSBL.sbl_activation(can_p,
         fixed_key='FFFFFFFFFF', stepno='4', purpose="DL and activate SBL")
        time.sleep(1)

    # step 5:
    # action: read DID F124 from SBL
    # result: Data record is returned
        result = result and step_5(can_p)
        time.sleep(1)

    # step 6:
    # action: Set to Default session before leaving
    # result: ECU reports modes
        result_end = SE10.diagnostic_session_control_mode1(can_p, 6)
        time.sleep(1)
        result = result and result_end

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
