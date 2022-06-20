"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487906
version: 1
title: : SecOC Key Programmed Status- Diagnostic Trouble Code
purpose: >
    Define the Secure On-board Communication key diagnostic trouble code to identify if ECU is
    provisioned with Initial keys or production keys since none of the vehicle shall leave
    factory without production keys.

description: >
    ECU shall set base DTC 0xD0C4 with failure byte 0x51 as defined in the GMRDB,
    if at least one of the supported SecOC keys in the ECU are Initial keys.

    ECU shall clear DTC, 0xD0C451, upon successful write operation of all supported
    SecOC keys in the ECU.

    If any of the supported SecOC keys are provisioned back to initial key(s) from
    key value other than initial keys then DTC 0xD0C451 shall be set in the ECU in
    order to indicate that one or all of the SecOC keys are provisioned with an initial key.

details: >
    Verify if ECU is provisioned with Initial keys or production keys.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def read_secoc_dtc_d0c4(dut, parameters):
    """
    Read SecOC DTC did 'D0C4' and verify failure byte 0x51
    Args:
        dut (Dut): dut instance
        parameters (dict): did, clear_dtc, dtc_service
    Returns:
        (bool): True when received positive response
    """
    dtc_did_payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                         bytes.fromhex(parameters['dtc_service']),
                                         bytes.fromhex(parameters['mask']))
    response_dtc = dut.uds.generic_ecu_call(dtc_did_payload)

    message = response_dtc.raw
    pos = message.find(parameters['dtc_service'])
    if message[pos+4:pos+6] == parameters['dtc_service'][:-2]:
        logging.info("Received positive response %s as expected", message[pos+4:pos+6])
        return True

    logging.error("Test failed: Expected positive response , received %s", message[pos+4:pos+6])
    return False


def step_1(dut: Dut, parameters):
    """
    action: Read DID 'D0CB' Key Write Status
    expected_result: Positive response '62'
    """
    # Set extended Diagnostic Session
    dut.uds.set_mode(3)
    # Read did 'D0CB'
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['sec_oc_did']))
    # verify response for service id(62)
    if response.raw[0:2] == '62':
        logging.info("Received positive response %s after reading DID 'D0CB'", response.raw[0:2])
        return True, response.raw

    logging.error("Test failed: Expected positive response, received %s", response.raw)
    return False, None


def step_2(dut: Dut, parameters, did_response):
    """
    action: verify if all the SecOC keys are provisioned with Initial key
    expected_result: True on verified all the SecOC keys are provisioned with an initial key
    """
    sec_oc_keys_count = int((did_response[6:8]), 16)
    logging.info("Number of supported SecOC keys are %s :", sec_oc_keys_count)

    key_start = 8
    secoc_key_and_status = {}
    for _ in range(sec_oc_keys_count):
        # SecOC key id from the response
        key = did_response[key_start:key_start+4]
        # Status of supported SecOC key from the response
        prog_status = did_response[key_start+4:key_start+6]
        secoc_key_and_status[key] = prog_status
        key_start+=6

    results = []
    non_programmed_keys = []
    for key,programmed_status in secoc_key_and_status.items():
        if programmed_status == '01':
            non_programmed_keys.append(key)
            results.append(False)
        else:
            results.append(True)

    if all(results):
        logging.info("All keys are programmed")
        result = read_secoc_dtc_d0c4(dut, parameters)
        if not result:
            logging.info("Checked DTC not are present")
            return True
        logging.error("Test Failed: DTC are present")
        return False

    logging.info("Checked DTC for not programmed keys %s ", non_programmed_keys[0])
    result = read_secoc_dtc_d0c4(dut, parameters)

    if result:
        logging.info("Successfully verified all the SecOC keys are provisioned with an initial"
                     " key")
        return True

    logging.error("Test failed: Failed to verify one or all of the SecOC keys are provisioned"
                  " with an initial key")
    return False


def run():
    """
    Verify SecOC Key Programmed Status- Diagnostic Trouble Code
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'sec_oc_did': '',
                       'dtc_service': '',
                       'mask': ''}
    try:
        dut.precondition(timeout=60)
        # Read parameters from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, response = dut.step(step_1, parameters, purpose="Read DID D0CB Key Write"
                                                                     " Status")

        if result_step:
            result_step = dut.step(step_2, parameters, response, purpose="Verify the SecOC keys "
                                                                         "are provisioned with an"
                                                                         " initial key")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
