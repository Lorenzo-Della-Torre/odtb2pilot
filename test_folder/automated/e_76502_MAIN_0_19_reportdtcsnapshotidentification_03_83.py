"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76502
version: 0
title: ReadDTCInformation (19) - reportDTCSnapshotIdentification (03)
purpose: >
    Since Volvo Car Corporation allows for multiple DTCSnapshot records for one DTC, it must be
    possible to read out which DTCSnapshot records a specific DTC has.

description: >
    The ECU shall support the service ReadDTCInformation - reportDTCSnapshotIdentification in all
    sessions where the ECU supports the service ReadDTCInformation.

details: >
    Verify ReadDTCInfoSnapshotIdentification and ReadDTCInfoSnapshotIdentification(83) with
    positive reply and empty response respectively in both default and extended session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_can import SupportCAN

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()


def request_snapshot_identification(dut):
    """
    Request ReadDTCInfoSnapshotIdentification
    Args:
        dut (Dut): An instance of Dut
    Return:
        (bool): True when received positive response
    """
    payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification", b'', b'')
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[4:8] != '5903':
        logging.error("Test Failed: Expected positive response '59', received %s",
                       response.raw[4:8])
        return False

    logging.info("Received positive response '59' as expected")
    return True


def request_snapshot_identification_83(dut):
    """
    Request ReadDTCInfoSnapshotIdentification(83)
    Args:
        dut (Dut): An instance of Dut
    Return:
        (bool): True when received empty response
    """
    payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification(83)", b'', b'')
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
    action: Request ReadDTCInfoSnapshotIdentification and ReadDTCInfoSnapshotIdentification(83)
            in default session
    expected result: Should give positive response for ReadDTCInfoSnapshotIdentification
                     and empty message for ReadDTCInfoSnapshotIdentification(83)
    """
    # Request ReadDTCInfoSnapshotIdentification
    result = request_snapshot_identification(dut)
    if not result:
        return False

    # Request ReadDTCInfoSnapshotIdentification(83)
    return request_snapshot_identification_83(dut)


def step_2(dut: Dut):
    """
    action: Request ReadDTCInfoSnapshotIdentification and ReadDTCInfoSnapshotIdentification(83)
            in extended session
    expected result: Should give positive response for ReadDTCInfoSnapshotIdentification
                     and empty message for ReadDTCInfoSnapshotIdentification(83)
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Request ReadDTCInfoSnapshotIdentification
    result = request_snapshot_identification(dut)
    if not result:
        return False

    # Request ReadDTCInfoSnapshotIdentification(83)
    result = request_snapshot_identification_83(dut)
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
    Verify ReadDTCInfoSnapshotIdentification and ReadDTCInfoSnapshotIdentification(83) with
    positive reply and empty response respectively in both default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)
        result_step = dut.step(step_1, purpose='Verify ReadDTCInfoSnapshotIdentification and '
                               'ReadDTCInfoSnapshotIdentification(83) in default session')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify ReadDTCInfoSnapshotIdentification and '
                                   'ReadDTCInfoSnapshotIdentification(83) in extended session')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
