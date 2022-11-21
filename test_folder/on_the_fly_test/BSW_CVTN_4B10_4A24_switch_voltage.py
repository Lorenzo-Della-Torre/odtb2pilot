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

#NS_EMU_CMS = 'emu_CMS' #has to match name in interfaces.json
#ns_emu_cms = 'RpiGPIO'
ns_emu_cvtn = 'emu_CVTN'

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
        teststep 1: set CVTNemu voltage values via emulator interface
    """

    stepno = 1
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    ### replace code here to send UDP request
    # I2C relay card: Relay1 ON
    #logging.debug("I2C_Relais_1 on (time_diff: ) %s", time.time()-time_tsend)
    stub = udp_p["netstub"]

    cellvoltage_001 = 0
    cellvoltage_002 = 0
    cellvoltage_003 = 0
    cellvoltage_004 = 0

    cv_001 = bytes.fromhex('{:04X}'.format(cellvoltage_001))
    cv_002 = bytes.fromhex('{:04X}'.format(cellvoltage_002))
    cv_003 = bytes.fromhex('{:04X}'.format(cellvoltage_003))
    cv_004 = bytes.fromhex('{:04X}'.format(cellvoltage_004))

    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages01", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)

    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages02", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages03", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages04", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages05", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages06", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages07", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages08", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages09", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages10", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages11", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages12", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages13", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages14", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages15", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages16", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages17", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages18", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages19", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages20", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)


    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_001", udp_p["namespace"], cv_001)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_002", udp_p["namespace"], cv_002)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_003", udp_p["namespace"], cv_003)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_004", udp_p["namespace"], cv_004)

    #time_tsend = time.time()
    #time.sleep(SLEEPTIME)
    #result = SUTE.teststep(can_p, cpay, etp)

    return result


#MEP1 BECM DID CVTN Carcom:
#4124 CVTN 1 Voltages
#4A27 CVTN 2 Voltages
#4A29 CVTN 3 Voltages
#
#4A2F CVTN 9 Voltages

#4A30 Module 6 temperaturs sensors
#
#4A52 Module 40 temperature sensore
#4B10 Module 1 Cell Voltages
#
#4B2A Module 27 Cell Voltages
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

def step_2_cma(can_p):
    """
        teststep 2: request DID CMS 4B10 (MEP1 CMA Module 1 Cell Voltages)
    """

    stepno = 2
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4B\x10', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request BECM DID 4B10 CVTN Module 1 Cell Voltages",\
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
    if SUTE.test_message(SC.can_messages[can_p['receive']], '624B10'):
        logging.info("Reply contains 624B10 as expected.")

    logging.info("DID sent:              %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CVTN Module 1 Cell Voltages Voltage1: %s",
                 SC.can_messages[can_p['receive']][0][2][10:12])
    logging.info("CVTN Module 1 Cell Voltages Voltage2: %s",
                 SC.can_messages[can_p['receive']][0][2][12:14])
    logging.info("CVTN Module 1 Cell Voltages Voltage3: %s",
                 SC.can_messages[can_p['receive']][0][2][14:16])
    logging.info("CVTN Module 1 Cell Voltages Voltage4: %s",
                 SC.can_messages[can_p['receive']][0][2][16:18])

    return result

def step_3_cma(can_p):
    """
        teststep 2: request DID CMS 4A24 (MEP1 CMA CVTN 1 Voltages)
    """

    stepno = 2
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x24', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request BECM DID 4A24 CVTN 1 Voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received  %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 624A24
    #if SUTE.test_message(SC.can_messages[can_p['receive']], '62a244'):
    if SUTE.test_message(SC.can_messages[can_p['receive']], '624B10'):
        logging.info("Reply contains 624B10 as expected.")

    logging.info("DID sent:              %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CVTN 1 Cell Voltage 1: %s", SC.can_messages[can_p['receive']][0][2][10:12])
    logging.info("CVTN 1 Cell Voltage 2: %s", SC.can_messages[can_p['receive']][0][2][12:14])
    logging.info("CVTN 1 Cell Voltage 3: %s", SC.can_messages[can_p['receive']][0][2][14:16])
    logging.info("CVTN 1 Cell Voltage 4: %s", SC.can_messages[can_p['receive']][0][2][16:18])
    logging.info("CVTN 1 Busbar Voltage 5: %s", SC.can_messages[can_p['receive']][0][2][18:20])
    logging.info("CVTN 1 Cell Voltage 6: %s", SC.can_messages[can_p['receive']][0][2][20:22])
    logging.info("CVTN 1 Cell Voltage 7: %s", SC.can_messages[can_p['receive']][0][2][22:24])
    logging.info("CVTN 1 Cell Voltage 8: %s", SC.can_messages[can_p['receive']][0][2][24:26])
    logging.info("CVTN 1 Cell Voltage 9: %s", SC.can_messages[can_p['receive']][0][2][26:28])
    logging.info("CVTN 1 Busbar Voltage 10: %s", SC.can_messages[can_p['receive']][0][2][28:30])
    logging.info("CVTN 1 Cell Voltage 11: %s", SC.can_messages[can_p['receive']][0][2][30:32])
    logging.info("CVTN 1 Cell Voltage 12: %s", SC.can_messages[can_p['receive']][0][2][32:34])
    logging.info("CVTN 1 Cell Voltage 13: %s", SC.can_messages[can_p['receive']][0][2][34:36])
    logging.info("CVTN 1 Cell Voltage 14: %s", SC.can_messages[can_p['receive']][0][2][36:38])
    logging.info("CVTN 1 Busbar Voltage 15: %s", SC.can_messages[can_p['receive']][0][2][38:40])

    return result




def step_4(udp_p):
    """
        teststep 4: set CVTNemu voltage values via emulator interface
    """

    stepno = 4
    result = True

    logging.info("Teststep Nr.: %s", stepno)

    ### replace code here to send UDP request
    # I2C relay card: Relay1 ON
    #logging.debug("I2C_Relais_1 on (time_diff: ) %s", time.time()-time_tsend)
    stub = udp_p["netstub"]

    cellvoltage_001 = 0x1000
    cellvoltage_002 = 0x4000
    cellvoltage_003 = 0x6000
    cellvoltage_004 = 0x8000

    cv_001 = bytes.fromhex('{:04X}'.format(cellvoltage_001))
    cv_002 = bytes.fromhex('{:04X}'.format(cellvoltage_002))
    cv_003 = bytes.fromhex('{:04X}'.format(cellvoltage_003))
    cv_004 = bytes.fromhex('{:04X}'.format(cellvoltage_004))

    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages01", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)

    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages02", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages03", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages04", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages05", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages06", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages07", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages08", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages09", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages10", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages11", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages12", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages13", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages14", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages15", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages16", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages17", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages18", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages19", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltages20", udp_p["namespace"],
                                    cv_001 + cv_002 + cv_003 + cv_004)

    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_001", udp_p["namespace"], cv_001)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_002", udp_p["namespace"], cv_002)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_003", udp_p["namespace"], cv_003)
    SEMU_UDP.t_send_udp_request_hex(stub, "CellVoltage_004", udp_p["namespace"], cv_004)

    #time_tsend = time.time()
    #time.sleep(SLEEPTIME)
    #result = SUTE.teststep(can_p, cpay, etp)

    return result



def step_5_cma(can_p):
    """
        teststep 5: request DID CMS 4B10 (MEP1 CMA Module 1 Cell Voltages)
    """

    stepno = 5
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4B\x10', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request BECM DID 4B10 CVTN Module 1 Cell Voltages",\
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
    if SUTE.test_message(SC.can_messages[can_p['receive']], '624B10'):
        logging.info("Reply contains 624B10 as expected.")

    logging.info("DID sent:              %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CVTN Module 1 Cell Voltages Voltage1: %s",
                 SC.can_messages[can_p['receive']][0][2][10:12])
    logging.info("CVTN Module 1 Cell Voltages Voltage2: %s",
                 SC.can_messages[can_p['receive']][0][2][12:14])
    logging.info("CVTN Module 1 Cell Voltages Voltage3: %s",
                 SC.can_messages[can_p['receive']][0][2][14:16])
    logging.info("CVTN Module 1 Cell Voltages Voltage4: %s",
                 SC.can_messages[can_p['receive']][0][2][16:18])

    return result

def step_6_cma(can_p):
    """
        teststep 6: request DID CMS 4A24 (MEP1 CMA CVTN 1 Voltages)
    """

    stepno = 6
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x24', b''),
                        "extra" : b''
                       }
    SIO.parameter_adopt_teststep(cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request BECM DID 4A24 CVTN 1 Voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.parameter_adopt_teststep(etp)

    result = SUTE.teststep(can_p, cpay, etp)

    #show what was received:
    logging.info("can_mess_received  %s", SC.can_messages[can_p["receive"]])

    #if you want to test if received message contains a certain string:
    #here: if reply should be a posivite reply, so it contains 624A24
    #if SUTE.test_message(SC.can_messages[can_p['receive']], '62a244'):
    if SUTE.test_message(SC.can_messages[can_p['receive']], '624B10'):
        logging.info("Reply contains 624B10 as expected.")

    logging.info("DID sent:              %s", SC.can_messages[can_p['receive']][0][2][6:10])
    logging.info("CVTN 1 Cell Voltage 1: %s", SC.can_messages[can_p['receive']][0][2][10:12])
    logging.info("CVTN 1 Cell Voltage 2: %s", SC.can_messages[can_p['receive']][0][2][12:14])
    logging.info("CVTN 1 Cell Voltage 3: %s", SC.can_messages[can_p['receive']][0][2][14:16])
    logging.info("CVTN 1 Cell Voltage 4: %s", SC.can_messages[can_p['receive']][0][2][16:18])
    logging.info("CVTN 1 Busbar Voltage 5: %s", SC.can_messages[can_p['receive']][0][2][18:20])
    logging.info("CVTN 1 Cell Voltage 6: %s", SC.can_messages[can_p['receive']][0][2][20:22])
    logging.info("CVTN 1 Cell Voltage 7: %s", SC.can_messages[can_p['receive']][0][2][22:24])
    logging.info("CVTN 1 Cell Voltage 8: %s", SC.can_messages[can_p['receive']][0][2][24:26])
    logging.info("CVTN 1 Cell Voltage 9: %s", SC.can_messages[can_p['receive']][0][2][26:28])
    logging.info("CVTN 1 Busbar Voltage 10: %s", SC.can_messages[can_p['receive']][0][2][28:30])
    logging.info("CVTN 1 Cell Voltage 11: %s", SC.can_messages[can_p['receive']][0][2][30:32])
    logging.info("CVTN 1 Cell Voltage 12: %s", SC.can_messages[can_p['receive']][0][2][32:34])
    logging.info("CVTN 1 Cell Voltage 13: %s", SC.can_messages[can_p['receive']][0][2][34:36])
    logging.info("CVTN 1 Cell Voltage 14: %s", SC.can_messages[can_p['receive']][0][2][36:38])
    logging.info("CVTN 1 Busbar Voltage 15: %s", SC.can_messages[can_p['receive']][0][2][38:40])

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
    #Read YML parameter for current function (get it from stack)
    SIO.parameter_adopt_teststep(can_p)

    ## where to connect to signal_broker
    #can_p: CanParam = {
    #    "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
    #    "send" : "Vcu1ToBecmFront1DiagReqFrame",
    #    "receive" : "BecmToVcu1Front1DiagResFrame",
    #    "namespace" : SC.nspace_lookup("Front1CANCfg0")
    #    }
    ##replace can_p parameters to project specific ones:
    #SIO.parameter_adopt_teststep(can_p)

    udp_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup(ns_emu_cvtn)
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

        # step2:
        # action: check current sensor
        # result:
        #result = step_2(can_p) and result
        result = step_2_cma(can_p) and result
        # step3:
        # action: set CVTN emu Voltage to new value
        # result:
        result = step_3_cma(can_p) and result

        # step4:
        # action: set CMS emu current
        # result:
        result = step_4(udp_p) and result

        # step2:
        # action: check current sensor
        # result:
        #result = step_2(can_p) and result
        result = step_5_cma(can_p) and result
        # step3:
        # action: set CVTN emu Voltage to new value
        # result:
        result = step_6_cma(can_p) and result
        time.sleep(2)



    ############################################
    # postCondition
    ############################################

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)


    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
