"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
Testscript Hilding MEPII
project:  BECM basetech MEPII
author:   hweiler (Hans-Klaus Weiler)
date:     2019-05-09
version:  1.0
reqprod:  76170

author:   HWEILER (Hans-Klaus Weiler)
date:     2020-08-13
version:  1.1
changes:  update for YML support

author:   DHJELM (Daniel Hjelm)
date:     2020-11-23
version:  2

title:

    ReadDataByIdentifier (22) - dataIdentifier(-s) ; 2

purpose:

    It shall be possible to read data from all ECUs

description:

    The ECU shall support the service readDataByIdentifer with the data
    parameter dataIdentifier(-s). The ECU shall implement the service
    accordingly:

    ### Supported sessions:

    The ECU shall support Service readDataByIdentifer in:

    - defaultSession
    - extendedDiagnosticSession
    - programmingSession, both primary and secondary bootloader

    ### Response time:

    Maximum response time for the service readDataByIdentifier (0x22) is 200
    ms.

    Effect on the ECU normal operation:

    The service readDataByIdentifier (0x22) shall not affect the ECU’s ability
    to execute non-diagnostic tasks.

    ### Entry conditions:

    The ECU shall not implement entry conditions for service
    readDataByIdentifier (0x22).

    ### Security access:

    The ECU are allowed to protect the service ReadDataByIdentifier (0x22),
    read by other than system supplier specific dataIdentifiers, by using the
    service securityAccess (0x27) only if approved by Volvo Car Corporation.

details:

    This test verifies the programmingSession mode.

"""

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanMFParam, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_2(can_p):
    """
    Teststep 2: send 1 requests - requires SF to send, MF for reply
    """

    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x21', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no" : 2,
        "purpose" : "Send 1 request - requires SF to send",
        "timeout" : 2,
        "min_no_messages" : -1,
        "max_no_messages" : -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)


    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        'block_size' : 0,
        'separation_time' : 0,
        'frame_control_delay' : 0, #no wait
        'frame_control_flag' : 48, #continue send
        'frame_control_auto' : False
        }
    SC.change_mf_fc(can_p["send"], can_mf_param)
    result = SUTE.teststep(can_p, cpay, etp)
    return result

def step_3(can_p):
    """
    Teststep 3: test if DIDs are included in reply
    """
    step_no = 3
    purpose = "test if requested DID are included in reply"

    SUTE.print_test_purpose(step_no, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")
    SC.update_can_messages(can_p)
    logging.debug("All can messages updated")
    logging.debug("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.debug("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.debug("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.debug("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")
    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='F121')
    return result


def step_4(can_p: CanParam): # pylint: disable=too-many-locals
    """
    Teststep 4: Send several requests at one time - requires SF to send, MF for reply
    """
    # Parameters for the teststep
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x21\xF1\x2A', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Send several requests at one time - requires SF to send",
        "timeout": 2,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0, #no wait
        "frame_control_flag": 48, #continue send
        "frame_control_auto": False
        }
    SC.change_mf_fc(can_p["send"], can_mf_param)
    result = SUTE.teststep(can_p, cpay, etp)
    return result

def step_5(can_p):
    """
    Teststep 5:  Verify if number for requests limited in programming session
    """
    step_no = 5
    purpose = "Verify if number for requests limited in programming session"

    SUTE.print_test_purpose(step_no, purpose)

    time.sleep(1)
    SC.clear_all_can_messages()
    logging.debug("all can messages cleared")
    SC.update_can_messages(can_p)
    logging.debug("all can messages updated")
    logging.debug("Step%s: messages received %s", step_no, len(SC.can_messages[can_p["receive"]]))
    logging.debug("Step%s: messages: %s\n", step_no, SC.can_messages[can_p["receive"]])
    logging.debug("Step%s: frames received %s", step_no, len(SC.can_frames[can_p["receive"]]))
    logging.debug("Step%s: frames: %s\n", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Test if string contains all IDs expected:")

    result = SUTE.test_message(SC.can_messages[can_p["receive"]],
                               teststring='037F223100000000')
    logging.info("Step%s: %s", step_no,
                 SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    # action: # Change to Programming session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 1)

    # step2:
    # action: send 1 request - requires SF to send, MF for reply
    # result: BECM reports default session
        result = result and step_2(can_p)

    # step 3: check if DID is included in reply
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_3(can_p)

    # step4:
    # action: send several requests at one time - requires SF to send, MF for reply
    # result: BECM reports default session
        result = result and step_4(can_p)

    # step 5: check if DIDs are included in reply including those from combined DID
    # action: check if expected DID are contained in reply
    # result: true if all contained, false if not
        result = result and step_5(can_p)

    # step6:
    # action: verify current session
    # result: BECM reports programming session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02', stepno=6)

    # step 7:
    # action: # Change to Default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, 7)
        time.sleep(1)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
