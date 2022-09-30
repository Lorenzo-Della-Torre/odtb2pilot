"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 129845
version: 0
title: Secondary Bootloader Software Version Number data record
purpose: >
    To enable readout of the version number of the Secondary Bootloader SW.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database (GMRDB).
    --------------------------------------------------------------------------------
    Description                                                         Identifier
    --------------------------------------------------------------------------------
    Secondary Bootloader Software Version Number data record            F124
    --------------------------------------------------------------------------------

    •   It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].
    •   The identifier shall be BCD encoded, right justified and all unused digit shall be filled
        with 0.

    The ECU shall support the identifier in the following sessions:
    •   Programming session (which includes secondary bootloader).

details: >
    Verify response and part number of DID 'F124' in PBL and SBL.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SSBL = SupportSBL()
SIO = SupportFileIO
SUTE = SupportTestODTB2()


def validate_and_get_pn_f124(message):
    """
    Validate and pretty print ECU delivery assembly part number.
    Args:
        message (str): ECU response message
    Returns:
        (bool): Boolean based on part number validity.
    """
    return SUTE.validate_serial_number_record(message[16:])


def step_1(dut: Dut, did):
    """
    action: Set to programming session and verify DID 'F124' from PBL.
    expected_result: ECU sends NRC-31(requestOutOfRange).
    """
    # Set to programming session
    dut.uds.set_mode(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    if response.raw[2:4] == '7F' and response.raw[6:8] == '31':
        logging.info("Received NRC-%s as expected", response.raw[6:8])
        return True

    logging.error("Test Failed: Expected negative response with NRC-31(requestOutOfRange), "
                  "received %s", response.raw)
    return False


def step_2(dut: Dut, did):
    """
    action: Activate SBL and verify did 'F124'.
    expected_result: ECU sends positive response and part number is verified.
    """
    SSBL.get_vbf_files()
    result_sbl = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

    if result_sbl is False:
        logging.error("Test Failed: SBL activation failed")
        return False

    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    if response.raw[4:6] != '62' and response.raw[6:10] != did:
        logging.error("Test Failed: Expected positive response '62' for "
                      "requestReadDataByIdentifier(0x22), received %s", response.raw)
        return False

    result = validate_and_get_pn_f124(message=response.raw)
    if result is False:
        logging.error("Test Failed: Invalid part number received")
        return False

    logging.info("Valid part number received")
    return True


def run():
    """
    Verify response and part number of DID 'F124' in PBL and SBL.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did': ''}

    try:
        dut.precondition(timeout=80)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters['did'], purpose="Set to programming session and "
                                                                  "verify DID 'F124' from PBL")
        if result_step:
            result_step = dut.step(step_2, parameters['did'], purpose="Activate SBL and verify "
                                                                      "did 'F124'")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
