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

from hilding.dut import Dut


SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE10 = SupportService10()

def step(dut : Dut, did : str):
    '''
    Diagnostic Read Out Identifier (0xEDC0)
    '''
    # cpay: CanPayload = {
    #     "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC0', b""),
    #     "extra": b'',
    # }
    # SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    # etp: CanTestExtra = {
    #     "step_no": 1,
    #     "purpose": "Diagnostic Read Out (0xEDC0),to support"\
    #                 "quality tracking of ECU ",
    #     "timeout": 1,
    #     "min_no_messages": -1,
    #     "max_no_messages": -1,
    # }
    # SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    # result = SUTE.teststep(can_p,cpay, etp)

    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    logging.info("ReadDataByIdentifier (%s): %s", did, res)
    result = res.details[did].lower() == "EDC0".lower()
    #result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='EDC0')
    return result

def step_2(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC1)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC1', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
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

def step_3(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC2)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC2', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
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

def step_4(can_p):
    '''
    Diagnostic Read Out Identifier (0xEDC3)
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xC3', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
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
    dut = Dut()

    start_time = dut.start()

    #SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    result = False

    ############################################
    # precondition
    ############################################
    SSBL.get_vbf_files()
    dut.precondition(timeout=30)


    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: Send ReadDataByIdentifier(0xEDC0)
    # result: ECU send requested DIDs
    result = dut.step(step, did = "EDC0", purpose = "To be written")

    # step 2:
    # action: Send ReadDataByIdentifier(0xEDC1)
    # result: ECU send requested DIDs
    result = result and dut.step(step, did = "EDC1", purpose = "To be written")

    # step 3:
    # action: Send ReadDataByIdentifier(0xEDC2)
    # result: ECU send requested DIDs
    result = result and dut.step(step, did = "EDC2", purpose = "To be written")

    # step 4:
    # action: Send ReadDataByIdentifier(0xEDC3)
    # result: ECU send requested DIDs
    result = result and dut.step(step, did = "EDC3", purpose = "To be written")

    ############################################
    # postCondition
    ############################################
    dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
