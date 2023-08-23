"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 481861
version: 0
title: : Check Security Access method supported.
purpose: >
    For the client to identify supported authentication method in the ECU.

description: >
    The server shall support the type 1 routine control "Check SecurityAccess Method"
    (routine identifier 0x0231) as defined in the Global Master Reference Database.
    The request "Record" shall be one byte long, hexadecimal representation, and contain
    the requested security access level (odd number, i.e. subfunction security_access_type
    for clientRequestSeed message).

    The response "Result value" parameter from "Check SecurityAccess Method" shall be two
    bytes long, hexadecimal representation, and contain the supported "authentication_method"
    when successfully completed.
    The server shall respond with result value 0xFFFF if no method is supported for requested
    security access level

    The server is required to response with supported "authentication_method" in actual
    diagnostic session only, i.e. if the client request is for a security access level
    not supported in active current session the server is allowed to respond with 0xFFFF.

    The routine control "Check SecurityAccess Method" shall not be protected by security
    access. It shall be supported in both programmingSession and extendedSession.
    The response time "P4server_max" in all supported sessions shall be equal to
    "P2Server_max", that is defined in general requirements for routine controls in
    programmingSession.

    Table - Routine Control "Check Security Access Method" request message structure-
    ===================================================================================
    Message direction:	    Client => Server
    Message Type:	        Diagnostic request Check SecurityAccess Method
    ===================================================================================
    Data byte   |	    Description                         |  Byte Value (Hex)
    ===================================================================================
    #1        	    Routine Control request SID	                31
    -----------------------------------------------------------------------------------
    #2	            Subfunction routine control type	        01
    -----------------------------------------------------------------------------------
    #3              Routine Identifier  [byte 1], msb           02
    #4	            Routine Identifier [byte 2], lsb	        31
    -----------------------------------------------------------------------------------
    #5	            Record: Security Access Level	            01, 03,  ..(odd number)
    -----------------------------------------------------------------------------------
    Notes: The routine control record byte (security access level) shall be the
    requested security access level for subfunction requestSeed, i.e. odd number only.
    ------------------------------------------------------------------------------------


    Table - Routine Control "Check Security Access Method" response message structure-
    ===================================================================================
    Message direction:	Client =>  Server
    Message Type:	Diagnostic response Check SecurityAccess Method
    ===================================================================================
    Data byte	        Description 	                       Byte Value (Hex)
    ===================================================================================
    #1	            Routine Control response SID	            71
    ------------------------------------------------------------------------------------
    #2	            Subfunction routine control type	        01
    ------------------------------------------------------------------------------------
    #3              Routine Identifier  [byte 1], msb           02
    #4	            Routine Identifier [byte 2], lsb	        31
    ------------------------------------------------------------------------------------
    #5	            Routine info (status and type)	            See general
                                                                diagnostic requirements
    ------------------------------------------------------------------------------------
    #6              Result value  [byte 1], msb                 00-FF
    #7	            [byte 2], lsb	                            00-FF
    ------------------------------------------------------------------------------------
    Notes: The result value shall be the supported authentication_method for requested
    security access level, i.e. byte 1 msb shall be the authentication_method msb.
    ------------------------------------------------------------------------------------

details: >
    Routine request verification for security access levels and check for response with supported
    authentication method i.e. '0001' or 'FFFF' based on the security access level for programming
    and extended session respectively.

"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

SE27 = SupportService27()
S_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def routine_control_request(dut, sa_level, p2server_max):
    """
    Call routine control request and verify response time is less than p2server_max time frame
    Args:
        dut (Dut): An instance of Dut
        sa_level (int): security access level
        p2server_max (int): maximum allowed response time based on session

    Returns:
        auth_method (str) : last 4 bytes of the routine control request response
    """
    # Preparing routine control request payload 31010231 + (Security access level)
    byte_routine_request = b'\x01\x02\x31' + bytes.fromhex(sa_level)
    payload = S_CARCOM.can_m_send("RoutineControlRequestSID", byte_routine_request, b'')

    response = dut.uds.generic_ecu_call(payload)
    time_elapsed = dut.uds.milliseconds_since_request()

    # Expecting 71 in response.raw[2:4] for positive response of routine control
    if response.raw[2:4] == '71':
        # Extract last 2 bytes of response which is authentication method
        auth_method = response.raw[-4:]
        if time_elapsed >= p2server_max:
            logging.error("Time elapsed %sms which is greater than p2Server_max %sms for SA level"
                          " %s", time_elapsed, p2server_max, sa_level)
            auth_method = ''
        else:
            logging.info("Elapsed time %sms is less than p2Server_max %sms for SA level %s as"
                        " expected", time_elapsed, p2server_max, sa_level)
    else:
        logging.error("Response received %s for routine control request(SA level - %s)",
                       response.data['nrc'], sa_level)
        auth_method = ''

    return auth_method


def verify_sa_levels_and_p2_server_max(dut, sa_levels_and_auth_method, max_response_time):
    """
    Verify security access levels and allowed authentication method is within max_response_time
    Args:
        dut (Dut): An instance of Dut
        sa_levels_and_auth_method (dict): dictionary containing security access levels
                    and allowed authentication method
        max_response_time (int): maximum response time for respective session
    Returns:
        (bool): True correct authentication method received for SA level
    """
    results = []
    for sa_level, allowed_value in sa_levels_and_auth_method.items():
        routine_control_response = routine_control_request(dut, sa_level, max_response_time)
        if routine_control_response == allowed_value:
            logging.info("Received %s for SA level %s as expected", routine_control_response,
                                                                    sa_level)
            results.append(True)
        elif routine_control_response == '':
            # Invalid response or response time exceeded max_response_time returns
            # empty routine_control_response, handled in routine_control_request()
            results.append(False)
        else:
            logging.error("Invalid authentication method %s received for SA level %s, expected %s",
                           routine_control_response, sa_level, allowed_value)
            results.append(False)

    if len(results) != 0 and all(results):
        return True

    return False


def verify_sa_levels(dut, sa_levels_and_auth_method, session):
    """
    Verify routine control request
    Args:
        dut (Dut): An instance of Dut
        sa_levels_and_auth_method (dict): dictionary containing security access levels
                    and allowed authentication method
        session (str): programming or extended
    Returns:
        (bool): True when received all SA level before security access
    """
    results = []
    for sa_level, allowed_value in sa_levels_and_auth_method.items():
        # Preparing routine control request payload 31010231 + (Security access level)
        byte_routine_request = b'\x01\x02\x31' + bytes.fromhex(sa_level)
        payload = S_CARCOM.can_m_send("RoutineControlRequestSID", byte_routine_request, b'')

        response = dut.uds.generic_ecu_call(payload)

        # Expecting 71 in response.raw[2:4] for positive response of routine control
        if response.raw[2:4] == '71':
            # Extract last 2 bytes of response which is authentication method
            response_auth_method = response.raw[-4:]
            if response_auth_method == allowed_value:
                logging.info("Received %s for SA level %s before security access as expected ",
                              response_auth_method, sa_level)
                results.append(True)
            else:
                logging.error("Invalid authentication method %s received for SA level %s , "
                              "expected %s before security access",response_auth_method,
                               sa_level, allowed_value)
                results.append(False)
        else:
            logging.error("Received NRC %s for SA level %s in %s session before security access.",
                           response.data['nrc'], sa_level, session)
            results.append(False)

    if len(results) != 0 and all(results):
        return True

    return False


def step_1(dut: Dut, yml_parameters):
    """
    action: Verify routine control request respond with authentication method i.e. '0001' or
            'FFFF' based on the security access level for programming session.

    expected_result: ECU should send supported authentication method for respective security access
            level for programming session.
    """
    dut.uds.set_mode(2)

    programming_sa_levels = yml_parameters['programming_sa_levels_and_auth_method']
    p2_server_max = yml_parameters['p2_server_max_programming']

    # Verify routine control request without security access
    result_without_security_access = verify_sa_levels(dut, programming_sa_levels, 'programming')

    # Security access
    sa_result = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                        step_no=272, purpose="SecurityAccess")

    if not sa_result:
        logging.error("Test failed: Security access denied for programming session")
        return False

    # Verify routine control request with security access
    result_with_security_access = verify_sa_levels_and_p2_server_max(dut, programming_sa_levels,
                                                                   p2_server_max)

    if result_with_security_access and result_without_security_access:
        return True

    logging.error("Test Failed: Verification of supported security access levels and allowed"
                                " authentication method failed for programming session")
    return False


def step_2(dut: Dut, yml_parameters):
    """
    action: Verify routine control request with supported authentication method i.e. '0001' or
            'FFFF' based on the security access level for extended session.

    expected_result: ECU should send supported authentication method for respective security access
                     level for extended session.
    """

    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    extended_sa_levels = yml_parameters['extended_sa_levels_and_auth_method']
    p2_server_max = yml_parameters['p2_server_max_extended']

    # Verify routine control request without security access
    result_without_security_access = verify_sa_levels(dut, extended_sa_levels, 'extended')

    # Security access
    time.sleep(10)
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                        step_no=272, purpose="SecurityAccess")

    if not sa_result:
        logging.error("Test failed: Security access denied for extended session")
        return False

    # Verify routine control request with security access of extended session
    result_with_security_access = verify_sa_levels_and_p2_server_max(dut, extended_sa_levels,
                                                                    p2_server_max)

    if result_with_security_access and result_without_security_access:
        return True

    logging.error("Test Failed: Verification of supported security access levels and allowed"
                                " authentication method failed for extended session")
    return False


def run():
    """
    Verify routine control request for different security access levels for programming or
    extended session. Routine request response should contain supported authentication method
    i.e. '0001' or 'FFFF' based on the security access level for programming and extended session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'programming_sa_levels_and_auth_method' : '',
                       'p2_server_max_programming' : '',
                       'extended_sa_levels_and_auth_method' : '',
                       'p2_server_max_extended' : ''}
    try:
        dut.precondition(timeout=70)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose=" Verify routine control request"
                              " respond with authentication method i.e. '0001' or 'FFFF' based"
                              " on the security access level for programming session")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify routine control request"
                                   " with supported authentication method i.e. '0001' or 'FFFF' "
                                   "based on the security access level for extended session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
