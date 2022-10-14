"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76496
version: 1
title: ClearDiagnosticInformation (14)
purpose: >
    It shall be possible to erase DTCs and DTC related information

description: >
    The ECU must support the service ClearDiagnosticInformation. The ECU shall implement the
    service accordingly:

    Supported sessions:
    The ECU shall support Service ClearDiagnosticInformation in:
        •   defaultSession
        •   extendedDiagnosticSession
    The ECU may, but are not required to, support clearDiagnosticInformation in programmingSession

    Response time:
    Maximum response time for the service ClearDiagnosticInformation (0x14) is 3500ms.

    Effect on the ECU normal operation:
    The service ClearDiagnosticInformation (0x14) shall not affect the ECU's ability to execute
    non-diagnostic tasks.

    Entry conditions:
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests, this requires an approval by Volvo Car Corporation.

    Security access:
    The ECU shall not protect service ClearDiagnosticInformation by using the service
    securityAccess (0x27).

details: >
    Verify ClearDiagnosticInformation(0x14) service is supported in default and extended session
    and not in programming session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def verify_clear_diagnostic_info(dut, response_time, session):
    """
    Verify ClearDiagnosticInformation(0x14) service supports in desired session
    Args:
        dut (Dut): Dut instance
        response_time (int): Response time
        session (str): Diagnostic session
    Return:
        (bool): True on successfully verified positive response '54'
    """
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("ClearDiagnosticInformation",
                                                              b'\x0B\x4A\x00',
                                                              b''))
    elapsed_time = dut.uds.milliseconds_since_request()

    if response.raw[2:4] == '54':
        logging.info("Successfully verified ClearDiagnosticInformation(0x14) service in %s "
                     "session", session)
        if elapsed_time <= response_time:
            logging.info("Response time %sms is less than or equal to %sms", elapsed_time,
                         response_time)
            return True

        logging.error("Test Failed: Response time %sms is greater than %sms", elapsed_time,
                      response_time)

    logging.error("Test Failed: Unable to verify ClearDiagnosticInformation(0x14) service in %s "
                  "session", session)
    return False


def step_1(dut: Dut, response_time):
    """
    action: Verify ClearDiagnosticInformation(0x14) service in default session
    expected_result: True when received positive response '54'
    """
    return verify_clear_diagnostic_info(dut, response_time, session='default')


def step_2(dut: Dut, response_time):
    """
    action: Verify ClearDiagnosticInformation(0x14) service in extended session
    expected_result: True when received positive response '54'
    """
    # Set to extended session
    dut.uds.set_mode(3)

    result = verify_clear_diagnostic_info(dut, response_time, session='extended')
    if result:
        # Verify active diagnostic session
        response = dut.uds.active_diag_session_f186()
        if response.data["details"]["mode"] == 3:
            logging.info('ECU is in extended session as expected')
            return True

        logging.error('Test Failed: ECU is not in extended session, received mode %s',
                      response.data["details"]["mode"])
    return False


def step_3(dut: Dut, programming_supported):
    """
    action: Verify ClearDiagnosticInformation(0x14) service in programming session
    expected_result: True when received negative response '7F'
    """
    # Set to programming session
    dut.uds.set_mode(2)

    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("ClearDiagnosticInformation",
                                                             b'\x0B\x4A\x00',
                                                             b''))
    if programming_supported == 'False':
        if response.raw[2:4] == '7F' and response.raw[6:8] == '11':
            logging.info("ClearDiagnosticInformation(0x14) service is not supported in programming"
                        " session as expected")
            return True

        logging.error("Test Failed: ClearDiagnosticInformation(0x14) service is supported in "
                    "programming session which is not expected")
        return False

    if response.raw[2:4] == '54':
        logging.info("Successfully verified ClearDiagnosticInformation(0x14) service is "
                     "supported in programming session")
        return True

    logging.error("Test Failed: ClearDiagnosticInformation(0x14) service is not supported in "
                  "programming session")
    return False


def run():
    """
    Verify ClearDiagnosticInformation(0x14) service is supported in default and extended session
    and not in programming session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'response_time': 0,
                       'programming_supported': ''}

    try:
        dut.precondition(timeout=40)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['response_time'], purpose="Verify "
                               "ClearDiagnosticInformation(0x14) service in default session")
        if result_step:
            result_step = dut.step(step_2, parameters['response_time'], purpose="Verify "
                                   "ClearDiagnosticInformation(0x14) service in extended session")
        if result_step:
            result_step = dut.step(step_3, parameters['programming_supported'], purpose="Verify "
                                "ClearDiagnosticInformation(0x14) service in programming session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
