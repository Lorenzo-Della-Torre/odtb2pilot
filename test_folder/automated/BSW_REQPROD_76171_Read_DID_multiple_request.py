# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-09
# version:  1.0
# reqprod:  76171

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-13
# version:  1.1
# changes:  update for YML support

# inspired by https://grpc.io/docs/tutorials/basic/python.html

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

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
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
    Teststep 1: send several requests at one time - requires SF to send, MF for reply
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x20\xF1\x2A',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "send several requests at one time - requires SF to send",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    return result

def step_2(can_p):
    """
    Teststep 2: test if DIDs are included in reply
    """
    step_no = 2
    purpose = "test if all requested DIDs are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")
    SC.update_can_messages(can_p["receive"])
    logging.debug("All can messages updated")

    logging.debug("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.debug("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.debug("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.debug("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F120')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F12A')
    return result


# teststep 4: request 10 DID in one request - those with shortest reply
def step_3(can_p):
    """
    Teststep 3: request 10 DID in one request - those with shortest reply
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47\x49\x50'\
                                        b'\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 3,
        "purpose": "request 10 DID in one request - those with shortest reply (MF send, MF reply)",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    return result


def step_4(can_p):
    """
    Teststep 4: test if DIDs are included in reply
    """
    step_no = 4
    purpose = "test if requested DID are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")
    SC.update_can_messages(can_p["receive"])
    logging.debug("All can messages updated")
    logging.debug("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.debug("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.debug("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.debug("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD02')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0A')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0C')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4947')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4950')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DAD0')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DAD1')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4802')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4803')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4945')
    return result


def step_5(can_p):
    """
    Teststep 5: request 11 DID at once
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\x49\x1A\xDD\x02\xDD\x0A\xDD\x0C\x49\x47'\
                                        b'\x49\x50\xDA\xD0\xDA\xD1\x48\x02\x48\x03\x49\x45',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 5,
        "purpose": "send 11 requests at one time - fails in current version (max10)",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    return result


def step_6(can_p):
    """
    Teststep 6: test if error received
    """
    step_no = 6
    purpose = "verify that error message received"

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

    result = SUTE.test_message(SC.can_messages[can_p["receive"]],
                               teststring='037F223100000000')
    logging.info("Step%s: %s", step_no,
                 SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    logging.info("Step%s: teststatus:%s\n", step_no, result)
    return result


def step_7(can_p):
    """
    Teststep 7: send 10 requests at one time - those with most bytes in return
    """

    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xED\xA0\xF1\x26\xF1\x2E\xDA\x80\xF1\x8C'\
                                        b'\xDD\x00\xDD\x0B\xDD\x01\x49\x45\xDB\x72',
                                        b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 7,
        "purpose": "send 10 requests at one time - those with most bytes in return",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    return result


def step_8(can_p):
    """
    Teststep 8: test if DIDs are included in reply including those from combined DID
    """
    step_no = 8
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

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='EDA0')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F120')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F12A')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F12B')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F12E')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F18C')

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F126')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F12E')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DA80')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F18C')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD00')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0B')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD01')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4945')
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DB72')
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
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports programmin session
        result = result and step_1(can_p)

    # step 2: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_2(can_p)

    # step3:
    # action: check current session
    # result: BECM reports default session
        result = result and step_3(can_p)

    # step 4: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_4(can_p)

    # step5:
    # action: send 11 requests at one time
    # result:
        result = result and step_5(can_p)

    # step 6: check if error message received
    # action: check if error message received
    # result: true if error message contained, false if not
        result = result and step_6(can_p)

    # step7:
    # action: send 10 requests at one time, containing combined DID
    # result:
        result = result and step_7(can_p)

    # step 8: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_8(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()