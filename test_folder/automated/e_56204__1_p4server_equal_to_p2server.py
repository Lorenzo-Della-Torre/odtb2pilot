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
date:      2021-01-28
version:   1.0
reqprod:   56204

title:
    P4Server_max equal to P2Server_max ; 1

purpose:
    To define the behaviour when the P4Server_max is equal to P2Server_max

description:
    The server is not allowed to response with a negative response
    code 0x78 (requestCorrectlyReceived-ResponsePending) if P4Server_max
    is the same as P2Server_max.

    Note: The value of P2Server_max is defined in section Timing parameters.
    P4Server_max is defined for each diagnostic service in LC : VCC - UDS Services.

details:
    Send multiple service 23 requests without delay trying to provoke a NRC 78.
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

# address And Length Format Identifier (ALFID).
ALFID = b'\x24'

# Memory range allowed for reading 70000000 -> 7003BFFF.
ADDRESS = b'\x70\x00\x00\x00'

# Using ALFID 0x24 number of bytes to read needs to be 2 bytes.
NUM_BYTES = b'\x00\x20'

# Number of times to send the service.
NUM_OF_RESENDS = 100

def step_1(can_p):
    """
    Request service 23, try to provoke a NRC 78.
    If NRC 78 is received test returns false.
    """
    purpose = 'Request service 23, try and provoke NRC 78.'
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Construct the message
    service_call = bytearray(b'\x23')
    service_call = service_call + ALFID + ADDRESS + NUM_BYTES
    cpay: CanPayload = {
        "payload": service_call,
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    # Send service 23
    for _ in range(NUM_OF_RESENDS):
        SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)
        result = evaluate_response(can_p, valid_data='102163', log=False)
        if not result:
            if not evaluate_response(can_p, valid_data='037F2378'):
                # Don't care about any other messages, reset result and keep going.
                result = True
            else:
                # Negative return code 78 received.
                break

    time.sleep(1)
    return result

def print_nrc(can_p):
    """
    Get and log NRC (Negative return code).
    """
    logging.info("NRC: %s\n",
                 SUTE.pp_can_nrc(
                 SC.can_messages[can_p["receive"]][0][2][6:8]))

def evaluate_response(can_p, valid_data, log=True):
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
    if log:
        logging.info("Result: %s\n", result)

        # Check if it was a negative return code. If so, print.
        if result and nrc:
            print_nrc(can_p)

        # If its not result and not a NRC possible corrupt message.
        else:
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

    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # Step 1:
        # Action: Send service 23. Try to provoke NRC 78.
        # Result: No NRC 78 received. (True)
        result = result and step_1(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
