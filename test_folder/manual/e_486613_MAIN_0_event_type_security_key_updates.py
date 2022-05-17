"""

/*********************************************************************************/


Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 486613
version: 0
title: Event Type - Security Key Updates

purpose: >
    Define general event types that are applicable for many ECUs.
description: >
    The ECU shall implement event type "Security Key Updates" data record with identifier 0xD0C1
    as defined in OEM diagnostic database. Events related to updates in security keys such as
    symmetric keys, asymmetric keys, certificates shall be logged. ECU may implement additional
    Event codes (0x7B-7F, 0x8B-0xFF) if more critical key or certificate update events are
    supported in ECU upon agreement with OEM.

    Event Header: SecurityEventHeaderType 2 shall be applied, i.e. using two counters.
                  Size 32+32 bits.
    Event Records:
    Time. Size 32 bits
    EventCode. As defined in "Table - Security Key Updates Event Code". Size 8 bits.
    AdditionalEventData. As defined in "Table - Security Key Updates Event Code". Size 16 bits.

    Event Code		Event	                            Additional EventData
    0x00	    	No History stored	                None
    0x01			Failed attempt to update Asymmetric Total number of failed key update attempts
                    Public key for Software
                    Authentication
    0x02			Failed attempt to update security   Security Access level
                    access confidential keys
    0x03			Failed attempt to update Root       Total number of failed key update attempts
                    of trust secure boot key
    0x04			Failed attempt to update software
                    verification keys for secure boot	Total number of failed key update attempts
    0x05			Failed attempt to update secure
                    log authentication key				Total number of failed key update attempts
    0x06			Failed attempt to update secure
                    log encryption key (if supported)	Total number of failed key update attempts
    0x07			Failed attempt to update secure
                    onboard communication keys		    Total number of failed key update attempts
    0x08			Failed attempt to install/update
                    root certificate				    Certificate identity number - 2 Byte
                                                        (User defined)
    0x09			Failed attempt to install/update
                    intermediate certificate	       Certificate identity number - 2 Byte
                                                       (User defined)
    0x0A			Failed attempt to verify
                    certificate						   Certificate identity number - 2 Byte
                                                       (User defined)
    0x0B-7F		    Reserved for future or ECU
                    specific event codes			   Reserved for future or ECU specific event
                                                       code additional data
    0x80			Reserved	Reserved
    0x81			Successfully updated Asymmetric
                    Public key for Software
                    Authentication                   Total number of successful key update attempts
    0x82			Successfully updated security
                    access confidential keys		 Security Access level
    0x83			Successfully updated Root of
                    trust secure boot keys			 Total number of successful key update attempts
    0x84			Successfully updated software
                    verification keys for secure
                    boot				             Total number of successful key update attempts
    0x85			Successfully updated secure
                    log authentication key			 Total number of successful key update attempts
    0x86			Successfully updated secure
                    log encryption key (if supported)Total number of successful key update attempts
    0x87			Successfully updated secure
                    onboard communication keys		 Total number of successful key update attempts
    0x88			Successfully installed/updated
                    root certificate				 Certificate identity number - 2 Byte
                                                     (User defined)
    0x89			Successfully installed/updated
                    intermediate certificate		 Certificate identity number - 2 Byte
                                                     (User defined)
    0x8A			Certificate verified successfullyCertificate identity number - 2 Byte
                                                     (User defined)
    0x8B-FF		    Reserved for future or ECU
                    specific event codes			 Reserved for future or ECU specific event code
                                                     additional data
    Table - Security Key Updates Event Code

    Access Control: Option (3) as defined in "REQPROD 469450: Security Audit Log - Access Control"
    shall be applied.

details: >
    Verify successful and failed event count for security key updates with both correct
    and incorrect checksum.
"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SIO = SupportFileIO
SUTE = SupportTestODTB2()
SSA = SupportSecurityAccess()


def security_access(dut: Dut, sa_level):
    """
    Unlock security access levels to ECU
    Args:
        dut (Dut): Dut instance
        level (str): security level
    Returns:
        Response (str): Can response
    """
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(int(sa_level))
    payload = SSA.prepare_client_request_seed()

    response = dut.uds.generic_ecu_call(payload)
    # Prepare server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    payload = SSA.prepare_client_send_key()

    response = dut.uds.generic_ecu_call(payload)

    # Process server response key
    result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    if result != 0:
        logging.error("Security access not successful")
        return False

    return True


def event_count(response, event_type):
    """
    Get total number of successful or failed event count
    Args:
        response (str): Ecu response
        event_type(str): successful/failed
    Returns:
        total_events(int): total number of successful or failed events
    """
    if event_type == 'successful':
        total_events = response.data['details']['response_items'][0]['sub_payload']
    elif event_type == 'failed':
        total_events = response.data['details']['response_items'][1]['sub_payload']
    else:
        return None

    total_events = int(total_events, 16)
    return total_events


def read_success_failed_events(dut, did, event_type):
    """
    read did and get total number of successful or failed event count
    Args:
        dut(Dut): An instance of Dut
        did(str): Security key read DID
        event_type(str ): successful/failed
    Returns:
        (bool): True on positive response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if response.raw[4:6] == '62':
        logging.info("Received positive response %s for request security key updates did ",
                     response.raw[4:6])
        num_of_events = event_count(response, event_type)
        return num_of_events
    logging.error("Test Failed: Expected positive response (62), but received response: %s",
                   response.raw)
    return False


def request_write_data_id(dut:Dut, message):
    """
    Request WriteDataByIdentifier (0x2E)
    Args:
        dut(Dut): An instance of Dut
        message(bytes): request message
    Returns:
        (bool): True on positive response
    """
    # Request WriteDataByIdentifier
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))
    if response.raw[6:8] == '6E':
        logging.info("Received Positive response 6E for WriteDataByIdentifier request")
        return True

    logging.error("Test Failed: Expected 6E for WriteDataByIdentifier, received %s",
                    response.raw)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify Event Type - Security Key Updates with WriteDataByIdentifier request and
            reading DID 'D0C1' with correct key and wrong checksum
    expected_result: True on receiving positive response
    """

    dut.uds.set_mode(3)
    # Security access to ECU
    security_access_result= security_access(dut, sa_level='05')
    if not security_access_result:
        logging.error("Test Failed: security access denied")
        return False

    # checking number of successful event counts before write data by id
    result_before_successful_event = read_success_failed_events(dut,
                                     parameters['security_key_read_did'],
                                     event_type='successful')

    if result_before_successful_event is None:
        logging.error("Unable to extract number of successful events")
        return False

    # preparing message with correct CRC
    sa_key_32byte = parameters['security_log_authentication_key_data_record']
    crc = SUTE.crc16(bytearray(sa_key_32byte.encode('utf-8')))
    crc_hex = hex(crc)
    message = bytes.fromhex(parameters['security_key_update_did'] +
              parameters['security_log_authentication_key_data_record'] + crc_hex[2:])

    # write data by identifier request
    result = request_write_data_id(dut,message)
    if not result:
        return False

    # get number of successful event after writing the key
    result_after_successful_event = read_success_failed_events(dut,
                                    parameters['security_key_read_did'],
                                    event_type='successful')
    if result_after_successful_event is None:
        logging.error("Unable to extract number of successful events")
        return False

    # verify successful events is increased by 1
    if result_before_successful_event + 1 == result_after_successful_event:
        logging.info("Total number successful of event count increased by 1 as expected")
        return True
    logging.error("Test Failed: Total number successful events not increased")
    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify Event Type - Security Key Updates with WriteDataByIdentifier request and
            reading DID 'D0C1' with correct key and wrong checksum
    expected_result: True on receiving positive response
    """
    dut.uds.set_mode(3)
    # Security access to ECU
    security_access_result= security_access(dut, sa_level='05')
    if not security_access_result:
        logging.error("Test Failed: security access denied")
        return False

    # get number of failed event counts before write data by id
    result_before_failed_event = read_success_failed_events(dut,
                                 parameters['security_key_read_did'], event_type='failed')
    if result_before_failed_event is None:
        logging.error("Unable to extract number of failed events")
        return False

    # preparing message with incorrect CRC
    sa_key_32byte_crc = 'FF'*32
    crc = SUTE.crc16(bytearray(sa_key_32byte_crc.encode('utf-8')))
    crc_hex = hex(crc)[2:]
    crc_hex_incorrect = crc_hex[::-1]
    message = bytes.fromhex(parameters['security_key_update_did'] + sa_key_32byte_crc +\
                             crc_hex_incorrect)

    # write data by identifier request with incorrect CRC
    result = request_write_data_id(dut, message)
    if result:
        logging.error("Test Failed: Expected to get negative response as incorrect CRC is "
                     "provided with Write data by identifier request")
        return False

    # get number of failed event after writing the key
    result_after_failed_event = read_success_failed_events(dut,
                                parameters['security_key_read_did'], event_type='failed')
    if result_after_failed_event is None:
        logging.error("Unable to extract number of failed events")
        return False

    # verify failed events is increased by 1
    if result_before_failed_event + 1 == result_after_failed_event:
        logging.info("Total number count for failed events increased by 1 as expected")
        return True
    logging.error("Test Failed: Total number failed events not increased")
    return False


def run():
    """
    Verify successful and failed event count for security key updates with both correct
    and incorrect checksum.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'security_key_update_did':'',
                       'security_log_authentication_key_data_record':'',
                       'security_key_read_did':''}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify Event Type - Security Key"
                                                   " Updates with WriteDataByIdentifier request"
                                                   " with correct key & checksum "
                                                   "and read DID 'D0C1'")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify Event Type - Security Key"
                                                   " Updates with WriteDataByIdentifier request"
                                                   " with correct key & wrong checksum "
                                                   "and read DID 'D0C1'")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
