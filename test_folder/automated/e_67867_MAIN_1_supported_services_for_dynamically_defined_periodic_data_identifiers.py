"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-12-04
# version:  2.0
# reqprod:  67867

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

from datetime import datetime
import time
import logging
import sys
import inspect
import odtb_conf
from supportfunctions.support_can           import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2    import SupportTestODTB2
from supportfunctions.support_precondition  import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_file_io       import SupportFileIO
from supportfunctions.support_carcom        import SupportCARCOM
from supportfunctions.support_service10     import SupportService10
from supportfunctions.support_service22     import SupportService22

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SIO = SupportFileIO
SE10 = SupportService10()
SE22 = SupportService22()


def step_1(can_p):
    """
    Teststep 1:
    Send DynamicallyDefineDataIdentifier (01 F2 00) and confirm
    that service 2C defines the periodic identifier 0xF200
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier",
                                        b'\x01\xF2\x00',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Define periodic DID 0xF200",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F200')
    logging.info("Step 1: Result test_message: %s", result)
    return result


def step_2(can_p):
    """
    Teststep 2:
    Send ReadDataByPeriodicIdentifier (01 F2 00) and confirm
    that service 2A responds with the DID
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier",
                                        b'\x01\xF2\x00',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "Read periodic DID 0xF200",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F200')
    logging.info("Step 2: Result test_message: %s", result)
    return result


def step_3(can_p):
    """
    Teststep 3:
    Send ReadDataByIdentifier (F2 00) and confirm
    that service 22 responds with requestOutOfRange
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF2\x00',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "Read DID 0xF200",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='223100')
    logging.info("Step 3: Result test_message: %s", result)
    return result

def step_4(can_p):
    """
    Teststep 4:
    Send WriteDataByIdentifier (01 F2 00) and confirm
    that service 2E responds with requestOutOfRange
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                        b'\01\xF2\x00',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Write DID 0xF200",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='2E3100')
    logging.info("Step 4: Result test_message: %s", result)
    return result


def step_5(can_p):
    """
    Teststep 5:
    Send DynamicallyDefineDataIdentifier (03 F2 00) and confirm
    that service 2C clears the periodic identifier 0xF200
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier",
                                        b'\x03\xF2\x00',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "Clear periodic DID 0xF200",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F200')
    logging.info("Step 5: Result test_message: %s", result)
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
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action:   Verify that service 2C can define periodic DID (F2 00)
        # result:   BECM reply positively
        result = step_1(can_p)

        # step 2:
        # action:   Verify that service 2A can read the previously defined DID (F2 00)
        # result:   BECM reply positively
        result = result and step_2(can_p)

        # step 3:
        # action:   Verify that service 22 can NOT read the previously defined DID (F2 00)
        # result:   BECM replies with requestOutOfRange
        result = result and step_3(can_p)

        # step 4:
        # action:   Verify that service 2E can NOT read the previously defined DID (F2 00)
        # result:   BECM replies with requestOutOfRange
        result = result and step_4(can_p)

        # step 5:
        # action:   Verify that service 2C can clear the previously defined periodic DID (F2 00)
        # result:   BECM reply positively
        result = result and step_5(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
