"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72026
version: 5
title: Storage of global DTC snapshot data when not available.

purpose: >
    If data received from the network is not available at the sampling moment
    the last received value will be the most useful to store.

description: >
    If global DTC snapshot data received from the vehicle network is not available
    when the sampling criteria is fulfilled, the latest received value shall be
    used and stored as DTC snapshot data.
    In case the ECU has not received a value in the current operation cycle,
    the ECU shall instead present a value representing “correct value not available.

details: >
    Read global DTC snapshot data and validate
"""

import logging
import copy
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding import get_conf
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def extract_sub_payload(payload):
    """
    Extract all 'F' from payload
    Args:
        payload(str): DTC DIDs sub payload
    Returns: extracted sub_payload
    """
    sub_payload = ''
    for val in payload:
        if val == 'F':
            sub_payload = sub_payload + val
    if not sub_payload:
        return payload
    return sub_payload


def extract_dtc_dids(response):
    """
    Extract DTC DIDs name from global snapshot
    Args:
        response(dict): DTC snapshot response
    Returns: Extracted DTC DIDs
    """
    dtc_did_list = []
    # Get DTC DIDs from DTC snapshot
    for snapshot in response.data['details']['snapshot_dids']:
        if snapshot['name'] == 'Global Snapshot':
            for did in snapshot['did_ref'].values():
                dtc_did_list.append(did)

    return dtc_did_list


def get_dtc_sub_payload_size_from_sddb(dtc_did):
    """
    Get all DTC DID sub payload size from sddb file
    Args:
    dtc_did(str) : DTC DID form global snapshot
    Returns: sub payload size of corresponding DID from sddb file
    """

    conf = get_conf()
    sddb_file = conf.rig.sddb_dids
    if sddb_file is None:
        logging.error('Test Failed: sddb_file is empty or not found')
        return None

    sddb_dids_dict = sddb_file['app_did_dict']
    size = None
    for sddb_did, value in sddb_dids_dict.items():
        if sddb_did == dtc_did:
            size = value['size']

    return size


def step_1(dut: Dut):
    '''
    action: Read global DTC snapshot and extract DTC DIDs from snapshot response
    expected_result: True with DTC DIDs, DTC response on successful reading DTC
                     snapshot and extract DIDs
    '''
    parameters_dict = {'dtc_service': '',
                       'mask': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None, None

    dtc_snapshot = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                         bytes.fromhex(parameters['dtc_service']),
                                         bytes.fromhex(parameters['mask']))
    dtc_response = dut.uds.generic_ecu_call(dtc_snapshot)

    if dtc_response.raw[4:6] != '59':
        logging.error("Test Failed: Invalid response or DTC snapshot not readable")
        return False, None, None

    # Extract DTC DIDs from global snapshot
    dtc_did_list = extract_dtc_dids(dtc_response)

    if len(dtc_did_list) > 0:
        logging.info("DTC DIDs extracted %s", dtc_did_list)
        return True, dtc_did_list, dtc_response.raw

    logging.error("Test Failed: No DTC DIDs found in snapshot")
    return False, None, None


def step_2(dut: Dut, dtc_did_list):
    '''
    action: Read DTC DIDs and extract sub_payload from DID response
    expected_result: True when successfully read DTC DIDs and sub_payload
    '''
    payload_size_list = []
    for dtc_did in dtc_did_list:
        # get DTC DID from sddb file
        size = get_dtc_sub_payload_size_from_sddb(dtc_did)

        response = dut.uds.read_data_by_id_22(bytes.fromhex(dtc_did))
        if response.raw[6:8] != '31':
            did_payload_dict = {}
            did_payload_dict['did_name'] = dtc_did
            did_payload_dict['size'] = size
            # Extract only F from sub payload and calculate length
            if response.data['body'][4:][:1] == 'F':
                sub_payload = extract_sub_payload(response.data['body'][4:])
                did_payload_dict['length'] = len(sub_payload) + \
                                             len(did_payload_dict['did_name'])
            else:
                did_payload_dict['length'] = len(response.data['body'])

            payload_size_list.append(did_payload_dict)
        else:
            logging.error("Test Failed: Invalid response or DID %s not readable", dtc_did)

    if len(payload_size_list) >0:
        logging.info("Sub payload extracted successfully")
        return True, payload_size_list

    logging.error("Test Failed: None of the DTC DIDs are readable")
    return False, None


def step_3(dut: Dut, payload_size_list, dtc_response):
    """"
    action: Verify and compare DTC snapshot data
    expected_result: True on successful verification fo DTC snapshot data
    """
    #pylint: disable=unused-argument
    results = []
    init_pos = 20
    for element in payload_size_list:
        # Read subpayload byte size
        payload_size_bytes = int(element['size'])

        # Copy DTC response
        dtc_data = copy.deepcopy(dtc_response[init_pos:init_pos+element['length']])
        # Extract subpayload of each DIDs from global snapshot
        dtc_sub_payload_data = extract_sub_payload(dtc_data[4:])
        init_pos = init_pos + element['length']

        # Compare DTC subpayload length
        if payload_size_bytes*2 == len(dtc_sub_payload_data) and dtc_sub_payload_data == \
            'FF'*payload_size_bytes:
            results.append(True)
            logging.info("Received payload %s and byte size %s as expected for DID %s",
                         dtc_sub_payload_data, payload_size_bytes, element['did_name'])
        else:
            results.append(False)
            logging.error("Test Failed: Expected %s, received payload %s and byte size %s "
                          "for DID %s", 'FF'*payload_size_bytes, dtc_sub_payload_data,
                          payload_size_bytes, element['did_name'])
    if all(results):
        logging.info("Received expected DTC snapshot data")
        return True

    logging.error("Test Failed: Unexpected DTC sub payload received")
    return False


def run():
    """
    Verify DTC snapshot data
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step, dtc_did_list, dtc_response = dut.step(step_1, purpose="Read the global "
                                                      "dtc snapshot and extract DTC DIDs")
        if result_step:
            result_step, payload_size_list = dut.step(step_2, dtc_did_list, purpose="Read DTC "
                                                 "DIDs and extract sub_payload")
        if result_step:
            result_step = dut.step(step_3, payload_size_list, dtc_response, purpose="Verify "
                                   "DTC snapshot data")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
