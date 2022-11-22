"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76170
version: 1
title: : ReadDataByIdentifier (22) - dataIdentifier(-s)
purpose: >
    It shall be possible to read data from all ECUs

description: >
    The ECU shall support the service readDataByIdentifer with the data parameter
    dataIdentifier(-s). The ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support Service readDataByIdentifer in:
    •   defaultSession
    •   extendedDiagnosticSession
    •   programmingSession, both primary and secondary bootloader

    Response time:
    Maximum response time for the service readDataByIdentifier (0x22) is 200 ms.
    Effect on the ECU normal operation:
    The service readDataByIdentifier (0x22) shall not affect the ECUs ability to
    execute non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service readDataByIdentifier (0x22).

    Security access:
    The ECU are allowed to protect the service ReadDataByIdentifier (0x22), read by other
    than system supplier specific dataIdentifiers, by using the service securityAccess (0x27)
    only if approved by Volvo Car Corporation.

details: >
    Verify service 22(ReadDataByIdentifier) in all supported diagnostic session
    •   defaultSession
    •   extendedDiagnosticSession
    •   programmingSession, both primary and secondary bootloader
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SE22 = SupportService22()
SIO = SupportFileIO()
SSBL = SupportSBL()


def read_data_by_id(dut, did_to_read, max_response_time, verify_two_dids_flag=False):
    """
    Verify the ReadDataByIdentifier service 22 with respective DID
    Args:
        dut (Dut): An instance of Dut
        did_to_read (str): DID for respective session (did_ext_def, did_prog)
        max_response_time (int): Response time
        verify_two_dids_flag (bool): Flag to test two DID's
    Returns:
        (bool): True when received positive response '62'
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did_to_read))
    time_elapsed = dut.uds.milliseconds_since_request()
    if time_elapsed >= max_response_time:
        logging.error("Test Failed: Elapsed time %sms is greater than %sms",
                       time_elapsed, max_response_time)
        return False

    logging.info("Elapsed time %sms is less than %sms as expected", time_elapsed,
                  max_response_time)

    if verify_two_dids_flag and response.raw[4:6] == '62' and \
        response.raw[6:10] == did_to_read[0:4] and response.raw[24:28] == did_to_read[4:8]:
        logging.info("Received positive response '62' for DID's %s, %s for request "
                     "ReadDataByIdentifier as expected", response.raw[6:10],
                      response.raw[24:28])
        return True

    if response.raw[4:6] == '62' and response.raw[6:10] == did_to_read:
        logging.info("Received positive response '62' for DID %s for request "
                        "ReadDataByIdentifier as expected", response.raw[6:10])
        return True

    logging.error("Test Failed: Expected positive response '62', received %s", response.raw)
    return False


def step_1(dut: Dut, did_ext_def, max_response_time):
    """
    action: Verify ReadDataByIdentifier in default session.
    expected_result: ECU should send positive response '62'.
    """
    result = read_data_by_id(dut, did_ext_def, max_response_time, False)
    if not result:
        logging.error("Test Failed: Unable to read DID %s in default session", did_ext_def)
        return False

    logging.info("Successfully read DID %s in default session", did_ext_def)
    return True


def step_2(dut: Dut, two_dids_ext_def, max_response_time):
    """
    action: Verify with two DID's ReadDataByIdentifier in default session.
    expected_result: ECU should send positive response '62'.
    """
    result = read_data_by_id(dut, two_dids_ext_def, max_response_time, True)
    if not result:
        logging.error("Test Failed: Unable to read DID%s in default session", two_dids_ext_def)
        return False

    logging.info("Successfully read DID%s in default session", two_dids_ext_def)
    return True


def step_3(dut: Dut, did_ext_def, max_response_time):
    """
    action: Verify ReadDataByIdentifier in extended session.
    expected_result: ECU should send positive response '62'.
    """
    # Set ECU to extended session
    dut.uds.set_mode(3)

    result = read_data_by_id(dut, did_ext_def, max_response_time, False)
    if not result:
        logging.error("Test Failed: Unable to read DID %s in extended session", did_ext_def)
        return False

    logging.info("Successfully read DID %s in extended session", did_ext_def)
    return True


def step_4(dut: Dut, two_dids_ext_def, max_response_time):
    """
    action: Verify with two DID's ReadDataByIdentifier in extended session
    expected_result: ECU should send positive response '62'
    """
    result = read_data_by_id(dut, two_dids_ext_def, max_response_time, True)
    if not result:
        logging.error("Test Failed: Unable to read DID %s in extended session", two_dids_ext_def)
        return False

    logging.info("Successfully read DID %s in extended session", two_dids_ext_def)
    result = SE22.read_did_f186(dut, dsession=b'\x03')
    if result:
        logging.info("ECU is in extended session as expected")
        # Set ECU to default session
        dut.uds.set_mode(1)
        return True

    logging.error("Test Failed: ECU is not in extended session")
    return False


def step_5(dut: Dut, did_prog, max_response_time):
    """
    action: Verify ReadDataByIdentifier in PBL session
    expected_result: ECU should send positive response '62'
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)

    # Verify current ECU mode is PBL session
    ecu_mode = SE22.verify_pbl_session(dut)
    if not ecu_mode:
        logging.error("Test Failed: Expected ECU to be in PBL session")
        return False

    result = read_data_by_id(dut, did_prog, max_response_time, False)
    if not result:
        logging.error("Test Failed: Unable to read DID %s in PBL session", did_prog)
        return False

    logging.info("Successfully read DID %s in PBL session", did_prog)
    return True


def step_6(dut: Dut, two_dids_prog):
    """
    action: Verify with two DID's ReadDataByIdentifier in PBL session
    expected_result: ECU should send negative response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(two_dids_prog))
    if response.raw[2:4] == '7F':
        logging.info("Received negative response %s for request ReadDataByIdentifier "
                     "as expected with NRC %s", response.raw, response.data['nrc'])

        # Verify current ECU mode is PBL session
        ecu_mode = SE22.verify_pbl_session(dut)
        if ecu_mode:
            logging.info("ECU is in PBL session")
            return True

        logging.error("Test Failed: Expected ECU to be in PBL session")
        return False

    logging.error("Test Failed: Expected negative response, received %s",response)
    return False


def step_7(dut: Dut, did_prog, max_response_time):
    """
    action: Verify ReadDataByIdentifier in SBL session
    expected_result: ECU should send positive response '62'
    """
   # Setting up keys
    sa_keys: SecAccessParam = dut.conf.default_rig_config

    # Load VBF files
    result = SSBL.get_vbf_files()
    if not result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # SBL activation
    result_ssbl_active = SSBL.sbl_activation(dut, sa_keys)
    if not result_ssbl_active:
        logging.error("Test Failed: Unable to activate SBL")
        return False

    # Get current ECU mode
    ecu_mode = SE22.verify_sbl_session(dut)
    if not ecu_mode:
        logging.error("Test Failed: Expected ECU to be in SBL session")
        return False

    result = read_data_by_id(dut, did_prog, max_response_time, False)
    if not result:
        logging.error("Test Failed: Unable to read DID %s in SBL session", did_prog)
        return False

    logging.info("Successfully read DID %s in SBL session", did_prog)
    return True


def step_8(dut: Dut, two_dids_prog):
    """
    action: Verify with two DID's ReadDataByIdentifier in SBL session
    expected_result: ECU should send negative response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(two_dids_prog))
    if response.raw[2:4] == '7F':
        logging.info("Received negative response %s for request ReadDataByIdentifier "
                     "as expected with NRC %s", response.raw, response.data['nrc'])

        # Verify current ECU mode is SBL session
        ecu_mode = SE22.verify_sbl_session(dut)
        if ecu_mode:
            logging.info("ECU is in SBL session")
            # Set ECU to default session
            dut.uds.set_mode(1)
            return True

        logging.error("Test Failed: Expected ECU to be in SBL session")
        return False

    logging.error("Test Failed: Expected negative response, received %s",response)
    return False


def run():
    """
    Verify service 22(ReadDataByIdentifier) in all supported diagnostic session
        •   Default session
        •   Extended session
        •   Programming session, both primary and secondary bootloader
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did_ext_def':'',
                       'did_prog':'',
                       'two_dids_ext_def':'',
                       'two_dids_prog':'',
                       'max_response_time': 0}
    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['did_ext_def'], parameters['max_response_time'],
                               purpose="Verify service 22 with DID 'F120' in Default session")
        if result_step:
            result_step = dut.step(step_2, parameters['two_dids_ext_def'],
                                   parameters['max_response_time'],  purpose="Verify service 22 "
                                   "with DIDs 'F120F12A' in Default session")
        if result_step:
            result_step = dut.step(step_3, parameters['did_ext_def'],
                                   parameters['max_response_time'], purpose="Verify service 22 "
                                   "with DID 'F120' in Extended session")
        if result_step:
            result_step = dut.step(step_4, parameters['two_dids_ext_def'],
                                   parameters['max_response_time'], purpose="Verify service 22 "
                                   "with DIDs 'F120F12A' in Extended session")
        if result_step:
            result_step = dut.step(step_5, parameters['did_prog'], parameters['max_response_time'],
                                   purpose="Verify service 22 with DID 'F121' in PBL session")
        if result_step:
            result_step = dut.step(step_6, parameters['two_dids_prog'], purpose="Verify "
                                   "service 22 with DIDs 'F121F12A' in PBL session")
        if result_step:
            result_step = dut.step(step_7, parameters['did_prog'], parameters['max_response_time'],
                                   purpose="Verify service 22 with DID 'F121' in SBL session")
        if result_step:
            result_step = dut.step(step_8, parameters['two_dids_prog'], purpose="Verify "
                                   "service 22 with DIDs 'F121F12A' in SBL session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
