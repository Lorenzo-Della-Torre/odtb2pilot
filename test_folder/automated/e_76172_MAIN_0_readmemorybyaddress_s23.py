"""
testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2020-01-08
version:    1.0
reqprod:    76172

title:
    ReadMemoryByAddress (23) ; 1

purpose:
    ReadMemoryByAddress shall primarily be used during development or
    for validation data written by WriteMemoryByAddress.

description:
    The ECU shall support the service readMemoryByAddress if the ECU is
    involved in propulsion or safety functions in the vehicle.
    Otherwise, the ECU may support the service readMemoryByAddress.
    If implemented, the ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support Service readMemoryByAddress in:
    •	defaultSession
    •	extendedDiagnosticSession
    The ECU shall not support service readMemoryByAddress in programmingSession.

    Response time:
    Maximum response time for the service readMemoryByAddress (0x23) is P2Server_max.

    Effect on the ECU normal operation:
    The service readMemoryByAddress (0x23) shall not affect the
    ECU’s ability to execute non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service readMemoryByAddress (0x23).

    Security access:
    The ECU may protect service readMemoryByAddress by using the service
    securityAccess (0x27). At least shall memory areas, which are included
    as data parameters in a dataIdentifier, have the same level of security
    access protection as for reading with service readDataByIdentifier (0x22).

details:
    1. The script subscribes to a non-diagnostic signal.
    2. ReadMemoryByAddress is sent multiple times.
    3. Verify that the non-diagnostic signal is still being sent
       and was not interrupted by service 23.
    4. Verify response in default session and verify response time
       (p2server max + 30ms test environment jitter)
    5. Change to extended session and repeat previous step.
    6. Change to programming session and repeat step 4.
    Done.
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

# address And Length Format Identifier (ALFID).
ALFID = b'\x24'

# Memory range allowed for reading 70000000 -> 7003BFFF.
ADDRESS = b'\x70\x00\x00\x00'

# Using ALFID 0x24 number of bytes to read needs to be 2 bytes.
NUM_BYTES = b'\x00\x0A'

DEF_SESSION = 'Default session'
PRG_SESSION = 'Programming session'
EXT_SESSION = 'Extended session'

def read_memory_by_address(can_p, session, step_no, cyclical=False):
    """
    Step read_memory_by_address: Send ReadMemoryByAddress with global
    variables ALFID, ADDRESS, NUM_BYTES. Expect positive reply in
    default and extended session. Expect negative reply in programming
    session.
    """
    purpose = f'ReadMemoryByAddress (S23) in {session}.'

    etp: CanTestExtra = {
        "step_no": step_no,
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

    # If cyclical - send multiple times to keep the ECU
    # busy while non-diagnostic signal is being sent.
    if cyclical:
        for _ in range(0, 20):
            SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)
            result = result and evaluate_response(can_p, valid_data='100B63', log=False)

    # If programming session, expect NRC.
    if session == PRG_SESSION:
        result = result and evaluate_response(can_p, valid_data='037F23')
    else:
        result = result and evaluate_response(can_p, valid_data='100B63')

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

def verify_registred_signal(can_p_ex, num_frames, step_no):
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

def elapsed_time(can_p, p2server_max, session, jitter_testenv, step):
    """
    Elapsed time checks if
    ((time_received - time_sent) + test environment jitter) <= p2server_max

    Returns true / false
    """
    purpose = f"Verifying elapsed time between sent and received message in {session}."
    SUTE.print_test_purpose(step, purpose)

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

    logging.info("Result: %s\n", result)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(
        format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT,
                                               odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    # Jitter for the test environment 30ms
    jitter = 0.030

    # P2Server_max 50ms for default and extended session.
    p2_server_max = 0.050

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
        # Action: Change to default session.
        # Result: ECU responds with a positive message.
        result = result and SE10.diagnostic_session_control_mode1(can_p, 1)

        # Step 2:
        # Action: register a non-diagnostic signal.
        # Result: BECM send requested signals.
        result, can_p_ex, num_frames = result and register_non_diagnostic_signal(can_p, 2)

        # Step 3:
        # Action: send ReadMemoryByAddress cyclically.
        # Result: BECM responds with a positive message.
        result = result and read_memory_by_address(
            can_p, DEF_SESSION, 3, cyclical=True)

        # Step 4:
        # Action: Verify signal is still sent.
        # Result: BECM send requested signals.
        result = result and verify_registred_signal(
            can_p_ex, num_frames, 4)

        # Step 5:
        # Action: Send ReadMemoryByAddress in default session.
        # Result: ECU responds with positive message.
        result = result and read_memory_by_address(
            can_p, DEF_SESSION, 5)

        # Step 6:
        # Action: Calculate the time it took from sent to received message.
        # Result: Time is less or equal to p2server_max.
        result = result and elapsed_time(
            can_p, p2_server_max, DEF_SESSION, jitter, 6)

        # Step 7:
        # Action: Change to extended session.
        # Result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode3(can_p, 7)

        # Step 8:
        # Action: Send ReadMemoryByAddress in extended session.
        # Result: ECU responds with positive message.
        result = result and read_memory_by_address(
            can_p, EXT_SESSION, 8)

        # Step 9:
        # Action: Calculate the time it took from sent to received message.
        # Result: Time is less or equal to p2server_max.
        result = result and elapsed_time(
            can_p, p2_server_max, EXT_SESSION, jitter, 9)

        # Step 10:
        # Action: Change to programming session.
        # Result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode2(can_p, 10)

        # P2Server_max is 25ms in programming session.
        p2_server_max = 0.025

        # Step 11:
        # Action: Send ReadMemoryByAddress in programming session.
        # Result: ECU responds with negative message.
        result = result and read_memory_by_address(
            can_p, PRG_SESSION, 11)

        # Step 12:
        # Action: Calculate the time it took from sent to received message.
        # Result: Time is less or equal to p2server_max.
        result = result and elapsed_time(
            can_p, p2_server_max, PRG_SESSION, jitter, 12)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
