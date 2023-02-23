"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469429
version: 1
title: Read out Security Event records
purpose: >
    Define how to read log using a diagnostic client. A typical use-case is to read the
    information while ECU application is running, i.e. without forcing the vehicle into
    programming session (convenience).

description: >
    It shall be possible to read all Security Event types via the diagnostic protocol,
    using the service ReadDataByIdentifier. Event types reported in programmingSession
    shall also be available to read in non-programmingSession.

    A unique DID shall be applied for each type.

details: >
    From an excel sheet attached to the Vira story the different events are obtained.
    Each of the events has a DID connected to it, these DIDs are read to verify that

    "It shall be possible to read all Security Event types via the diagnostic protocol,
    using the service ReadDataByIdentifier."

    A check is also done to make sure that the sizes of the DIDs are correct.
    This increases the likelyhood that the DID is correct.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()

def read_did_and_check_size(dut: Dut, did: str, did_size):
    """
    Request ReadDataByIdentifier(0x22) service and check the availability of DID and its size
    Args:
        dut (Dut): An instance of Dut
        did (str): DIDs
        did_size (dict): DIDs size
    Returns:
        (bool): True when received positive response '62' and size of DIDs are correct
    """
    logging.info("Test that %s works as intended", did)

    # Check length of DIDs
    if len(did) != 4:
        logging.error("Did id is not the correct size (should be 4)")
        return False

    # Read data by identifier
    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    if res.raw[4:6] != '62' and res.raw[6:10] != did:
        logging.error("Test Failed: Expected positive response '62' for request "
                      "ReadDataByIdentifier(0x22) service, received %s", res.raw)
        return False

    logging.info("Received positive response %s for request ReadDataByIdentifier(0x22) with DID %s",
                  res.raw[4:6], did)
    logging.info("ECUs response for %s : %s ", did, res)


    try:
        if res.empty() or not res.data["did"] == did:
            logging.error("Test Failed: The response from the ECU is empty or the did response"
                          " doesn't match")
            return False
    except KeyError:
        logging.error("Test Failed: The response from the ECU does not contain the DID id (%s)",
                       did)
        return False

    # Check size of DIDs
    if res.data["details"]["size"] != did_size:
        logging.error("Test Failed: The response from the ECU does not contain info about the "
                      "DIDs size or has the wrong size, %s instead of %s",
                      res.data["details"]["size"], did_size)
        return False

    logging.info("DID %s has the correct size", did)
    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify possibility to read all security event types with DIDs
            (D046, D048, D0B7, D0C1, D03C, D0BC) & Verify correct size of DIDs.
    expected_result: ECU should give positive response for DID's (D046, D048, D0B7, D0C1, D03C,
                     D0BC) with correct size
    """
    results = []

    # Get all DIDs for SDDB files "app_did_dict" dictionary
    app_did_dict = dut.conf.rig.sddb_dids["app_did_dict"]
    did_dict = {parameters['event_type_sa_prog_session'] : app_did_dict[parameters
                ['event_type_sa_prog_session']]["size"],
                parameters['event_type_software_updates_boot'] : app_did_dict[parameters
                ['event_type_software_updates_boot']]["size"],
                parameters['event_type_secure_boot'] : app_did_dict[parameters
                ['event_type_secure_boot']]["size"],
                parameters['event_type_security_key_updates'] : app_did_dict[parameters
                ['event_type_security_key_updates']]["size"],
                parameters['event_type_sa_application'] : app_did_dict[parameters
                ['event_type_sa_application']]["size"],
                parameters['event_type_secure_onboard_communication'] : app_did_dict[parameters
                ['event_type_secure_onboard_communication']]["size"]}

    for did in did_dict:
        results.append(read_did_and_check_size(dut, did, did_dict[did]))

    if all(results) and len(results) != 0:
        return True

    return False


def run():
    """
    Verify possibility to read all Security Event types & Verify correct size of DIDs.
    """
    dut = Dut()
    start_time = dut.start()

    parameters_dict = {'event_type_sa_prog_session': '',
                       'event_type_software_updates_boot':'',
                       'event_type_secure_boot':'',
                       'event_type_security_key_updates':'',
                       'event_type_sa_application':'',
                       'event_type_secure_onboard_communication':''}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose="Verify possibility to read all security"
                                          " event types with DIDs(D046, D048, D0B7, D0C1, D03C,"
                                          " D0BC) & Verify correct size of DIDs")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
