"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

#﻿
# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-10-07
# version:  2.0
# reqprod:  76524

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

The Python implementation of the gRPC route guide client.
"""

from datetime import datetime
import time
import logging
import sys
import inspect
import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SIO = SupportFileIO
SE10 = SupportService10()
SE22 = SupportService22()


def step_2(can_p):
    """
    teststep 2: Verify that ReadDTCInfoSnapshotIdentification are sent.
    Message contains Snapshot information using subservice (03)
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification",
                                        b'',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "Verify that ReadDTCInfoSnapshotIdentification are sent",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='5903')

    # Save message for use in next steps
    ecu_message = SC.can_messages[can_p["receive"]][0][2]
    return result, ecu_message


def step_3(can_p, ecu_message):
    """
    teststep 3: Verify that message contains information of DTC for specific Snapshot
    record Number selected from service 19 subservice ReadDTCInfoSnapshotIdentification
    """
    # Checking if the message is long enough to contain a DTC
    if len(ecu_message) >= 16:
        # Pick first DTC
        result = True
        dtc = ecu_message[8:14]
    else:
        result = False
        dtc = 'BADBAD'

    # Make it a byte string
    dtc_bytes = bytearray.fromhex(dtc)
    logging.debug(              \
        '------------------\n'  \
        'dtc:        %s\n'      \
        'dtc_bytes:  %s\n'      \
        '------------------',dtc, dtc_bytes)

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber",
                                        dtc_bytes,
                                        b'\xFF'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "Verify that message contains information of DTC for specific Snapshot record\
            Number selected from service 19 subservice ReadDTCInfoSnapshotIdentification",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = result and SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], 'EF04')
    return result, dtc_bytes


def step_4(can_p, dtc_bytes):
    """
    teststep 4: Request report Generic Snapshot By DTC Number
    """
    cpay: CanPayload = {
        "payload": \
            SC_CARCOM.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber(84)",
                                        dtc_bytes,
                                        b'\xFF'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Empty reply using service AF with suppressPosRspMsgIndicationBit = True",
        "timeout": 1,
        "min_no_messages": 0,
        "max_no_messages": 0
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
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
        # action: Change to extended session
        # result: BECM report mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, stepno=1)

        # step 2:
        # action: Verify that ReadDTCInfoSnapshotIdentification are sent.
        # Message contains Snapshot information using subservice (03)
        # result: BECM reply positively
        step_result, ecu_message = step_2(can_p)
        result = result and step_result

        # step 3:
        # action: Verify that message contains information of DTC for specific Snapshot
        # record Number selected from service 19 subservice ReadDTCInfoSnapshotIdentification
        # result: BECM reply positively
        step_result, dtc_bytes = step_3(can_p, ecu_message)
        result = result and step_result

        # step 4:
        # action: Verify empty reply using service AF with suppressPosRspMsgIndicationBit = True
        # result: BECM replies with empty reply
        result = result and step_4(can_p, dtc_bytes)

        # step 5:
        # action: Verify Extended session active
        # result: BECM sends active mode
        result = result and SE22.read_did_f186(can_p, b'\x03', stepno=5)

        # step 6:
        # action: Change BECM to default
        # result: BECM report mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=6)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
