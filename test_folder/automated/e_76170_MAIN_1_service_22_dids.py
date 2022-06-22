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
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession, both primary and secondary bootloader

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
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession
"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SE22 = SupportService22()
SIO = SupportFileIO


def read_data_id_with_two_dids(dut:Dut, did_to_read):
    """
    Verify the ReadDataByIdentifier service 22 with two DIDs
    Args:
        dut (Dut): An instance of Dut
        did_to_read(str): DIDs for respective session (two_dids_ext_def, two_dids_prog)
    Returns:
        (bool): True when ECU positive response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did_to_read))
    if response.raw[4:6] == '62' and response.raw[6:10] == did_to_read[0:4] and\
        response.raw[24:28] == did_to_read[4:8]:
        logging.info("Received positive response %s and %s for request ReadDataByIdentifier ",
                    response.raw[6:10],response.raw[24:28])
        return True

    logging.error("Test Failed:Expected Positive response, but received %s",response)
    return False


def read_data_id(dut:Dut, did_to_read):
    """
    Verify the ReadDataByIdentifier service 22 with respective DID
    Args:
        dut (Dut): An instance of Dut
        did_to_read(str): DID for respective session (did_ext_def, did_prog)
    Returns:
        (bool): True when ECU positive response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did_to_read))

    if response.raw[4:6] == '62' and response.raw[6:10] == did_to_read:
        logging.info("Received positive response %s for request ReadDataByIdentifier ",
                    response.raw[6:10])
        return True
    logging.error("Test Failed: Expected positive response, but received %s",response)
    return False


def step_1(dut: Dut, did_ext_def):
    """
    action: Verify service 22 with DID 'F120' in default session
    expected_result: True on positive response
    """
    result = read_data_id(dut, did_ext_def)
    if not result:
        logging.error("Test Failed: ECU unable to read DID %s in default session", did_ext_def)
        return False
    logging.info("ECU successfully read DID %s in default session", did_ext_def)
    return True


def step_2(dut: Dut, two_dids_ext_def):
    """
    action: Verify service 22 with DID 'F120F12A' in default session.
    expected_result: True on positive response
    """
    result = read_data_id_with_two_dids(dut, two_dids_ext_def)
    if not result:
        logging.error("Test Failed: ECU unable to read DID%s in default session", two_dids_ext_def)
        return False
    logging.info("ECU successfully read DID %s in default session", two_dids_ext_def)
    return True


def step_3(dut: Dut, did_ext_def):
    """
    action: Verify service 22 with DID 'F120' in extended session
    expected_result: True on positive response
    """
    # Set ECU to Extended session
    dut.uds.set_mode(3)

    result = read_data_id(dut, did_ext_def)
    if not result:
        logging.error("Test Failed: ECU unable to read DID %s in extended session", did_ext_def)
        return False
    logging.info("ECU successfully read DID %s in extended session", did_ext_def)
    return True


def step_4(dut: Dut, two_dids_ext_def):
    """
    action: Verify service 22 with DID 'F120F12A' in extended session
    expected_result: True on positive response
    """
    result = read_data_id_with_two_dids(dut, two_dids_ext_def)

    if not result:
        logging.error("Test Failed: ECU unable to read DID%s in extended session", two_dids_ext_def)
        return False

    result = SE22.read_did_f186(dut, dsession=b'\x03')
    if result:
        logging.info("ECU successfully read DID %s in extended session", two_dids_ext_def)
        # Set ECU to Default session
        dut.uds.set_mode(1)
        return True

    logging.error("Test Failed: ECU not in extended session")
    return False


def step_5(dut: Dut, did_prog):
    """
    action: Verify service 22 with DID 'F121' in programming session
    expected_result: True on positive response
    """
    # Set ECU to Programming session
    dut.uds.set_mode(2)

    result = read_data_id(dut, did_prog)
    if not result:
        logging.error("Test Failed: ECU unable to read DID %s in programming session", did_prog)
        return False
    logging.info("ECU successfully read DID %s in programming session", did_prog)
    return True


def step_6(dut: Dut, two_dids_prog):
    """
    action: Verify service 22 with DID 'F121F12A' in programming session
    expected_result: True on negative response and ECU is in programming session
    """

    response = dut.uds.read_data_by_id_22(bytes.fromhex(two_dids_prog))

    if response.raw[2:4] == '7F':
        logging.info("Received negative response %s for request ReadDataByIdentifier and NRC %s ",
                    response.raw, response.data['nrc'])
        result = SE22.read_did_f186(dut, dsession=b'\x02')
        if result:
            logging.info("ECU is in programming session")
            # Set ECU to Default session
            dut.uds.set_mode(1)
            return True

    logging.error("Test Failed: Expected negative response, but received %s",response)
    return False


def run():
    """
    Verify service 22 (ReadDataByIdentifier) is supported in default session, extended session
    and programming session
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did_ext_def':'',
                       'did_prog':'',
                       'two_dids_ext_def':'',
                       'two_dids_prog':''}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['did_ext_def'], purpose="Verify service 22 with"
                                                                " DID 'F120' in Default session")
        if result_step:
            result_step = dut.step(step_2, parameters['two_dids_ext_def'], purpose="Verify service"
                                                    " 22 with DIDs 'F120F12A' in Default session")
        if result_step:
            result_step = dut.step(step_3, parameters['did_ext_def'], purpose="Verify service "
                                                        "22 with DID 'F120' in Extended session")
        if result_step:
            result_step = dut.step(step_4, parameters['two_dids_ext_def'], purpose="Verify service"
                                                  " 22 with DIDs 'F120F12A' in Extended session")
        if result_step:
            result_step = dut.step(step_5, parameters['did_prog'], purpose="Verify service 22 with"
                                                              "DID 'F121' in programming session")
        if result_step:
            result_step = dut.step(step_6, parameters['two_dids_ext_def'], purpose="Verify service"
                                                " 22 with DIDs 'F121F12A' in programming session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
