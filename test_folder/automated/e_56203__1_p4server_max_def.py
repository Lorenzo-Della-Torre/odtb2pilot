"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
reqprod: 56203
version: 1
title: P4Server_max definition
purpose: >
    To define and set the performance timing conditions how long time
    the server is allowed to process a diagnostic request.

description: >
    The timing parameter P4Server_max is the maximum time between the
    reception of a request (Server T_Data.ind) and the start of
    transmission of the final response (Server T_Data.req).

    Note:
        A final response is a positive response or a negative response other
        than response code 0x78 “requestCorrectlyReceived-ResponsePending".
        In case of a request to schedule periodic responses, the initial
        positive or negative response that indicates the acceptance or 30
        non-acceptance of the request to schedule periodic responses shall be
        considered the final response.

details:
    Loop through all possible services, if the service is defined in the .sddb
    we check if the defined service has a P4server_max != P2server_max. In that
    case we send a predefined request to the server and check that the response
    is within P4server_max.
"""
import sys
import logging
import time

from hilding.dut import Dut
from hilding.dut import DutTestError


# Test environment jitter estimated at 30 milliseconds
TEST_ENV_JITTER = 30

# P4Server_max lookup table (in milliseconds).
# Taken from SWRS chapter: 3.1.3.2.1.2.4, revision 4.
p4server_lut = {'22' : 200,
                '2A' : 200,
                '2C' : 200,
                '2E' : 5000,
                '3D' : 5000,
                '14' : 3500,
                '19' : 500,
                '31' : {
                    'type_1' : 5000,
                    'type_x' : 200},
                '34' : 1000,
                '35' : 1000,
                '36' : 5000,
                '37' : 15000,
                '38' : 1000}

# Individual payloads for each service where p2Server_max != P4Server_max
service_lut =  {
    # Picked a random DID - EDA0 seemed appropriate
    '22' : b'\x22\xED\xA0',
    # Data (2-4) bytes taken from REQ 67867
    '2A' : b'\x2A\x01\xF2\x00',
    # Data (2-4) bytes taken from REQ 67867
    '2C' : b'\x2C\x01\xF2\x00',
    # Unsure if 2E is implemented (REQ 67867 checks that response is:
    # 'ServiceNotSupported')
    '2E' : b'\x00\x00\x00\x00',
    # Not implemented as of writing this script, see REQ 76489.
    '3D' : b'\x00\x00\x00\x00',
    # Data (2-4) bytes taken from REQ 76496
    '14' : b'\x14\x0B\x4A\x00',
    # Taken from support_carcom.py (ReadDTCInfoSnapshotIdentification)
    '19' : b'\x19\x03',
    '31' : {
    # All services below, unsure which data bytes are the correct ones to send.
        'type_1' : b'\x00\x00',
        'type_x' : b'\x00\x00'},
    '34' : b'\x00\x00',
    '35' : b'\x00\x00',
    '36' : b'\x00\x00',
    '37' : b'\x00\x00',
    '38' : b'\x00\x00'}


def p4_server_max_services(dut: Dut, sw_level):
    """
    Loop through all services and if it is defined
    in the .sddb and p4server_max != p2server_max for
    that service, send request and make sure it is
    less than p4server_max.
    """
    for i in range(0xFF + 1):
        # Convert integer (i) to its hex representation without the '0x' prefix.
        service_str = f'{i:X}'

        if service_str in sw_level and service_str in p4server_lut:
            # Service 31 is a special case since it has two different
            # p4server_max alternatives.
            if service_str == '31':
                # First send a type 1 routine which has 5000ms to respond.
                __send(dut, service_str, service_lut[service_str]['type_1'],
                            p4server_lut[service_str]['type_1'])

                time.sleep(1)

                # Send a another type of routine which has 200ms to respond.
                __send(dut, service_str, service_lut[service_str]['type_x'],
                            p4server_lut[service_str]['type_x'])

            else:
                # All other p4server_max services.
                __send(dut, service_str, service_lut[service_str],
                            p4server_lut[service_str])


def __send(dut: Dut, service, payload, timeout):
    """
    Send request and measure time

    Work in progress comment:

        I am unsure if this is the right way to measure
        the time, the responses seem to be very quick.
    """
    dut.uds.generic_ecu_call(payload)

    # Wait P4Servermax to get the timestamp for the last received response?
    logging.debug("Waiting p4server_max: %sms", timeout)
    time.sleep(timeout/1000)

    # Check final response < p4server_max
    elapsed_time = dut.uds.milliseconds_since_request()
    actual = timeout + TEST_ENV_JITTER
    if elapsed_time > actual:
        raise DutTestError(
            f'Response took too long for service: {service}\n'
            f'Allowed: elapsed_time\nActual: {actual}\n')

    logging.debug("Time for response: %sms", elapsed_time)


def run():
    """
    Run - Call other functions from here

    Note: 'manage.py sddb' must be run before this script.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 1000 seconds.
        dut.precondition(timeout=1000)

        services = dut.conf.rig.sddb_services

        # P4server_max in application (Default)
        dut.step(p4_server_max_services, services["app"])

        # Change to programming sessoin
        logging.info("Changing mode to mode 2 (primary bootloader)")
        dut.step(dut.uds.set_mode, 2, False)

        # P4server_max in primary bootloader
        dut.step(p4_server_max_services, services["pbl"])

        # Activate secondary bootloader
        logging.info("Activating secondary bootloader.")
        dut.step(dut.uds.enter_sbl)

        # P4server_max in secondary bootloader
        dut.step(p4_server_max_services, services["sbl"])

        # Wait for the ECU exit programming session.
        time.sleep(5)
        result = True

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
