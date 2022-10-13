"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487972
version: 1
title: SecOC Cluster Key Identifier Storage
purpose: >
    Define SecOC Cluster Key Identifier storage requirements in ECU.

description: >
    ECU shall persistently store all the pre-configured SecOC Cluster Key
    Identifiers supported in the ECU.

    The SecOC Cluster Key Identifier(s) stored in ECU shall be protected
    from unauthorized use and it must not exist any other service/interface
    to alter the SecOC Cluster Key Identifier, e.g. by using diagnostic services
    (writeDataByIdentifer, requestUpload, writeMemoryByAddress, etc.) or by any other
    debug interface or -protocol.

details: >
    Verify SecOC Cluster Key Identifier is protected by using diagnostic service
    (ReadDataByIdentifier) in programming and extended session, with and without security access.
"""

import time
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
        response.raw (str): response from ECU
    """
    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                     bytes.fromhex(did)
                                   + bytes.fromhex(cluster_id)
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def verify_negative_response(response, cluster_id):
    """
    verify the negative response (NRC 7F)
    Args:
        response (str): ECU response
        cluster_id (str): cluster key identifier
    Returns:
        (bool): True when NRC 7F found
    """
    if response[2:4] == '7F' and response[6:8] == '7F':
        logging.info("Received negative response and ECU is protected from unauthorized access "
                    "by any other service/interface to alter the SecOC Cluster Key Id: %s",
                    cluster_id)
        return True

    logging.error("Test failed: Expected response NRC 7F, received %s and ECU is not protected"
                  " from unauthorized access.", response)
    return False


def step_1(dut:Dut, parameters):
    """
    action: Verify ECU shall be protected from unauthorized access without security access
    expected_result: True when NRC 7F for all of the SecOC cluster key identifiers
    """
    results = []
    for cluster_id in parameters['cluster_key_identifier']:
        response = request_cluster_key_identifiers(dut, parameters['did'], cluster_id)
        results.append(verify_negative_response(response, cluster_id))

    if len(results) != 0 and all(results):
        return True

    return False


def step_2(dut:Dut, parameters):
    """
    action: Verify ECU shall be protected from unauthorized access to alter while any of the
            services with security access in Programming session
    expected_result: True when NRC 7F for all of the SecOC cluster key identifiers
    """
    # Sleep time to avoid NRC37
    time.sleep(5)
    # Set ECU to Programming Session
    dut.uds.set_mode(2)
    result = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                step_no=272, purpose="SecurityAccess")
    if not result:
        logging.error("Test Failed: Security access denied")
        return False

    results = []
    for cluster_id in parameters['cluster_key_identifier']:
        response = request_cluster_key_identifiers(dut, parameters['did'], cluster_id)
        results.append(verify_negative_response(response, cluster_id))

    if len(results) != 0 and all(results):
        return True

    return False


def step_3(dut:Dut, parameters):
    """
    action: Verify ECU shall be protected from unauthorized access to alter while any of the
            services with security access in Extended session
    expected_result: True when NRC 7F for all of the SecOC cluster key identifiers
    """
    # Set ECU to Extended Session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                step_no=272, purpose="SecurityAccess")
    if not result:
        logging.error("Test Failed: Security access denied")
        return False

    results = []
    for cluster_id in parameters['cluster_key_identifier']:
        response = request_cluster_key_identifiers(dut, parameters['did'], cluster_id)
        results.append(verify_negative_response(response, cluster_id))

    if len(results) != 0 and all(results):
        return True

    return False


def run():
    """
    Verify ECU is been protected from unauthorized use and it must not exist any other
    service/interface to alter the SecOC Cluster Key Identifiers.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    # Read yml parameters
    parameters_dict = { 'did': '',
                        'cluster_key_identifier':''}

    try:
        dut.precondition(timeout=30)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify ECU shall be protected from"
                                          " unauthorized access without security access")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify ECU shall be protected from"
                                  " unauthorized access to alter while any of the services with "
                                  "security access in Programming session")

        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify ECU shall be protected from"
                                   " unauthorized access to alter while any of the services with"
                                   " security access in Extended session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
