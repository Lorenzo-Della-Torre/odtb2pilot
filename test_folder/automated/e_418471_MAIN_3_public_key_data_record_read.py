"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 418471
version: 3
title: Public Key data record
purpose: >
    To enable programming of the Public Key, for ECUs supporting Software Authentication where
    only the key (and not certificates) is used to verify the authenticity of the software.

description: >
    If the ECU supports the Software Authentication concept where the data file is verified using
    a Public Key as defined in Ref[LC : General Software Authentication], a data record shall be
    implemented as specified in the table below.

    Description	          Identifier
    -----------------------------------
    Public Key	            D01C
    -----------------------------------

    •	It shall be possible to read the “Public Key CheckSum” parameter in the data record by
    using the diagnostic service specified in Ref[LC : Volvo Car Corporation - UDS Services -
    Service 0x22 (ReadDataByIdentifier) Reqs] in programming session (which includes both primary
    and secondary bootloader). It shall not be possible to read other parts of the key.
    •	It shall be possible to write the value of the data record in secondary bootloader by
    diagnostic service as specified in Ref[LC : VCC - UDS Services - Service 0x2E
    (WriteDataByIdentifier) Reqs] in secondary bootloader.

details: >
    Verify response of ReadDataByIdentifier service in programming session (which includes both
    primary and secondary bootloader)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service22 import SupportService22

SE22 = SupportService22()
SSBL = SupportSBL()


def read_did(dut: Dut, ecu_mode):
    """
    Read public key data record did 'D01C'
    Args:
        dut (class obj): Dut instance
        ecu_mode (str): ECU mode
    Return:
        (bool): True on successfully verified positive response
        response.raw (str): ECU response
    """
    # Read public key data record did 'D01C'
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D01C'))
    if response.raw[2:4] == '62':
        logging.info("Successfully read DID 'D01C' with positive response %s in %s ecu mode",
                        response.raw[2:4], ecu_mode)
        return True, response.raw

    logging.error("Test Failed: Expected positive response 62 for DID 'D01C' in %s ecu mode,"
                  " received %s", ecu_mode, response.raw)
    return False, None


def step_1(dut: Dut):
    """
    action: Read public key data record in PBL session
    expected_result: True when ECU is in PBL session and respond to ReadDataByIdentifier request
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)

    # Verify programming session
    result = SE22.read_did_f186(dut, dsession=b'\x02')
    if not result:
        logging.error("Expected ECU to be in programming session")
        return False, None

    # Verify current ECU mode is pbl
    ecu_mode = SE22.verify_pbl_session(dut)
    if not ecu_mode:
        logging.error("Test Failed: Expected ECU to be in PBL mode")
        return False, None

    # Verify ECU mode and read public key data record did 'D01C'
    pbl_result, response_pbl = read_did(dut, ecu_mode='PBL')

    return pbl_result, response_pbl


def step_2(dut: Dut, response_pbl):
    """
    action: Read public key data record in SBL session and compare the public key read from
            the PBL and SBL
    expected_result: True when response of pbl and sbl is equal
    """
    # Set ECU to Default session
    dut.uds.set_mode(1)

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
        logging.error("Test Failed: Expected ECU to be in SBL mode")
        return False, None

    result_sbl, response_sbl = read_did(dut, ecu_mode='SBL')

    if not result_sbl:
        return False

    if response_pbl == response_sbl:
        # Set ECU to Default session
        dut.uds.set_mode(1)

        logging.info("Successfully verified that public key read response from the PBL and SBL"
                     " are equal")
        return True

    logging.error("Test Failed: public key read response from the PBL and SBL are not equal")
    return False


def run():
    """
    Verify response of ReadDataByIdentifier service in programming session (which includes both
    primary and secondary bootloader)
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=90)

        result_step, response_pbl = dut.step(step_1, purpose="Read public key Data record in PBL"
                                                             " Session ")
        if result_step:
            result_step = dut.step(step_2, response_pbl, purpose="Read public key Data record in"
                                                                 " SBL Session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
