# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-05-17
# version:  1.0
# reqprod:  60006

# author:   hweiler (Hans-Klaus Weiler)
# date:     2020-08-10
# version:  1.1
# changes:  update for YML-parameter, updated support functions

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
import logging
import sys
#import os
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()


def step_2(can_p):
    """
    Teststep 2: send request with MF to send
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",\
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47',\
                                        b''),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 2,
        "purpose" : "send several requests at one time - requires MF to send",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    # verify FC parameters from BECM for block_size
    logging.info("FC parameters used:")
    logging.info("Step%s: frames received %s", etp["step_no"], len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.info("len FC %s", len(SC.can_cf_received[can_p["receive"]]))
    logging.info("FC: %s", SC.can_cf_received[can_p["receive"]])
    #logging.info("FC: %s", Support_CAN.can_cf_received)
    result = result and\
             SUTE.test_message(SC.can_cf_received[can_p["receive"]], teststring='30000A0000000000')

def step_3(can_p):
    """
    Teststep 3: test if DIDs are included in reply
    """
    step_no = 3
    purpose = "test if all requested DIDs are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    logging.info("Step%s: messages received %s", step_no,
                 len(SC.can_messages[can_p["receive"]]))
    logging.info("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.info("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD02')
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0A') and result
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0C') and result
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4947') and result
    #print()
    return result


def step_4(can_p):
    """
    Teststep 4: build longer message to send
    """

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",\
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47',\
                                        b''),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 4,
        "purpose" : "send several requests at one time - requires MF to send",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)


    # build a longer message to be sent:
    # add bytes to payload:

    #pl_max_length = 4090
    pl_max_length = 12
    while len(cpay["payload"]) < pl_max_length:
        cpay["payload"] = cpay["payload"] + b'\x00'

    result = SUTE.teststep(can_p, cpay, etp)

    # verify FC parameters from BECM for block_size
    logging.info("FC parameters used:")
    logging.info("Step%s: frames received %s", etp["step_no"], len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.info("len FC %s", len(SC.can_cf_received[can_p["receive"]]))
    logging.info("FC: %s", SC.can_cf_received[can_p["receive"]])
    #logging.info("FC: ", Support_CAN.can_cf_received)
    return result

def step_5(can_p):
    """
    Teststep 5: test if DIDs are included in reply
    """

    step_no = 5
    purpose = "test if all requested DIDs are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    logging.info("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.info("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.info("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD02')
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0A') and result
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0C') and result
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4947') and result
    return result


def step_6(can_p):
    """
    Teststep 6: build longer message to send
    """

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47',
                                        b''),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 6,
        "purpose" : "send several requests at one time - requires MF to send",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # build a longer message to be sent:
    # add bytes to payload:

    #pl_max_length = 4090
    #pl_max_length = 252
    pl_max_length = 251
    #pl_max_length = 51
    while len(cpay["payload"]) < pl_max_length:
        cpay["payload"] = cpay["payload"] + b'\x00'

    result = SUTE.teststep(can_p, cpay, etp)
    # verify FC parameters from BECM for block_size
    logging.info("FC parameters used:")
    logging.info("Step%s: frames received %s", etp["step_no"], len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.info("len FC %s", len(SC.can_cf_received[can_p["receive"]]))
    logging.info("FC: %s", SC.can_cf_received[can_p["receive"]])
    return result


def step_7(can_p):
    """
    Teststep 7: test if DIDs are included in reply
    """

    step_no = 7
    purpose = "test if all requested DIDs are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    logging.info("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.info("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.info("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])

    #logging.info("Test if string contains all IDs expected:")
    #result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD02') and result
    #result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0A') and result
    #result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0C') and result
    #result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4947') and result

    result = (SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F2231') or
              SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F2213'))
    logging.info("Step%s, Error  message: ", step_no)
    logging.info("Step%s, SC.can_messages[can_p[receive]] %s", step_no,
                 SC.can_messages[can_p["receive"]][0][2])
    logging.info("Step%s, decode response: %s", step_no,\
                 SUTE.pp_decode_7f_response(SC.can_messages[can_p["receive"]][0][2]))
    logging.info("Step%s, teststatus:%s\n", step_no, result)
    return result

# teststep 8: build payload >255 bytes
#def step_8(stub, s, r, ns):
def step_8(can_p):
    """
    Teststep 8: build payload >255 bytes
    """

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47',
                                        b''),
        "extra": ''
        }
    # Parameters for the teststep
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 8,
        "purpose" : "send several requests at one time - requires MF to send",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    #pl_max_length = 1090
    pl_max_length = 256
    #pl_max_length = 400
    while len(cpay["payload"]) < pl_max_length:
        cpay["payload"] = cpay["payload"] + b'\x00'

    logging.info("send  mmessage with 256 bytes")
    logging.info("message: %s", cpay["payload"])

    result = SUTE.teststep(can_p, cpay, etp)

    # verify FC parameters from BECM for block_size
    logging.info("Step%s: frames received %s", etp["step_no"], len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.info("len FC %s", len(SC.can_cf_received[can_p["receive"]]))
    logging.info("FC: %s", SC.can_cf_received[can_p["receive"]])
    #logging.info("FC: %s", SC.can_cf_received)
    return result


def step_9(can_p):
    """
    Teststep 9: test if DIDs are included in reply
    """

    step_no = 9
    purpose = "test if all requested DIDs are included in reply"

    # No normal teststep done,
    # instead: update CAN messages, verify all serial-numbers received
    #          (by checking ID for each serial-number)
    ##teststep(stub, can_m_send, can_mr_extra, s, r, ns,
    #          step_no, purpose, timeout, min_no_messages, max_no_messages)
    #result = SUTE.teststep(can_p, cpay, etp)

    SUTE.print_test_purpose(step_no, purpose)

    logging.info("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.info("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.info("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.info("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])

    #logging.info("Test if string contains all IDs expected:")
    #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD02')
    #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0A')
    #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0C')
    #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='4947')

    result = SUTE.test_message(SC.can_frames[can_p["receive"]], teststring='32000A')

    #logging.info("Error  message: ")
    #logging.info("SC.can_messages[can_p['receive']] %s",SC.can_messages[can_p["receive"]][0][2])
    #logging.info("%s", SUTE.PP_Decode_7F_response(SC.can_messages[can_p["receive"]][0][2]))
    #logging.info("Step%s" teststatus:\n", stepno, result)
    return result



def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    ############################################
    # precondition
    ############################################
    timeout = 60   #seconds
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify default session
    # result: BECM reports mode
        result = SE22.read_did_f186(can_p, dsession=b'\x01', stepno=1)
        #step_1(can_p)

    # step2:
    # action: send request with MF to send
    # result: BECM reports programming session
        result = result and step_2(can_p)

    # step3:
    # action: test if DIDs are included in reply
    # result: all DIDs are included
        result = result and step_3(can_p)

    # step4:
    # action: build longer message (payload 12 bytes) to be sent, send it
    # result: message is received by other side (control framecontrol FC)
        result = result and step_4(can_p)

    # step5:
    # action: test if DIDs are included in reply
    # result: DIDs are included
        result = result and step_5(can_p)

    # step6:
    # action: build longer message (payload 251 bytes) to be sent, send it
    # result: message is received by other side (control framecontrol FC)
        result = result and step_6(can_p)

    # step7:
    # action: test if DIDs are included in reply
    # result: NRC received instead
        result = result and step_7(can_p)


    # step8:
    # action: build longer message (payload 255 bytes) to be sent, send it
    # result: message is received by other side (control framecontrol FC)
        result = result and step_8(can_p)


    # step9:
    # action: test if DIDs are included in reply
    # result: Message not received, but aborted (FC code 32)
        result = result and step_9(can_p)

    # step10:
    # action: verify default session
    # result: default session reported
        result = SE22.read_did_f186(can_p, dsession=b'\x01', stepno=10)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
