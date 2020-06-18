# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-10
# version:  1.1
# reqprod:  74180

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
from support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service11 import SupportService11

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE11 = SupportService11()

def step_1(can_par):
    """
    Teststep 1: register another signal
    """
    stepno = 1
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=1,
        purpose="register another signal",
        timeout=15,
        min_no_messages=-1,
        max_no_messages=-1
        )
    can_par_ex: CanParam = SIO.extract_parameter_yml(
        "main",
        netstub=SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        send="ECMFront1Fr02",
        receive="BECMFront1Fr02",
        namespace=SC.nspace_lookup("Front1CANCfg0")
        )

    SC.subscribe_signal(can_par_ex, etp["timeout"])
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_par["receive"])
    logging.info("all can messages updated")
    time.sleep(1)
    logging.info("Step%s: messages received %s", etp["step_no"],
                 len(SC.can_messages[can_par_ex["receive"]]))
    logging.info("Step%s: messages: %s \n", etp["step_no"],
                 SC.can_messages[can_par_ex["receive"]])
    logging.info("Step%s: frames received %s", etp["step_no"],
                 len(SC.can_frames[can_par_ex["receive"]]))
    logging.info("Step%s: frames: %s \n", etp["step_no"],
                 SC.can_frames[can_par_ex["receive"]])

    frame_step_2 = len(SC.can_frames[can_par_ex["receive"]])
    #min number of non-diagnostic frames received allowed
    result = (len(SC.can_frames[can_par_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", etp["step_no"], result)
    return result, can_par_ex, frame_step_2

def step_2(can_par, can_par_ex, frame_step_2):
    """
    Teststep 2: verify ReadDTCInfoSnapshotIdentification reply positively
    """
    stepno = 2
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification", b'', b''),
        extra=''
        )
    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=2,
        purpose="verify ReadDTCInfoSnapshotIdentification reply positively",
        timeout=1,
        min_no_messages=-1,
        max_no_messages=-1
        )
    waiting_time = 2 #seconds
    max_diff = 50 #max difference allowed for number of frame non-diagnostic received
    number_of_frames_received = 0
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    now = int(time.time())
    SC.update_can_messages(can_par["receive"])
    while now + waiting_time > int(time.time()):
        result = SUTE.teststep(can_par, cpay, etp)
        result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],
                                              teststring='5903')
    number_of_frames_received = len(SC.can_frames[can_par_ex["receive"]])
    logging.info("Step %s frames received: %s", stepno, number_of_frames_received)
    result = result and ((number_of_frames_received + max_diff) > frame_step_2 > \
        (number_of_frames_received - max_diff))
    logging.info("Step %s teststatus: %s \n", stepno, result)
    return result

def step_3(can_par, can_par_ex, frame_step_2):
    """
    Teststep 3: Verify subscribed signal is still sent
    """
    stepno = 3
    purpose = "Verify subscribed signal is still sent"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_par["receive"])
    logging.info("all can messages updated")
    time.sleep(1)
    logging.info("Step%s: messages received %s", stepno,\
                 len(SC.can_messages[can_par_ex["receive"]]))
    logging.info("Step%s: messages: %s \n", stepno,\
                 SC.can_messages[can_par_ex["receive"]])
    logging.info("Step%s: frames received %s", stepno,\
                 len(SC.can_frames[can_par_ex["receive"]]))
    logging.info("Step%s: frames: %s \n", stepno,\
                 SC.can_frames[can_par_ex["receive"]])

    number_of_frames_received = len(SC.can_frames[can_par_ex["receive"]])
    result = ((number_of_frames_received + 15) > frame_step_2 > \
        (number_of_frames_received - 15))

    logging.info("Step%s teststatus: %s \n", stepno, result)

    return result

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
    # step 1:
    # action: Register not diagnostic message
    # result: BECM send requested signals
        resultt, can_par_ex, frame_step_2 = step_1(can_par)
        result = result and resultt

    # step2:
    # action:
    # result: BECM reports confirmed message
        result = result and step_2(can_par, can_par_ex, frame_step_2)

    # step3:
    # action: Verify signal is still sent
    # result: BECM send requested signals
        result = result and step_3(can_par, can_par_ex, frame_step_2)

    ############################################
    # postCondition
    ############################################

    result = POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
