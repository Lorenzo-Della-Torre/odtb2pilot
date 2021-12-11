/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO
# date:     2020-12-07
# version:  1.1
# reqprod:  60064

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
import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload, CanMFParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SUTE = SupportTestODTB2()


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
        "frame_control_delay": 0,  # Wait max 1000 ms before sending FC frame back
        "frame_control_flag": 0x30,  # FC.WAIT
        "frame_control_auto": True
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_mf)

    SC.change_mf_fc(can_p["send"], can_mf)

    return SUTE.teststep(can_p, cpay, etp)


def step_3(can_p):
    """
    Step 3: Verify received message
    """
    time.sleep(5)
    time_stamp = [0]
    frame_stamp =["Sent"]

    SUTE.print_test_purpose(stepno=5, purpose="Verify received message")
    logging.info("Sent message: %s", can_p["send"])
    logging.info("Recived message: %s", can_p["receive"])

    logging.info("Step3: frames sent %s", len(SC.can_frames[can_p["send"]]))
    logging.info("Step3: frames received %s", len(SC.can_frames[can_p["receive"]]))

    SC.clear_all_can_messages()
    SC.update_can_messages(can_p)

    time_stamp[0] = SC.can_frames[can_p["send"]][0][0]
    frame_stamp[0] = "Sent: " + SC.can_frames[can_p["send"]][0][2]
    time_stamp.append(SC.can_frames[can_p["receive"]][0][0])
    frame_stamp.append("Received:" + SC.can_frames[can_p["receive"]][0][2])
    time_stamp.append(SC.can_frames[can_p["send"]][1][0])
    frame_stamp.append("Sent: " + SC.can_frames[can_p["send"]][1][2])

    for i in range(1,len(SC.can_frames[can_p["receive"]])):
        time_stamp.append(SC.can_frames[can_p["receive"]][i][0])
        frame_stamp.append("Received:" + SC.can_frames[can_p["receive"]][i][2])

    #First fram the request
    logging.info("timeStamp: %s, timeDiff: %s ms, diffToPrev: %s ms, %s",
                 time_stamp[0],
                 round(1000 * (time_stamp[0] - time_stamp[0]), 3),
                 round(1000 * (time_stamp[0] - time_stamp[0]), 3),
                 frame_stamp[0])

    #Second frame the FC.CTS
    logging.info("timeStamp: %s, timeDiff: %s ms, diffToPrev: %s ms, %s",
                 time_stamp[1],
                 round(1000 * (time_stamp[1] - time_stamp[0]), 3),
                 round(1000 * (time_stamp[1] - time_stamp[0]), 3),
                 frame_stamp[1])
    result = True

    #The rest of frames, the Consecutive Frames
    for i in range(2,len(SC.can_frames[can_p["receive"]])+len(SC.can_frames[can_p["send"]])):
        logging.info("timeStamp: %s, timeDiff: %s ms, diffToPrev: %s ms, %s",
                     time_stamp[i],
                     round(1000 * (time_stamp[i] - time_stamp[0]), 3),
                     round(1000 * (time_stamp[i] - time_stamp[i-1]), 3),
                     frame_stamp[i])
        result = result and (round(1000 * (time_stamp[i] - time_stamp[i-1]), 3) < 20.001)
    logging.info("All diffPrev between FC and CF < 20 ms : %s", result)

    #for frame_type, frames in SC.can_frames.items():
    #    logging.info("%s:", frame_type)
    #    for frame in frames:
    #        ts, ft, fb = frame
    #        logging.info("%s", [round(1000 * (ts - time_stamp[0]), 3), ft, fb])

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
        result = result and SE22.read_did_f186(can_p, b'\x01', 1)

        # step 2:
        # action: request EDA0 - complete ECU part/serial number default session
        # result:
        result = result and step_2(can_p)

        # step 3:
        # action: verify received message
        # result: verify whole message received
        result = result and step_3(can_p)

        # step 4:
        # action: verify default session
        # result:
        result = result and SE22.read_did_f186(can_p, b'\x01', 4)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
