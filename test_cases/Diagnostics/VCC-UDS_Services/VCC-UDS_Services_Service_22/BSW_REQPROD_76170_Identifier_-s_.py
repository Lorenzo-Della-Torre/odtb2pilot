# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-09
# version:  1.0
# reqprod:  76170

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
from support_can import SupportCAN, CanMFParam, CanParam, CanTestExtra, CanPayload
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()


# teststep 1: send 1 requests - requires SF to send, MF for reply
def step_1(can_p: CanParam): # pylint: disable=too-many-locals
    """
    Teststep 1: send 1 requests - requires SF to send, MF for reply
    """

    # Parameters for the teststep
    etp: CanTestExtra = {
        "step_no" : 1,
        "purpose" : "Send 1 request - requires SF to send",
        "timeout" : 5,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }

    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        'block_size' : 0,
        'separation_time' : 0,
        'frame_control_delay' : 0, #no wait
        'frame_control_flag' : 48, #continue send
        'frame_control_auto' : False
        }
    SC.change_mf_fc(can_p["send"], can_mf_param)

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x20', b''),
        "extra": ''
        }

    result = SUTE.teststep(can_p, cpay, etp)
    return result


# teststep 2: test if DIDs are included in reply
def step_2(can_receive):
    ''' Step 2 '''
    stepno = 2
    purpose = "test if requested DID are included in reply"

    SUTE.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")
    SC.update_can_messages(can_receive)
    logging.debug("All can messages updated")
    logging.debug("Step2: messages received %s", len(SC.can_messages[can_receive]))
    logging.debug("Step2: messages: %s\n", SC.can_messages[can_receive])
    logging.debug("Step2: frames received %s", len(SC.can_frames[can_receive]))
    logging.debug("Step2: frames: %s\n", SC.can_frames[can_receive])
    logging.info("Test if string contains all IDs expected:")
    result = SUTE.test_message(SC.can_messages[can_receive], teststring='F120')
    return result


# teststep 3: send several requests at one time - requires SF to send, MF for reply
def step_3(can_p: CanParam): # pylint: disable=too-many-locals
    '''' Step 3 '''
    # Parameters for the teststep
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "Send several requests at one time - requires SF to send",
        "timeout": 5,
        "min_no_messages": -1,
        "max_no_messages": -1
        }

    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0, #no wait
        "frame_control_flag": 48, #continue send
        "frame_control_auto": False
        }

    SC.change_mf_fc(can_p["send"], can_mf_param)

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x20\xF1\x2A', b''),
        "extra": ''
        }

    result = SUTE.teststep(can_p, cpay, etp)
    return result

# teststep 4: test if DIDs are included in reply
def step_4(can_receive):
    ''' Step 4 '''
    stepno = 4
    purpose = "test if all requested DIDs are included in reply"

    SUTE.print_test_purpose(stepno, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("all can messages cleared")
    SC.update_can_messages(can_receive)
    logging.debug("all can messages updated")
    logging.debug("Step4: messages received %s", len(SC.can_messages[can_receive]))
    logging.debug("Step4: messages: %s\n", SC.can_messages[can_receive])
    logging.debug("Step4: frames received %s", len(SC.can_frames[can_receive]))
    logging.debug("Step4: frames: %s\n", SC.can_frames[can_receive])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_receive], teststring='F120')
    result = result and SUTE.test_message(SC.can_messages[can_receive],
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

    # step1:
    # action: send 1 request - requires SF to send, MF for reply
    # result: BECM reports default session
        logging.debug("step_1 start: %s", datetime.now())
        result = result and step_1(can_p)
        logging.debug("step_1 end: %s", datetime.now())

    # step 2: check if DID is included in reply
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_2(can_p["receive"])

    # step3:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports default session
        result = result and step_3(can_p)

    # step 4: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_4(can_p["receive"])

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
