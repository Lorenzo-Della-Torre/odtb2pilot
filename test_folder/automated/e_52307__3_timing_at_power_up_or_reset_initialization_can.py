"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52307
version: 3
title: Timing at power up or reset initialization CAN
purpose: >
    To ensure sufficient response time on frame level.

description: >
    A node shall be ready to receive and transmit CAN frames maximum TCANPowerWakeUpToApp
    after power is applied, a hardware reset and a diagnostic ECU Reset(hardReset).

    For nodes Type A, Type B and Type C the following case applies:
    - The permanent power supply is applied.

    For nodes Type D the following cases applies:
    - Power is supplied by a relay.
    - Ignition On or Clamp-15 goes active.

details: >
    Verify a node is ready to receive and transmit CAN frames within TCANPowerWakeUpToApp
    after power is applied or diagnostic ECU hard reset
    Steps-
        1. ECU hard rest
        2. Clear CAN messages
        3. Request to ECU for positive response within TCANPowerWakeUpToApp
"""

import logging
from threading import Thread
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import IoVmsDid
from supportfunctions.support_can import SupportCAN, CanParam, PerParam
from supportfunctions.support_can import CanMFParam
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SIO = SupportFileIO()


def start_periodic(stub, per_param):
    """
    Start sending periodic signal to ECU
    Args:
        stub(class object): Network stub
        per_param(dict): Can parameters
    Returns: None
    """
    SC.can_periodic[per_param["name"]] = [per_param["send"],
                                          per_param["id"],
                                          per_param["nspace"],
                                          per_param["frame"],
                                          per_param["interval"]]

    # Start periodic, repeat every per_interval (ms)
    thread_1 = Thread(target=SC.send_periodic, args=(stub, per_param["name"]))

    # Attached PeriodicThread and start
    thread_1.name = "PeriodicThread"
    thread_1.daemon = True
    thread_1.start()


def start_heartbeat(stub, hb_param):
    """
    Start heartbeat
    Args:
        stub(class object): Network stub
        hb_param(dict): Can parameters
    Returns: None
    """
    per_param = dict()
    per_param["name"] = 'heartbeat'
    per_param["send"] = True
    per_param["id"] = hb_param["id"]
    per_param["nspace"] = hb_param["nspace"]
    per_param["frame"] = hb_param["frame"]
    per_param["interval"] = hb_param["interval"]
    start_periodic(stub, per_param)


def send_signal(dut: Dut):
    """
    Send signal to ECU
    Args:
        dut(Dut): An instance of Dut
    Returns: DID response
    """
    # Set step number
    dut.uds.step = 100
    # Start heartbeat, repeat every 0.8 second
    heartbeat_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : dut.conf.rig.signal_periodic,
        "nspace" : dut.namespace.name,
        "protocol" : "can",
        "framelength_max" : 8,
        "padding" : True,
        "frame" : bytes.fromhex(dut.conf.rig.wakeup_frame),
        "interval" : 0.4
        }

    # Start heartbeat, repeat every x second
    start_heartbeat(dut.network_stub, heartbeat_param)

    can_p: CanParam = {"netstub": dut.network_stub,
                        "send": dut.conf.rig.signal_receive,
                        "receive": dut.conf.rig.signal_send,
                        "namespace": dut.namespace,
                        "protocol": dut.protocol,
                        "framelength_max": dut.framelength_max,
                        "padding" : dut.padding
                        }
    SC.subscribe_signal(can_p, timeout=30)

    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 10,
        "frame_control_flag": 48,
        "frame_control_auto": False
        }
    SC.change_mf_fc(can_p["receive"], can_mf)

    response = dut.uds.read_data_by_id_22(IoVmsDid.pbl_software_part_num_f125)
    # Reset step number
    dut.uds.step = 0
    return response.raw


def step_1(dut: Dut):
    """
    action: ECU hard reset and verify a node is ready to receive and transmit CAN frames
            within TCANPowerWakeUpToApp
    expected_result: True on successfully received positive response after ECU hard reset
    """
    # Read yml parameters
    parameters_dict = {'tcan_power_wakeup_time': 0}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    # ECU hard reset
    ecu_response = dut.uds.generic_ecu_call(bytes.fromhex('1101'))
    # ECU wakekup time
    ecu_wakeup_time = dut.uds.milliseconds_since_request()
    # Clear can message after successful ECU reset
    SC.clear_can_message(dut["receive"])

    if ecu_response.raw[2:4] == '51' and ecu_wakeup_time >= 5:
        # Send request to ECU after 5ms at least and get positive response
        response = send_signal(dut)
        # ECU positive response time
        response_time = dut.uds.milliseconds_since_request()
        # Time since ECU reset and positive response
        total_time = ecu_wakeup_time + response_time

        if response[4:6] == '62' and total_time <= 150:
            logging.info("Positive response (%s) time %sms after ECU reset is within "
                        "TCANPowerWakeUpToApp time %sms: ", response[4:6], total_time,
                        parameters['tcan_power_wakeup_time'])
            return True

        logging.error("Positive response (%s) time %sms after ECU reset is not within "
                    "TCANPowerWakeUpToApp time %sms: ", response[4:6], total_time,
                    parameters['tcan_power_wakeup_time'])
        return False

    logging.error("ECU hard reset did not performed")
    return False


def run():
    """
    Verify a node is ready to receive and transmit CAN frames within TCANPowerWakeUpToApp
    after power is applied or diagnostic ECU hard reset
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose="Verify ECU transmit frame within "
                          "TCANPowerWakeUpToApp time")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
