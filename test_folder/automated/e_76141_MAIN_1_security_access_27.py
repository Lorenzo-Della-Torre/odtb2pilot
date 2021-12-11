"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2020-12-12
version:    1.0
reqprod:    76141

title:
    SecurityAccess (27) ; 2

purpose:
    Define availability of SecurityAccess service.

description:
    The ECU shall implement SecurityAccess (0x27) service accordingly:

    Supported session:
        *   SecurityAccess shall not be supported in the defaultSession.

        *   The services securityAccess – requestSeed 0x01 and sendKey
            0x02 shall only be supported in programmingSession, both
            primary and secondary bootloader.

        *   The services securityAccess – requestSeed in the range
            0x03-0x41 and sendKey in the range 0x04-0x42 may be
            supported by the ECU but only in the extendedDiagnosticSession.

    SecurityAccess algorithm:
    The requestSeed range 0x01-0x41 and corresponding sendKey
    range 0x02-0x42 shall use the standardized SecurityAccess
    algorithm specified by Volvo Car Corporation.

    The requestSeed range 0x61-0x7E and corresponding sendKey
    range 0x62-0x7F are not allowed to use the standardized
    SecurityAccess algorithm specified by Volvo Car Corporation
    but shall use another SecurityAccess algorithm provided by
    the implementer. The number of bytes of the data parameter
    securityKey is specified by the implementer.
    Note that VCC tools are not required to support the range.

    P4Server_max response time:
    Maximum response time for the service
    securityAccess (0x27) is P2Server_max.

    Effect on the ECU operation:
    The service securityAccess (0x27) shall not affect
    the ECU’s ability to execute non-diagnostic tasks.

    Entry conditions:
    Entry conditions for service SecurityAccess (0x27) are not allowed.


details:
    The secondary bootloader wont request the security access since it is
    already in an unlocked state after flashing the SBL.

    Verify that the service wont interfere with the ECU ability to process
    non-diagnostic tasks.
    Verify that default session gives a negative response.
    Verify that programming session (PBL) gives a positive response on
        RequestSeed 0x01
        SendKey 0x02
    Verify that extended session gives a negative response for all
    combinations of RequestSeed and Sendkey except
        RequestSeed 0x05
        SendKey 0x06

    Measure the time for each response in the above mentioned sessions,
    make sure that they are <= p2server_max.

"""
from datetime import datetime

import time
import inspect
import sys
import logging
import odtb_conf

from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service11 import SupportService11

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SSA = SupportSecurityAccess()
SSBL = SupportSBL()

PBL = 'Primary bootloader'
DEF_SESSION = 'Default session'
PRG_SESSION = 'Programming session'
EXT_SESSION = 'Extended session'

def security_access_def_session(can_p, step_no):
    """
    Request seed in default session, expect negative response.
    Do not request SendKey since requestSeed will always give
    a negative response.
    Evaluate the response and measure the time it took to receive
    the response.
    """
    purpose = "Request seed (0x01) in default session."
    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Send RequestSeed with 0x01.
    cpay: CanPayload = {
        "payload": b'\x27\x01',
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    # Send message
    result = SUTE.teststep(can_p, cpay, etp)

    # Not supported, expect negative response.
    result = result and evaluate_response(can_p, '037F27')

    # Make sure time from sent message to received < max limit.
    result = result and elapsed_time(can_p, DEF_SESSION)

    return result

def security_access_prg_session(can_p, step_no):
    """
    Request seed and Send key in programming session,
    expect positive response for values
        RequestSeed: 0x01
        SendKey: 0x02.
    Evaluate the response and measure the time it took
    to receive the response.
    """
    purpose = "RequestSeed (0x01) in programming session (Primary bootloader)."
    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # RequestSeed 0x01
    cpay: CanPayload = {
        "payload": b'\x27\x01',
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    # Send message.
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and evaluate_response(can_p, '6701')

    # Make sure time from sent message to received < max limit.
    result = result and elapsed_time(can_p, PRG_SESSION)
    if not result:
        return False

    # Extract seed from the reply.
    request_seed = SC.can_messages[can_p["receive"]][0][2][6:12]
    logging.debug("Received data: %s", SC.can_messages[can_p["receive"]][0][2])
    logging.debug("Extracted seed: %s", request_seed)

    # Modify received seed with the security access algorithm.
    modified_seed = SSA.set_security_access_pins(request_seed,
                                                 fixed_key='FFFFFFFFFF')

    # Security access service with send key 0x02
    service_call = bytearray(b'\x27\x02')

    # Append the modified seed to the service call
    service_call += modified_seed

    purpose = "SendKey (0x02) in programming session (Primary bootloader)."
    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # SendKey 0x02.
    cpay: CanPayload = {
        "payload": service_call,
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    # Send message.
    result = result and SUTE.teststep(can_p, cpay, etp)
    result = result and evaluate_response(can_p, '6702')

    time.sleep(1)

    # Make sure time from sent message to received < max limit.
    result = result and elapsed_time(can_p, PRG_SESSION)

    return result

def security_access_ext_session(can_p, step_no):
    """
    Loop through the following values for each
    RequestSeed and SendKey
        - Request seed 0x03 - 0x41
        - SendKey 0x04 - 0x42
    Expect RequestSeed 0x05 and SendKey 0x06 to pass.
    Finally, measure the time for ECU to respond.
    """
    SUTE.print_test_purpose("Purpose: Security access in extended session.", step_no)
    result = True
    se27 = b'\x27'
    hex_counter = 3

    # Initialize the RequestSeed list
    r_seed = []
    for i in range(0x03, 0x41 + 1):
        r_seed.append(se27 + i.to_bytes((i.bit_length() + 7) // 8 or 1, 'big'))

    # Initialize the SendKey list
    s_key = []
    for i in range(0x04, 0x42 + 1):
        s_key.append(se27 + i.to_bytes((i.bit_length() + 7) // 8 or 1, 'big'))

    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : "",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    list_length = len(s_key)
    # Loop through all seed and key combinations.
    # Make sure 0x05 gives a positive response.
    for i in range(0, list_length):
        etp: CanTestExtra = {
            "step_no": step_no,
            "purpose" : f"RequestSeed: {hex(hex_counter).upper()}",
            "timeout" : 1,
            "min_no_messages" : -1,
            "max_no_messages" : -1
        }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

        # Send Request seed.
        cpay: CanPayload = {
            "payload": r_seed[i],
            "extra": ''
        }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

        # Send message
        SUTE.teststep(can_p, cpay, etp)

        if i == 2: # RequestSeed 0x05
            result = result and evaluate_response(can_p, '056705')
        else:
            result = result and evaluate_response(can_p, '037F')
        if not result:
            return False

        # Extract seed from the reply.
        request_seed = SC.can_messages[can_p["receive"]][0][2][6:12]
        logging.debug("Received data: %s", SC.can_messages[can_p["receive"]][0][2])
        logging.debug("Extracted seed: %s", request_seed)

        # Modify received seed with the security algorithm.
        modified_seed = SSA.set_security_access_pins(request_seed,
                                                     fixed_key='7D122F43AF')
        logging.debug("Modified seed: %s", modified_seed)

        # Append the modified seed to the service call
        s_key[i] += modified_seed

        etp: CanTestExtra = {
            "step_no": step_no,
            "purpose" : f"SendKey: {hex(hex_counter + 1).upper()}",
            "timeout" : 1,
            "min_no_messages" : -1,
            "max_no_messages" : -1
        }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

        # Send 'SendKey'
        cpay: CanPayload = {
            "payload": s_key[i],
            "extra": ''
        }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

        # Send message
        SUTE.teststep(can_p, cpay, etp)

        if i == 2: # SendKey 0x06
            result = result and evaluate_response(can_p, '0267')
        else:
            result = result and evaluate_response(can_p, '037F')
        hex_counter += 1

    # Finally measure the time for the response.
    result = result and elapsed_time(can_p, EXT_SESSION)
    return result

def security_access_cyclically(can_p, step_no):
    """
    Step request seed cyclically in extended session.
    """
    purpose = "Request seed cyclically (0x05) in extended session."
    etp: CanTestExtra = {
        "step_no": step_no,
        "purpose" : purpose,
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    # Send Request seed with 0x01.
    cpay: CanPayload = {
        "payload": b'\x27\x05',
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    for _ in range(0, 20):
        SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)
        result = result and evaluate_response(can_p, valid_data='056705', log=False)

    result = result and evaluate_response(can_p, valid_data='056705')
    return result

def print_nrc(can_p):
    """
    Get and log NRC (Negative return code).
    """
    logging.info("NRC: %s",
                 SUTE.pp_can_nrc(
                 SC.can_messages[can_p["receive"]][0][2][6:8]))

def evaluate_response(can_p, valid_data='', log=True):
    """
    Log result of data comparison (true/false)
    If it was a NRC - pretty print number and corresponding string
    If comparison is false and data does not contain a NRC log as unexpected.
    Finally, return result.
    """
    # Check if empty
    if not can_p["receive"]:
        logging.info("No data in can_p['receive']")
        return False

    nrc = SC.can_messages[can_p["receive"]][0][2][0:4] == '037F'
    result = SUTE.test_message(SC.can_messages[can_p["receive"]],
                               teststring=valid_data)

    # Check if it was a negative return code. If so, print.
    if result and nrc:
        print_nrc(can_p)

    # If its not result and not a NRC, possible corrupt message.
    if not result and not nrc:
        logging.info("Unexpected data received: %s\n",
                     SC.can_messages[can_p["receive"]][0][2])
    # Log result
    if log:
        logging.info("Result: %s\n", result)

    return result

def register_non_diagnostic_signal(can_p, step_no):
    """
    Register a non diagnostic signal.
    """
    etp: CanTestExtra = {
        "step_no" : "",
        "purpose" : "",
        "timeout" : 15,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    can_p_ex: CanParam = {
        "netstub" : SC.connect_to_signalbroker(
            odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "ECMFront1Fr02",
        "receive" : "BECMFront1Fr02",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)

    purpose = 'Register a non-diagnostic signal.'
    SUTE.print_test_purpose(step_no, purpose)

    # Subscribe to signal
    SC.subscribe_signal(can_p_ex, etp["timeout"])
    time.sleep(1)

    SC.clear_all_can_messages()
    logging.debug("All can messages cleared")

    SC.clear_all_can_frames()
    SC.update_can_messages(can_p)
    logging.debug("All can messages updated")

    time.sleep(4)
    num_frames = len(SC.can_frames[can_p_ex["receive"]])
    logging.debug("Number of frames received: %s", num_frames)

    # Check if any frames were received
    result = (len(SC.can_frames[can_p_ex["receive"]]) > 10)

    logging.info("Result: %s\n", result)
    return result, can_p_ex, num_frames

def verify_registered_signal(can_p_ex, num_frames, step_no):
    """
    Verify subscribed signal is is still sent.
    """
    purpose = "Verify subscribed non-diagnostic signal is still sent."
    SUTE.print_test_purpose(step_no, purpose)

    SC.clear_all_can_frames()
    SC.update_can_messages(can_p_ex)

    time.sleep(4)

    result = ((len(SC.can_frames[can_p_ex["receive"]]) + 50) >\
              num_frames >\
              (len(SC.can_frames[can_p_ex["receive"]]) - 50))

    logging.info("Result: %s\n", result)
    return result

def elapsed_time(can_p, session):
    """
    Elapsed time checks if
    ((time_received - time_sent) + test environment jitter) <= p2server_max

    Returns true / false
    """
    # Test environment jitter estimated at 30ms.
    jitter_testenv = 0.030

    # P2Server_max is 50ms in default and extended, 25ms in programming.
    if session == PRG_SESSION:
        p2server_max = 0.025
    else:
        p2server_max = 0.050

    t_sent = float(SC.can_frames[can_p["send"]][0][0])
    t_received = float(SC.can_frames[can_p["receive"]][0][0])

    t_elapsed = (t_received - t_sent)
    t_allowed = (p2server_max + jitter_testenv)

    if t_elapsed <= t_allowed:
        result = True
    else:
        logging.info("Failed: Response received outside time limit! \
            \n Allowed: %s\n Actual: %s", \
            round(t_allowed, 3), round(t_elapsed, 3))
        result = False

    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

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
    SSBL.get_vbf_files()
    timeout = 200
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # Step 1:
        # Action: Change to extended session.
        # Result: ECU responds with a positive message.
        result = result and \
            SE10.diagnostic_session_control_mode3(can_p, 1)

        # Step 2:
        # Action: Register a non-diagnostic signal.
        # Result: BECM send requested signals.
        result, can_p_ex, num_frames = result and \
            register_non_diagnostic_signal(can_p, 2)

        # Step 3:
        # Action: Send security access requestSeed cyclically
        # Result: Positive replies for all requests.
        result = result and \
            security_access_cyclically(can_p, 3)

        # Step 4:
        # Action: Verify signal is still sent.
        # Result: BECM send requested signals.
        result = result and \
            verify_registered_signal(can_p_ex, num_frames, 4)

        # Step 5:
        # Action: Security access in extended session and verify response time.
        # Result: Positive reply from becm.
        result = result and \
            security_access_ext_session(can_p, 5)

        # Step 6:
        # Action: Change to default session
        # Result: Positive reply from becm
        result = result and \
            SE10.diagnostic_session_control_mode1(can_p, 6)

        # Step 7:
        # Action: Security access in default session and verify response time.
        # Result: Negative reply from becm
        result = result and \
            security_access_def_session(can_p, 7)

        # Step 8:
        # Action: Change to programming session
        # Result: Positive reply from becm
        result = result and \
            SE10.diagnostic_session_control_mode2(can_p, 8)

        # Step 9:
        # Action: Security access in programming session
        #         (Primary bootloader) and verify response time.
        # Result: Positive reply from becm
        result = result and \
            security_access_prg_session(can_p, 9)

        # Step 10:
        # Action: Active secondary bootloader
        # Result: Positive reply from becm
        result = result and SSBL.sbl_activation(
            can_p, fixed_key='FFFFFFFFFF', stepno='11', purpose='Activate secondary bootloader')

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()

# end_of_file
