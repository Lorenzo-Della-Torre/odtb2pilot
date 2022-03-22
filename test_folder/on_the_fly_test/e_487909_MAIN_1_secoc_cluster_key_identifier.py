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
    Verify the identify and differentiate key for each SecOC cluster participating in Secure
    On-Board communication
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM


CNF = Conf()
SE27 = SupportService27()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def cluster_key_identifier(dut, did, cluster_id):
    """
    cluster_key_identifier request
    Args:
        dut (class object): dut instance
        did (str): did to be read
        cluster_id (str): cluster identifier
        parameters (dict): yml parameters
    Returns:
        response (str): ECU response code
    """

    payload = SC_CARCOM.can_m_send("DynamicallyDefineDataIdentifier", b'\x01'
                                   + bytes.fromhex(did)
                                   + bytes.fromhex(cluster_id)
                                   , b'')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw

def step_1(dut):
    """
    action: Initiate security access in Extended session
    expected_result: Security access successful in extended session
    """
    # Define did from yml file
    parameters_dict = { 'define_did': '',
                        'cluster_key_identifier':'',
                        'cluster_key_identifier2':''}

    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # ECU in Extended Session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Security access Successful")
        return True, parameters

    logging.error("Test Failed: Security access denied")
    return False


def step_2(dut, parameters):
    """
    action: Verify SecOC Cluster Key Identifier (i.e 0001)
    expected_result: Positive response
    """
    response = cluster_key_identifier(dut, parameters['define_did'],
                                      parameters['cluster_key_identifier'])

    if response[0:2] == '71':
        logging.info("Received positive response %s for RoutineControlRequestSID", response[0:2])

        if response[10:14] == parameters['cluster_key_identifier']:
            logging.info("SecOC Cluster Key Identifier %s",response[10:14])
            return True

    msg ="Test failed: Expected positive response, received {} & Incorrect SecOC ClusterKeyId "\
          .format(response)
    logging.error(msg)
    return False


def step_3(dut, parameters):
    """
    action: Verify SecOC Cluster Key Identifier (i.e 0002)
    expected_result: Positive response
    """
    response = cluster_key_identifier(dut, parameters['define_did'],
                                      parameters['cluster_key_identifier2'])

    if response[0:2] == '71':
        logging.info("Received positive response %s for RoutineControlRequestSID", response[0:2])

        if response[10:14] == parameters['cluster_key_identifier2']:
            logging.info("SecOC Cluster Key Identifier %s",response[10:14])
            return True

    msg ="Test failed: Expected positive response, received {} & Incorrect SecOC ClusterKeyId "\
          .format(response)
    logging.error(msg)
    return False


def run():
    """
    Verify the identify and differentiate key for each SecOC cluster participating in Secure
    On-Board communication
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, parameters = dut.step(step_1, purpose="Initiate security Access in Extended"
                                          " session diagnostic session")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose=" Verify SecOC Cluster Key Identifier"
                               " (i.e 0001)")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose=" Verify SecOC Cluster Key Identifier"
                               " (i.e 0002)")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
