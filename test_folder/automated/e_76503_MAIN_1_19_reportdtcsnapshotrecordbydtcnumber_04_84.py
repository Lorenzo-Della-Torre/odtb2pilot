"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76503
version: 1
title: ReadDTCInformation (19) - reportDTCSnapshotRecordByDTCNumber (04)
purpose: >
    Snapshot of data values shall be stored along with the DTC when the criteria is fulfilled in
    order for sampling a snapshot. This snapshot data shall be possible to read out.

description: >
    The ECU shall support the service ReadDTCInformation - reportDTCSnapshotRecordByDTCNumber
    in all sessions where the ECU supports the service ReadDTCInformation.

details: >
    Verify ReadDTCInfoSnapshotRecordByDTCNumber and ReadDTCInfoSnapshotRecordByDTCNumber(84) with
    positive reply and empty response respectively in both default and extended session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_can import SupportCAN

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()


def request_snapshot_record_dtc_no(dut):
    """
    Request ReadDTCInfoSnapshotRecordByDTCNumber
    Args:
        dut (Dut): An instance of Dut
    Return:
        (bool): True when received positive response
    """
    payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                    bytes.fromhex('058D00'), bytes.fromhex('FF'))
    response = dut.uds.generic_ecu_call(payload)

    if response.raw[2:6] != '5904':
        logging.error("Test Failed: Expected positive response '59', received %s",
                       response.raw[2:6])
        return False

    logging.info("Received positive response '59' as expected")
    return True


def request_snapshot_record_dtc_no_84(dut):
    """
    Request ReadDTCInfoSnapshotRecordByDTCNumber(84)
    Args:
        dut (Dut): An instance of Dut
    Return:
        (bool): True when received empty response
    """
    payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber(84)",
                                    bytes.fromhex('058D00'), bytes.fromhex('FF'))
    try:
        dut.uds.generic_ecu_call(payload)
    except UdsEmptyResponse:
        pass

    if not SC.can_messages[dut["receive"]]:
        logging.info("Empty response received from ECU as expected")
        return True

    logging.error("Test Failed: Expected empty response, received %s",
                   SC.can_messages[dut["receive"]])
    return False


def step_1(dut: Dut):
    """
    action: Verify ReadDTCInfoSnapshotRecordByDTCNumber and
            ReadDTCInfoSnapshotRecordByDTCNumber(84) in default session
    expected result: True when received positive response for ReadDTCInfoSnapshotRecordByDTCNumber
                     and empty message for ReadDTCInfoSnapshotRecordByDTCNumber(84)
    """
    # Request ReadDTCInfoSnapshotRecordByDTCNumber
    result = request_snapshot_record_dtc_no(dut)
    if not result:
        return False

    # Request ReadDTCInfoSnapshotRecordByDTCNumber(84)
    return request_snapshot_record_dtc_no_84(dut)


def step_2(dut: Dut):
    """
    action: Verify ReadDTCInfoSnapshotRecordByDTCNumber and
            ReadDTCInfoSnapshotRecordByDTCNumber(84) in extended session
    expected result: True when received positive response for ReadDTCInfoSnapshotRecordByDTCNumber
                     and empty message for ReadDTCInfoSnapshotRecordByDTCNumber(84)
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Request ReadDTCInfoSnapshotRecordByDTCNumber
    result = request_snapshot_record_dtc_no(dut)
    if not result:
        return False

    # Request ReadDTCInfoSnapshotRecordByDTCNumber(84)
    result = request_snapshot_record_dtc_no_84(dut)
    if not result:
        return False

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 3:
        logging.info("ECU is in extended session as expected")
        return True

    logging.error("Test Failed: ECU is not in extended session")
    return False


def run():
    """
    Verify ReadDTCInfoSnapshotRecordByDTCNumber and ReadDTCInfoSnapshotRecordByDTCNumber(84) with
    positive reply and empty response respectively in both default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)
        result_step = dut.step(step_1, purpose='Verify ReadDTCInfoSnapshotRecordByDTCNumber and '
                                               'ReadDTCInfoSnapshotRecordByDTCNumber(84) in '
                                               'default session')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify ReadDTCInfoSnapshotRecordByDTCNumber '
                                                   'and ReadDTCInfoSnapshotRecordByDTCNumber(84) '
                                                   'in extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
