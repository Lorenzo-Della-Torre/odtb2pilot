"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72041
version: 3
title: Support for DTC time stamp #20
purpose: >
    To provide enhanced information about the occurrence of a fault, that may be useful in the
    analysis of the fault.

description: >
    For all DTCs supported by the ECU a data record identified by DTCExtendedDataRecordNumber=20
    shall be implemented according to the following definition:
    •	The record value shall be equal to the global real time (data record 0xDD00) that is taken
        the first time FDC10 reaches a value that is equal to or greater than UnconfirmedDTCLimit,
        since DTC information was last cleared.
    •	The stored data record shall be reported as a 4 byte value.

details: >
    Verify DTC snapshot has a time record 'DD00'
    Steps:
        1. Get time data from DTC snapshot
        2. Retrieve a timestamp from the response
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import global_timestamp_dd00
from supportfunctions.support_carcom import SupportCARCOM

SC_CARCOM = SupportCARCOM()


def step_1(dut: Dut):
    """
    action: Get time data from DTC snapshot
    expected_result: True when DTC snapshot has a time record 'DD00'
    """
    payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                    b'\x0B\x4A\x00',
                                    b'\x20')
    response = dut.uds.generic_ecu_call(payload)

    if response.raw[2:4] != '59':
        logging.error("Test Failed: Expected positive response 59 for DTC, received %s",
                       response.raw)
        return False, None

    # Get global snapshot from DTC snapshot
    filtered_global_snapshot=[]
    for snapshot_dids in response.data['details']['snapshot_dids']:
        if snapshot_dids['name'] == 'Global Snapshot':
            filtered_global_snapshot.append(snapshot_dids)

    if len(filtered_global_snapshot) == 0:
        logging.error("Test Failed: No global snapshot DID found in the DTC snapshot")
        return False, None

    # Get did 'DD00' from global snapshot in DTC snapshot
    for snapshot in filtered_global_snapshot:
        if 'DD00' in snapshot['did_ref'].values():
            logging.info("Time record found in the DTC snapshot")
            return True, response

    logging.error("Test Failed: No time record found in the DTC snapshot")
    return False, None


def step_2(dut: Dut, dtc_response):
    """
    action: Retrieve a timestamp from the response
    expected_result: True when retrieved timestamp is greater than or equal
                     to unconfirmed dtc limit
    """
    response = dut.uds.read_data_by_id_22(global_timestamp_dd00)

    if response.raw[2:4] == '7F':
        logging.error("No global_timestamp data received")
        return False

    global_real_time = (int(response.raw[8:16], 16))*100
    unconfirmed_dtc_limit = int(dtc_response.data['details']['unconfirmed_dtc_limit'])

    # Comparing global real time with unconfirmed dtc limit
    if global_real_time >= unconfirmed_dtc_limit:
        logging.info("Received time stamp %s, which is greater than %s, as expected",
                      global_real_time, unconfirmed_dtc_limit)
        return True

    logging.error("Test Failed: Expected %s time stamp, received %s", unconfirmed_dtc_limit,
                   global_real_time)
    return False


def run():
    """
    Verify DTC snapshot has a time record 'DD00'
    Steps:
        1. Get time data from DTC snapshot
        2. Retrieve a timestamp from the response
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step, dtc_response = dut.step(step_1, purpose="Get time data from DTC snapshot")

        if result_step:
            result_step = dut.step(step_2, dtc_response, purpose="Retrieve a timestamp from"
                                                                 " the response")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
