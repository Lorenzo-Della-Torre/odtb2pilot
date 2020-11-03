# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   G-HERMA6 (Gunnar Hermansson)
# date:     2020-10-13
# version:  2.0
# reqprod:  60003

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

from datetime import datetime
import inspect
import logging
import time
import sys

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload, CanMFParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_test_odtb2 import SupportTestODTB2

import parameters.odtb_conf as odtb_conf

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SUTE = SupportTestODTB2()

def step_1(can_p):
    """
    Step 1: Verify ECU is in default session.
    """
    SUTE.print_test_purpose(1, "Verify ECU is in default session.")
    return SE22.read_did_f186(can_p, b'\x01')

def step_2(can_p):
    """
    Step 2: Request EDA0 - Complete ECU part/serial number default session
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": "Request EDA0 - Complete ECU part/serial number to get MF reply",
        "timeout": 0.0, # Don't wait - need to send FC frames
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 970,  # Wait max 1000 ms before sending FC frame back
        "frame_control_flag": 49,    # Wait
        "frame_control_auto": False,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_mf)

    SC.change_mf_fc(can_p["send"], can_mf)

    return SUTE.teststep(can_p, cpay, etp)


def step_3(can_p):
    """
    Step 3: Loop: Wait maxtime to send reply for first frame, send reply
    """
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "Verify FC with max number of WAIT frames",
        "timeout": 0.0,  # Don't wait - need to send FC frames
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 970,  # Requirement: Wait max 1000 ms before sending FC frame back
        "frame_control_flag": 0x31,  # Wait
        "frame_control_auto": False,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_mf)

    SUTE.print_test_purpose(etp['step_no'], etp['purpose'])

    max_delay = 254

    SC.change_mf_fc(can_p["send"], can_mf)

    sig = can_p["send"]

    for _ in range(max_delay):
        time.sleep(SC.can_subscribes[sig][3]/1000)  # frame_control_delay / 1000
        SC.send_fc_frame(can_p, frame_control_flag=SC.can_subscribes[sig][4],
                         block_size=SC.can_subscribes[sig][1],
                         separation_time=SC.can_subscribes[sig][2])
        logging.info("DelayNo.: %s, Number of can_frames received: %s",
                     SC.can_subscribes[sig][5], len(SC.can_frames[sig]))
        SC.can_subscribes[sig][5] += 1  # frame_control_responses


def step_4(can_p):
    """
    Step 4: Send flow control with continue flag (0x30), block_size=0, separation_time=0
    """
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Change FC to continue (0x30)",
        "timeout": 0.0,  # Don't wait - need to send FC frames
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0,
        "frame_control_flag": 0x30,
        "frame_control_auto": True,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_mf)

    SUTE.print_test_purpose(etp['step_no'], etp['purpose'])
    sig = can_p["send"]
    time.sleep(SC.can_subscribes[sig][3]/1000)
    SC.change_mf_fc(can_p["send"], can_mf)
    SC.send_fc_frame(can_p, SC.can_subscribes[sig][4],
                     SC.can_subscribes[sig][1], SC.can_subscribes[sig][2])


def step_5(can_p):
    """
    Step 5: Verify received message
    """
    SUTE.print_test_purpose(stepno=5, purpose="Verify received message")

    sig = can_p["receive"]

    SC.clear_all_can_messages()
    SC.update_can_messages(sig)

    logging.info("Step5: messages received %s", len(SC.can_messages))
    logging.info("Step5: messages:")
    for message, data in SC.can_messages.items():
        logging.info("%s: %s", message, data)
    logging.info("Step5: frames received %s", len(SC.can_frames))
    logging.info("Step5: frames:")
    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            logging.info("%s", frame)
    logging.info("Test if string contains all IDs expected:")

    result = True
    result = result and SUTE.test_message(SC.can_messages[sig], teststring='62EDA0')
    result = result and SUTE.test_message(SC.can_messages[sig], teststring='F120')
    result = result and SUTE.test_message(SC.can_messages[sig], teststring='F12A')
    result = result and SUTE.test_message(SC.can_messages[sig], teststring='F12B')
    result = result and SUTE.test_message(SC.can_messages[sig], teststring='F12E')
    result = result and SUTE.test_message(SC.can_messages[sig], teststring='F18C')

    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

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
    result = PREC.precondition(can_p, timeout=300)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: verify default session
        # result:
        result = result and step_1(can_p)

        # step 2:
        # action: request EDA0 - complete ECU part/serial number default session
        # result:
        result = result and step_2(can_p)

        # step 3:
        # action: loop: wait maxtime to send reply for first frame
        # result:
        step_3(can_p)

        # step 4:
        # action: send flow control with continue flag
        # result:
        step_4(can_p)

        # step 5:
        # action: verify received message
        # result: verify whole message received
        result = result and step_5(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
