"""
reqprod: 74109
version: 2
title: Allowed diagnostic services
purpose: >
    Define which diagnostic services to allow. Ensure all suppliers uses the
    same diagnostic services as well as preventing supplier from using not
    not allowed diagnostic services.

description: >
    The ECU shall only support the diagnostic services specified in the
    requirement sections from Volvo Car Corporation.

details:
    Read which serives are defined in the sddb file.
    If the service is not defined, send the request to the ECU and
    expect a negative response.

    The time for last frame sent to first frame received is measured
    for each undefined service and compared against P2Server_max.

    According to REQPROD 74140 the ECU shall use P2Server_max as P4Server_max
    as the timing parameterfor a negative response for diagnostic
    services not supported by the ECU.
"""
import sys
import logging
import time
import build.services as services

from hilding.dut import Dut
from hilding.dut import DutTestError

# Test environment jitter estimated at 30 milliseconds
TEST_ENV_JITTER = 30

def step_1(dut, application, p2server_max):
    """
    action:
        Loop through 0 - FF and check if the service is defined
        in the .sddb file.
        If the service is defined, the service is not called by the script.

        However if the service is not defined the script sends a request
        to the ECU and expects a negative response.

        A check of p2server_max is also done for each undefined service.

    expected_result:
        Negative response within the time limit of p2server_max.
    """
    __allowed_diagnostic_services(dut, application, p2server_max)

def step_3(dut, pbl, p2server_max):
    """
    action:
        Loop through 0 - FF and check if the service is defined
        in the .sddb file.
        If the service is defined, the service is not called by the script.

        However if the service is not defined the script sends a request
        to the ECU and expects a negative response.

        A check of p2server_max is also done for each undefined service.

    expected_result:
        Negative response within the time limit of p2server_max.
    """
    __allowed_diagnostic_services(dut, pbl, p2server_max)

def step_5(dut, sbl, p2server_max):
    """
    action:
        Loop through 0 - FF and check if the service is defined
        in the .sddb file.
        If the service is defined, the service is not called by the script.

        However if the service is not defined the script sends a request
        to the ECU and expects a negative response.

        A check of p2server_max is also done for each undefined service.

    expected_result:
        Negative response within the time limit of p2server_max.
    """
    __allowed_diagnostic_services(dut, sbl, p2server_max)

def __allowed_diagnostic_services(dut: Dut, sw_level, p2server_max):

    payload = b'\x00'
    for i in range(0xFF + 1):
        # Convert integer (i) to its hex representation without the '0x' prefix.
        service_str = f'{i:X}'

        if service_str not in sw_level:
            # If the service is not defined the .sddb file we need to check the response.
            service_str = i.to_bytes((i.bit_length() + 7) // 8 or 1, 'big')

            # Append some data bytes (irrelevant what the data is).
            payload = service_str + b'\x00\x00'

            # Send undefined service, expect a negative response.
            received_data = dut.uds.generic_ecu_call(payload)

            if '037F' not in received_data.raw:
                # Something else than a negative response was received.
                raise DutTestError(f"Failed: Response for service {service_str} is not negative.")

            if dut.uds.milliseconds_since_request() > p2server_max + TEST_ENV_JITTER:
                # Took too long to receive response from the server.
                raise DutTestError(f"Failed: Service {service_str} took too long to respond.")
        else:
            logging.info("Service %s is defined in sddb, pass.", service_str)

def run():
    """
    Run - Call other functions from here

    Note: 'manage.py sddb' must be run before this script.
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()

    # P2server_max is 50ms in application.
    p2server_max = 50

    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 1000 seconds.
        dut.precondition(timeout=1000)

        # Start with application since default session is active.
        dut.step(step_1, services.app, p2server_max, purpose='Checking services in application.')

        # Step down to programming session.
        logging.info("Changing mode to mode 2 (primary bootloader)")
        dut.step(dut.uds.set_mode, 2, False)

        # P2server_max is 25ms in programming session (PBL and SBL)
        p2server_max = 25

        # Go through the primary bootloader services.
        dut.step(step_3, services.pbl, p2server_max, purpose='Checking services in PBL.')

        # Activate secondary bootloader
        logging.info("Activating secondary bootloader.")
        dut.step(dut.uds.enter_sbl)

        # Go through the secondary bootloader services.
        dut.step(step_5, services.sbl, p2server_max, purpose='Checking services in SBL.')

        # Wait for the ECU exit programming session.
        time.sleep(5)
        result = True

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
