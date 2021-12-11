"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
testscript: Hilding MEPII
project:   BECM basetech MEPII
author:    GANDER10 (Gustav Andersson)
date:      2020-12-23
version:   1.0
reqprod:   68177

title:
    Active Diagnostic Session Data Record ; 1

purpose:
    To enable readout of the active diagnostic session.

description:
    A data record with identifier as specified in the
    table below shall be implemented exactly
    as defined in Carcom - Global Master Reference Database.

    Description	Identifier
    Active diagnostic session	F186

    •	It shall be possible to read the data record by
        using the diagnostic service specified in Ref
        [LC : Volvo Car Corporation - UDS Services -
        Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following
    sessions:
    •	Default session
    •	Programming session
            (which includes both primary and secondary bootloader)
    •	Extended Session

details:
    Sends ReadDataByIdentifier(F186) in all sessions and
    verifying a positive response and validates the data.
    In programming session both PBL and SBL are tested.
"""

from datetime import datetime
import sys
import time
import logging
import inspect

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_SBL import SupportSBL

SSBL = SupportSBL()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def read_data_by_identifier(can_p, session, boot, step):
    """
    Step read data by identifier (F186).
    Read and verify response from the different sessions.
    In programming both PBL and SBL.
    """
    if session == 'Programming session':
        purpose = f"ReadDataByIdentifier (F186) in {session} ({boot})."
    else:
        purpose = f"ReadDataByIdentifier (F186) in {session}"

    etp: CanTestExtra = {
        "step_no": step,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x86',
                                        b''),
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    if session == 'Default session':
        result = result and evaluate_response(can_p, '0462F18601')
    elif session == 'Programming session':
        result = result and evaluate_response(can_p, '0462F18602')
    elif session == 'Extended session':
        result = result and evaluate_response(can_p, '0462F18603')

    return result

def print_nrc(can_p):
    """
    Get and log NRC (Negative return code).
    """
    logging.info("NRC: %s\n",
                 SUTE.pp_can_nrc(
                 SC.can_messages[can_p["receive"]][0][2][6:8]))

def evaluate_response(can_p, valid_data):
    """
    Log result of data comparison (true/false)
    If it was a NRC - pretty print number and corresponding string
    If comparison is false and data does not contain a NRC log as unexpected.
    Finally, return result.
    """
    # Check if empty
    if not can_p["receive"]:
        logging.info("No data in can_p['receive']\n")
        return False

    nrc = SC.can_messages[can_p["receive"]][0][2][0:4] == '037F'
    result = SUTE.test_message(SC.can_messages[can_p["receive"]],
                               teststring=valid_data)
    # Log result
    logging.info("Result: %s\n", result)

    # Check if it was a negative return code. If so, print.
    if nrc:
        print_nrc(can_p)

    # If its not result and not a NRC possible corrupt message.
    if not result and not nrc:
        logging.info("Unexpected data received: %s\n",
                     SC.can_messages[can_p["receive"]][0][2])
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # Where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(
            odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
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
    SSBL.get_vbf_files()

    timeout = 200
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # Step 1:
        # Action: Make sure default session is set.
        # Result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode1(can_p, 1)

        # Step 2:
        # Action: Read active diagnostic session.
        # Result: ECU responds with a positive message.
        result = result and read_data_by_identifier(
            can_p, 'Default session', None, 2)

        # Step 3:
        # Action: Change to extended session.
        # Result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode3(can_p, 3)

        # Step 4:
        # Action: Read active diagnostic session.
        # Result: ECU responds with a positive message.
        result = result and read_data_by_identifier(
            can_p, 'Extended session', None, 4)

        # Step 5:
        # Action: Change to programming session.
        # Result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode2(can_p, 5)

        # Step 6:
        # Action: Read active diagnostic session in primary bootloader.
        # Result: ECU responds with a positive message.
        result = result and read_data_by_identifier(
            can_p, 'Programming session', 'Primary bootloader', 6)

        # Step 7:
        # Action: Activate secondary bootloader.
        # Result: ECU responds with a positive message.
        result = result and SSBL.sbl_activation(
            can_p, fixed_key='FFFFFFFFFF', stepno='7', purpose="Activate Secondary bootloader")

        # Step 8:
        # Action: Read active diagnostic session in secondary bootloader.
        # Result: ECU responds with a positive message.
        result = result and read_data_by_identifier(
            can_p, 'Programming session', 'Secondary bootloader', 8)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
