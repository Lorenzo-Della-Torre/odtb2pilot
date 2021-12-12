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
# author:   hweiler (Hans-Klaus Weiler)
# date:     2020-08-11
# version:  1.1
# reqprod:  60010

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import logging
import sys
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

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
    Teststep 2: send request with MF to send
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",\
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47',\
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 2,
        "purpose" : "send several requests at one time - requires MF in request",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

# verify FC parameters from BECM for block_size
    logging.info("FC parameters used:")
    logging.info("Step%s: frames received %s", etp["step_no"], len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.info("len FC %s", len(SC.can_cf_received[can_p["receive"]]))
    logging.info("FC: %s", SC.can_cf_received[can_p["receive"]])
    logging.info("Verify if FC is as required. "\
                 "Continue to send (0x30): 0x%s separation_time: 0x%s",\
                 int(SC.can_cf_received[can_p["receive"]][0][2][0:2], 16).to_bytes(1, 'big').hex(),\
                 int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16).to_bytes(1, 'big').hex())
    logging.info("Verify separation_time less then 15ms: 15 > %s: %s",\
                 int((SC.can_cf_received[can_p["receive"]][0][2][4:6]), 16),\
                 int((SC.can_cf_received[can_p["receive"]][0][2][4:6]), 16) < 15)
    result = result and (int((SC.can_cf_received[can_p["receive"]][0][2][4:6]), 16) < 15)
    #print ("FC: ", Support_CAN.can_cf_received)
    #result = result andS UTE.test_message(SC.can_cf_received[can_p["receive"]],\
    #                                      teststring='30000A0000000000')
    logging.info("Step %s teststatus: %s\n", etp["step_no"], result)
    return result

def step_5(can_p):
    """
    Teststep 5: send request requiring MF to send
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",\
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47',\
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 5,
        "purpose" : "send several requests at one time - requires MF in request",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    # verify FC parameters from BECM for block_size
    logging.info("FC parameters used:")
    logging.info("Step%s: frames received %s", etp["step_no"], len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.info("len FC %s", len(SC.can_cf_received[can_p["receive"]]))
    logging.info("FC: %s", SC.can_cf_received[can_p["receive"]])
    logging.info("Verify if FC is as required. "\
                 "Continue to send (0x30): 0x%s separation_time: 0x%s",\
                 int(SC.can_cf_received[can_p["receive"]][0][2][0:2], 16).to_bytes(1, 'big').hex(),\
                 int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16).to_bytes(1, 'big').hex())
    logging.info("Verify separation_time less then 15ms: 15 > %s: %s",\
                 int((SC.can_cf_received[can_p["receive"]][0][2][4:6]), 16),\
                 int((SC.can_cf_received[can_p["receive"]][0][2][4:6]), 16) < 15)
    result = result and (int((SC.can_cf_received[can_p["receive"]][0][2][4:6]), 16) < 15)
    logging.info("Step %s teststatus: %s\n", etp["step_no"], result)
    return result


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    ############################################
    # precondition
    ############################################
    timeout = 60   #seconds
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify current session
    # result: default session reported
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=1)

    # step2:
    # action: send MF request
    # result: FC frame received with separation_time timing in required range
        result = result and step_2(can_p)

    # action: verify current session
    # result: extended session reported
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=3)

    # action: request extended session
    # result: change to extended session reported
        result = SE10.diagnostic_session_control_mode3(can_p, stepno=4)

    # action: send MF request
    # result: FC frame received with separation_time timing in required range
        result = result and step_5(can_p)

    # action: verify current session
    # result: extended session reported
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=6)

    # action: request default session
    # result: change to default session reported
        result = SE10.diagnostic_session_control_mode1(can_p, stepno=7)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
