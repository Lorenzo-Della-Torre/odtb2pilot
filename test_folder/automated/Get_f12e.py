"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-06-22
# version:  1.0

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from hilding.dut import Dut

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SC_CARCOM = SupportCARCOM()


'''def step_1(can_p: CanParam):
    """
    Teststep 2: Request APP PN while in Mode 1
    """
    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        b'\xF1\x2E', b''),
                        "extra": ''
                       }
    etp: CanTestExtra = {"step_no": 2,
                         "purpose": "Service22: Request APP PN while in Mode1",
                         "timeout": 1,
                         "min_no_messages": -1,
                         "max_no_messages": -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s", etp["step_no"],
                  SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s", etp["step_no"],
                  SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F125: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F125')
        if not pos1 == -1:
            logging.info("Primary Bootloader Software Part Number %s\n",
                         SUTE.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F125)")
        result = False
    return result

def step_3(can_p: CanParam):
    """
    Teststep 3: SE22: AUTOSAR BSW Vendor IDs and Cluster Versions
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x26', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 3,
                         "purpose" : "SE22: AUTOSAR BSW Vendor IDs and Cluster Versions",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F126: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F126')
        if not pos1 == -1:
            logging.info("Autosar BSW Cluster Versions (no PrettyPrint)\n")
        else:
            result = False
    else:
        logging.info("Could not read DID F126)")
        result = False
    return result

def step_6(can_p: CanParam):
    """
    Teststep 6: Service22: F12C ECU Software Structure Part Number
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x2C', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 6,
                         "purpose" : "Service22: F12C ECU Software Structure Part Number",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F12C: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F12C')
        if not pos1 == -1:
            logging.info("ECU Software Structure Part Number %s\n",
                         SUTE.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F12C)")
        result = False
    return result'''

def step_7(can_p: CanParam):
    """
    Teststep 7: Service22: F12E ECU Software Part Numbers
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x2E', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 7,\
                         "purpose" : "Service22: F12E ECU Software Part Numbers",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F12E: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F12E')
        if not pos1 == -1:
            logging.info("ECU Software Part Numbers %s\n",
                         SUTE.pp_partnumber(message[pos1+6: pos1+20], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F12E)")
        result = False
    return result

'''def step_8(can_p: CanParam, sa_keys):
    """
    Teststep 8: Activate SBL
    """
    step_no = 8
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(can_p,\
                                 sa_keys,
                                 step_no, purpose)
    return result

def step_10(can_p: CanParam):
    """
    Teststep 10: PBL DB Part Number
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x21', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 10,
                         "purpose" : "Service22: F121 Primary Bootloader Diagnostic Database "\
                            "Part Number",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F121: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F121')
        if not pos1 == -1:
            logging.info("Primary Bootloader Diagnostic Database %s\n",
                         SUTE.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F121")
        result = False
    return result

def step_11(can_p: CanParam):
    """
    Teststep 11: Primary Bootloader Software Part Number
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x25', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 11,
                         "purpose" : "Service22: F125 Primary Bootloader Software Part Number",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F125: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F125')
        if not pos1 == -1:
            logging.info("Primary Bootloader Software Part Number %s\n",
                         SUTE.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F125)")
        result = False
    return result

def step_12(can_p: CanParam):
    """
    Teststep 12: ECU Software Structure Part Number
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x2C', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 12,
                         "purpose" : "Service22: F12C ECU Software Structure Part Number",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F12C: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F12C')
        if not pos1 == -1:
            logging.info("ECU Software Structure Part Number %s\n",
                         SUTE.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F12C)")
        result = False
    return result

def step_13(can_p: CanParam):
    """
    Teststep 13: F12E ECU Software Part Numbers
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x2E', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 13,
                         "purpose" : "Service22: F12E ECU Software Part Numbers",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F12E: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F12C')
        if not pos1 == -1:
            logging.info("ECU Software Structure Part Number %s\n",
                         SUTE.pp_partnumber(message[pos1+4: pos1+18], message[pos1:pos1+4]))
        else:
            result = False
    else:
        logging.info("Could not read DID F12E)")
        result = False

    return result'''

def run():
    """
    Run - Call other functions from here
    """

    dut = Dut()
    # start logging
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # where to connect to signal_broker
    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': dut.conf.platforms[platform]['signal_send'],
        'receive': dut.conf.platforms[platform]['signal_receive'],
        'namespace': dut.conf.platforms[platform]['namespace'],
        'signal_periodic': dut.conf.platforms[platform]['signal_periodic'],
        'signal_tester_preset': dut.conf.platforms[platform]['signal_tester_present'],
        'wakeup_frame': dut.conf.platforms[platform]['wakeup_frame'],
        'protocol': dut.conf.platforms[platform]['protocol'],
        'framelength_max': dut.conf.platforms[platform]['framelength_max'],
        'padding': dut.conf.platforms[platform]['padding']
        }
    #Read YML parameter for current function (get it from stack)
    SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################


    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 180
    result = PREC.precondition(can_p, timeout)

    #Init parameter for SecAccess Gen1 / Gen2
    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    sa_keys = {
        "SecAcc_Gen" : dut.conf.platforms[platform]['SecAcc_Gen'],
        "fixed_key": dut.conf.platforms[platform]["fixed_key"],
        "auth_key": dut.conf.platforms[platform]["auth_key"],
        "proof_key": dut.conf.platforms[platform]["proof_key"]
    }

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: verify combined did EDA0 in default session
        # result: BECM sends positive reply with PN as serial numbers as expected
        '''result = SE22.read_did_eda0(can_p, stepno='1')

        # step 2:
        # action: Request PBL PN while in Mode 1
        # result: BECM sends requested PN
        result = step_2(can_p) and result

        # step 3:
        # action: SE22: AUTOSAR BSW Vendor IDs and Cluster Versions
        # result: BECM sends requested IDs
        result = result and step_3(can_p)

        # step 4:
        # action: Switch to programming mode
        # result: BECM sends positive reply
        result = SE10.diagnostic_session_control_mode2(can_p, stepno=4) and result

        # step 5:
        # action: request_did_eda0
        # result: BECM sends requested IDs
        result = SE22.read_did_eda0(can_p, stepno='5') and result

        # step 6:
        # action: ervice22: F12C ECU Software Structure Part Number
        # result: BECM sends requested IDs
        #result = step_6(can_p) and result'''

        # step 7:
        # action: Service22: F12E ECU Software Part Numbers
        # result: BECM sends requested IDs
        #result = step_7(can_p) and result

        # F12E only defined in MEP2 PBL
        step_7(can_p)

        # step 8:
        # action: activate SBL
        # result:
        #result = step_8(can_p, sa_keys) and result

        # step 9:
        # action: request_did_eda0
        # result: BECM sends requested IDs
        #result = SE22.read_did_eda0(can_p, stepno='9') and result


        # Next steps left commented out:
        # Should be tested when implemented in MEP2

        # step 10:
        # action: F121 Primary Bootloader Diagnostic Database Part Number
        # result: BECM sends requested PN
        #result = step_10(can_p) and result

        # step 11:
        # action: F125 Primary Bootloader Software Part Number
        # result:
        #result = step_11(can_p) and result

        # step 12:
        # action: Service22: F12C ECU Software Structure Part Number
        # result:
        #result = step_12(can_p) and result

        # step 13:
        # action: F12E ECU Software Part Numbers
        # result:
        #result = step_13(can_p) and result

        # F12E only defined in MEP2 SBL
        #step_13(can_p)

    ############################################
    # postCondition
    ############################################

    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    run()
