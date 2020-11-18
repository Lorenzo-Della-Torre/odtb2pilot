# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-09
# version:  1.0
# reqprod:  76170

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-13
# version:  1.1
# changes:  update for YML support

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

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanMFParam, CanParam, CanTestExtra, CanPayload
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

def step_2(can_p): # pylint: disable=too-many-locals
    """
    Teststep 2: send 1 requests - requires SF to send, MF for reply
    """

    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x20', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no" : 2,
        "purpose" : "Send 1 request - requires SF to send",
        "timeout" : 2,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        'block_size' : 0,
        'separation_time' : 0,
        'frame_control_delay' : 0, #no wait
        'frame_control_flag' : 48, #continue send
        'frame_control_auto' : False
        }
    SC.change_mf_fc(can_p["send"], can_mf_param)
    result = SUTE.teststep(can_p, cpay, etp)
    return result


def step_3(can_p):
    """
    Teststep 3: test if DIDs are included in reply
    """
    step_no = 3
    purpose = "test if requested DID are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")
    SC.update_can_messages(can_p["receive"])
    logging.debug("All can messages updated")
    logging.debug("Step2: messages received %s", len(SC.can_messages[can_p["receive"]]))
    logging.debug("Step2: messages: %s\n", SC.can_messages[can_p["receive"]])
    logging.debug("Step2: frames received %s", len(SC.can_frames[can_p["receive"]]))
    logging.debug("Step2: frames: %s\n", SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F120')
    return result


def step_4(can_p: CanParam): # pylint: disable=too-many-locals
    """
    Teststep 4: Send several requests at one time - requires SF to send, MF for reply
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x20\xF1\x2A', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Send several requests at one time - requires SF to send",
        "timeout": 2,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0, #no wait
        "frame_control_flag": 48, #continue send
        "frame_control_auto": False
        }
    SC.change_mf_fc(can_p["send"], can_mf_param)
    result = SUTE.teststep(can_p, cpay, etp)
    return result

def step_5(can_p):
    """
    Teststep 5:  test if DIDs are included in reply
    """
    step_no = 5
    purpose = "test if all requested DIDs are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("all can messages cleared")
    SC.update_can_messages(can_p["receive"])
    logging.debug("all can messages updated")
    logging.debug("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.debug("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.debug("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.debug("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F120')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],
                                          teststring='F12A')
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
    # action: # Change to Extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 1)

    # step2:
    # action: send 1 request - requires SF to send, MF for reply
    # result: BECM reports default session
        result = result and step_2(can_p)

    # step 3: check if DID is included in reply
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_3(can_p)

    # step4:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports default session
        result = result and step_4(can_p)

    # step 5: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_5(can_p)

    # step6:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=6)

    # step 7:
    # action: # Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 7)


    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
