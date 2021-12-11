"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
reqprod: 469440
version: 0
title: Security Event Header
purpose: >
    Define general event types that are applicable for many ECUs.
    If there are other requirements that limits the possibility to log data, e.g. if the
    ECU is in a state where it lacks capabilities to write to non-volatile memory,
    the security audit log shall not override those requirements.
    Such an example might be bootloaders that lack write/erase non-volatile
    memory instructions (due to other requirements specified elsewhere).

description: >
    The ECU shall implement event type "Software Updates boot" data record with identifier 0xD048,
    i.e. for software download in ProgrammingSesssion. The trigger for a software update is
    started is a transition from 'no update of a "logical block" active' to 'update of logical
    block ongoing'. See "REQPROD 400894: Request Download - restrictions on number of addressed
    logical blocks" for transition conditions.

    Event Header: SecurityEventTypeHeader 2. Size 32+32 bits.
    Event Records:
    EventCode. As defined in "Table - Software Updates boot Event Code". Size 8 bits.
    AdditionalEventData:
    For successful updates: Software partnumber where the digits shall be BCD encoded and the
    3 characters (version suffix) shall be coded in ASCII, right justified with any unused
    digit filled with 0, in total 7 bytes. Any unused version suffix shall be filled with space,
    left justified. Example: "1234567<space><space>A" is represented (hex)
    as: "01 23 45 67 20 20 41", i.e. according to partnumber format requirements. Size 56 bits.
    If application partnumber location is not possible to derive in this session,
    the logical block number shall be used. When the logical block number is used,
    the unused bytes shall be set to zeroes, i.e. the first logical block is represented
    as 0x00000000000001. Size 56 bits.

    For failed attempts: The addressed logical block number, where value 0x01 is the first
    part checked in "Complete & Compatible" routine control response, 0x02 is the second and so on.
    Size 8 bits.

    Event Code    Event
    0x00    No History stored
    0x01    Software Download started but failed prior to CheckMemory (optional, see note)
    0x02    Software Download started but failed at CheckMemory

    0x80    Software Download started and successfully completed at CheckMemory
    Table - Software Updates boot Event Code

    Access Control: Option (3) as defined in "REQPROD 469450 : Security Audit Log - Access Control"
    shall be applied.

    Design considerations: If partnumber is part of log data, the design must ensure that a change
    of partnumber allocation does not require a bootloader update.

    Note.
    If EventCode 0x01 is supported, it shall be applied for all conditions that results in a
    transition from 'update of logical block ongoing' to any other state, except when the
    state transition is triggered by a successful CheckMemory.



details:
    The did is read from the ECU. It is verified that the DID is read and that the sddb
    contains header, event code and additional data.

    Script needs to be updated to fully cover requirement.
    More verification of the log content is needed. One would need to trigger several events
    to make sure the logs are correct. Right now only some smaller verifications are made
    of the content.

"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

SS27 = SupportService27()
SS34 = SupportService34()
SS31 = SupportService31()
SS11 = SupportService11()

def _get_success_reject(dut : Dut):
    """Extract the data for all accepted and rejected events

    Args:
        dut (Dut): [An Dut instance]

    Returns:
        [Lists]: [Returns 2 lists. One with successful event
        and one with rejected]
    """
    did = "D048"

    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))

    ret = {}

    ret["number_of_registered_successes"] =\
        int(res.extract_from_did('Total number of successful events')["data"])

    ret["number_of_registered_rejects"] =\
        int(res.extract_from_did('Total number of rejected events')["data"])

    logging.debug("ECUs response for %s : %s", did, res)

    sddb_response_items = dut.conf.rig.sddb_dids["resp_item_dict"][did]

    index_of_last_successful = int(len(sddb_response_items)/2)
    index_of_last_rejected = -2
    nbr_of_success_events = sddb_response_items[index_of_last_successful]["name"][0:2]
    nbr_of_reject_events = sddb_response_items[index_of_last_rejected]["name"][0:2]

    success_messages = []
    reject_messages = []

    #Creating a list containing all accepted events as dictionaries.
    for i in range(int(nbr_of_success_events)):
        #Look on sddb to understand the indexing
        event_code = \
            res.extract_from_did(sddb_response_items[2*i+2]["name"])
        additional_data = \
            res.extract_from_did(sddb_response_items[2*i+3]["name"])
        success_messages.append({"event_code" : event_code,"additional_data" : additional_data})

    #Creating a list containing all rejected events as dictionaries.
    rejected_start_index = int(nbr_of_success_events)*2+2
    for i in range(int(nbr_of_reject_events)):
        event_code = \
            res.extract_from_did(sddb_response_items[rejected_start_index+2*i]["name"])
        additional_data = \
            res.extract_from_did(sddb_response_items[rejected_start_index+1+2*i]["name"])
        reject_messages.append({"event_code" : event_code,"additional_data" : additional_data})

    ret["success_messages"] = success_messages
    ret["rejected_messages"] = reject_messages

    return ret

def __evaluate_did(dut: Dut, nbr_accepted, nbr_rejected):

    result = True

    res = _get_success_reject(dut)

    def test_accepted(result):
        event_code = message['event_code']["data"]

        try:
            bytes_object = bytes.fromhex(message["additional_data"]["data"][4*2:])
            ascii_string = bytes_object.decode("ASCII")

            additional_data = message["additional_data"]["data"][0:4*2] + ascii_string

            software_partnumber = dut.conf.rig.sddb_dids["sbl_diag_part_num"]

            if software_partnumber.replace("_"," ") == additional_data:
                result = False
                logging.error("Software part number not correct %s", software_partnumber)

        except UnicodeDecodeError:
            logging.info("Additional data does not contain valid ascii,\
                        must be logical block number %s",
                        message["additional_data"]["data"])

        if event_code != "80":
            result = False
            logging.error("Event code for accepted event is not 80 it is: %s", event_code)

        return result

    def test_rejected(result):
        event_code = message["event_code"]["data"]

        if int(event_code, base = 16) >= 0 and int(event_code, base = 16) < 3:
            result = result and True
        else:
            result = False
            logging.error("The event code of the rejected event does not have a valid value %s",
            event_code)

        return result


    if int(res["number_of_registered_successes"]) > nbr_accepted:
        #New accepted events exists
        success_messages = res["success_messages"]

        for message in success_messages:
            result = test_accepted(result)

        logging.info("Accepted checked with result %s", result)

    else:
        logging.error("No new accepted events added")
        result = False

    if int(res["number_of_registered_rejects"]) > nbr_rejected:
        #New rejected events exists
        rejected_messages = res["rejected_messages"]

        for message in rejected_messages:
            result = test_rejected(result) and result

        logging.info("Rejected checked with result %s", result)

    else:
        logging.error("No new rejected events added")
        result = False

    return result

def step_1(dut : Dut):
    """
    action:
        Check if there are any events before test starts

    expected_result:
        Successful calculation of current number of registered events

    """

    return _get_success_reject(dut)


def step_2(dut : Dut):
    """
    action:
        Set ECU to correct mode (programming session)

    expected_result:
        ECU set to programming session successfully

    """
    dut.uds.set_mode(2)

    if dut.uds.mode == 2:
        return True

    return False

def step_3():
    """
    action:
        Do something that triggers
        -Software Download started and successfully completed at CheckMemory

    expected_result:
        successful event added to event list

    """
    result = True

    return result

def step_4():
    """
    action:
        Do something that triggers a failed attempt

    expected_result:
        failed event added to event list

    """
    result = True

    return result

def step_5(dut : Dut, nbr_accepted, nbr_rejected):
    """
    action:
        Test DID D048

    expected_result:
        DID read containing correct data
    """
    return __evaluate_did(dut, nbr_accepted, nbr_rejected)


def run():
    """
    Run - Call other functions from here

    """
    logging.warning("Script needs to be updated to fully cover requirement.\
 More verification of the log content is needed. One would need to trigger several events\
 to make sure the logs are correct")
    dut = Dut()

    start_time = dut.start()

    result = False
    try:
        # Communication with ECU lasts 60 seconds.
        dut.precondition(timeout=30)

        result = True

        res = dut.step(step_1,purpose="Check for set events")

        res["number_of_registered_successes"] = -1 #Should be removed once test is updated

        res["number_of_registered_rejects"] = -1 #Should be removed once test is updated

        #result = dut.step(step_2,purpose="Enter programming session")Skipped until test is updated

        #result = dut.step(step_3,purpose="Successfull event")Skipped until test is updated

        #result = dut.step(step_4,purpose="Failed event")Skipped until test is updated

        result = dut.step(step_5,
            res["number_of_registered_successes"],
            res["number_of_registered_rejects"],
            purpose="Make sure did returns correct data") and result

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        result = False
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
