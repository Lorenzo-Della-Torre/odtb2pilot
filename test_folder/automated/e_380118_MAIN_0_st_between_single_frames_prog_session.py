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
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-26
# version:  1.0
# reqprod:  380118

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE10 = SupportService10()
SE22 = SupportService22()
PREC = SupportPrecondition()
POST = SupportPostcondition()

def step_2(can_p):
    """
    Teststep 2: verify that two single frame can be sent with ST = 0
    """
    result = True

    cpay_1: CanPayload = {
        "payload_1": b'\x03\x22\xF1\x8C\x00\x00\x00\x00',
        "extra": ''
        }
    SIO.parameter_adopt_teststep(cpay_1)

    cpay_2: CanPayload = {
        "payload_2": b'\x03\x22\xF1\x2B\x00\x00\x00\x00',
        "extra": ''
        }
    SIO.parameter_adopt_teststep(cpay_2)

    etp: CanTestExtra = {"step_no": 2,
                         "purpose" : "verify that two single frame can be sent with ST = 0",
                        }

    SIO.parameter_adopt_teststep(etp)

    SC.clear_all_can_messages()
    SC.clear_all_can_frames()

    #send two SF request consecutively
    SC.t_send_signal_hex(can_p["netstub"], can_p["send"], can_p["namespace"],
                         cpay_1["payload_1"])
    SC.t_send_signal_hex(can_p["netstub"], can_p["send"], can_p["namespace"],
                         cpay_2["payload_2"])

    time.sleep(1)
    SC.update_can_messages(can_p)
    logging.info("Time first request sent: %s \n", SC.can_frames[can_p["send"]][0][0])
    logging.info("Time second request sent: %s \n", SC.can_frames[can_p["send"]][1][0])
    logging.info("Time difference between two frame sent: %s \n",
                 SC.can_frames[can_p["send"]][1][0] - SC.can_frames[can_p["send"]][0][0])
    logging.info("frames received: %s \n", SC.can_frames[can_p["receive"]])
    #expected content reply and frame number to compare with from a default requests
    first_reply_cont = 'F18C'
    frame_to_comp_first_rep = SC.can_frames[can_p["receive"]][0][2]
    second_reply_cont = 'F12B'
    frame_to_comp_second_rep = SC.can_frames[can_p["receive"]][1][2]
    logging.info("Step%s: first_reply_cont before YML: %s", etp["step_no"], first_reply_cont)
    logging.info("Step%s: frame_to_comp_first_rep before YML: %s", etp["step_no"],
                 frame_to_comp_first_rep)
    logging.info("Step%s: second_reply_cont before YML: %s", etp["step_no"], second_reply_cont)
    logging.info("Step%s: frame_to_comp_second_rep before YML: %s", etp["step_no"],
                 frame_to_comp_second_rep)

    # use YML to specifying the expected reply if a different request is sended
    first_reply_cont_new = SIO.parameter_adopt_teststep('first_reply_cont')
    frame_to_comp_first_rep_new = SIO.parameter_adopt_teststep('frame_to_comp_first_rep')
    second_reply_cont_new = SIO.parameter_adopt_teststep('second_reply_cont')
    frame_to_comp_second_rep_new = SIO.parameter_adopt_teststep('frame_to_comp_second_rep')

    # don't set empty value if no replacement was found for first reply:
    if first_reply_cont_new:
        first_reply_cont = first_reply_cont_new
        frame_to_comp_first_rep = frame_to_comp_first_rep_new
    else:
        logging.info("Step%s first_reply_cont_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: first_reply_cont after YML: %s", etp["step_no"], first_reply_cont)
    logging.info("Step%s: frame_to_comp_first_rep after YML: %s", etp["step_no"],
                 frame_to_comp_first_rep)

    # don't set empty value if no replacement was found for second reply:
    if second_reply_cont_new:
        second_reply_cont = second_reply_cont_new
        frame_to_comp_second_rep = frame_to_comp_second_rep_new
    else:
        logging.info("Step%s second_reply_cont_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: second_reply_cont after YML: %s", etp["step_no"], second_reply_cont)
    logging.info("Step%s: frame_to_comp_second_rep after YML: %s", etp["step_no"],
                 frame_to_comp_second_rep)

    result = result and first_reply_cont in frame_to_comp_first_rep
    result = result and second_reply_cont in frame_to_comp_second_rep
    logging.info("Step %s teststatus:%s \n", etp['step_no'], result)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

    # step1:
    # action: # Change to programming session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 1)

    # step2:
    # action: send two single frames requests consecutively
    # result: BECM sends positive reply for both reqests
        result = result and step_2(can_p)

    # step3:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02', stepno=3)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
