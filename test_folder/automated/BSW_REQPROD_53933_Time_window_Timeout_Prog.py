# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-30
# version:  1.0
# reqprod:  53933

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-22
# version:  1.1
# reqprod:  53933

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
import sys
import logging
import inspect

from supportfunctions.support_can import SupportCAN, CanParam, PerParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_rpi_gpio import SupportRpiGpio

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

import odtb_conf

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SGPIO = SupportRpiGpio()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE31 = SupportService31()
SE34 = SupportService34()

def step_1(can_p):
    """
    Teststep 1: Switch the ECU off and on
    """
    stepno = 1
    purpose = "Switch the ECU off and on"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    result = True
    logging.info("Relais1 on")
    SGPIO.t_send_gpio_signal_hex(can_p["netstub"], "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x00')
    time.sleep(3)
    logging.info("Relais1 off")
    SGPIO.t_send_gpio_signal_hex(can_p["netstub"], "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x01')
    return result

def step_2(can_p):
    """
    Teststep 2: Send burst Diagnostic Session Control Programming Session with
    periodicity of 10ms for 40 ms window
    """
    stepno = 2
    purpose = """Send burst Diagnostic Session Control Programming Session with
                 periodicity of 10ms for 40 ms window"""
    SUTE.print_test_purpose(stepno, purpose)

    burst_param: PerParam = {
        "name" : "Burst",
        "send" : True,
        "id" : "Vcu1ToAllFuncFront1DiagReqFrame",
        "nspace" : can_p["namespace"],
        "frame" : b'\x02\x10\x82\x00\x00\x00\x00\x00',
        "intervall" : 0.010
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), burst_param)
    # Send NM burst (4 frames):
    # t_send_signal_hex(self, stub, signal_name, namespace, payload_value)
    # SC.send_burst(self, stub, burst_id, burst_nspace, burst_frame,
    # burst_intervall, burst_quantity)
    SC.send_burst(can_p["netstub"], burst_param, 4)
    time.sleep(2)

def step_4(can_p):
    """
    Teststep 4: Switch the ECU off and on
    """
    stepno = 4
    purpose = "Switch the ECU off and on"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    result = True
    logging.info("Relais1 on")
    SGPIO.t_send_gpio_signal_hex(can_p["netstub"], "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x00')
    time.sleep(3)
    logging.info("Relais1 off")
    SGPIO.t_send_gpio_signal_hex(can_p["netstub"], "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x01')
    return result

def step_5(can_p):
    """
    Teststep 5: Send burst Diagnostic Session Control Programming Session with
    periodicity of 2ms for 40 ms window
    """
    stepno = 5
    purpose = """Send burst Diagnostic Session Control Programming Session with
                 periodicity of 1ms for 40 ms window"""
    SUTE.print_test_purpose(stepno, purpose)
    burst_param: PerParam = {
        "name" : "Burst",
        "send" : True,
        "id" : "Vcu1ToAllFuncFront1DiagReqFrame",
        "nspace" : can_p["namespace"],
        "frame" : b'\x02\x10\x82\x00\x00\x00\x00\x00',
        "intervall" : 0.001
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), burst_param)
    # Send NM burst (20 frames):
    # t_send_signal_hex(self, stub, signal_name, namespace, payload_value)
    # SC.send_burst(self, stub, burst_id, burst_nspace, burst_frame,
    # burst_intervall, burst_quantity)
    SC.send_burst(can_p["netstub"], burst_param, 40)
    time.sleep(2)

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
    timeout = 100
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action: Switch the ECU off and on
        # result: BECM sends positive reply
        result = result and step_1(can_p)

        # step2:
        # action: Send burst Diagnostic Session Control Programming Session with
        # periodicity of 10ms for 40 ms window
        # result:
        step_2(can_p)

        # step3:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=3)

        # step4:
        # action: Switch the ECU off and on
        # result:
        result = result and step_4(can_p)

        # step5:
        # action: Send burst Diagnostic Session Control Programming Session with
        # periodicity of 1ms for 40 ms window
        # result:
        step_5(can_p)

        # step6:
        # action: verify ECU in programming session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x02', stepno=6)

        # step7:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=7)

        # step8:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=8)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
