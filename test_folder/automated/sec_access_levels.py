"""
/*********************************************************************************/



Copyright



/*********************************************************************************/


reqprod:
version:
title:

purpose: >
    Test Security Access Area 11

description: >
    nil

details: >
    nil
"""

import logging
import time
from hilding.dut import DutTestError
from hilding.dut import Dut
from hilding.conf import Conf
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_carcom import SupportCARCOM

SIO = SupportFileIO()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SSA = SupportSecurityAccess()
CNF = Conf()

#DID Secret Key For Immobilizer Target #1
IMMO = b'\x41\xD0'
IMMO_99 = IMMO + b'\x99'*32
IMMO_55 = IMMO + b'\x55'*32
#Routine request set vehicle speed limit to 30km/h
ROUTINE_REQUEST = b'\x01\x40\x03\x1E'

def routine_control_request_speed_30km(dut):
    """
    Action:
    request routine control speed limit to 30 km/h
    Expected result:
    positive response for request routine control
    """
    # Preparing routine control request payload 31010231 + (Security access level)
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", ROUTINE_REQUEST, b'')

    response = dut.uds.generic_ecu_call(payload)
    logging.info("Response from routine control: %s", response.raw)

    return response.raw

def write_immo_code(dut):
    """
    Action:
    write immo code depending on default value
    expected result:
    write immo request response is positive
    output:
    raw response for write immo request
    """
    #
    result = True
    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", IMMO, b'')

    response_read = dut.uds.generic_ecu_call(payload)
    logging.info("Response from read immo before change: %s", response_read.raw)

    if '6241D055' in response_read.raw:
        payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", IMMO_99, b'')
        response_write = dut.uds.generic_ecu_call(payload)
    elif '6241D099' in response_read.raw:
        payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", IMMO_55, b'')
        response_write = dut.uds.generic_ecu_call(payload)

    elif '7F' in response_read.raw:
        logging.info("Conditions not corrects on reading: NRC")
        result = False

    if '6E41D0' not in response_write.raw:
        logging.info("IMMO code has not been written")
        result = False

    elif '7F' in response_write.raw:
        logging.info("Conditions not corrects on writing: NRC")
        result = False

    return result, response_read.raw

def read_immo_code(dut, response_read):
    """
    input:
    1- default value of immo code
    Action:
    verify immo code has been changed from default value
    expected result:
    immo code has been changed form default value
    """

    result = True
    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", IMMO, b'')

    response = dut.uds.generic_ecu_call(payload)
    logging.info("Response from read immo after change: %s", response.raw)

    if '6241D055' in response_read:
        if '6241D099' not in response.raw:
            logging.info("IMMO code has not been written")
            result = False
        #Restore original IMMO code
        payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", IMMO_55, b'')
        dut.uds.generic_ecu_call(payload)
    elif '6241D099' in response_read:
        if '6241D055' not in response.raw:
            logging.info("IMMO code has not been written")
            result = False
        #Restore original IMMO code
        payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", IMMO_99, b'')
        dut.uds.generic_ecu_call(payload)
    elif '7F' in response.raw:
        logging.info("Conditions not corrects: NRC")
        result = False

    return result

def step_1(dut: Dut):
    """
    action:
    Set ECU to extended session and security access
    Routine vehicle speed limit, change to 30 km/h
    expected_result:
    Security access should be successful in extended session for level 31
    Speed limit change request should be positive
    """
    # Set ECU in extended session
    dut.uds.set_mode(3)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey_level\
        (dut, 49, sa_keys=dut.conf.default_rig_config)

    if result:
        logging.info("Security access successful in extended session level 31")

        response = routine_control_request_speed_30km(dut)

        # Extract last 2 bytes of response which is authentication method
        if response[2:4] == '71':
            logging.info("Test Succeed: positive response for routine request speed 30km/h")
        else:
            logging.error("Test Failed: negative response for routine request speed 30km/h")
            result = False
    else:
        logging.error("Test Failed: Unable to unlock ECU in extended session level 31")

    return result

def step_2(dut:Dut):
    """
    action:
    Set ECU to extended session without security access
    Routine vehicle speed limit, change to 30 km/h
    expected_result:
    Speed limit change request should be reply with NRC
    """
    #set mode to application
    dut.uds.set_mode(1)

    # Sleep time to avoid NRC37
    time.sleep(2)

    response = routine_control_request_speed_30km(dut)

    # Expecting 7F3133 in response.raw[2:4] for negative response of routine control
    if response[2:8] == '7F3133':
        logging.info("Test Succeed: negative response\
                      securityAccessDenied for routine request speed 30km/h")
        # Extract last 2 bytes of response which is authentication method
        return True

    logging.info("Test Failed: response not NRC:\
                  securityAccessDenied for routine request speed 30km/h")
    return False

def step_3(dut: Dut):
    """
    action:
    Set ECU to extended session and security access
    Change immo code
    expected_result:
    Security access should be successful in extended session for level 11
    Immo code has been successfully changed
    """

    #sa_keys = SSA.set_keys(CNF.default_rig_config)

    # Set ECU in extended session
    dut.uds.set_mode(3)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey_level\
        (dut, 17, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: Unable to unlock ECU in extended session level 11")
        return False
    logging.info("Security access successful in extended session level 11 ")

    result_write, response_read = write_immo_code(dut)

    if not result_write:
        logging.error("Test Failed: Unable to send write immo code request")
        return False
    logging.info("Write immo code request sent successfully")

    result_read = read_immo_code(dut, response_read)

    if not result_read:
        logging.error("Test Failed: Unable to write immo code")
        return False

    logging.info("immo code written successfully")

    return True

def run():
    """
    Verify respective security access key are programmed for different access levels in all
    diagnostic sessions.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=120)

        result_step = dut.step(step_1, purpose="Verify security access request seed "
                               "for supported security level 31 in extended session")

        result_step = result_step and dut.step\
            (step_2, purpose="Verify negative response for routine without sec acc")

        result = result_step and dut.step(step_3, purpose="Verify security access request seed "
                                          "for supported security level 11 in extended session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
