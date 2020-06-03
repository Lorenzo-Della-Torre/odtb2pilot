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

import logging
from datetime import datetime
import time
import sys
from support_test_odtb2 import SupportTestODTB2
from support_can import SupportCAN, CanMFParam, CanParam, CanTestExtra, CanPayload, PerParam
from support_carcom import SupportCARCOM
#from support_precondition import SupportPrecondition
import odtb_conf as ODTB_config

SC = SupportCAN()
SUPPORT_TEST = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()


# precondition for test running:
# BECM has to be kept alive: start heartbeat
def precondition(can_p):
    ''' Precondition '''

    # start heartbeat, repeat every 0.8 second
    hb_param: PerParam = {
        "id" : "EcmFront1NMFr",
        "nspace" : "Front1CANCfg0",
        "frame" : b'\x20\x40\x00\xFF\x00\x00\x00\x00',
        "intervall" : 0.8
    }
    SC.start_heartbeat(can_p["netstub"], hb_param)

    time.sleep(4) #wait for ECU startup
    timeout = 40  #seconds
    SC.subscribe_signal(can_p, timeout)

    # Record signal we send as well (switch send and rec)
    can_p2: CanParam = {
        "netstub": can_p["netstub"],
        "send": can_p["receive"],
        "receive": can_p["send"],
        "namespace": can_p["namespace"],
    }
    SC.subscribe_signal(can_p2, timeout)

    test_result = step_0(can_p)
    logging.info("Precondition test ok: %s\n", test_result)
    return test_result


# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(can_p: CanParam):
    ''' Step 0 '''
    etp: CanTestExtra = {
        "step_no" : 0,
        "purpose" : "Complete ECU Part/Serial Number(s)",
        "timeout" : 5,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }

    cpay: CanPayload = {
        "payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xED\xA0', b''),
        "extra" : ''
        }

    test_result = SUPPORT_TEST.teststep(can_p, cpay, etp)

    logging.debug("can_p['receive']: %s", can_p["receive"])
    logging.debug("SC.can_messages: %s", SC.can_messages)
    logging.debug("SC.can_messages[can_p['receive']]: %s",
                  SC.can_messages[can_p["receive"]])
    logging.info(SUPPORT_TEST.pp_combined_did_eda0(SC.can_messages[can_p["receive"]][0][2],
                                                   title=''))
    return test_result


# teststep 1: send 1 requests - requires SF to send, MF for reply
def step_1(can_p: CanParam): # pylint: disable=too-many-locals
    ''' Step 1 '''

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
        "payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x20', b''),
        "extra" : ''
        }

    test_result = SUPPORT_TEST.teststep(can_p, cpay, etp)
    return test_result


# teststep 2: test if DIDs are included in reply
def step_2(can_receive):
    ''' Step 2 '''
    stepno = 2
    purpose = "test if requested DID are included in reply"

    SUPPORT_TEST.print_test_purpose(stepno, purpose)

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
    test_result = SUPPORT_TEST.test_message(SC.can_messages[can_receive], teststring='F120')
    return test_result


# teststep 3: send several requests at one time - requires SF to send, MF for reply
def step_3(can_p: CanParam): # pylint: disable=too-many-locals
    '''' Step 3 '''
    # Parameters for the teststep
    etp: CanTestExtra = {
        'step_no' : 3,
        'purpose' : "Send several requests at one time - requires SF to send",
        'timeout' : 5,
        'min_no_messages' : -1,
        'max_no_messages' : -1
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
        "payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x20\xF1\x2A', b''),
        "extra" : ''
        }

    test_result = SUPPORT_TEST.teststep(can_p, cpay, etp)
    return test_result

# teststep 4: test if DIDs are included in reply
def step_4(can_receive):
    ''' Step 4 '''
    stepno = 4
    purpose = "test if all requested DIDs are included in reply"

    SUPPORT_TEST.print_test_purpose(stepno, purpose)

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

    test_result = SUPPORT_TEST.test_message(SC.can_messages[can_receive], teststring='F120')
    test_result = test_result and SUPPORT_TEST.test_message(SC.can_messages[can_receive],
                                                            teststring='F12A')
    return test_result


def main():
    ''' Main '''
    # Setting up logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # can_p = dict()
    # # where to connect to signal_broker
    # can_p["netstub"] = SC.connect_to_signalbroker(ODTB_config.ODTB2_DUT, ODTB_config.ODTB2_PORT)
    # can_p["send"] = "Vcu1ToBecmFront1DiagReqFrame"
    # can_p["receive"] = "BecmToVcu1Front1DiagResFrame"
    # can_p["namespace"] = SC.nspace_lookup("Front1CANCfg0")

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(ODTB_config.ODTB2_DUT, ODTB_config.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time %s\n", time.time())

    ############################################
    # precondition
    ############################################
    logging.debug("precondition start: %s", datetime.now())

    test_result = precondition(can_p)
    #test_result = SupportPrecondition.precondition(can_p, 40)

    logging.debug("Precondition end: %s", datetime.now())

    ############################################
    # teststeps
    ############################################

    # step1:
    # action: send 1 request - requires SF to send, MF for reply
    # result: BECM reports default session
    logging.debug("step_1 start: %s", datetime.now())
    test_result = test_result and step_1(can_p)
    logging.debug("step_1 end: %s", datetime.now())

    # step 2: check if DID is included in reply
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    test_result = test_result and step_2(can_p["receive"])

    # step3:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports default session
    test_result = test_result and step_3(can_p)

    # step 4: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
    test_result = test_result and step_4(can_p["receive"])


    ############################################
    # postCondition
    ############################################

    logging.info("\ntime %s", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %d", int(time.time() - starttime))
    logging.info("Do cleanup now...")
    logging.info("Stop heartbeat sent")
    SC.stop_heartbeat()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if test_result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    main()
