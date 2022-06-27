"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487895
version: 1
title: SecOC Diagnostic Trouble Code - Detection of corrupt data received
purpose: >
    To handle the situation where there may be a customer complaint and a symptom associated
    with the ECU generating the DTC but the root cause is located on another ECU which may or
    may not be exhibiting any symptoms.

description: >
    If the ECU at application layer detects, by the verification result provided by the SecOC data
    protection mechanism, that a data value received from other ECU is corrupted and where this
    eventually causes the receiving ECU to take failsafe actions that causes customer symptoms
    (reconfiguration with reduced functionality, driver notification etc.) this shall be identified
    with a corresponding DTC. A data value is corrupt if the final SecOC verification is
    not successful. The same DTC is to be set for a tested signal independent of type of SecOC
    verification failure reported to the application layer (verification failure, freshness or
    authentication code failure).

    The monitor shall be implemented as follows:
    • Test Run Criteria (TRC):
        o The DTC test for detection of corrupt data received from other ECU by SecOC shall run
          each time updated data, for which a test is implemented, is received from another ECU.
          The DTC shall be set when the number of SecOC verification failures for any signal
          exceeds its configurable limit for setting the DTC.
        o The ECU shall have a common base DTC 0xD0C5 for all signals protected by SecOC in a ECU.
        o The DTC shall use Failure Type Byte (FTB) 0x68.
        o The ECU supporting SecOC shall implement a mandatory global DTC snapshot data record that
          shall include the following data identifier record, as defined in Global Master Reference
          Database (GMRDB).
            • 0xD0CC - Secure On-board Communication verification failures

    Example.
    An ECU has two SecOC protected signals, sent in two separate PDUs.
    The failure limits for both signals are 100.
    At ECU reset/start, the current failure counters are reset for both signals.
    If 100 (0x64) final SecOC verification failures are detected for Signal 2 and 72 (0x48) for
    Signal 1, the DTC shall be set with following snapshot data record:

    Parameter name                                  Length(Bits)          Values

    Signal 1 SecOC failure count limit exceeded         1               "No" - 0b0
    Signal 2 SecOC failure count limit exceeded         1               "Yes" - 0b1

details: >
    Verify the status of DTC 0xD0C568 when the failure count limit is exceeded for all of the
    SecOC protected signals.
"""

import logging
import odtb_conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_can import SupportCAN, CanParam

SIO = SupportFileIO()
SC_CARCOM = SupportCARCOM()
SC = SupportCAN()


def subscribe_to_signal(parameters):
    """
    Request subscribe to signal
    Args:
        parameters (dict): send, receive
    """
    can_p_ex: CanParam = {
    "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
    "send" : parameters['send'],
    "receive" : parameters['receive'],
    "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.parameter_adopt_teststep(can_p_ex)

    # Subscribe to signal
    SC.subscribe_signal(can_p_ex, 15)


def request_read_dtc_snapshot(dut, parameters):
    """
    Request read DTC information snapshot
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): dtc_did, failure_type_byte, mask
    Returns:
        dtc_response (dict): dtc_response
    """
    dtc_snapshot = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                        bytes.fromhex(parameters['dtc_did']+
                                        parameters['failure_type_byte']),
                                        bytes.fromhex(parameters['mask']))
    dtc_response = dut.uds.generic_ecu_call(dtc_snapshot)
    return dtc_response


def verify_dtc_snapshot_data(dut, parameters, signal_name):
    """
    Verify DTC snapshot information data
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): dtc_did, failure_type_byte, mask
        signal_name (str): SecOC signals
    Returns:
        (bool): True when DTC is triggered
    """
    dtc_response = request_read_dtc_snapshot(dut, parameters)

    if dtc_response.raw[4:6] != '59':
        logging.error("Test Failed: Expected positive response '59' for signal: %s, received %s",
                      signal_name, dtc_response.raw)
        return False

    # Get data identifier record 'D0CC' from global snapshot in DTC snapshot
    dtc_response_data = dtc_response.data['details']['snapshot_dids']
    for snapshot_dids in dtc_response_data:
        if snapshot_dids['name'] == 'Global Snapshot':
            if 'D0CC' in dtc_response_data['did_ref'].values():
                logging.info("DTC has triggered for signal: %s as expected", signal_name)
                return True

    logging.error("Test Failed: DTC has not triggered for signal: %s", signal_name)
    return False


def verify_sec_oc_signals(dut, parameters):
    """
    Verify dtc snapshot for each SecOC protected signal
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): dtc_did, failure_type_byte, mask, signals
    Returns:
        results (list): Results of SecOC signals
    """
    results= []
    # Read dtc snapshot for all SecOC protected signal
    for signal_name, sig_data in parameters['signals'].items():

        # Subscribe to signal
        subscribe_to_signal(parameters)

        for _ in range(int(sig_data['failure_count_byte'], 16)):
            # Send faulty data of SecOC protected signal to ECU
            dut.uds.generic_ecu_call(bytes.fromhex(sig_data['data']))

        result = verify_dtc_snapshot_data(dut, parameters, signal_name)
        results.append(result)

        # Unsubscribe to signal
        SC.unsubscribe_signal(signal_name)

    return results


def step_1(dut: Dut):
    """
    action: Verify the status of DTC 0xD0C568 for all of the SecOC protected signals
    expected_result: True when successfully verified the status of DTC for all SecOC signals
    """
    # Read yml parameters
    parameters_dict = {'send': '',
                       'receive': '',
                       'dtc_did': '',
                       'failure_type_byte': '',
                       'mask': '',
                       'signals':{}}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    results = verify_sec_oc_signals(dut, parameters)

    if all(results) and len(results) != 0:
        logging.info("Successfully verified the status of DTC for all signals")
        return True

    logging.error("Test Failed: Failed to verify the status of DTC for some signals")
    return False


def run():
    """
    Verify the status of DTC 0xD0C568 when the failure count limit is exceeded for all of the
    SecOC protected signals.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=900)

        result= dut.step(step_1, purpose="Verify the status of DTC 0xD0C568 for all of the "
                                         "SecOC protected signals")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
