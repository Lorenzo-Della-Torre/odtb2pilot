"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 480618
version: 1
title: Security Access message identifier

purpose: >
    To ensure that different inputs is used when calculating authentication data and
    for easy identification of message in the sequence

description: >
    The message_identifier for the different messages shall be:
    clientRequestSeed: 0x0001
    serverResponseSeed: 0x0002
    clientSendKey: 0x0003
    serverResponseKey: 0x0004, reserved for future use.

details: >

    Validate Security Access response of clientRequestSeed,
    serverResponseSeed, clientSendKey with correct message identifier.

    Validate Security Access response of  clientRequestSeed and
    clientSendKey with incorrect message identifier

"""

import time
import logging
from hilding.conf import Conf
from hilding.dut import DutTestError
from hilding.dut import Dut
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

CNF = Conf()
SSA = SupportSecurityAccess()
SIO = SupportFileIO()


def security_access_method(dut: Dut):
    """
    Security Access to ECU and store response of all sub functions in dictionary
    Args:
                dut (class object): dut instance

    Results: payload_dict
    """
    payload_dict = {'client_seed': '', 'server_seed': '', 'client_key': ''}

    SSA.set_keys(CNF.default_rig_config)
    SSA.set_level_key(1)
    # Prepare request for a “client request seed”
    payload = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(payload)
    payload_dict['client_seed'] = payload
    # Prepare server seed payload by truncating first 2 bytes of message
    payload_dict['server_seed'] = response.raw[4:]

    result = SSA.process_server_response_seed(bytearray.fromhex(payload_dict['server_seed']))
    payload = SSA.prepare_client_send_key()
    payload_dict['client_key'] = payload
    response = dut.uds.generic_ecu_call(payload)
    # Prepare response from  6th byte to 6+4 bytes for server response key
    response = response.raw[6:(6+4)]
    result = SSA.process_server_response_key(bytearray.fromhex(response))
    if result != 0:
        logging.error("Security Access to ECU not Successful")
    return payload_dict


def step_1(dut: Dut):
    """
    action: Perform all the Security Access methods i.e clientRequestSeed,
            serverResponseSeed, clientSendKey and Validate correct
            message identifiers.
    expected_result: Positive response with valid message identifier.
    """
    # Sleep time to avoid NRC37
    time.sleep(5)
    parameters = SIO.extract_parameter_yml("*", "message_identifier")
    if parameters is not None:
        message_identifier = parameters
        dut.uds.set_mode(2)
        # Security Access to ECU
        payload_dict = security_access_method(dut)

        # comparing bytearray converted client_seed payload value from 4:8(0001) with
        # message identifier 0001
        if bytearray.hex(payload_dict['client_seed'][4:6]) != message_identifier[0]:
            msg = "Incorrect message identifier {} received for clientRequestSeed\
                               ".format(bytearray.hex(payload_dict['client_seed'][4:6]))
            raise DutTestError(msg)

        # comparing server_seed payload value from 4:8(0002) with message identifier 0002
        if payload_dict['server_seed'][4:8] != message_identifier[1]:
            msg = "Incorrect message identifier {} received for serverResponseSeed\
                              ".format(payload_dict['server_seed'][4:8])
            raise DutTestError(msg)

        # comparing bytearray converted client_key payload value from 4:8(0003) with
        # message identifier 0003
        if bytearray.hex(payload_dict['client_key']).upper()[4:8] != message_identifier[2]:
            msg = "Incorrect message identifier {} received for clientSendKey\
                               ".format(bytearray.hex(payload_dict['client_key']).upper()[4:8])
            raise DutTestError(msg)

        msg = "Message identifiers for subfunctions clientRequestSeed, serverResponseSeed and "\
              "clientSendKey are {}, {}, {} as expected".format(\
               bytearray.hex(payload_dict['client_seed'][4:6]),payload_dict['server_seed'][4:8],\
               bytearray.hex(payload_dict['client_key']).upper()[4:8])

        logging.info(msg)
        return True

    logging.error("Test Failed: Yml Parameter not Found or incorrect message identifier")
    return False


def step_2(dut: Dut):
    """
    action: Perform clientRequestSeed with incorrect message identifier
            and compare response with 7F to validate negative response.
    expected_result: Negative response 0x7F in the can message.
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(2)
    SSA.set_keys(CNF.default_rig_config)
    SSA.set_level_key(1)

    # prepare request for a “client request seed”
    payload = SSA.prepare_client_request_seed()

    # Corrupt payload with message identifier 0x0004
    payload[2] = 0x00
    payload[3] = 0x04
    response = dut.uds.generic_ecu_call(payload)

    # Check NRC 31(requestOutOfRange) for corrupted client key in response.raw
    if response.raw[6:8] == "31":
        logging.info("Received NRC 31(requestOutOfRange) for incorrect message identifier for seed"
                    " request as expected")
        return True
    msg = "Test failed: Expected NRC 31(requestOutOfRange), received {}".format(response)
    logging.error(msg)
    return False


def step_3(dut: Dut):
    """
    action: Perform clientSendKey with incorrect message identifier
        and compare response with 7F to validate negative response.
    expected_result: Negative response 7F in the can message.
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(2)
    SSA.set_keys(CNF.default_rig_config)
    SSA.set_level_key(1)

    # prepare client request seed
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Prepare server seed payload by truncating first 2 bytes of message
    server_res_seed = response.raw[4:]
    SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))
    payload = SSA.prepare_client_send_key()

    # Corrupt payload with message identifier 0x0004
    payload[2] = 0x00
    payload[3] = 0x04
    response = dut.uds.generic_ecu_call(payload)

    # Check NRC 31(requestOutOfRange) for corrupted client key in response.raw
    if response.raw[6:8] == "31":
        logging.info("Received NRC 31(requestOutOfRange) for incorrect message identifier for key "
        "response as expected")
        return True

    msg = "Test failed: Expected NRC 31(requestOutOfRange), received {}".format(response)
    logging.error(msg)
    return False


def run():
    """
    Validate Security Access response of clientRequestSeed,
    serverResponseSeed, clientSendKey with correct message identifier
    and incorrect message identifier.

    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Security Access to ECU and verify correct message"
                              " identifiers")

        if result_step:
            result_step = dut.step(step_2, purpose="Check clientRequestSeed with incorrect message"
                                  " identifier")

        if result_step:
            result_step = dut.step(step_3, purpose="Check clientSendKey with incorrect message"
                                   " identifier")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
