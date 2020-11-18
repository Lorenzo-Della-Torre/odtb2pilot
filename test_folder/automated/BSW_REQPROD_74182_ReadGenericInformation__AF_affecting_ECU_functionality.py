# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-10-09
# version:  2.0
# reqprod:  74182

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

""" Python implementation of REQPROD 74182"""

from datetime import datetime
import time
import logging
import sys
import inspect
import parameters.odtb_conf as odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SIO = SupportFileIO

WAITING_TIME = 10
FRAME_DEVIATION = 50


def step_1(can_p):
    """
    Teststep 1: Subscribe non-diagnostic signal and verify received frames
    """
    # fetch any signal sent from BECM when awake
    can_p_ex: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "ECMFront1Fr02",
        'receive': "BECMFront1Fr02",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)
    etp: CanTestExtra = {
        'step_no': 1,
        'purpose': "Subscribe non-diagnostic signal and verify received frames",
        'timeout': 300,
        'min_no_messages': -1,
        'max_no_messages': -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    logging.info("Step:     %s", etp["step_no"])
    logging.info("Purpose:  %s", etp["purpose"])
    SC.subscribe_signal(can_p_ex, etp["timeout"])
    time.sleep(1)

    SC.clear_all_can_messages()
    logging.debug("all can messages cleared")
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p["receive"])
    logging.debug("all can messages updated")
    time.sleep(WAITING_TIME)

    logging.debug("Step %s: messages received %s", etp["step_no"], \
        len(SC.can_messages[can_p_ex["receive"]]))
    logging.debug("Step %s: messages: %s", etp["step_no"], SC.can_messages[can_p_ex["receive"]])
    frames_step1 = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step %s: frames received %s", etp["step_no"], frames_step1)
    logging.debug("Step %s: frames: %s", etp["step_no"], SC.can_frames[can_p_ex["receive"]])

    result = (frames_step1 > 10)
    logging.info("Result step %s: %s\n", etp["step_no"], result)
    return result, can_p_ex, frames_step1


def step_2(can_p, can_p_ex, frames_step1):
    """
    Teststep 2: After start counting rec frames again, we send some requests Read Generic
    Information cyclically in between. Then we compare number of received frames within same
    timespan as step1 (should be roughly the same number).
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber",
                                        b'\xFF\xFF\xFF',
                                        b'\xFF'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose": 'Send Read Generic Information cyclically in between. '    \
            'Compare number of received frames within same timespan as step1 ' \
            '(should be roughly the same number).',
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    SC.clear_all_can_messages()
    logging.debug("all can messages cleared")
    SC.clear_all_can_frames()

    now = int(time.time())
    logging.debug("Start time: %s", now)
    while now + WAITING_TIME > int(time.time()):
        SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)

    number_of_frames_received = len(SC.can_frames[can_p_ex["receive"]])
    logging.debug("Step %s: payload: %s", etp["step_no"], cpay["payload"])
    logging.info("Step %s: frames received: %s", etp["step_no"], number_of_frames_received)
    result = result and ((number_of_frames_received + FRAME_DEVIATION) > frames_step1)
    result = result and (frames_step1 > (number_of_frames_received - FRAME_DEVIATION))
    logging.info("Result step %s: %s\n", etp["step_no"], result)
    return result


def step_3(can_p, can_p_ex, frames_step1):
    """
    Teststep 3: Verify frames still received.
    """
    etp: CanTestExtra = {
        'step_no': 3,
        'purpose': "Verify subscribed non-diagnostic signal is still sent as in step 1",
        'timeout': 300,
        'min_no_messages': -1,
        'max_no_messages': -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SC.clear_all_can_messages()
    logging.debug("Step %s: all can messages cleared", etp["step_no"])
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p["receive"])
    logging.debug("Step %s: all can messages updated", etp["step_no"])
    time.sleep(WAITING_TIME)

    number_of_frames_received = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Step%s: frames received %s", etp["step_no"], number_of_frames_received)
    logging.debug("Step%s: frames: %s \n", etp["step_no"], SC.can_frames[can_p_ex["receive"]])

    result = ((number_of_frames_received + FRAME_DEVIATION) > frames_step1)
    result = result and (frames_step1 > (number_of_frames_received - FRAME_DEVIATION))

    logging.info("Result step %s: %s\n", etp["step_no"], result)
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
        # action: Subscribe non-diagnostic signal and verify received frames
        # result: BECM send requested signals
        test_result, can_p_ex, frames_step1 = step_1(can_p)
        result = result and test_result

        # step 2:
        # action: Send ReadDTCInformation cyclically
        # result: BECM reply positively
        result = result and step_2(can_p, can_p_ex, frames_step1)

        # step3:
        # action: Verify signal is still sent as in step 1
        # result: BECM send requested signals
        result = result and step_3(can_p, can_p_ex, frames_step1)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
