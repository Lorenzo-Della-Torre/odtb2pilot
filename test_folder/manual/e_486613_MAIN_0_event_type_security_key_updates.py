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
    Verify event type 'Security key update' is implemented by programming keys and calling
    security key update did.
"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_sec_acc import SecAccessParam
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
        sa_level (str): HEX security level
    Returns:
        Response (bool): True if ECU is unlocked with given security access level
    """

    # Request a seed from ECU
    SSA.set_keys(dut.conf.default_rig_config)
    sa_level_base_16 = int(sa_level, 16)
    SSA.set_level_key(sa_level_base_16)
    payload = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(payload)

    # Calculate the key with the server seed
    server_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_seed))

    # Send key to unlock ECU
    payload = SSA.prepare_client_send_key()
    response = dut.uds.generic_ecu_call(payload)

    # Process response from ECU
    result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    if result != 0:
        logging.error("Security access denied.")
        return False

    logging.info("ECU unlock with security access %s", sa_level)
    return True


def program_key(dut: Dut, did, sa_key, valid_checksum=True):
    """
    Send a request to program the security access key
    Args:
        dut (Dut): Dut instance
        did (str): Security access DID
        sa_key (str): Security access key to write
    response
        response.raw (str): ECU response
    """

    # calculate crc16 checksum
    if valid_checksum:
        checksum = hex(SUTE.crc16(bytes.fromhex(sa_key)))
    else:
        checksum = hex(SUTE.crc16(bytes.fromhex(sa_key))+1)

    # prepare request to send to the ECU
    message = bytes.fromhex(did + sa_key + checksum[2:])

    # send request and store response
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                            message, b''))
    return response.raw


def read_success_failed_events(dut, did, event_type):
    """
    read did and get total number of successful or failed event count
    Args:
        dut(Dut): An instance of Dut
        did(str): Security key read DID
        event_type(str ): successful/failed
    Returns:
        (int): number of events of selected type
    """

    # read security key did
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    if response.raw[4:6] != '62':
        logging.error("Unable to read did %s. Received response: %s", did, response.raw)

    # count events
    if event_type == 'successful':
        total_events = response.data['details']['response_items'][0]['sub_payload']
    elif event_type == 'failed':
        total_events = response.data['details']['response_items'][1]['sub_payload']
    else:
        logging.error("event_type shall be 'successful' or 'failed' but is: %s", event_type)
        return None

    base = 16
    return int(total_events, base)


def step_1(dut: Dut, parameters):
    """
    action: Try to update security access key with incorrect checksum and verify failed events
            counter is increasing
    expected_result: Failed events counter is increased by one
    """

    # Setting up key
    sa_key: SecAccessParam = dut.conf.default_rig_config
    sa_key2write = sa_key["auth_key"]+sa_key["proof_key"]

    # Switch to extended diagnostic session
    dut.uds.set_mode(3)

    # Security access to ECU
    unlock_security_access = security_access(dut, sa_level='05')
    if not unlock_security_access:
        logging.error("Test Failed: security access denied")
        return False

    # count number of failed events
    init_failed_events = read_success_failed_events(dut, parameters['security_key_read_did'],
                                event_type='failed')
    if init_failed_events is None:
        logging.error("Unable to extract number of failed events")
        return False

    # program security access key
    response = program_key(dut, parameters['security_key_update_did'], sa_key2write,
                           valid_checksum=False)

    if response[2:8] != '7F2E31':
        logging.error("Incorrect response code. Expected 7F2E31 and received: %s", response)
        return False
    logging.info("Unable to update security access key with incorrect checksum")

    # Switch back to default session to disable security access
    dut.uds.set_mode(1)

    # count number of failed events
    final_failed_events = read_success_failed_events(dut, parameters['security_key_read_did'],
                                event_type='failed')
    if final_failed_events is None:
        logging.error("Unable to extract number of failed events")
        return False

    # compare number of failed events before and after trying to update key
    if init_failed_events + 1 != final_failed_events:
        logging.error("Test Failed: Unexpected number of failed events")
        return False
    logging.info("failed events counter increased by one as expected")

    return True


def step_2(dut: Dut, parameters):
    """
    action: Update security access key and verify successful events counter is increasing
    expected_result: Successful events counter is increased by one
    """

    # Setting up key
    sa_key: SecAccessParam = dut.conf.default_rig_config
    sa_key2write = sa_key["auth_key"]+sa_key["proof_key"]

    # switch to extended diagnostic session
    dut.uds.set_mode(3)

    # Security access to ECU
    unlock_security_access = security_access(dut, sa_level='05')
    if not unlock_security_access:
        logging.error("Test Failed: security access denied")
        return False

    # count number of successful events
    init_successful_events = read_success_failed_events(dut, parameters['security_key_read_did'],
                                event_type='successful')
    if init_successful_events is None:
        logging.error("Unable to extract number of successful events")
        return False

    # program security access key
    response = program_key(dut, parameters['security_key_update_did'], sa_key2write)

    if response[2:4] != '6E':
        logging.error("Unable to program security access key. response code: %s", response)
        return False
    logging.info("Security access key successfully updated")

    # Switch back to default session to disable security access
    dut.uds.set_mode(1)

    # count number of successful events
    final_successful_events = read_success_failed_events(dut, parameters['security_key_read_did'],
                                event_type='successful')
    if final_successful_events is None:
        logging.error("Unable to extract number of successful events")
        return False

    # compare number of successful events before and after updating key
    if init_successful_events + 1 != final_successful_events:
        logging.error("Test Failed: Unexpected number of successful events")
        return False
    logging.info("Successful events counter increased by one as expected")

    return True


def run():
    """
    Verify event type 'Security key update' is implemented by programming keys and calling
    security key update did.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'security_key_update_did':'',
                       'security_key_read_did':''}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Try to update "
                                "security access key with incorrect checksum and verify "
                                "failed events counter is increasing")
        result_step = result_step and dut.step(step_2, parameters, purpose="Update security "
                               "access key and verify successful events counter is increasing")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
