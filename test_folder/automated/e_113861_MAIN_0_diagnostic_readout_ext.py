# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   T-KUMARA (Tanuj Kumar Aluru)
# date:     2020-10-29
# version:  1.0
# reqprod:  113861
#
# inspired by https://grpc.io/docs/tutorials/basic/python.html
#
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

from supportfunctions.support_can import SupportCAN, CanParam,CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10


SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE10 = SupportService10()

def step_3(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC0)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC0', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "Diagnostic Read Out (0xEDC0),to support"\
                    "quality tracking of ECU ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    logging.info("ReadDataByIdentifier (0xEDC0): %s",SC.can_messages[can_p['receive']][0][2])
    result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='EDC0')
    return result

def step_4(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC1)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC1', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Diagnostic Read Out (0xEDC1),to support"\
                    "quality tracking of ECU ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    logging.info("ReadDataByIdentifier (0xEDC1): %s",SC.can_messages[can_p['receive']][0][2])
    result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='EDC1')
    return result

def step_5(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC2)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC2', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "Diagnostic Read Out (0xEDC2),to support"\
                    "quality tracking of ECU ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    logging.info("ReadDataByIdentifier (0xEDC2): %s",SC.can_messages[can_p['receive']][0][2])
    result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='EDC2')
    return result

def step_6(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC3)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC3', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 6,
        "purpose": "Diagnostic Read Out (0xEDC3),to support"\
                    "quality tracking of ECU ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    logging.info("ReadDataByIdentifier (0xEDC3): %s",SC.can_messages[can_p['receive']][0][2])
    result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='EDC3')
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
    SSBL.get_vbf_files()
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Change to Extended Session
        # result: ECU send requested DIDs
        result = result and SE10.diagnostic_session_control_mode3(can_p,1)

        # step 2:
        # action: Verify the active diagnostic session
        # result: ECU send requested DIDs
        result = result and SE22.read_did_f186(can_p, b'\x03',2)

        # step 3:
        # action: Send ReadDataByIdentifier(0xEDC0)
        # result: ECU send requested DIDs
        result = result and step_3(can_p)

        # step 4:
        # action: Send ReadDataByIdentifier(0xEDC1)
        # result: ECU send requested DIDs
        result = result and step_4(can_p)

        # step 5:
        # action: Send ReadDataByIdentifier(0xEDC2)
        # result: ECU send requested DIDs
        result = result and step_5(can_p)

        # step 6:
        # action: Send ReadDataByIdentifier(0xEDC3)
        # result: ECU send requested DIDs
        result = result and step_6(can_p)

        # step 7:
        # action: Change to Default Session
        # result: ECU send requested DIDs
        result = result and SE10.diagnostic_session_control_mode1(can_p,7)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
