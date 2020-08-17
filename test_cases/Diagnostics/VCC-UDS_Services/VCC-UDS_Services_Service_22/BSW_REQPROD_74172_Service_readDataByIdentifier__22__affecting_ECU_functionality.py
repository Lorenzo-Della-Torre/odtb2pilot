# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-09-17
# version:  2.0
# reqprod:  74172

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-13
# version:  2.1
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

from support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
import odtb_conf

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()


def step_1(can_p):
    """
    Teststep 1: register another signal
    """
    stepno = 1
    etp: CanTestExtra = {
        "purpose" : "register another signal",
        "timeout" : 15,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    can_p_ex: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "ECMFront1Fr02",
        "receive" : "BECMFront1Fr02",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)

    SC.subscribe_signal(can_p_ex, etp["timeout"])
    time.sleep(1)
    SC.clear_all_can_messages()
    logging.info("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p["receive"])
    logging.info("all can messages updated")
    time.sleep(4)
    logging.info("Step%s: messages received %s", stepno,
                 len(SC.can_messages[can_p_ex["receive"]]))
    logging.info("Step%s: messages: %s \n", stepno,
                 SC.can_messages[can_p_ex["receive"]])
    num_frames_step1 = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", stepno, num_frames_step1)
    logging.debug("Step%s: frames: %s \n", stepno,
                  SC.can_frames[can_p_ex["receive"]])

    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Step%s teststatus: %s \n", stepno, result)
    return result, can_p_ex, num_frames_step1


def step_2(can_p, can_p_ex, num_frames_step1):
    """
    Teststep 2: verify non-diagnostic signal is not effected while service 22 is cyclically sent
    """
    step_no = 2
    purpose = "verify non-diagnostic signal is not effected while service 22 is cyclically sent"
    SUTE.print_test_purpose(step_no, purpose)
    number_of_frames_received = 0
    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")
    SC.clear_all_can_frames()

    #can_rec = "BECMFront1Fr02"
    now = int(time.time())
    print(now)

    SC.update_can_messages(can_p["receive"])

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x20',
                                        b''),
        "extra": ''
        }
    while now + 4 > int(time.time()):
        SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)
    number_of_frames_received = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step%s frames received: %s", step_no, number_of_frames_received)
    result = ((number_of_frames_received + 50) >\
              num_frames_step1 >\
              (number_of_frames_received - 50))
    logging.info("Step%s teststatus: %s\n", step_no, result)
    return result

def step_3(can_p_ex, num_frames_step1):
    """
    Teststep 3: Verify subscribed signal in step 1 is still sent
    """
    step_no = 3
    purpose = "Verify subscribed non-diagnostic signal is still sent as in step 1"
    SUTE.print_test_purpose(step_no, purpose)
    #can_rec = "BECMFront1Fr02"
    #SC.update_can_messages(r)
    logging.debug("All can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p_ex["receive"])
    logging.info("all can messages updated")
    time.sleep(4)
    logging.info("Step%s received: %s", step_no, len(SC.can_frames[can_p_ex["receive"]]))
    logging.debug("Step%s frames: %s\n", step_no, SC.can_frames[can_p_ex["receive"]])

    result = ((len(SC.can_frames[can_p_ex["receive"]]) + 50) >\
              num_frames_step1 >\
              (len(SC.can_frames[can_p_ex["receive"]]) - 50))

    logging.info("Step%s teststatus: %s\n", step_no, result)
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
    # step 1:
    # action: register a non-diagnostic signal
    # result: BECM send requested signals
        result, can_p_ex, num_frames_step1 = result and step_1(can_p)

    # step2:
    # action: send ReadDataByIdentifier cyclically
    # result: BECM reports confirmed message
        result = result and step_2(can_p, can_p_ex, num_frames_step1)

    # step3:
    # action: Verify signal is still sent
    # result: BECM send requested signals
        result = result and step_3(can_p_ex, num_frames_step1)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
