"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67767
version: 2
title: ECU identification and configuration data records
purpose: >
    Volvo car corporation defines mandatory data records in GMRDB

description: >
    ECU identification and configuration data records with data identifiers in the range as
    specified in the table below shall be implemented exactly as they are defined in
    carcom - global master reference database
    --------------------------------------------------------------
    Manufacturer	                Identifier range
    --------------------------------------------------------------
    Volvo Car Corporation	        EDA0 - EDFF
    Geely	                        ED20 - ED7F
    --------------------------------------------------------------

details: >
    Compare the range 0xEDA0-0xEDFF and 0xED20-0xED7F with the SDDB and verify all DIDs are
    readable or not by ReadDataByIdentifier(0x22).

    EDC1 is not part of scope, it is for the application teams to test
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanTestExtra, CanPayload
from supportfunctions.support_carcom  import SupportCARCOM

SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()


def req_read_data_by_id(dut: Dut, did_hex):
    """
    Request ReadDataByIdentifier(0x22) and get the ECU response
    Args:
        dut(Dut): An instance of Dut
        did_hex(str): DID to read
    Returns:
        (bool): True on successfully verified positive response
    """
    # dut.uds.read_data_by_id_22() has timeout of 1 sec but for DID 'EDC0' timeout should be
    # greater than 1 sec (because of its size), hence below apporoach is used.
    # Size of DID 'EDC0' : 1816 bytes

    payload = SC_CARCOM.can_m_send("ReadDataByIdentifier", bytes.fromhex(did_hex), b'')

    cpay: CanPayload = {"payload" : payload,
                        "extra" : ''
                        }
    etp: CanTestExtra = {"step_no": 200,
                        "purpose" : "Test DID: %s" % did_hex.upper(),
                        "timeout" : 2,
                        "min_no_messages" : -1,
                        "max_no_messages" : -1
                        }

    SUTE.teststep(dut, cpay, etp)
    response = SC.can_messages[dut["receive"]][0][2]

    if response[4:6]=='62' and response[6:10] == did_hex:
        logging.info("DID %s is readable", did_hex)
        return True

    logging.error("Test Failed: Unable to read DID %s", did_hex)
    return False


def prepare_lookup_dids(parameters):
    """
    Prepare list of all DIDs within the specified ranges
    Args:
        parameters(list): did_list_range
    Returns:
        did_list(list): List of all DIDs within the given range
    """
    did_list = []

    # Get the length of did_list_range
    no_of_range = len(parameters['did_list_range'])

    # Prepare list of DIDs present in all specified ranges
    for i in range(no_of_range):
        start_did = int(parameters['did_list_range'][i][0], 16)
        end_did = int(parameters['did_list_range'][i][1], 16)

        for did in range(start_did, end_did+1):
            # Excluded DID 'EDC1'
            if hex(did)[2:].upper() != 'EDC1':
                did_list.append(hex(did)[2:].upper())

    return did_list


def filter_dids(lookup_did_list, app_did_dict):
    """
    Filtere DIDs of specified ranges from sddb DIDs list
    Args:
        lookup_did_list(list): Lookup DIDs list within the range
        app_did_dict(dict): Dict of DIDs
    Returns:
        filtered_dids_list(list): List of filtered DIDs
    """
    filtered_dids_list = []

    for did in lookup_did_list:
        if did in app_did_dict:
            filtered_dids_list.append(did)
    if len(filtered_dids_list) == 0:
        logging.error("No valid DIDs found in sddb DIDs list")
    return filtered_dids_list


def result_of_read_did(dut, filtered_dids_list):
    """
    Get result of readable DIDs in a given range
    Args:
        dut(Dut): An instance of Dut
        filtered_dids_list(list): List of DIDs
    Returns:
        result_list(list): List of results
    """
    result_list = []

    for did in filtered_dids_list:
        result = req_read_data_by_id(dut, did)
        result_list.append(result)
        time.sleep(1)

    return result_list


def step_1(dut: Dut):
    """
    action: Read sddb file and get dict of DIDs present in app_did_dict
    expected_result: True when successfully extracted app_did_dict from sddb file
    """
    sddb_file = dut.conf.rig.sddb_dids

    if 'app_did_dict' in sddb_file.keys():
        logging.info("Successfully extracted dict of DIDs present in app_did_dict")
        return True, sddb_file['app_did_dict']

    logging.error("Test Failed: Unable to extract dict of DIDs present in app_did_dict")
    return False, None


def step_2(dut, app_did_dict, parameters):
    """
    action: Read and verify DIDs present in app_did_dict with ReadDataByIdentifier(0x22)
    expected_result: True when successfully read all the DIDs in the specified ranges
    """
    lookup_did_list = prepare_lookup_dids(parameters)

    filtered_did_list = filter_dids(lookup_did_list, app_did_dict)

    result_list = result_of_read_did(dut, filtered_did_list)

    if len(result_list) > 0 and all(result_list):
        logging.info("Successfully read all the DIDs in the specified ranges")
        return True

    logging.info("Test Failed: Unable to read all DIDs in the specified ranges")
    return False


def run():
    """
    Compare the range 0xEDA0-0xEDFF and 0xED20-0xED7F with the SDDB and verify all DIDs are
    readable or not by ReadDataByIdentifier(0x22)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did_list_range' : []}

    try:
        dut.precondition(timeout=30)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, app_did_dict = dut.step(step_1, purpose="Read sddb file and get dict of "
                                                             "DIDs present in app_did_dict")
        if result_step:
            result_step = dut.step(step_2, app_did_dict, parameters, purpose= "Read and verify "
                                   "filtered DIDs list with ReadDataByIdentifier(0x22)")
            result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
