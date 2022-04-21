"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487909
version: 1
title: SecOC Cluster Key Identifier
purpose: >
    To uniquely identify and differentiate key for each SecOC cluster participating in Secure
    On-Board communication

description: >
    All ECUs in SecOC cluster shall use the same secret key to generate or verify authentic
    message(s) between them. Secret key for each SecOC cluster shall be identified by a unique
    identifier, "Secure Onboard Communication Cluster Key Identifier" (a.k.a. SecOC Keyid),
    represented in two bytes length hexadecimal value and defined by OEM.
    ECU that support multiple SecOC clusters, that needs to store multiple keys for secure
    communication, shall use SecOC Cluster Key Identifier value to differentiate different keys
    for identifying respective SecOC clusters.

    ECU shall pre-configure and store all the SecOC Cluster Key Identifiers supported in the ECU.
    Which key identifiers that shall be configured and stored for each ECU shall be agreed with
    the OEM.

    Example configuration of SecOC Cluster Key Identifiers:
    SecOC Clusters		SecOC Cluster Key Identifier
    ECU A, ECU B  			0x0001
    ECU C, ECU D, ECU E 	0x0002
    ECU B, ECU A, ECU C 	0x0003

    Table: Example SecOC Cluster Key Identifiers

    From above example:
    ECU A will configure key identifiers 0x0001 and 0x0003
    ECU B will configure key identifiers 0x0001 and 0x0003
    ECU C will configure key identifiers 0x0002 and 0x0003
    ECU D and ECU E will configure key identifiers 0x0002 respectively

details: >
    Verify and differentiate key for each SecOC cluster participating in Secure
    On-Board communication
    Steps-
        1. Security access in Extended session
        2. Verify SecOC Cluster Key Identifiers (0001, 0002, 0003)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM

SE27 = SupportService27()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def request_cluster_key_identifiers(dut, did, cluster_id):
    """
    Routine Control Request SID(x31) to ECU
    Args:
        dut (Dut): dut instance
        did (str): Data identifier
        cluster_id (str): cluster key identifier
    Returns:
        response (str): raw response of ECU
    """

    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x01'
                                   + bytes.fromhex(did)
                                   + bytes.fromhex(cluster_id)
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def verify_response(response, cluster_id):
    """
    verify the response for service 0x31 and SecOC Cluster Key Identifier
    Args:
        response (str): ECU response
        cluster_id (str): cluster key identifier
    Returns:
        (bool): True when Valid SecOC Cluster Key Identifier received
    """
    # Extract and compare positive response 71
    if response[2:4] == '71':
        logging.info("Received positive response %s for RoutineControlRequestSID", response[2:4])

        # Extract and compare Cluster Key Identifiers
        if response[12:16] == cluster_id:
            logging.info("Valid SecOC Cluster Key Identifier %s received as expected",
                          response[12:16])
            return True
        logging.error("Test failed: Expected SecOC Cluster Key Identifier %s, received %s",
                       cluster_id, response[12:16])
        return False

    logging.error("Test failed: Expected response 71, received %s ", response)
    return False


def step_1(dut:Dut):
    """
    action: Initiate Security access in Extended session
    expected_result: Security access successful in Extended session
    """
    # Read yml parameters
    parameters_dict = { 'define_did': '',
                        'cluster_key_identifier':''}

    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Set ECU to Extended Session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Security access Successful")
        return True, parameters

    logging.error("Test Failed: Security access denied")
    return False, None


def step_2(dut:Dut, parameters):
    """
    action: Verify SecOC Cluster Key Identifiers(0001, 0002, 0003)
    expected_result: True on Successfully verified all of the SecOC cluster key identifiers
    """

    results = []
    for cluster_id in parameters['cluster_key_identifier']:
        response = request_cluster_key_identifiers(dut, parameters['define_did'], cluster_id)
        results.append(verify_response(response, cluster_id))

    if len(results) != 0 and all(results):
        return True

    return False


def run():
    """
    Verify and differentiate SecOC key for each SecOC cluster participating in Secure
    On-Board communication
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, parameters = dut.step(step_1, purpose="Initiate security access in extended"
                                                            " diagnostic session")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify SecOC Cluster Key"
                                                            " Identifiers(0001, 0002, 0003)")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
