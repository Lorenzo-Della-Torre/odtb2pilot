# Testscript GPIO test
# project:  Signalbroker Remote GPIO
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-11-22
# version:  1.0
# reqprod:  GPIO

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
import odtb_conf

#from gpiozero import LED

from support_can import SupportCAN, CanParam, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_file_io import SupportFileIO
from support_rpi_gpio import SupportRpiGpio
from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SGPIO = SupportRpiGpio()
PREC = SupportPrecondition()
POST = SupportPostcondition()

# Global variable:
#testresult = True

#Led1=LED(16)
#Led2=LED(12)


def step_1(can_p):
    """
    Teststep 1: Trigger Rpi GPIO
    """
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Trigger Rpi GPIO",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    stub = can_p["netstub"]
    ns_rpiGPIO = SC.nspace_lookup("RpiGPIO")

    for i in range(10):
        # Led1 ON
        print("Led1 on")
        SGPIO.t_send_gpio_signal_hex(stub, "Led1", ns_rpiGPIO, b'\x01')
        time.sleep(1)
        # Led1 OFF
        print("Led1 off")
        SGPIO.t_send_gpio_signal_hex(stub, "Led1", ns_rpiGPIO, b'\x00')
        # Led2 ON
        time.sleep(1)
        print("Led2 on")
        SGPIO.t_send_gpio_signal_hex(stub, "Led2", ns_rpiGPIO, b'\x01')
        # Led2 OFF
        time.sleep(1)
        print("Led1 off")
        SGPIO.t_send_gpio_signal_hex(stub, "Led2", ns_rpiGPIO, b'\x00')
        # Relais1 ON
        time.sleep(1)
        print("Relais1 on")
        SGPIO.t_send_gpio_signal_hex(stub, "Relais1", ns_rpiGPIO, b'\x01')
        # Relais2 OFF
        time.sleep(3)
        print("Relais1 off")
        SGPIO.t_send_gpio_signal_hex(stub, "Relais1", ns_rpiGPIO, b'\x00')
        time.sleep(3)

    #testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


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
    # action: bTest Relais / LED on/off
    # result:
        step_1(can_p)
    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
