"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67821
version: 1
title: Identification Option - Vehicle Manufacturer Specific data records

purpose: >
    Volvo Car Corporation defines mandatory data records in GMRDB

description: >
    Identification Option - Vehicle Manufacturer Specific data records with data identifiers in
    the range as specified in the table below shall be implemented exactly as they are defined
    in Carcom - Global Master Reference Database.

    Description											    Identifier range
    Identification Option - Vehicle Manufacturer Specific	 0xF100 - 0xF17F
          											         0xF1A0 - 0xF1EF

    It shall be possible to read the data record by using the diagnostic service specified in
    Ref[LC ; Volvo Car Corporation UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

details: >
    Verify ReadDataByIdentifier(0x22) service for DIDs from Sddb file within specified range
    0xF100 - 0xF17F and F1A0 - F1EF respectively in default and programming session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL

SIO = SupportFileIO()
SSBL = SupportSBL()


def get_did_from_sddb(sddb_dids_dict):
    """
    Get all DIDs from sddb dictionary into a list
    Args:
        sddb_dids_dict (dict): DIDs from sddb file(pbl, sbl, app)
    Returns:
        dids_list (list): Sddb DIDs
    """
    dids_list = []
    # Getting all DIDs from Sddb file
    for did in sddb_dids_dict.keys():
        dids_list.append(did)
    if len(dids_list) == 0:
        logging.error("No DIDs found in sddb dictionary")
    return dids_list


def prepare_lookup_dids(start_did, end_did):
    """
    Prepare lookup DIDs for the specified ranges
    Args:
        start_did (int): Starting DID number
        end_did (int): Ending DID number
    Returns:
        dids_list (list): Lookup DIDs within the range
    """
    did_list = []
    # Preparing lookup DIDs list within range
    for did in range(start_did, end_did):
        did_list.append(hex(did)[2:].upper())
    return did_list


def filter_dids(lookup_did_list, sddb_did_list):
    """
    Filter 0xF100 to 0xF17F and 0xF1A0 to 0xF1EF DIDs from sddb DIDs list
    Args:
        lookup_did_list (list): Lookup DIDs within the range
        sddb_did_list (list): DIDs from sddb file
    Returns:
        filtered_dids_list (list): Filtered DIDs
    """
    filtered_dids_list = []
    # Getting the DIDs according to the required ranges
    for did in lookup_did_list:
        if did in sddb_did_list:
            filtered_dids_list.append(did)
    if len(filtered_dids_list) == 0:
        logging.error("No valid DIDs found in sddb DIDs list")

    return filtered_dids_list


def verify_read_data_by_identifier(dut, did_dict, mode, session):
    """
    Verify ReadDataByIdentifier(0x22) service with respective DIDs
    Args:
        dut (Dut): An instance of dut
        did_dict (dict): Active session DIDs
        mode (int): Diagnostic mode
        session (str): Diagnostic session
    Returns:
        (bool): True when all DIDs are successfully verified with positive response '62'
    """
    results = []
    dut.uds.set_mode(mode)

    if len(did_dict) == 0:
        logging.error("Test Failed: No DIDs found for %s session", session)
        return False

    failed_dids = []
    for did in did_dict:
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        # Checking 62 in response
        if response.raw[4:6] == '62':
            results.append(True)
            logging.info("Received %s for did %s as expected", response.raw[4:6], did)
        else:
            failed_dids.append(did)
            logging.error("Test Failed: Expected positive response '62', received %s for did %s",
                           response.raw, did)
            results.append(False)

    if len(results) != 0 and all(results):
        return True

    logging.error("Test Failed: Received unexpected response from the ECU for %s DIDs request"
                  " in %s session", ", ".join(failed_dids), session)
    return False


def step_1(dut: Dut, did_range_dict):
    """
    action: Read Sddb file & get all the DIDs, prepare the list of DIDs within specified range
            0xF100-0xF17F and 0xF1A0-0xF1EF
    expected_result: List of DIDs in range 0xF100-0xF17F and 0xF1A0-0xF1EF
    """
    # pylint: disable=unused-argument
    filtered_did_dict = {'programming_pbl': '',
                         'programming_sbl': '',
                         'default': ''}

    sddb_file = dut.conf.rig.sddb_dids
    if sddb_file is None:
        logging.error('Test Failed: sddb_file is empty')
        return False, None

    sddb_did_list_programming_pbl = get_did_from_sddb(sddb_file['pbl_did_dict'])
    sddb_did_list_programming_sbl = get_did_from_sddb(sddb_file['sbl_did_dict'])

    if len(sddb_did_list_programming_pbl)==0 and len(sddb_did_list_programming_sbl)==0 :
        logging.error('Test Failed: sddb DIDs list empty')
        return False, None

    sddb_did_list_default = get_did_from_sddb(sddb_file['app_did_dict'])

    if len(sddb_did_list_default) == 0:
        logging.error('Test Failed: sddb DIDs list empty')
        return False, None

    # Prepare lookup DIDs list within range F100-F17F
    lookup_did_list = prepare_lookup_dids(int(did_range_dict['start_did_f100'], 16),
                                          int(did_range_dict['end_did_f17f'], 16))

    # Extend lookup DIDs list within range F1A0-F1EF
    lookup_did_list.extend(prepare_lookup_dids(int(did_range_dict['start_did_f1a0'],
                                              16),int(did_range_dict['end_did1_f1ef']
                                              , 16)))

    # Filtered programming session(PBL) SDDB DIDs within range F100-F17F and F1A0-F1EF
    filtered_did_dict['programming_pbl'] = filter_dids(lookup_did_list,
                                           sddb_did_list_programming_pbl)

    # Filtered programming session(SBL) SDDB DIDs within range F100-F17F and F1A0-F1EF
    filtered_did_dict['programming_sbl'] = filter_dids(lookup_did_list,
                                           sddb_did_list_programming_sbl)

    # Filtered default session SDDB DIDs within range F100-F17F and F1A0-F1EF
    filtered_did_dict['default'] = filter_dids(lookup_did_list, sddb_did_list_default)

    if filtered_did_dict is None:
        logging.error("Test Failed: There are no DIDs available in the sddb file in the range of"
                      " %s and %s", did_range_dict['start_did_f1a0'],
                        did_range_dict['end_did1_f1ef'])
        return False, None

    return True, filtered_did_dict


def step_2(dut: Dut, default_did_dict):
    """
    action: Verify ReadDataByIdentifier(0x22) service with respective DIDs in default session
    expected_result: True when all DIDs are successfully verified with positive response '62'
    """
    return verify_read_data_by_identifier(dut, default_did_dict, mode=1, session='default')


def step_3(dut: Dut, programming_pbl_did_dict):
    """
    action: Verify ReadDataByIdentifier(0x22) service with respective DIDs in PBL session
    expected_result: True when all DIDs are successfully verified with positive response '62'
    """
    return verify_read_data_by_identifier(dut, programming_pbl_did_dict, mode=2, session='PBL')


def step_4(dut: Dut):
    """
    action: Activation of SBL
    expected_result: True on SBL activation
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Activate SBL
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_5(dut: Dut, programming_sbl_did_dict):
    """
    action: Verify ReadDataByIdentifier(0x22) service with respective DIDs in SBL session
    expected_result: True when all DIDs are successfully verified with positive response '62'
    """
    return verify_read_data_by_identifier(dut, programming_sbl_did_dict, mode=2, session='SBL')


def run():
    """
    Verify ReadDataByIdentifier(0x22) service for DIDs from Sddb file within specified range
    0xF100 - 0xF17F and F1A0 - F1EF respectively in default and programming session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did_range_dict': {}}

    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, filtered_did_dict = dut.step(step_1, parameters['did_range_dict'], purpose=
                                                  'Get DIDs in range 0xF100-0xF17F and '
                                                  '0xF1A0-0xF1EF from sddb file')
        if result_step:
            result_step = dut.step(step_2, filtered_did_dict['default'], purpose='Read DIDs in '
                                   'Default session and verify positive response(62) of service '
                                   '0x22')
        if result_step:
            result_step = dut.step(step_3, filtered_did_dict['programming_pbl'], purpose='Read '
                                   'DIDs in PBL session and verify positive response(62) of '
                                   'service 0x22')
        if result_step:
            result_step = dut.step(step_4, purpose='Activation of SBL')
        if result_step:
            result_step = dut.step(step_5, filtered_did_dict['programming_sbl'], purpose='Read '
                                   'DIDs in SBL session and verify positive response(62) of '
                                   'service 0x22')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
