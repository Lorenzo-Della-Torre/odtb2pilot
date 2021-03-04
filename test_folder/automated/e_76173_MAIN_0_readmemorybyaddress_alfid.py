"""
testscript: ODTB2 MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2020-12-09
version:    1.0
reqprod:    76173

title:
    ReadMemoryByAddress (23) - addressAndLengthFormatIdentifier (ALFID) ; 1

purpose:
    To make it easier for VOLVO CAR CORPORATION tools, the ECU shall support
    standarized requests.

description:
    The ECU shall support the service ReadMemoryByAddress with the data
    parameter addressAndLengthFormatIdentifier set to one of the following
    values:
        -0x14
        -0x24

    The ECU shall support the data parameter in all sessions where the ECU
    supports the service ReadMemoryByAddress which is:
        - Default session & Extended session

    Programming session is not supported.

details:
    Each session asks to read 10 bytes of data from memory address 70000000h
    with both 0x14 and 0x24 set as ALFID.
    Default and extended sessions expects a positive response.
    Programming sessions expects a negative response.
"""

from datetime import datetime
import sys
import time
import logging
import inspect

import odtb_conf

from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanParam
from supportfunctions.support_can import CanTestExtra
from supportfunctions.support_can import CanPayload
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

DEF_SESSION = 'Default session'
PRG_SESSION = 'Programming session'
EXT_SESSION = 'Extended session'

def read_memory_by_address_0x14(can_p, session, step_no):
    """
    Step Read Memory By Address: Send ReadMemoryByAddress with
    ALFID = 0x14 and verify that the ECU replies.
    """
    if session == PRG_SESSION:
        purpose = \
            f"ALFID = 0x14 in {session}, verify a negative response."
    else:
        purpose = \
            f"ALFID = 0x14 in {session}, verify a positive response."

    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Read 10 bytes from memory position 0x70000000-0x7000000A using alfid id 0x14.
    cpay: CanPayload = {
        "payload": b'\x23\x14\x70\x00\x00\x00\x0A',
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    # Check if session is programming mode.
    if session == PRG_SESSION:
        result = evaluate_response(can_p, '037F23')
    else:
        result = evaluate_response(can_p, '100B63')

    return result

def read_memory_by_address_0x24(can_p, session, step_no):
    """
    Step Read Memory By Address: Send ReadMemoryByAddress with
    ALFID = 0x24 and verify that the ECU replies.
    """
    if session == PRG_SESSION:
        purpose = \
            f"ALFID = 0x24 in {session}, verify a negative response."
    else:
        purpose = \
            f"ALFID = 0x24 in {session}, verify a positive response."

    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Read 10 bytes from memory position 0x70000000-0x7000000A using alfid id 0x24.
    cpay: CanPayload = {
        "payload": b'\x23\x24\x70\x00\x00\x00\x00\x0A',
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    # Check if session is programming mode.
    if session == PRG_SESSION:
        result = evaluate_response(can_p, '037F23')
    else:
        result = evaluate_response(can_p, '100B63')

    return result

def print_nrc(can_p):
    """
    Get and log NRC (Negative return code).
    """
    logging.info("NRC: %s",
                 SUTE.pp_can_nrc(
                 SC.can_messages[can_p["receive"]][0][2][6:8]))

def evaluate_response(can_p, valid_data):
    """
    Log result and return data comparison result (true/false)
    """
    # Check if empty
    if not can_p["receive"]:
        logging.info("No data in can_p['receive']")
        return False

    nrc = SC.can_messages[can_p["receive"]][0][2][0:4] == '037F'
    result = SUTE.test_message(SC.can_messages[can_p["receive"]],
                               teststring=valid_data)
    if result:
        logging.info("Result teststep: True")
    else:
        logging.info("Result teststep: Failed")

    # Check if it was a negative return code. If so, print.
    if nrc:
        print_nrc(can_p)

    # If its not a NRC possible corrupt message.
    if not result and not nrc:
        logging.info("Unexpected data received: %s",
                     SC.can_messages[can_p["receive"]][0][2])
    # Log a new line
    logging.info(" ")
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(
        format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
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
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Make sure default session is set.
        # result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode1(can_p, 1)

        # step 2:
        # action: Send ReadMemoryByAddress(ALFID: 0x14)
        # result: ECU responds with positive message
        result = result and read_memory_by_address_0x14(can_p, DEF_SESSION, 2)

        # step 3:
        # action: Send ReadMemoryByAddress(ALFID: 0x24)
        # result: ECU responds with positive message
        result = result and read_memory_by_address_0x24(can_p, DEF_SESSION, 3)

        # step 4:
        # action: Change to extended session.
        # result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode3(can_p, 4)

        # step 5:
        # action: Send ReadMemoryByAddress(ALFID: 0x14)
        # result: ECU responds with positive message
        result = result and read_memory_by_address_0x14(can_p, EXT_SESSION, 5)

        # step 6:
        # action: Send ReadMemoryByAddress(ALFID: 0x24)
        # result: ECU responds with positive message
        result = result and read_memory_by_address_0x24(can_p, EXT_SESSION, 6)

        # step 7:
        # action: Change to programming session.
        # result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode2(can_p, 7)

        # step 8:
        # action: Send ReadMemoryByAddress(ALFID: 0x14)
        # result: ECU responds with negative message
        result = result and read_memory_by_address_0x14(can_p, PRG_SESSION, 8)

        # step 9:
        # action: Send ReadMemoryByAddress(ALFID: 0x24)
        # result: ECU responds with negative message
        result = result and read_memory_by_address_0x24(can_p, PRG_SESSION, 9)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
