"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56204
version: 1
title: P4Server_max equal to P2Server_max
purpose: >
    To define the behaviour when the P4Server_max is equal to P2Server_max

description: >
    The server is not allowed to response with a negative response code 0x78
    (requestCorrectlyReceived-ResponsePending) if P4Server_max is the same as P2Server_max.

    Note: The value of P2Server_max is defined in section Timing parameters. P4Server_max is
    defined for each diagnostic service in LC : VCC - UDS Services.

details: >
    Send multiple service 23 requests without delay trying to provoke a NRC 78.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL

SC = SupportCAN()
SUTE = SupportTestODTB2()
SIO = SupportFileIO
SC_CARCOM = SupportCARCOM()
SSBL = SupportSBL()


def evaluate_response(dut, negative_resp, valid_data, log=True):
    """
    Log result of data comparison (true/false)
    If it was a NRC - pretty print number and corresponding string
    If comparison is false and data does not contain a NRC log as unexpected.
    Finally, return result.
    Args:
        dut (Dut): dut instance
        negative_resp (str): negative response
        valid_data (str): string of bytes
        log (bool): Log result of data comparison (true/false)
    Returns:
        result (bool)
    """
    # Check if empty
    if len(dut["receive"]) == 0:
        logging.error("No data in dut['receive']")
        return False

    nrc = SC.can_messages[dut["receive"]][0][2][0:4] == negative_resp
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring=valid_data)

    # Log result
    if log:
        logging.info("Result: %s", result)

        # Check if it was a negative return code. If so, print.
        if result and nrc:
            logging.info("NRC: %s", SUTE.pp_can_nrc(SC.can_messages[dut["receive"]][0][2][6:8]))

        # If its not result and not a NRC possible corrupt message.
        else:
            logging.info("Unexpected data received: %s", SC.can_messages[dut["receive"]][0][2])

    return result


def step_1(dut: Dut, parameters):
    """
    action: Request service 23, try to provoke a NRC 78.
    expected_result: If NRC 78 is received test returns False
    """
    etp: CanTestExtra = {"step_no": 1,
                         "purpose" : 'Request service 23, try to provoke a NRC 78',
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1 }

    # Construct the message
    service_call = bytearray(bytes.fromhex(parameters['uds_service']))
    service_call = service_call + bytes.fromhex(parameters['address_and_length_format_identifier'])\
                   + bytes.fromhex(parameters['memory_address'])\
                   + bytes.fromhex(parameters['memory_size'])

    cpay: CanPayload = {"payload": service_call,
                        "extra": ''}

    result = SUTE.teststep(dut, cpay, etp)

    # Send service 23
    for _ in range(parameters['num_of_resend']):
        SC.t_send_signal_can_mf(dut, cpay, True, 0x00)
        result = evaluate_response(dut, negative_resp=parameters['negative_resp'],
                                   valid_data=parameters['positive_resp_valid_data'], log=False)
        if not result:
            if not evaluate_response(dut, negative_resp=parameters['negative_resp'],
                                     valid_data=parameters['negative_resp_valid_data']):
                # Don't care about any other messages, reset result and keep going.
                result = True
            else:
                # Negative return code 78 received.
                break

    time.sleep(1)
    return result


def run():
    """
    Send multiple service 23 requests without delay trying to provoke a NRC 78
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    parameters_dict = {'uds_service': '',
                       'address_and_length_format_identifier': '',
                       'memory_address': '',
                       'memory_size': '',
                       'num_of_resend': 0,
                       'negative_resp': '',
                       'positive_resp_valid_data': '',
                       'negative_resp_valid_data': ''}
    try:
        dut.precondition(timeout=60)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose="Request service 23, try to "
                                                      "provoke a NRC 78")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
