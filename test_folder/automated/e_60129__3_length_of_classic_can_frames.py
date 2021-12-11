"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-25
# version:  1.1
# reqprod:  60129

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
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()

def step_1(can_p):
    """
    Teststep 1: verify that a single frame reply is filled up to 8 bytes with x00
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x86', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "verify that a single frame reply is filled up to 8 bytes with x00",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #verify received message from default request is filled with 0 up to 8 bytes
    res_padded_frame = '62F18601000000'
    logging.info("Step%s: reply padded frame before YML: %s", etp["step_no"], res_padded_frame)
    #use YML to specify the expected frame if different request is sended
    res_padded_frame_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'res_padded_frame')
    # don't set empty value if no replacement was found:
    if res_padded_frame_new:
        res_padded_frame = res_padded_frame_new
    else:
        logging.info("Step%s padded_frame_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: padded_frame after YML: %s", etp["step_no"], res_padded_frame)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],
                                          teststring=res_padded_frame)

    return result

def step_2(can_p):
    """
    Teststep 2: verify that the last frame of a MF reply to FD00 is filled up to 8 bytes with x00
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xFD\x00', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": """verify that the last frame of a MF reply to FD00
                      is filled up to 8 bytes with x00""",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #the reply to default FD00 request is 12 bytes so the last frame should be filled
    #with 5 bytes of 0
    last_frame_padding = '0000000000'
    logging.info("Step%s: last_frame_padding before YML: %s", etp["step_no"], last_frame_padding)
    # use YML to specifying the expected padding if a different request is sended
    last_frame_padding_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]),
                                                       'last_frame_padding')
    # don't set empty value if no replacement was found:
    if last_frame_padding_new:
        last_frame_padding = last_frame_padding_new
    else:
        logging.info("Step%s last_frame_padding_new is empty. Discard.", etp["step_no"])
    logging.info("Step%s: last_frame_padding after YML: %s", etp["step_no"], last_frame_padding)
    result = result and SUTE.test_message([SC.can_frames[can_p["receive"]]
                                           [len(SC.can_frames[can_p["receive"]])-1]],
                                          teststring=last_frame_padding)

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
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

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
    # action: Send request requiring SF to reply.
    # result: BECM replies with Single Frame.
        result = result and step_1(can_p)

    # step2:
    # action: Send request requiring MF to reply.
    # result: BECM replies with Multi Frame.
        result = result and step_2(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
