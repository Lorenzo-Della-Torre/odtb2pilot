"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53856
version: 2
title: : The SBL shall include all PBL functionality
purpose: >
    To simplify the bootloader implementation, to have the possibility to do a workaround
    if an error has occurred in the PBL and that no calls are necessary from the SBL to the PBL.

description: >
    The SBL shall include the complete PBL functionality.

details: >
    Verify all of the PBL services are included in SBL services
    Steps:
        1. Get all PBL and SBL services from sddb services dictionary
        2. Compare and verify all of the PBL services are included in SBL services
"""

import logging
from hilding.dut import DutTestError
from hilding.dut import Dut


def get_boot_loader_service(dut, boot_loader_type):
    """
    Get boot loader services from sddb services dictionary
    Args:
        dut (Dut): An instance of Dut
        boot_loader_type (str): Boot loader type (pbl or sbl)
    Returns:
        services_list (list): Boot loader services
    """
    services = dut.conf.rig.sddb_services
    services_list = []
    for service in services[boot_loader_type]:
        services_list.append(service)

    if len(services_list) != 0:
        return services_list

    logging.error("%s services not found in sddb services dictionary", boot_loader_type)
    return None


def step_1(dut: Dut):
    """
    action: Get primary boot loader services
    expected_result: True when received list of PBL services
    """
    pbl_services_list = get_boot_loader_service(dut, 'pbl')
    if pbl_services_list is not None:
        logging.info("Received PBL services as expected")
        return True, pbl_services_list

    logging.error("Test Failed: Received unexpected services %s", pbl_services_list)
    return False, None


def step_2(dut: Dut):
    """
    action: Get secondary boot loader services
    expected_result: True when received list of SBL services
    """
    sbl_services_list = get_boot_loader_service(dut, 'sbl')
    if sbl_services_list is not None:
        logging.info("Received SBL services as expected")
        return True, sbl_services_list

    logging.error("Test Failed: Received unexpected services %s", sbl_services_list)
    return False, None


def step_3(dut: Dut, pbl_services_list, sbl_services_list):
    """
    action: Compare and verify all of the primary boot loader services are
            included in secondary boot loader services
    expected_result: True when all PBL services are present in SBL services
    """
    # pylint: disable=unused-argument
    result = []
    unsupported_pbl = []

    # Comparing the length of PBL and SBL service list
    if len(sbl_services_list) >= len(pbl_services_list):
        for pbl_service in pbl_services_list:
            if pbl_service in sbl_services_list:
                result.append(True)
            else:
                result.append(False)
                unsupported_pbl.append(pbl_service)

    if all(result) and len(result) != 0:
        logging.info("All PBL services are present in SBL services as expected")
        return True

    logging.error("Test Failed: PBL services %s are not present in SBL services", unsupported_pbl)
    return False


def run():
    """
    Verify all of the PBL services are included in SBL services
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=25)
        result_step, pbl_services_list = dut.step(step_1, purpose='Get PBL services')

        if result_step:
            result_step, sbl_services_list = dut.step(step_2, purpose='Get SBL services')

        if result_step:
            result_step = dut.step(step_3, pbl_services_list, sbl_services_list, purpose='Compare'
                                                                           ' SBL and PBL services')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
