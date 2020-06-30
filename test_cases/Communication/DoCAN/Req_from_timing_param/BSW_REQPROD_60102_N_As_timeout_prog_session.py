# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-25
# version:  1.0
# reqprod:  60102

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
from support_service11 import SupportService11
from support_service10 import SupportService10
from support_sec_acc import SupportSecurityAccess
from support_SBL import SupportSBL


SSA = SupportSecurityAccess()
SSBL = SupportSBL()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE11 = SupportService11()
SE10 = SupportService10()
SE22 = SupportService22()

def step_3():
    """
    Teststep 3: Read VBF files for SBL file (1st Logical Block)
    """
    stepno = 3
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    offset, data, _, data_format, _ = SSBL.read_vbf_file_sbl(SSBL.get_sbl_filename())
    return offset, data, data_format

def step_4(offset, data):
    """
    Teststep 4: Extract data for the 1st block from SBL VBF
    """
    stepno = 4
    purpose = "EXtract data for the 1st block from SBL VBF"

    SUTE.print_test_purpose(stepno, purpose)
    _, _, block_addr, block_len, _ = SSBL.block_data_extract(offset, data)
    block_addr_by = bytes.fromhex("{0:08X}".format(block_addr))
    block_len_by = bytes([block_len])
    logging.info(block_len_by)
    logging.info(block_addr_by)
    return block_addr_by, block_len_by

def step_5(can_par, data_format, block_addr_by, block_len_by):
    """
    Teststep 5: Send first frame of a multi frame request
    """
    stepno = 5
    purpose = "Send first frame of a multi frame request"
    result = True
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("RequestDownload",
                                     data_format + b'\x44'+ block_addr_by + block_len_by, b''),
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

def step_6(can_par):
    """
    Teststep 6: send CF with with CF delay < 1000 ms
    """
    stepno = 6
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
        frame_control_auto=False
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
    Teststep 7: verify ECU reply with NRC 31
    """
    stepno = 7
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=7,
        purpose="verify ECU reply with NRC 31",
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
            result = SUTE.test_message(SC.can_frames[can_par["receive"]],
                                       can_answer.hex().upper())

    logging.info("verify NRC frame are included in reply:")

    result = '7F3431' in SC.can_frames[can_par["receive"]][1][2]
    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_par["receive"]][1][2]))

    return result

def step_8(can_par):
    """
    Teststep 8: verify session PBL
    """
    stepno = 8
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x21', b''),
        extra=''
        )

    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=8,
        timeout=1,
        purpose="Verify Programming session in PBL",
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
                                          teststring='F121')

    return result

def step_9(can_par, data_format, block_addr_by, block_len_by):
    """
    Teststep 9: Send first frame of a multi frame request DIDs
    """
    stepno = 9
    purpose = "Send first frame of a multi frame request DIDs"
    result = True
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("RequestDownload",
                                     data_format + b'\x44'+ block_addr_by + block_len_by, b''),
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

def step_10(can_par):
    """
    Teststep 10: send CF with with CF delay > 1000 ms
    """
    stepno = 10
    purpose = "send CF with with CF delay > 1000 ms"
    result = True
    SUTE.print_test_purpose(stepno, purpose)

    #change Control Frame parameters
    can_mf: CanMFParam = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        block_size=0,
        separation_time=0,
        frame_control_delay=1050,
        frame_control_flag=48,
        frame_control_auto=False
        )
    SC.change_mf_fc(can_par["send"], can_mf)
    #send consecutive frame
    #verify 1st consecutive frame is sent
    if SC.send_cf_can(can_par) != "OK: MF message sent":
        result = False
    logging.info("Step %s: Result teststep: %s \n", stepno, result)
    return result

def step_11(can_par, wait_start, can_answer):
    """
    Teststep 11: verify no frame in reply
    """
    stepno = 11
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=11,
        purpose="verify no frame in reply",
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
            result = SUTE.test_message(SC.can_frames[can_par["receive"]],
                                       can_answer.hex().upper())

    logging.info("verify no frame are included in reply:")

    logging.info("verify that 0 reply received: len(frames_received) == 0 : %r",\
         len(SC.can_frames[can_par["receive"]]) == 0)
    result = (len(SC.can_frames[can_par["receive"]]) == 0)

    return result

def step_12(can_par):
    """
    Teststep 12: set back frame_control_delay to default
    """
    stepno = 12
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
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 20
    #timeout = 600
    result = PREC.precondition(can_par, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action: # Change to programming session
        # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_par, 1)

        # step2:
        # action:
        # result: whole message received
        result = result and SSA.activation_security_access(can_par, 2, "activate security access")

        # step3:
        # action:
        # result:
        offset, data, data_format = step_3()

        # step4:
        # action:
        # result:
        block_addr_by, block_len_by = step_4(offset, data)

        # step5:
        # action:
        # result:
        wait_start, can_answer, result_step_5 = step_5(can_par,\
             data_format, block_addr_by, block_len_by)
        result = result and result_step_5

        # step6:
        # action:
        # result:
        result = result and step_6(can_par)

        # step7:
        # action:
        # result:
        step_7(can_par, wait_start, can_answer)

        # step8:
        # action:
        # result:
        result = result and step_8(can_par)

        # step9:
        # action:
        # result:
        wait_start_1, can_answer_1, result_step_9 = step_9(can_par,\
             data_format, block_addr_by, block_len_by)
        result = result and result_step_9

        # step10:
        # action:
        # result:
        result = result and step_10(can_par)

        # step11:
        # action:
        # result:
        step_11(can_par, wait_start_1, can_answer_1)

        # step12:
        # action:
        # result:
        step_12(can_par)

        # step13:
        # action: verify current session
        # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x02')#, 13)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
