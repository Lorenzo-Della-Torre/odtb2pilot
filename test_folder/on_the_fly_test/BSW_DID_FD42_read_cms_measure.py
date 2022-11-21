# Testscript ODTB2 MEPII
# project:  DID overnight test with asleep/awake
# author:   hweiler (Hans-Klaus Weiler)
# date:     2020-06-05
# version:  1.0
# reqprod:  DID overnight test with asleep/awake

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

import re
import subprocess
from collections import deque
#from typing import Dict

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam,\
                                         CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE3E = SupportService3e()

Last_candumpfiles = deque([])


def start_candump():
    """
        start_candump: start new candump can0 if running on linux
    """
    #global Last_Step9_message
    #result = True

    stepno = 999
    purpose = "execute command: Start new CANDUMP CAN0"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    logging.info("\ntime {:.3f}".format(time.time()))
    f_name_temp = re.split(r"(BSW_)", sys.argv[0])
    f_name = re.split(r"(.py)", f_name_temp[1]+f_name_temp[2])[0]
    t_str = str(time.time()).replace('.', '_')
    f_name = f_name + '_' + t_str + '_can.log'
    #logging.info("Start new canlog: %s", f_name)
    if sys.platform == 'linux':
    #if sys.platform == 'win32':
        logging.info("linux - Start new canlog: %s", f_name)
        #start candump with timestamp, stop after 10sec without signals
        subprocess.Popen(["candump", "-ta", "-T10000", "can0"], stdout=open(f_name, 'w'))
        Last_candumpfiles.append(f_name)
        logging.debug("Last candump_files: %s", Last_candumpfiles)
        if len(Last_candumpfiles) > 10:
            rem_file = Last_candumpfiles.popleft()
            #save only data from last 10 loops
            subprocess.call(["rm", "-f", rem_file])
    else:
        logging.info("operating system %s: Can't start candump.", sys.platform)



#def step_1(can_p):
def step_1():
    """
        teststep 1: set CMSemu current value via emulator interface
    """

    stepno = 1
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    ### replace code here to send UDP request
    # I2C relay card: Relay1 ON
    #logging.debug("I2C_Relais_1 on (time_diff: ) %s", time.time()-time_tsend)
    #SGPIO.t_send_gpio_signal_hex(stub, "I2C_GPIO", ns_rpi_gpio, b'Rx\x01')
    #time_tsend = time.time()
    #time.sleep(SLEEPTIME)
    #result = SUTE.teststep(can_p, cpay, etp)

    return result


#MEP1 BECM DID CMS Carcom:
#D93a HV Battery Raw Current
#D93B Charge (Coulomb count / quality factor)
#D93C Charge loss time
#DB8A CMD Device ID
#DB8B CMS CMS Device ID NVRAM
#DB95 CMS Safety Mechanism Status

#MEP2 BECM DID for CMS
#DAE4 Rotating buffer CMS current
#DB8A CMS Device ID
#DB8B CMS Device ID NVRAM
#FD40 CMS Error
#FD41 CMS Calibration result
#FD42 CMS Measurements
#FD61 CMS Communication Status
#FD62 CMS CMS sense supply status

def step_2(can_p):
    """
        teststep 2: request DID CMS FD42 (MEP2 HVBM CMS Measurements)
    """

    stepno = 2
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x42', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request HVBM DID FD42 CMS Measurements",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received  %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 62FD42
    if SUTE.test_message(SC.can_messages[can_p['receive']], '62FD42'):
        logging.info("Reply contains 62FD42 as expected.")

    logging.info("DID sent:                    %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CMS current (HvBatt/ActRaw): %s", SC.can_messages[can_p['receive']][0][2][10:18])
    logging.info("CoulombCnt:                  %s", SC.can_messages[can_p['receive']][0][2][20:28])
    logging.info("TempNTC (HvBatt/ActNtc):     %s", SC.can_messages[can_p['receive']][0][2][30:34])

    return result


#def step_3(can_p):
def step_3():
    """
        teststep 1: set CMSemu current value via emulator interface
    """

    stepno = 1
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    ### replace code here to send UDP request
    # I2C relay card: Relay1 ON
    #logging.debug("I2C_Relais_1 on (time_diff: ) %s", time.time()-time_tsend)
    #SGPIO.t_send_gpio_signal_hex(stub, "I2C_GPIO", ns_rpi_gpio, b'Rx\x01')
    #time_tsend = time.time()
    #time.sleep(SLEEPTIME)
    #result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_4(can_p):
    """
        teststep 4: request DID CMS FD42 (MEP2 HVBM CMS Measurements)
    """

    stepno = 4
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x42', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request HVBM DID FD42 CMS Measurements",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 62FD42
    if SUTE.test_message(SC.can_messages[can_p['receive']], '62FD42'):
        logging.info("Reply contains 62FD42 as expected.")

    logging.info("DID sent:                    %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CMS current (HvBatt/ActRaw): %s", SC.can_messages[can_p['receive']][0][2][10:18])
    logging.info("CoulombCnt:                  %s", SC.can_messages[can_p['receive']][0][2][20:28])
    logging.info("TempNTC (HvBatt/ActNtc):     %s", SC.can_messages[can_p['receive']][0][2][30:34])

    return result

def step_5(can_p):
    """
        teststep 5: request DID CMS FD462 (MEP2 HVBM CMS CMS sense supply status)
    """

    stepno = 4
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x62', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request HVBM DID FD62 CMS sense supply status",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 62FD62
    if SUTE.test_message(SC.can_messages[can_p['receive']], '62FD62'):
        logging.info("Reply contains 62FD62 as expected.")

    logging.info("DID sent:                    %s", SC.can_messages[can_p['receive']][0][2][4:8])
    sense_supply_status = SC.can_messages[can_p['receive']][0][2][8:10]
    logging.info("CMS sense supply status    : %s", sense_supply_status)
    if sense_supply_status == '00':
        logging.info("00 = CMS Sense supply enabled")
    elif sense_supply_status == '01':
        logging.info("01 = CMS Sense supply disabled")
    else:
        logging.info("%s = unknown CMS Sense supply status")

    return result




def run():
    """
        OnTheFly testscript
    """
    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }
    #replace can_p parameters to project specific ones:
    SIO.parameter_adopt_teststep(can_p)
    #logging.debug("Stack output %s", inspect.stack())

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 0 #(run forever)

    # if you want a candump (works directly on Rpi only):
    #start_candump()

    result = PREC.precondition(can_p, timeout)
    #TesterPresent not needed in this testscript
    #SE3E.stop_periodic_tp_zero_suppress_prmib()
    #result, can_af = precondition_extra(can_p, timeout)


    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    result = SE22.read_did_f186(can_p, dsession=b'\x01')

    #if result:
    while True:
    #for i in range(2):
        # step1:
        # action: set CMS emu current
        # result:
        result = step_1() and result

        # step2:
        # action: check current sensor
        # result:
        result = step_2(can_p) and result

        # step3:
        # action: set CMS emu current to new value
        # result:
        #result = step_3(can_p) and result
        result = step_3() and result

        # step4:
        # action: check current sensor
        # result:
        result = step_4(can_p) and result

        # step5:
        # action: check CMS sense supply status FD62
        # result:
        result = step_5(can_p) and result
        time.sleep(2)



    ############################################
    # postCondition
    ############################################

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)


    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
