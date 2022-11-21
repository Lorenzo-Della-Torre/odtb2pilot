# Testscript ODTB2 MEPII
# project:  CMS/CVTN emu
# author:   hweiler (Hans-Klaus Weiler)
# date:     2022-01-27
# version:  1.0
# reqprod:  none, set current/power for CMS emu, read CMS status

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
#from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_cms_cvtn_emu import Support_emu_udp

from hilding.dut import Dut

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
#SE3E = SupportService3e()
SEMU_UDP = Support_emu_udp

Last_candumpfiles = deque([])

SLEEPTIME = 5

ns_emu_cms = 'emu_CMS' #has to match name in interfaces.json
#ns_emu_cms = 'RpiGPIO'
#ns_emu_cvtn = 'emu_CVTN'

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



def step_1(udp_p):
    """
        teststep 1: set CMSemu current value via emulator interface
    """

    stepno = 1
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    ### replace code here to send UDP request
    # I2C relay card: Relay1 ON
    #logging.debug("I2C_Relais_1 on (time_diff: ) %s", time.time()-time_tsend)
    stub = udp_p["netstub"]

    constant = { 'LSBC1' : 377.877e-12,
                 'LSBE1' : 2.32175e-9,
                 'LSBC2' : 377.877e-12,
                 'LSBE2' : 2.32175e-9
               }

    value = {   #values for signals to set
                'Charge1' : 0, #ARRP1a 100 Vs coulomb count?
                'Charge2' : 0, #ARRP2a 100 Vs coulomb count?
                'Energy1' : 0, #ARRP1b
                'Energy2' : 0, #ARRP2b

                'current1' : 411, #NARRP1a
                'power1' : 2411,
                'current2' : 412,
                'power2' : 2412,

                'i1_avg' : 311, ##NARP1b
                'i1_h1' : 411,
                'i2_avg' : 321,
                'i2_h1' : 421
             }

    signal = { #signal in ARRP1a
               'C1_Charge1' : bytes.fromhex('{:016X}'.format(int(value['Charge1'] /
                                            constant['LSBC1']))),
               #signal in ARRP2a
               'C2_Charge2' : bytes.fromhex('{:016X}'.format(int(value['Charge2'] /
                                            constant['LSBC2']))),
               #signal in ARRP1b
               'E1_Energy1' : bytes.fromhex('{:016X}'.format(int(value['Energy1'] /
                                            constant['LSBE1']))),
               #signal in ARRP2b
               'E2_Energy2' : bytes.fromhex('{:016X}'.format(int(value['Energy2'] /
                                            constant['LSBE2']))),

               'I1' : bytes.fromhex('{:06X}'.format(value['current1'])), #signal in NARRP1a
               'P1' : bytes.fromhex('{:06X}'.format(value['power1'])),
               'I2' : bytes.fromhex('{:06X}'.format(value['current2'])), #signal in NARRP2a
               'P2' : bytes.fromhex('{:06X}'.format(value['power2'])),

               'I1AVG' : bytes.fromhex('{:06X}'.format(value['i1_avg'])), #signal in NARRP1b
               'I1H1' : bytes.fromhex('{:06X}'.format(value['i1_h1'])),
               'I2AVG' : bytes.fromhex('{:06X}'.format(value['i2_avg'])), #signal in NARRP2b
               'I2H1' : bytes.fromhex('{:06X}'.format(value['i2_h1']))
             }


    #Send messages vi UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1a", udp_p["namespace"], signal['C1_Charge1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2a", udp_p["namespace"], signal['C2_Charge2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1b", udp_p["namespace"], signal['E1_Energy1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2b", udp_p["namespace"], signal['E2_Energy2'])

    #Send messages via UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1a", udp_p["namespace"], signal['I1']
                                                                         + b'\00' + signal['P1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2a", udp_p["namespace"], signal['I2']
                                                                         + b'\00' + signal['P2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1b", udp_p["namespace"], signal['I1AVG']
                                                                         + b'\00' + signal['I1H1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2b", udp_p["namespace"], signal['I2AVG']
                                                                         + b'\00' + signal['I2H1'])

    time.sleep(SLEEPTIME)
    #result = SUTE.teststep(can_p, cpay, etp)

    return result


def step_2(udp_p):
    """
        teststep 2: set CMSemu current value via emulator interface
        Send same data as from step_1, but use signal.
    """

    stepno = 2
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    ### replace code here to send UDP request
    # I2C relay card: Relay1 ON
    #logging.debug("I2C_Relais_1 on (time_diff: ) %s", time.time()-time_tsend)
    stub = udp_p["netstub"]

    constant = { 'LSBC1' : 377.877e-12,
                 'LSBE1' : 2.32175e-9,
                 'LSBC2' : 377.877e-12,
                 'LSBE2' : 2.32175e-9
               }

    value = {   #values for signals to set
                'Charge1' : 12, #ARRP1a 100 Vs coulomb count?
                'Charge2' : 22, #ARRP2a 100 Vs coulomb count?
                'Energy1' : 321, #ARRP1b
                'Energy2' : 322, #ARRP2b

                'current1' : 421, #NARRP1a
                'power1' : 2821,
                'current2' : 422,
                'power2' : 2922,

                'i1_avg' : 362, ##NARP1b
                'i1_h1' : 442,
                'i2_avg' : 372,
                'i2_h1' : 472
             }

    signal = { #signal in ARRP1a
               'C1_Charge1' : bytes.fromhex('{:016X}'.format(int(value['Charge1'] /
                                            constant['LSBC1']))),
               #signal in ARRP2a
               'C2_Charge2' : bytes.fromhex('{:016X}'.format(int(value['Charge2'] /
                                            constant['LSBC2']))),
               #signal in ARRP1b
               'E1_Energy1' : bytes.fromhex('{:016X}'.format(int(value['Energy1'] /
                                            constant['LSBE1']))),
               #signal in ARRP2b
               'E2_Energy2' : bytes.fromhex('{:016X}'.format(int(value['Energy2'] /
                                            constant['LSBE2']))),

               'I1' : bytes.fromhex('{:06X}'.format(value['current1'])), #signal in NARRP1a
               'P1' : bytes.fromhex('{:06X}'.format(value['power1'])),
               'I2' : bytes.fromhex('{:06X}'.format(value['current2'])), #signal in NARRP2a
               'P2' : bytes.fromhex('{:06X}'.format(value['power2'])),

               'I1AVG' : bytes.fromhex('{:06X}'.format(value['i1_avg'])), #signal in NARRP1b
               'I1H1' : bytes.fromhex('{:06X}'.format(value['i1_h1'])),
               'I2AVG' : bytes.fromhex('{:06X}'.format(value['i2_avg'])), #signal in NARRP2b
               'I2H1' : bytes.fromhex('{:06X}'.format(value['i2_h1']))
             }


    #Send messages vi UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1a", udp_p["namespace"], signal['C1_Charge1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2a", udp_p["namespace"], signal['C2_Charge2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1b", udp_p["namespace"], signal['E1_Energy1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2b", udp_p["namespace"], signal['E2_Energy2'])

    #Send messages via UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1a", udp_p["namespace"], signal['I1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1a", udp_p["namespace"], signal['P1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2a", udp_p["namespace"], signal['I2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2a", udp_p["namespace"], signal['P2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1b", udp_p["namespace"], signal['I1AVG'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1b", udp_p["namespace"], signal['I1H1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2b", udp_p["namespace"], signal['I2AVG'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2b", udp_p["namespace"], signal['I2H1'])

    time.sleep(SLEEPTIME)
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

def step_3(can_p):
    """
        teststep 3: request DID CMS DAE4 (MEP2 HVBM CMS Measurements)
    """

    stepno = 3
    #cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
    #                                                     b'\xDA\xE4', b''),
    #                    "extra" : b''
    #                   }
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x48\x02', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request HVBM DID DAE4 CMS Measurements",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received  %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 62DAE4
    #if SUTE.test_message(SC.can_messages[can_p['receive']], '62DAE4'):
    if SUTE.test_message(SC.can_messages[can_p['receive']], '624802'):
        logging.info("Reply contains 62DAE4 as expected.")

    logging.info("DID sent:              %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CMS current 0s       : %s", SC.can_messages[can_p['receive']][0][2][10:14])
    logging.info("CMS current -200 ms  : %s", SC.can_messages[can_p['receive']][0][2][14:18])
    logging.info("CMS current -300 ms  : %s", SC.can_messages[can_p['receive']][0][2][18:22])
    logging.info("CMS current -400 ms  : %s", SC.can_messages[can_p['receive']][0][2][22:26])
    logging.info("CMS current -1000 ms : %s", SC.can_messages[can_p['receive']][0][2][26:30])
    logging.info("CMS current -2000 ms : %s", SC.can_messages[can_p['receive']][0][2][30:34])

    return result


def step_4(udp_p):
    """
        teststep 4: set CMSemu current value via emulator interface
    """

    stepno = 4
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    stub = udp_p["netstub"]

    constant = { 'LSBC1' : 377.877e-12,
                 'LSBE1' : 2.32175e-9,
                 'LSBC2' : 377.877e-12,
                 'LSBE2' : 2.32175e-9
               }

    value = {   #values for signals to set
                'Charge1' : 115, #ARRP1a 100 Vs coulomb count?
                'Charge2' : 125, #ARRP2a 100 Vs coulomb count?
                'Energy1' : 615, #ARRP1b
                'Energy2' : 725, #ARRP2b

                'current1' : 451, #NARRP1a
                'power1' : 2751,
                'current2' : 452,
                'power2' : 2852,

                'i1_avg' : 385, ##NARP1b
                'i1_h1' : 425,
                'i2_avg' : 375,
                'i2_h1' : 435
            }

    signal = { #signal in ARRP1a
               'C1_Charge1' : bytes.fromhex('{:016X}'.format(int(value['Charge1'] /
                                            constant['LSBC1']))),
               #signal in ARRP2a
               'C2_Charge2' : bytes.fromhex('{:016X}'.format(int(value['Charge2'] /
                                            constant['LSBC2']))),
               #signal in ARRP1b
               'E1_Energy1' : bytes.fromhex('{:016X}'.format(int(value['Energy1'] /
                                            constant['LSBE1']))),
               #signal in ARRP2b
               'E2_Energy2' : bytes.fromhex('{:016X}'.format(int(value['Energy2'] /
                                            constant['LSBE2']))),

               'I1' : bytes.fromhex('{:06X}'.format(value['current1'])), #signal in NARRP1a
               'P1' : bytes.fromhex('{:06X}'.format(value['power1'])),
               'I2' : bytes.fromhex('{:06X}'.format(value['current2'])), #signal in NARRP2a
               'P2' : bytes.fromhex('{:06X}'.format(value['power2'])),

               'I1AVG' : bytes.fromhex('{:06X}'.format(value['i1_avg'])), #signal in NARRP1b
               'I1H1' : bytes.fromhex('{:06X}'.format(value['i1_h1'])),
               'I2AVG' : bytes.fromhex('{:06X}'.format(value['i2_avg'])), #signal in NARRP2b
               'I2H1' : bytes.fromhex('{:06X}'.format(value['i2_h1']))
             }


    #Send messages vi UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1a", udp_p["namespace"], signal['C1_Charge1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2a", udp_p["namespace"], signal['C2_Charge2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1b", udp_p["namespace"], signal['E1_Energy1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2b", udp_p["namespace"], signal['E2_Energy2'])

    #Send messages via UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1a", udp_p["namespace"], signal['I1']
                                                                         + b'\00' + signal['P1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2a", udp_p["namespace"], signal['I2']
                                                                         + b'\00' + signal['P2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1b", udp_p["namespace"], signal['I1AVG']
                                                                         + b'\00' + signal['I1H1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2b", udp_p["namespace"], signal['I2AVG']
                                                                         + b'\00' + signal['I2H1'])
    time.sleep(SLEEPTIME)

    return result

def step_5(udp_p):
    """
        teststep 5: set CMSemu current value via emulator interface
    """

    stepno = 5
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    stub = udp_p["netstub"]

    constant = { 'LSBC1' : 377.877e-12,
                 'LSBE1' : 2.32175e-9,
                 'LSBC2' : 377.877e-12,
                 'LSBE2' : 2.32175e-9
               }

    value = {   #values for signals to set
                'Charge1' : 114, #ARRP1a 100 Vs coulomb count?
                'Charge2' : 124, #ARRP2a 100 Vs coulomb count?
                'Energy1' : 514, #ARRP1b
                'Energy2' : 524, #ARRP2b

                'current1' : 441, #NARRP1a
                'power1' : 2441,
                'current2' : 442,
                'power2' : 2442,

                'i1_avg' : 314, ##NARP1b
                'i1_h1' : 414,
                'i2_avg' : 324,
                'i2_h1' : 424
            }

    signal = { #signal in ARRP1a
               'C1_Charge1' : bytes.fromhex('{:016X}'.format(int(value['Charge1'] /
                                            constant['LSBC1']))),
               #signal in ARRP2a
               'C2_Charge2' : bytes.fromhex('{:016X}'.format(int(value['Charge2'] /
                                            constant['LSBC2']))),
               #signal in ARRP1b
               'E1_Energy1' : bytes.fromhex('{:016X}'.format(int(value['Energy1'] /
                                            constant['LSBE1']))),
               #signal in ARRP2b
               'E2_Energy2' : bytes.fromhex('{:016X}'.format(int(value['Energy2'] /
                                            constant['LSBE2']))),

               'I1' : bytes.fromhex('{:06X}'.format(value['current1'])), #signal in NARRP1a
               'P1' : bytes.fromhex('{:06X}'.format(value['power1'])),
               'I2' : bytes.fromhex('{:06X}'.format(value['current2'])), #signal in NARRP2a
               'P2' : bytes.fromhex('{:06X}'.format(value['power2'])),

               'I1AVG' : bytes.fromhex('{:06X}'.format(value['i1_avg'])), #signal in NARRP1b
               'I1H1' : bytes.fromhex('{:06X}'.format(value['i1_h1'])),
               'I2AVG' : bytes.fromhex('{:06X}'.format(value['i2_avg'])), #signal in NARRP2b
               'I2H1' : bytes.fromhex('{:06X}'.format(value['i2_h1']))
             }


    #Send messages vi UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1a", udp_p["namespace"], signal['C1_Charge1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2a", udp_p["namespace"], signal['C2_Charge2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP1b", udp_p["namespace"], signal['E1_Energy1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "ARRP2b", udp_p["namespace"], signal['E2_Energy2'])

    #Send messages via UDP
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1a", udp_p["namespace"], signal['I1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1a", udp_p["namespace"], signal['P1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2a", udp_p["namespace"], signal['I2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2a", udp_p["namespace"], signal['P2'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1b", udp_p["namespace"], signal['I1AVG'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP1b", udp_p["namespace"], signal['I1H1'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2b", udp_p["namespace"], signal['I2AVG'])
    SEMU_UDP.t_send_udp_request_hex(stub, "NARRP2b", udp_p["namespace"], signal['I2H1'])

    time.sleep(SLEEPTIME)

    return result

def step_6(can_p):
    """
        teststep 6: request DID CMS DAE4 (MEP2 HVBM CMS Measurements)
    """

    stepno = 6
    #cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
    #                                                     b'\xDA\xE4', b''),
    #                    "extra" : b''
    #                   }
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x48\x02', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request HVBM DID DAE4 CMS Measurements",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 62DAE4
    #if SUTE.test_message(SC.can_messages[can_p['receive']], '62DAE4'):
    if SUTE.test_message(SC.can_messages[can_p['receive']], '624802'):
        logging.info("Reply contains 62DAE4 as expected.")

    logging.info("DID sent:              %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CMS current 0s       : %s", SC.can_messages[can_p['receive']][0][2][10:14])
    logging.info("CMS current -200 ms  : %s", SC.can_messages[can_p['receive']][0][2][14:18])
    logging.info("CMS current -300 ms  : %s", SC.can_messages[can_p['receive']][0][2][18:22])
    logging.info("CMS current -400 ms  : %s", SC.can_messages[can_p['receive']][0][2][22:26])
    logging.info("CMS current -1000 ms : %s", SC.can_messages[can_p['receive']][0][2][26:30])
    logging.info("CMS current -2000 ms : %s", SC.can_messages[can_p['receive']][0][2][30:34])

    return result




def run():
    """
        OnTheFly testscript
    """
    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    dut = Dut()

    # where to connect to signal_broker
    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': dut.conf.platforms[platform]['signal_send'],
        'receive': dut.conf.platforms[platform]['signal_receive'],
        'namespace': dut.conf.platforms[platform]['namespace'],
        'signal_periodic': dut.conf.platforms[platform]['signal_periodic'],
        'signal_tester_present': dut.conf.platforms[platform]['signal_tester_present'],
        'wakeup_frame': dut.conf.platforms[platform]['wakeup_frame'],
        'protocol': dut.conf.platforms[platform]['protocol'],
        'framelength_max': dut.conf.platforms[platform]['framelength_max'],
        'padding': dut.conf.platforms[platform]['padding'],
        'clientid': dut.conf.scriptname
        }
    #replace can_p parameters to project specific ones:
    SIO.parameter_adopt_teststep(can_p)

    udp_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup(ns_emu_cms)
        }

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
        result = step_1(udp_p) and result
        result = step_2(udp_p) and result

        # step2:
        # action: check current sensor
        # result:
        result = step_3(can_p) and result

        # step3:
        # action: set CMS emu current to new value
        # result:
        result = step_4(udp_p) and result
        result = step_5(udp_p) and result

        # step4:
        # action: check current sensor
        # result:
        result = step_6(can_p) and result
        time.sleep(2)



    ############################################
    # postCondition
    ############################################

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)


    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
