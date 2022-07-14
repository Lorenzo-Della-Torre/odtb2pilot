"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72168
version: 1
title: Check Complete & Compatible routine
purpose: >
    All ECUs must support routines defined for SWDL.

description: >
    The Check Complete & Compatible routine with routine identifier as specified in the table below
    shall be implemented as defined in Carcom - Global Master Reference Database (GMRDB).

    Description	                         Identifier
    -------------------------------------------------
    Check Complete & Compatible	         0205
    -------------------------------------------------

    •	It shall be possible to execute the control routine with service as specified in
        Ref[LC : VCC - UDS Services - Service 0x31 (RoutineControl) Reqs].
    •	The response time P4server_max for the Check Complete & Compatible routine shall be equal
        to P2server_max.
    •	The routine shall be implemented as a type 1 routine

    The ECU shall support the identifier in the following sessions:
    •	Programming session (which includes both primary and secondary bootloader)

details: >
    Request software download & check complete and compatibility. Also, verify response
    time is less than or equal to P2server_max.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.flash import load_vbf_files, activate_sbl, download_ess, download_application_and_data
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_file_io import SupportFileIO

SSBL = SupportSBL()
SIO = SupportFileIO()


def request_software_download(dut):
    """
    Request software download
    Args:
        dut(Dut): Dut instance
    Return:
        (bool): True on successful download
    """
    # Loads the rig specific VBF files
    vbf_result = load_vbf_files(dut)
    if not vbf_result:
        return False

    # Downloads and activate SBL on the ECU using support function from support_SBL
    sbl_result = activate_sbl(dut)
    if not sbl_result:
        return False

    # Download the ESS file to the ECU
    ess_result = download_ess(dut)
    if not ess_result:
        return False

    # Download the application and data to the ECU
    app_data_result = download_application_and_data(dut)
    if not app_data_result:
        return False

    logging.info("Software download successful")
    return True


def step_1(dut: Dut, p2_server_max):
    """
    action: Request software download & check complete and compatibility. Also, verify response
            time is less than or equal to P2server_max.
    expected_result: True when response time is less than or equal to P2server_max
    """
    # Software download
    swdl_result = request_software_download(dut)
    if not swdl_result:
        logging.error("Test Failed: Software download failed")
        return False

    # Check complete and compatibility
    result = SSBL.check_complete_compatible_routine(dut, stepno=1)
    if not result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    # Validating response time
    response_time = dut.uds.milliseconds_since_request()
    if response_time <= p2_server_max:
        logging.info("Response time %sms is less than or equal to %sms as expected",
                      response_time, p2_server_max)
        return True

    logging.error("Test Failed: Response time %sms is greater than %sms which is not expected",
                   response_time, p2_server_max)
    return False


def run():
    """
    Request software download & check complete and compatibility. Also, verify response
    time is less than or equal to P2server_max.
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'p2_server_max': 0}

    try:
        dut.precondition(timeout=600)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters['p2_server_max'], purpose="Request software download "
                                  "& check complete and compatibility. Also, verify response time "
                                  "is less than or equal to P2server_max")
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
