"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76486
version: 3
title: WriteDataByIdentifier (2E)
purpose: >
    Primary purpose for using the service WriteDataByIdentifier is to store configuration
    parameters in an ECU.

description: >
    The ECU shall support the service WriteDataByIdentifier if other requirements from Volvo Car
    Corporation specifies that the value of a data record, pointed out by a dataIdentifier, shall be
    possible to write.
    Otherwise, the ECU may support the service WriteDataByIdentifier in one, some or all sessions.
    When the ECU is in programming session, the service WriteDataByIdentifier shall only be
    supported in the secondary bootloader.

    The ECU shall support the service writeDataByIdentifier with the data parameter
    dataIdentifier(-s). The ECU shall implement the service accordingly:

    Supported sessions:
    The ECU may support Service writeDataByIdentifier in:
        • defaultSession
        • extendedDiagnosticSession
        • programmingSession, secondary bootloader only

    Response time:
    Maximum response time for the service writeDataByIdentifier (0x2E) is 5000 ms.

    Effect on the ECU normal operation:
    The service writeDataByIdentifier (0x2E) is allowed to affect the ECU's ability to execute
    non-diagnostic tasks. The service is not allowed to reset the ECU.

    Entry conditions:
    Entry conditions for service writeDataByIdentifier (0x2E) are allowed only if approved by Volvo
    Car Corporation.
    If the ECU implement safety requirements with an ASIL higher than QM it shall,
    in all situations when diagnostic services may violate any of those safety requirements, reject
    the critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests, this requires an approval by Volvo Car Corporation.

    Security access:
    The ECU is allowed to protect the service WriteDataByIdentifier (0x2E) (in other session than
    programmingSession) by using the service securityAccess (0x27) but only if this is approved of
    and required by Volvo Car Corporation.
    The ECU is required to protect service writeDataByIdentifier (0x2E) in programmingSession by
    using the service securityAccess (0x27).

details: >
    Verify service WriteDataByIdentifier(0x2E) in extended session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def request_read_data_by_id(dut, did):
    """
    Read DID 'DB90'
    Args:
        dut (Dut): An instance of Dut
        did (str): DID
    Returns:
        response (str): ECU response code
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    return response


def step_1(dut: Dut):
    """
    action: Set ECU to extended session and request security access
    expected_result: Security access should be granted in extended session
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] != 3:
        logging.error("Test Failed: ECU is not in extended session")
        return False

    # Security access
    sa_result = dut.SE27.activate_security_access_fixedkey(dut,
                                                           sa_keys=dut.conf.default_rig_config)
    if not sa_result:
        logging.error("Test Failed: Security access denied in extended session")
        return False

    logging.info("Security access successful in extended session")
    return True


def step_2(dut: Dut, parameters):
    """
    action: Set data record of DID to '00' value
    expected_result: ECU should send positive response '6E' with data record value '00'
    """
    message = bytes.fromhex(parameters['did']) + bytes.fromhex('00')
    response = dut.uds.generic_ecu_call(dut.SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                                 message, b''))

    if response.raw[2:4] == '6E' and response.raw[4:10] == 'DB9000':
        logging.info("Successfully set data record value of DID to '00'")
        return True

    logging.error("Test Failed: Data record of DID is not set to '00', received value %s",
                  response)
    return False


def step_3(dut: Dut, parameters):
    """
    action: Request ReadDataByIdentifier(0x22) before overwriting data records of DID
    expected_result: ECU should send positive response '6E' and the response should contain
                     default data records of DID
    """
    response = request_read_data_by_id(dut, parameters['did'])
    # Default data record of DID 'DB90': 1st byte is '00'
    if response.raw[2:4] == '62' and response.raw[8:10] == '00':
        logging.info("ECU response contains default data record %s as expected",
                      response.data['details']['item'])
        return True

    logging.error("Test Failed: Expected ECU response contains default data record"
                  ", received %s", response.data['details']['item'])
    return False


def step_4(dut: Dut, parameters):
    """
    action: Verify service WriteDataByIdentifier(0x2E) in extended session
    expected_result: ECU should send positive response '6E'
    """
    message = bytes.fromhex(parameters['did']) + bytes.fromhex(parameters['data_record'])
    response = dut.uds.generic_ecu_call(dut.SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message,
                                                             b''))
    # Verify response time
    response_time = dut.uds.milliseconds_since_request()
    if response_time >= parameters['max_response_time']:
        logging.error("Test Failed: Elapsed time %sms is greater than %sms", response_time,
                       parameters['max_response_time'])
        return False

    logging.info("Elapsed time %sms is less than %sms as expected", response_time,
                  parameters['max_response_time'])

    # Verify service response
    if response.raw[2:4] == '6E' and response.raw[4:8] == parameters['did']:
        logging.info("Received positive response '6E' for DID %s for a request "
                     "WriteDataByIdentifier(0x2E) as expected", parameters['did'])
        return True

    logging.error("Test Failed: Expected positive response '6E', received %s", response.raw)
    return False


def step_5(dut: Dut, parameters):
    """
    action: Request ReadDataByIdentifier(0x22) after overwriting data records of DID
    expected_result: ECU should send positive response '6E' and the response should contain
                     defined data records of DID
    """
    response = request_read_data_by_id(dut, parameters['did'])
    if response.raw[2:4] == '62' and response.raw[8:10] == parameters['data_record']:
        logging.info("ECU response contains defined data record %s as expected",
                      response.data['details']['item'])
        return True

    logging.error("Test Failed: Expected ECU response contains defined data record"
                  ", received %s", response.data['details']['item'])
    return False


def step_6(dut: Dut, parameters):
    """
    action: Restore default data records of DID using WriteDataByIdentifier(0x2E)
    expected_result: ECU should send positive response '6E' and default data records of DID
                     should be restored
    """
    message = bytes.fromhex(parameters['did']) + bytes.fromhex('00')
    response = dut.uds.generic_ecu_call(dut.SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message,
                                                             b''))
    # Verify service response
    if response.raw[2:4] == '6E' and response.raw[4:8] == parameters['did']:
        return True

    return False


def run():
    """
    Verify service WriteDataByIdentifier(0x2E) in extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did': '',
                       'data_record': '',
                       'max_response_time': 0}

    parameters = dut.SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        raise DutTestError("yml parameters not found")

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose='Set ECU to extended session and request security '
                                               'access')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Set data record of DID to '00' "
                                                               "value")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Request ReadDataByIdentifier(0x22)'
                                           ' before overwriting data records of DID')
        if result_step:
            result_step = dut.step(step_4, parameters, purpose='Verify service '
                                           'WriteDataByIdentifier(0x2E) in extended session')
        if result_step:
            result_step = dut.step(step_5, parameters, purpose='Request ReadDataByIdentifier(0x22)'
                                           ' after overwriting data records of DID')
        if result_step:
            result_step = dut.step(step_6, parameters, purpose='Restore default data records of '
                                           'DID using WriteDataByIdentifier(0x2E)')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
