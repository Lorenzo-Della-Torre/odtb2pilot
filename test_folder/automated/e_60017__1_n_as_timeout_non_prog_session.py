"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-24
# version:  1.0
# reqprod:  60017

# author:   HWEILER (Hans-Klaus Weile4r)
# date:     2020-07-29
# version:  1.1
# changes:  YML parameters corrected, error setting FC-delay corrected, step order changed.

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

"""The Python implementation of the gRPC route guide client."""

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
from supportfunctions.support_sec_acc import SupportSecurityAccess

SSA = SupportSecurityAccess()
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
    Change delay to reply to FF: delay < 1000 ms
    """
    step_no = 1
    purpose = "set Frame Control delay < 1000 ms"
    result = True
    SUTE.print_test_purpose(step_no, purpose)

    #change Control Frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 950,
        "frame_control_flag": 48,
        "frame_control_auto": True
        }
    #SC.change_mf_fc(can_p["send"], can_mf)
    SC.change_mf_fc(can_p["receive"], can_mf)
    return result

def step_2(can_p):
    """
    Teststep 2: Send multi frame request DIDs with FC delay < 1000ms
    """
    result = True
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xDD\x02\xDD\x0A\xDD\x0C\xF1\x86', b''),
                        "extra" : ''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 2,
                         "purpose": "Send multi frame request DIDs with FC delay < 1000ms",
                         "timeout": 1,
                         "min_no_messages": -1,
                         "max_no_messages": -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    #test if frames contain all the IDs expected
    logging.info("Test if string contains all IDs expected:")
    logging.debug("Frames received: %s", SC.can_frames[can_p["receive"]])
    logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])

    result = result and 'DD02' in SC.can_messages[can_p["receive"]][0][2]
    if not result:
        logging.info("Result after test DD02: %s", result)
    result = result and 'DD0A' in SC.can_messages[can_p["receive"]][0][2]
    if not result:
        logging.info("Result after test DD0A: %s", result)
    result = result and 'DD0C' in SC.can_messages[can_p["receive"]][0][2]
    if not result:
        logging.info("Result after test DD0C: %s", result)
    result = result and 'F186' in SC.can_messages[can_p["receive"]][0][2]
    if not result:
        logging.info("Result after test F186: %s", result)

    logging.info("Step%s teststatus: %s \n", etp["step_no"], result)
    logging.info("Step %s: Result teststep: %s \n", etp["step_no"], result)
    return result

def step_3(can_p):
    """
    Teststep 3: set FC delay > 1000 ms
    """
    stepno = 3
    purpose = "set FC delay > 1000 ms"
    result = True
    SUTE.print_test_purpose(stepno, purpose)
    #change multi frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 1050,
        "frame_control_flag": 48,
        "frame_control_auto": True
        }
    #SC.change_mf_fc(can_p["send"], can_mf)
    SC.change_mf_fc(can_p["receive"], can_mf)
    return result

def step_4(can_p):
    """
    Teststep 4: Send multi frame request DIDs with FC delay > 1000ms
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', b''),
        "extra" : ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": 4,
                         "purpose": "Send multi frame request DIDs with FC delay > 1000ms",
                         "timeout": 1,
                         "min_no_messages": -1,
                         "max_no_messages": -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("Result after teststep: %s", result)
    #test if frames contain all the IDs expected
    logging.info("Test if request timed out:")
    logging.debug("Frames received: %s", SC.can_frames[can_p["receive"]])
    logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])

    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info("Len Mess received: %s", len(SC.can_messages[can_p["receive"]]))

    logging.info("Step %s: Result teststep: %s \n", etp["step_no"], result)

    return result

def step_5(can_p):
    """
    Teststep 5: set back frame_control_delay to default
    """

    stepno = 5
    purpose = "set back frame_control_delay to default"

    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0,
        "frame_control_flag": 48,
        "frame_control_auto": True
        }

    SUTE.print_test_purpose(stepno, purpose)
    SC.change_mf_fc(can_p["receive"], can_mf)

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
    # action: change delay for reply to FC frame
    # result:
        result = result and step_1(can_p)

    # step2:
    # action: send request with FC_delay < timeout
    # result: whole message received
        result = result and step_2(can_p)

    # step3:
    # action: set FC_delay > timeout
    # result:
        result = result and step_3(can_p)

    # step4:
    # action: send request with FC_delay > timeout
    # result: no reply received
        result = result and step_4(can_p)

    # step5:
    # action:
    # result: set back frame_control_delay to default
        step_5(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
