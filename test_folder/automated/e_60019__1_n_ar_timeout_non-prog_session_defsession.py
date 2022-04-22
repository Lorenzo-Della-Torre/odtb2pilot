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
# date:     2019-05-17
# version:  1.0
# reqprod:  60019

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-03
# version:  1.1
# changes:

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-07-30
# version:  1.2
# changes:  update to use YML parameter
#           step2: compare if whole MF message received (frames differ between projects)

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

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanMFParam, CanPayload, CanTestExtra
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

def step_1(can_p):
    """
    Teststep 1: request EDA0 - with FC delay < timeout 1000 ms
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",\
                                        b'\xED\xA0',\
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no" : 2,
        "purpose" : "request EDA0 - with FC delay < timeout 1000 ms",
        "timeout" : 2,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    #change Control Frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 950,
        "frame_control_flag": 48,
        "frame_control_auto": True
        }
    SC.change_mf_fc(can_p["receive"], can_mf)
    result = SUTE.teststep(can_p, cpay, etp)

    logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
    result = (len(SC.can_messages[can_p["receive"]]) == 1)
    if result:
        logging.info("FC delay < Timeout: ")
        logging.info("Whole message received as expected: %s",
                     len(SC.can_messages[can_p["receive"]]))
    else:
        logging.info("FAIL: No request reply received. Received frames: %s",
                     len(SC.can_frames[can_p["receive"]]))
    logging.info("Step %s: Result teststep: %s \n", etp["step_no"], result)
    return result

def step_2(can_p):
    """
    Teststep 2: request EDA0 - with FC delay > timeout 1000 ms
    """
    n_frame = 1
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",\
                                        b'\xED\xA0',\
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 3,
        "purpose" : "request EDA0 - with FC delay > timeout 1000 ms",
        "timeout" : 5,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    #change Control Frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 1100,
        "frame_control_flag": 48,
        "frame_control_auto": True
        }
    SC.change_mf_fc(can_p["receive"], can_mf)
    result = SUTE.teststep(can_p, cpay, etp)

    result = (len(SC.can_frames[can_p["receive"]]) == n_frame)
    if len(SC.can_frames[can_p["receive"]]) == n_frame:
        logging.info("Timeout due to FC delay: ")
        logging.info("number of frames received as expected: %s",\
                     len(SC.can_frames[can_p["receive"]]))
    else:
        logging.info("FAIL: Wrong number of frames received. Expeced %s Received: %s",\
                     n_frame, len(SC.can_frames[can_p["receive"]]))
    return result

def step_3(can_p):
    """
    Teststep 3: set back frame_control_delay to default
    """
    step_no = 3

    purpose = "set back frame_control_delay to default"








    #change Control Frame parameters to default again
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0,
        "frame_control_flag": 48,
        "frame_control_auto": True
        }
    SC.change_mf_fc(can_p["receive"], can_mf)
    SUTE.print_test_purpose(step_no, purpose)

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "Vcu1ToBecmFront1DiagReqFrame",
        'receive': "BecmToVcu1Front1DiagResFrame",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    #Read YML parameter for current function (get it from stack)
    logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
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
    # action: send request with FC_delay < timeout
    # result: whole message received
        result = result and step_1(can_p)

    # step2:
    # action: send request with FC_delay > timeout
    # result: only first frame received
        result = result and step_2(can_p)

    # step3:
    # action: restore FC_delay again
    # result:
        step_3(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
