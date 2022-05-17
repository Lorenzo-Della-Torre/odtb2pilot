"""

/*********************************************************************************/


Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 469463
version: 1
title: Key storage

purpose: >
    A key is used when calculating the Authentication Data, and must be protected from
    being manipulated or read out.

description: >
    The secret key used to calculate the Authentication Data shall be stored in a protected ECU
    area and programmed at OEM end-of-line. It must not be possible to read or alter, e.g. by
    using diagnostic services (readMemoryByAddress, readDataByIdentifier, requestUpload,
    writeMemoryByAddress, software download services, etc.) or by any other debug interface or
    protocol. Only trusted entities (secure operations) must be able to request operations using
    the secret key.

    Note.
    The best available solution provided by the ECU shall be used to protect a key and its
    cryptographic operations in ECU.

details: >
    Verify secret key is not altered after using diagnostic software download
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.flash import software_download
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SE22 = SupportService22()
SE27 = SupportService27()
SIO = SupportFileIO()


def step_1(dut: Dut, parameters):
    """
    action: Change key into ECU by using writeDataByIdentifier
    expected_result: True when successfully changed the key using writeDataByIdentifier.
    """
    sa_key_32byte_crc = parameters['dev_key']
    crc = SUTE.crc16(bytearray(sa_key_32byte_crc.encode('utf-8')))
    crc_hex = hex(crc)[2:]
    message = bytes.fromhex(parameters['did'] + sa_key_32byte_crc + crc_hex)

    # Request WriteDataByIdentifier
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                              message, b''))

    # Extract and validate positive response
    if response.raw[6:8] == '6E':
        logging.info("Received positive response %s as expected", response.raw)
        return True

    logging.error("Test Failed: Expected 6E, received %s", response.raw)
    return False


def step_2(dut: Dut):
    """
    action: Software Download
    expected_result: True on successful download
    """
    result = software_download(dut)

    if result:
        logging.info("Software download successful")
        return True

    logging.error("Test Failed: Software download failed")
    return False


def step_3(dut: Dut):
    """
    action: Verify the new development key is stored by false security access attempt to ECU
            with initial key(16 bytes FF)
    expected_result: True when security access not unlocked with initial key
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)

    # Security access to ECU with initial key
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if not result:
        logging.info("Security access to ECU failed with initial key as expected since it was"
                     " updated before software download with development key")
        return True

    logging.error("Test Failed: Development key is not updated")
    return False


def run():
    """
    Verify secret key is not altered after using diagnostic software download
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did': '',
                       'dev_key': ''}

    try:
        # Read parameters from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        dut.precondition(timeout=500)

        result_step = dut.step(step_1, parameters, purpose="Change key into ECU by using"
                                                           " writeDataByIdentifier")
        if result_step:
            result_step = dut.step(step_2, purpose="Initiate Software download")

        if result_step:
            result_step = dut.step(step_3, purpose="Verify the key has not been changed back to"
                                                   " the default key")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
