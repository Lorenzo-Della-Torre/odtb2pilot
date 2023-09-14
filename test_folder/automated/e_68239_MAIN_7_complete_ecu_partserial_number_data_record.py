"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68239
version: 7
title: Complete ECU PartSerial Number data record
purpose: >
    To enable readout of the complete set of ECU Part/Serial numbers.

description: >
    A data record (called "composite" data record) with identifier 0xEDA0 shall be implemented.
    The data records shall contain several data items in an arbitrary order. Each data item shall
    consist of a data identifier followed by the record data that is identified by the data
    identifier. The "composite" data record with identifier 0xEDA0 shall contain the following
    data items(the data items is depending of the currently active executing software):

    Description       Identifier
    ------------------------------------------------------------------------------
                                               Application    PBL         SBL
    ------------------------------------------------------------------------------
    Diagnostic Database Part number                F120       F121       F122
    ECU Core Assembly Part Number                  F12A       F12A       F12A
    ECU Delivery Assembly Part Number              F12B       F12B       F12B
    ECU Serial Number                              F18C       F18C       F18C
    Software Part Number                           F12E       F125       F124
    Private ECU(s) or component(s) Serial Number   F13F         -          -
    ------------------------------------------------------------------------------
    •   The data records shall be implemented exactly as defined in Carcom - Global Master
        Reference Database.
    •   It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    •    Default session
    •    Programming session (which includes both primary and secondary bootloader)
    •    Extended Session

details: >
    Validate Part/Serial numbers of DID 'EDA0' in default, extended and programming(PBL & SBL)
    session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO

SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SIO = SupportFileIO()


def validate_part_and_serial_no(dut, pn_sn):
    """
    Validate part numbers and serial numbers in the response of DID 'EDA0'
    Args:
        dut (Dut): An instance of DUT
        pn_sn (List): Part/serial number
    Return:
        (bool): True when all part/serial numbers present in the response are valid
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('EDA0'))
    result = SUTE.validate_combined_did_eda0(response.raw, pn_sn)
    return result


def verify_active_session(dut, expected_session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of DUT
        expected_session (int): Mode of diagnostic session
    Returns:
        (bool): True when ECU is in the expected session
    """
    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    current_session = active_session.data["details"]["mode"]

    # Verify active diagnostic session
    if current_session == expected_session:
        logging.info("ECU is in session %s as expected", current_session)
        return True

    logging.error("Test Failed: ECU is in %s session, expected to be in %s session",
                   current_session, expected_session)
    return False


def step_1(dut:Dut, pn_sn_def_ext):
    """
    action: Validate part numbers and serial numbers in the response of DID 'EDA0' in default
            session
    expected result: All part/serial numbers present in the response are valid
    """
    result = validate_part_and_serial_no(dut, pn_sn_def_ext)
    if not result:
        logging.error("Test Failed: All part/serial numbers present in the response of DID 'EDA0' "
                      "in default session are not valid")
        return False

    logging.info("All part/serial numbers present in the response of DID 'EDA0' in default session"
                 " are valid")
    return True


def step_2(dut:Dut, pn_sn_def_ext):
    """
    action: Validate part numbers and serial numbers in the response of DID 'EDA0' in extended
            session
    expected result: All part/serial numbers present in the response are valid
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Verify active diagnostic session
    active_session = verify_active_session(dut, expected_session=3)
    if not active_session:
        return False

    result = validate_part_and_serial_no(dut, pn_sn_def_ext)
    if not result:
        logging.error("Test Failed: All part/serial numbers present in the response of DID 'EDA0' "
                      "in extended session are not valid ")
        return False

    logging.info("All part/serial numbers present in the response of DID 'EDA0' in extended "
                 "session are valid")
    return True


def step_3(dut: Dut, pn_sn_pbl):
    """
    action: Validate part numbers and serial numbers in the response of DID 'EDA0' in PBL
    expected result: All part/serial numbers present in the response are valid
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Verify active diagnostic session
    active_session = verify_active_session(dut, expected_session=2)
    if not active_session:
        return False

    result = validate_part_and_serial_no(dut, pn_sn_pbl)
    if not result:
        logging.error("Test Failed: All part/serial numbers present in the response of DID 'EDA0' "
                      "in PBL are not valid ")
        return False

    logging.info("All part/serial numbers present in the response of DID 'EDA0' in PBL are valid")
    return True


def step_4(dut: Dut, pn_sn_sbl):
    """
    action: Validate part numbers and serial numbers in the response of DID 'EDA0' in SBL
    expected result: All part/serial numbers present in the response are valid
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Aborting SBL activation due to problems when loading VBFs")
        return False

    # Download and activate SBL on the ECU
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation unsuccessful")
        return False

    result = validate_part_and_serial_no(dut, pn_sn_sbl)
    if not result:
        logging.error("Test Failed: All part/serial numbers present in the response of DID 'EDA0' "
                      "in SBL are not valid")
        return False

    logging.info("All part/serial numbers present in the response of DID 'EDA0' in SBL are valid")
    return True


def run():
    """
    Validate Part/Serial numbers of DID 'EDA0' in default, extended and programming(PBL & SBL)
    session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'pn_sn_def_ext': [],
                       'pn_sn_pbl': []}

    try:
        dut.precondition(timeout=100)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['pn_sn_def_ext'], purpose= "Validate part "
                               "numbers and serial numbers in the response of DID 'EDA0' in "
                               "default session")
        if result_step:
            result_step = dut.step(step_2, parameters['pn_sn_def_ext'], purpose= "Validate part "
                                   "numbers and serial numbers in the response of DID 'EDA0' in "
                                   "extended session")
        if result_step:
            result_step = dut.step(step_3, parameters['pn_sn_pbl'], purpose= "Validate part "
                                   "numbers and serial numbers in the response of DID 'EDA0' in "
                                   "PBL")
        '''if result_step:
            result_step = dut.step(step_4, parameters['pn_sn_sbl'] , purpose= "Validate part "
                                   "numbers and serial numbers in the response of DID 'EDA0' in "
                                   "SBL")'''
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
