"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 486608
version: 0
title: Event Type - Secure OnBoard Communication
purpose: >
    Define general event types that are applicable for many ECUs supporting secure onboard
    communication

description: >
    Only applicable to ECUs supporting Secure On-Board Communication using Autosar SecOC Module as
    specified in "LC: Secure on-board communication".

    The ECU shall implement event type "Secure OnBoard Communication" data record with identifier
    0xD0BC as defined in OEM diagnostic database. Events related to secure on-board communication
    in ECU shall be logged. ECU may implement additional event codes (0x0A-0xFF) if more critical
    secure onboard communication events are supported upon agreement with OEM.

    Event Header: SecurityEventHeaderType 1 shall be applied, i.e. using one counter. Size 32 bits.
    Event Records:
    Time: Size 32 bits
    EventCode: As defined in "Table - Secure OnBoard Communication Event Code". Size 8 bits.
    AdditionalEventData:
    As defined in "Table: Secure OnBoard Communication Event Code". Size 32 bits.

    Event Code		Event	                            Additional EventData

    0x00	    	No History stored	                None;Default value: 0xFFFFFFFF

    0x01			An API service was called with      None;Default value: 0xFFFFFFFF
                    a null pointer
                    (SECOC_E_PARAM_POINTER)

    0x02			API service used without            None; Default value: 0xFFFFFFFF
                    module initialization
                    (SECOC_E_UNINIT )

    0x03			Invalid Message ID/ I-PDU           Invalid Message Identifier
                    Identifier to authenticate
                    (SECOC_E_INVALID_PDU_SDU_ID)

    0x04			Crypto service failed               None; Default value: 0xFFFFFFFF
                    (SECOC_E_CRYPTO_FAILURE)

    0x05			SecOC message authentication        Failed Message Identifier
                    verification failed

    0x06			Freshness value at limit or         None; Default value: 0xFFFFFFFF
                    reached maximum value

    0x07			Initialization of SecOC failed      None; Default value: 0xFFFFFFFF
                   (SECCOC_E_INIT_FAILED)

    0x08		    No freshness value available        None; Default value: 0xFFFFFFFF
                    from the Freshness Manager
                    (SECOC_E_FRESHNESS_FAILURE)

    0x09			Invalid freshness value				None; Default value: 0xFFFFFFFF
                    from the Freshness Manager

    0x0A-FF		    Reserved for future use             None; Default value: 0xFFFFFFFF
                    /ECU specific event codes

    Table: Secure OnBoard Communication Event Code

    Access Control: Option (3) as defined in "REQPROD 469450: Security Audit Log - Access Control"
    shall be applied.

details:
    Verify Event Type - Secure On-Board Communication with WriteDataByIdentifier request and
    reading DID 'D0BC' and compare response length to event time, event code & event data
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SIO = SupportFileIO
SUTE = SupportTestODTB2()


def compare_event_len_with_respective_bits(event_type ,res_event_len, expected_bit_len):
    """
    compare length of event time, event code, event data are equal to 32-bits, 8-bits and 32 bits
    Args:
        event_type (str) : event time, event code or event data
        res_event_len (str) : length of event time, event code or event data from response
        expected_bit_len(str): expected length of event time, event code or event data
    Returns:
        bool: True when response event length is equal to expected event length of
              respective event type
    """
    if res_event_len == expected_bit_len:
        logging.info("%s:%s is equal to %s", event_type, res_event_len, expected_bit_len)
        return True

    logging.info("%s:%s is not equal to %s", event_type, res_event_len, expected_bit_len)
    return False


def verify_event_time_code_data(response_items):
    """
    Verify length of event time, event code, event data are equal to 32-bits, 8-bit and 32 bits.
    Args:
        response_items (dict) : response from ECU
    Returns:
        bool: True on lengths of event time, event code, event data are as expected
    """
    results = []
    event_time_len = len(response_items[2]['sub_payload'])
    event_code_len = len(response_items[3]['sub_payload'])
    event_data_len = len(response_items[4]['sub_payload'])

    #Compare Latest successful event - Time is 32 bits
    results.append(compare_event_len_with_respective_bits('event time', event_time_len, 8))

    #Compare Latest successful event - Event Code is 8 bits
    results.append(compare_event_len_with_respective_bits('event code', event_code_len, 2))

    #Compare Latest successful event - Additional Event Data 32 bits
    results.append(compare_event_len_with_respective_bits('event data', event_data_len, 8))

    if len(results) != 0 and all(results):
        logging.info('Event Time, Code & Data Length are as expected')
        return True

    logging.error('Event Time, Code & Data Length are not as expected')
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify Event Type - Secure On-Board Communication with WriteDataByIdentifier request
            and reading DID 'D0BC' and compare responses length to event time, event code & event
            data
    expected_result: True on receiving positive response and length matching with expected
                     event time, event code & event data length
    """

    sec_oc_key_32byte = parameters['sec_oc_key']
    crc = SUTE.crc16(bytearray(sec_oc_key_32byte.encode('utf-8')))
    crc_hex = hex(crc)
    message = bytes.fromhex(parameters['sec_oc_did'] +
              parameters['sec_oc_key'] + crc_hex[2:])

    # Request WriteDataByIdentifier
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))
    if response[2:4] == '6E' and response[4:8] == parameters['sec_oc_did']:
        logging.info("Received positive response %s for request WriteDataByIdentifier ",
                    response[2:4])
        response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['sec_oc_event_read_did']))
        # compare Length of event time, event code, event data
        result = verify_event_time_code_data(response.data['details']['response_items'])
        return result

    logging.error("Test Failed: Expected positive response (6E), received"
                    " %s for request WriteDataByIdentifier", response[2:4])
    return False


def run():
    """
    Verify the Event Type - Secure On-Board Communication
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    parameters_dict = {'sec_oc_did':'',
                       'sec_oc_key':'',
                       'sec_oc_event_read_did':''}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose="Verify the Event Type-Secure On-Board "
                        " Communication")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
