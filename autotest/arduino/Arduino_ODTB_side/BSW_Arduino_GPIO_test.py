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


#import os
#import sys

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
sleeptime = 0.7

#Led1=LED(16)
#Led2=LED(12)

    # teststep 1: Test relais connected to Arduino
def step_1(can_p):
    """
    Teststep 1: Test relais connected to Arduino
    """

    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Test relais connected to Arduino",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    stub = can_p["netstub"]

    ns_rpiGPIO = SC.nspace_lookup("RpiGPIO")
    #print hex: print("Rx%02X"%c)
    time_tsend = time.time()
    
    # Led1 ON
    print("Arduino_Relais_0 on (time_diff: )", time.time()-time_tsend)
    SGPIO.t_send_gpio_signal_hex(stub, "PsR", ns_rpiGPIO, b'On')
    time_tsend = time.time()
    time.sleep(sleeptime)
    # Led1 OFF
    print("Arduino_Relais_0 off (time_diff: )", time.time()-time_tsend)
    SGPIO.t_send_gpio_signal_hex(stub, "PsR", ns_rpiGPIO, b'Off')

    for i in range(5):
        # Led1 ON
        print("Arduino_Relais_0 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x01')
        time_tsend = time.time()
        time.sleep(sleeptime)
        # Led1 OFF
        print("Arduino_Relais_0 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        # Led2 ON
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_1 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x02')
        # Led2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_1 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        # Relais1 ON
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_2 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x04')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_2 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_3 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x08')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_3 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_4 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x10')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_4 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_5 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x20')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_5 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_6 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x40')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_6 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_7 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x80')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_7 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)

    #testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


    # teststep 2: Test relais connected to Arduino with mask sent
def step_2(can_p):

    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Test relais connected to Arduino",
        "timeout": 1,
        "min_no_messages": 1,
        "max_no_messages": 1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    stub = can_p["netstub"]

    ns_rpiGPIO = SC.nspace_lookup("RpiGPIO")

    #print hex: print("Rx%02X"%c)
    time_tsend = time.time()

    for i in range(5):
        # PsR ON
        print("Arduino_Relais_0 (PsR) on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'On')
        time_tsend = time.time()
        time.sleep(sleeptime)
        # PsR OFF
        print("Arduino_Relais_0 (PsR) off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Off')
        # Led2 ON
        time_tsend = time.time()
        time.sleep(sleeptime)


        # Led1 ON
        print("Arduino_Relais_0 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x01')
        time_tsend = time.time()
        time.sleep(sleeptime)
        # Led1 OFF
        print("Arduino_Relais_0 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        # Led2 ON
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_1 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x02')
        # Led2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_1 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        # Relais1 ON
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_2 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x04')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_2 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_3 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x08')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_3 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_4 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x10')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_4 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_5 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x20')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_5 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_6 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x40')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_6 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_7 on (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x80')
        # Relais2 OFF
        time_tsend = time.time()
        time.sleep(sleeptime)
        print("Arduino_Relais_7 off (time_diff: )", time.time()-time_tsend)
        SGPIO.t_send_gpio_signal_hex(stub, "Arduino_GPIO", ns_rpiGPIO, b'Rx\xff\x00')
        time_tsend = time.time()
        time.sleep(sleeptime)

    #testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)




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
    timeout = 150
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: bTest Relais / LED on/off
    # result:
        step_1(can_p)

     # step 2:
    # action: bTest Relais / LED on/off
    # result:
        step_2(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
