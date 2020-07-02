# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-24
# version:  1.0
# reqprod:  60017

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

import ODTB_conf

from support_can import SupportCAN, CanParam, CanMFParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service22 import SupportService22
from support_service10 import SupportService10
from support_sec_acc import SupportSecurityAccess

SSA = SupportSecurityAccess()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_2(can_par):
    """
    Teststep 2: Send first frame of a multi frame request DIDs
    """
    stepno = 2
    purpose = "Send first frame of a multi frame request DIDs"
    result = True
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                     b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', b''),
        extra=''
        )

    SC.clear_old_cf_frames()
    logging.debug("Clear old messages")
    SC.clear_all_can_frames()
    SC.clear_all_can_messages()

    SUTE.print_test_purpose(stepno, purpose)
    # wait for messages
    # define answer to expect
    logging.debug("Build answer can_frames to receive")
    can_answer = SC.can_receive(cpay['payload'], cpay['extra'])
    logging.debug("CAN frames to receive: %s", can_answer)

    wait_start = time.time()
    logging.debug("To send:   [%s, %s, %s]", time.time(), can_par["send"],
                  (cpay["payload"]).hex().upper())
    SC.clear_all_can_messages()

    #number of frames to send, array of frames to send
    SC.can_mf_send[can_par["send"]] = [0, []]

    # build array of frames to send:
    mess_length = len(cpay["payload"])

    # verify multi_frame:
    result = (8 < mess_length < 4096)

    #send_mf
    SC.send_mf(can_par, cpay, True, 0x00)
    result = result and (len(SC.can_mf_send[can_par["send"]][1]) < 0x7ff)
    print("send payload as MF")
    # send payload as MF

    #send FirstFrame:
    SC.send_ff_can(can_par, freq=0)

    logging.info("Step %s: Result teststep: %s \n", stepno, result)
    return wait_start, can_answer, result

def step_3(can_par):
    """
    Teststep 3: send CF with with CF delay < 1000 ms
    """
    stepno = 3
    purpose = "send CF with with CF delay < 1000 ms"
    result = True
    SUTE.print_test_purpose(stepno, purpose)

    #change Control Frame parameters
    can_mf: CanMFParam = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        block_size=0,
        separation_time=0,
        frame_control_delay=950,
        frame_control_flag=48,
        frame_control_auto=True
        )
    SC.change_mf_fc(can_par["send"], can_mf)
    #send consecutive frame
    #verify 1st consecutive frame is sent
    if SC.send_cf_can(can_par) != "OK: MF message sent":
        result = False
    logging.info("Step %s: Result teststep: %s \n", stepno, result)
    return result

def step_4(can_par, wait_start, can_answer):
    """
    Teststep 4: test if all requested DIDs are included in reply
    """
    stepno = 4
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=4,
        purpose="test if all requested DIDs are included in reply",
        timeout=2,
        min_no_messages=-1,
        max_no_messages=-1
        )
    SUTE.print_test_purpose(stepno, etp["purpose"])

    #wait timeout for getting subscribed data
    if etp["max_no_messages"] == -1:
        time.sleep(etp["timeout"])
        SC.update_can_messages(can_par["receive"])
    else:
        SC.update_can_messages(can_par["receive"])
        while((time.time()-wait_start <= etp["timeout"])\
            and (len(SC.can_messages[can_par["receive"]]) < etp["max_no_messages"])):
            SC.clear_all_can_messages()
            SC.update_can_messages(can_par["receive"])

    logging.debug("Rec can frames: %s", SC.can_frames[can_par["receive"]])
    if SC.can_frames[can_par["receive"]]:
        if etp["min_no_messages"] >= 0:
            result = result and\
                SUTE.test_message(SC.can_frames[can_par["receive"]],\
                    can_answer.hex().upper())

    #test if frames contain all the IDs expected
    logging.info("Test if string contains all IDs expected:")
    result = 'DD02' in SC.can_frames[can_par["receive"]][1][2]
    result = result and 'DD0A' in SC.can_frames[can_par["receive"]][1][2]
    result = result and 'DD0C' in SC.can_frames[can_par["receive"]][2][2]
    result = result and '4947' in SC.can_frames[can_par["receive"]][2][2]
    logging.info("Step%s teststatus: %s \n", stepno, result)
    logging.info("Step %s: Result teststep: %s \n", etp["step_no"], result)
    return result

def step_5(can_par):
    """
    Teststep 5: Send first frame of a multi frame request DIDs
    """
    stepno = 5
    purpose = "Send first frame of a multi frame request DIDs"
    result = True
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                     b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', b''),
        extra=''
        )

    SC.clear_old_cf_frames()
    logging.debug("Clear old messages")
    SC.clear_all_can_frames()
    SC.clear_all_can_messages()

    SUTE.print_test_purpose(stepno, purpose)

    # wait for messages
    # define answer to expect
    logging.debug("Build answer can_frames to receive")
    can_answer = SC.can_receive(cpay['payload'], cpay['extra'])
    logging.debug("CAN frames to receive: %s", can_answer)

    wait_start = time.time()
    logging.debug("To send:   [%s, %s, %s]", time.time(), can_par["send"],
                  (cpay["payload"]).hex().upper())
    SC.clear_all_can_messages()

    #number of frames to send, array of frames to send
    SC.can_mf_send[can_par["send"]] = [0, []]

    # build array of frames to send:
    mess_length = len(cpay["payload"])
    # verify multi_frame:
    result = (8 < mess_length < 4096)
    #send_mf
    SC.send_mf(can_par, cpay, True, 0x00)
    result = result and (len(SC.can_mf_send[can_par["send"]][1]) < 0x7ff)
    logging.info("send payload as MF")
    # send payload as MF

    #send FirstFrame:
    SC.send_ff_can(can_par, freq=0)
    logging.info("Step %s: Result teststep: %s \n", stepno, result)
    return wait_start, can_answer, result

def step_6(can_par):
    """
    Teststep 6: send CF with with CF delay > 1000 ms
    """
    stepno = 6
    purpose = "send CF with with CF delay > 1000 ms"
    result = True
    SUTE.print_test_purpose(stepno, purpose)
    #change multi frame parameters
    can_mf: CanMFParam = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        block_size=0,
        separation_time=0,
        frame_control_delay=1050,
        frame_control_flag=48,
        frame_control_auto=True
        )
    SC.change_mf_fc(can_par["send"], can_mf)
    #send consecutive frame
    #verify 1st consecutive frame is sent
    if SC.send_cf_can(can_par) != "OK: MF message sent":
        result = False
    logging.info("Step %s: Result teststep: %s \n", stepno, result)
    return result

def step_7(can_par, wait_start, can_answer):
    """
    Teststep 7: test if none of the requested DIDs are included in reply
    """
    stepno = 7
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=7,
        purpose="test if none of the requested DIDs are included in reply",
        timeout=2,
        min_no_messages=-1,
        max_no_messages=-1
        )
    SUTE.print_test_purpose(stepno, etp["purpose"])

    #wait timeout for getting subscribed data
    if etp["max_no_messages"] == -1:
        time.sleep(etp["timeout"])
        SC.update_can_messages(can_par["receive"])
    else:
        SC.update_can_messages(can_par["receive"])
        while((time.time()-wait_start <= etp["timeout"])\
            and (len(SC.can_messages[can_par["receive"]]) < etp["max_no_messages"])):
            SC.clear_all_can_messages()
            SC.update_can_messages(can_par["receive"])

    logging.debug("Rec can frames: %s", SC.can_frames[can_par["receive"]])
    if SC.can_frames[can_par["receive"]]:
        if etp["min_no_messages"] >= 0:
            result = result and\
                SUTE.test_message(SC.can_frames[can_par["receive"]],\
                                      can_answer.hex().upper())

    logging.info("verify only Flow Control frame are included in reply:")

    logging.info("verify that 1 reply received: len(frames_received) == 1 : %r",\
         len(SC.can_frames[can_par["receive"]]) == 1)
    result = len(SC.can_frames[can_par["receive"]]) == 1

    return result

def step_8(can_par):
    """
    Teststep 8: set back frame_control_delay to default
    """

    stepno = 8
    purpose = "set back frame_control_delay to default"

    can_mf: CanMFParam = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        block_size=0,
        separation_time=0,
        frame_control_delay=0,
        frame_control_flag=48,
        frame_control_auto=True
        )

    SUTE.print_test_purpose(stepno, purpose)
    SC.change_mf_fc(can_par["receive"], can_mf)

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_par: CanParam = SIO.extract_parameter_yml(
        "main",
        netstub=SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        send="Vcu1ToBecmFront1DiagReqFrame",
        receive="BecmToVcu1Front1DiagResFrame",
        namespace=SC.nspace_lookup("Front1CANCfg0")
        )

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_par, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step1:
    # action: # Change to extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_par, 1)

    # step2:
    # action:
    # result: whole message received
        wait_start, can_answer, result_step_2 = step_2(can_par)
        result = result and result_step_2

    # step3:
    # action: send request with FC_delay > timeout
    # result: whole message received
        result = result and step_3(can_par)

    # step4:
    # action: send request with FC_delay > timeout
    # result: whole message received
        result = result and step_4(can_par, wait_start, can_answer)

    # step5:
    # action:
    # result: whole message received
        wait_start, can_answer, result_step_5 = step_5(can_par)
        result = result and result_step_5

    # step6:
    # action: send request with FC_delay > timeout
    # result: whole message received
        result = result and step_6(can_par)

    # step7:
    # action:
    # result: whole message received
        result = result and step_7(can_par, wait_start, can_answer)

    # step8:
    # action:
    # result: whole message received
        step_8(can_par)

    # step9:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x03')#, 9)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
