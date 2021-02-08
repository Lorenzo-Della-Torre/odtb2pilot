# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2020-10-21
# version:  1.0
# reqprod:  68197
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
    Teststep 2: send requests DID F126 - in Default Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x26',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "Request DID F126 - in Default Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F126')
    logging.info(SC.can_messages[can_p["receive"]])

    default_f126_result = SC.can_messages[can_p["receive"]][0][2]
    logging.info(default_f126_result)
    return result, default_f126_result

def step_3(message):
    """
    Teststep 3: Verify the F126 Autosar BSW cluster version data record
    From SDDB:
      '22F126': {'Name': 'AUTOSAR BSW Vendor IDs and Cluster Versions', 'ID': 'F126', 'Size': '51'}
    """
    step_no = 3
    purpose = "Verify the F126 Autosar BSW cluster version data record"
    SUTE.print_test_purpose(step_no, purpose)

    pos = message.find('F126')
    result = (pos > 0)
    m_length = (len(message) - pos - 4)/2
    result = result and ( m_length== 51)
    logging.info("F126 Size = %s", m_length)

    logging.info("Result Step 3: %s", result)

    return result


def step_5(can_p):
    """
    Teststep 5: send requests DID F126 - in Default Session
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x26',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "Request DID F126 - in Extended Session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F126')
    logging.info(SC.can_messages[can_p["receive"]])

    extended_f126_result = SC.can_messages[can_p["receive"]][0][2]

    logging.info(extended_f126_result)

    return result, extended_f126_result


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
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

    # step 1:
    # action: Check if Default session
    # result: BECM reports modeS
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=1)
        time.sleep(1)

    # step 2:
    # action: send requests DID F126 in Default Session
    # result: Data record with Autosar BSW cluster version is returned
        result_step_2, default_f126_result = step_2(can_p)
        result = result and result_step_2

    # step 3:
    # action: Verify the F126 Autosar BSW cluster version data record
    # result: The record shall be valid

        result = result and step_3(default_f126_result)

    # step 4:
    # action: Change to Extended session
    # result: BECM reports mode

        result = result and SE10.diagnostic_session_control_mode3(can_p, 4)
        time.sleep(1)

    # step 5:
    # action: send requests DID F126 in Extended Session
    # result: Data record with Autosar BSW cluster version is returned
        result_step_5, extended_f126_result  = step_5(can_p)
        time.sleep(1)
        result = result and result_step_5

    # step 6:
    # action: Complete the testcase
    # result: The content shall be equal of content recieved in step 1
        result = result and (default_f126_result == extended_f126_result)

    # step7:
    # action: Set to Default session before leaving
    # result: BECM reports modes
        result_end = SE10.diagnostic_session_control_mode1(can_p, 7)
        time.sleep(1)
        result = result and result_end

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
