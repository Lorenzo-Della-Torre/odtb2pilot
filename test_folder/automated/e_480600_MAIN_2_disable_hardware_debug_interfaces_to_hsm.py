"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 480600
version: 2
title: Disable Hardware Debug Interfaces to HSM

purpose: >
    Prevent hardware debug interfaces to be used by an attacker to analyze, control and modify
    the hardware security modules

description: >
    Only applicable for ECUs with Hardware Security Modules (HSM).

    Hardware debug interface to a Hardware Security Module shall by default be
    permanently disabled.

    Note:
    A Hardware Security Module is a general term used to realize hardware security and is
    usually a dedicated hardware or a logically isolated secure environment, handling
    cryptographic keys and sensitive security operations. Commonly implemented and referred
    as HSM/SHE/TPM/TEE or any other vendor specific secure environments.

details: >
    Verify hardware debug interface security with boot loader did 'F1FD' in both programming
    and extended session.
    Steps-
        1. Verify negative response in programming session without security access
        2. Verify positive response in programming session with security access
        3. Verify negative response in extended session without security access
        4. Verify negative response in extended session with security access
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27

SE27 = SupportService27()
SIO = SupportFileIO()


def step_1(dut: Dut, did):
    """
    action: Verify hardware debug interface security with boot loader did 'F1FD' in programming
            session without security access
    expected_result: True when negative response received
    """
    dut.uds.set_mode(2)

    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if response.raw[2:4] == '7F':
        logging.info("Received negative response %s as expected", response.raw[2:4])
        return True

    logging.error("Test failed: Expected negative response received %s", response.raw)
    return False


def step_2(dut: Dut, did):
    """
    action: Verify hardware debug interface security with boot loader did 'F1FD' in programming
            session with security access
    expected_result: True when positive response received
    """
    # Security access to ECU
    result_sa = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config)

    if result_sa is False:
        logging.error("Test failed: Security access denied")
        return False

    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if response.raw[2:4] == '62':
        logging.info("Received positive response %s as expected", response.raw[2:4])
        return True

    logging.error("Test failed: Expected positive response received %s", response.raw)
    return False


def step_3(dut: Dut, did):
    """
    action: Verify hardware debug interface security with boot loader did 'F1FD' in extended
            session without security access
    expected_result: True when negative response received
    """
    time.sleep(10)
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if response.raw[2:4] == '7F':
        logging.info("Received negative response %s as expected", response.raw[2:4])
        return True

    logging.error("Test failed: Expected negative response received %s", response.raw)
    return False


def step_4(dut: Dut, did):
    """
    action: Verify hardware debug interface security with boot loader did 'F1FD' in extended
            session with security access
    expected_result: True when negative response received
    """
    # Security access to ECU
    result_sa = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config)

    if result_sa is False:
        logging.error("Test failed: Security access denied")
        return False

    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if response.raw[2:4] == '7F':
        logging.info("Received negative response %s as expected", response.raw[2:4])
        return True

    logging.error("Test failed: Expected negative response received %s", response.raw)
    return False


def run():
    """
    Verify hardware debug interface security with boot loader did 'F1FD' in both programming
    and extended session.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = {'did': ''}
    try:
        dut.precondition(timeout=30)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, parameters['did'], purpose="Verify negative response in"
                                               " programming session without security access")

        if result_step:
            result_step = dut.step(step_2, parameters['did'], purpose="Verify positive response in"
                                                   " programming session with security access")

        if result_step:
            result_step = dut.step(step_3, parameters['did'], purpose="Verify negative response in"
                                                   " extended session without security access")

        if result_step:
            result_step = dut.step(step_4, parameters['did'], purpose="Verify negative response in"
                                                   " extended session with security access")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
