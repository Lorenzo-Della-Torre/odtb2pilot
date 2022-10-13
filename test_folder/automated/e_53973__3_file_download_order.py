"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53973
version: 3
title: File download order
purpose: >
    To be able to download data files to the ECU individually or in any grouping combination
    independent of order.

description: >
    No restrictions on the download order/sequence of the downloadable data files are allowed,
    with the exception of the SBL which shall be downloaded first.
    It shall be possible to download each data file separately without any requirements of
    downloading other data files before, exception is the SBL.
    Note: If an ECU Software Structure (ESS) is to be downloaded, it shall always be downloaded
    next to the SBL. Added here for information, it is a client requirement.

details: >
    Verify it is possible to download each data file separately without any requirements of
    downloading other data files previously, except SBL.
"""

import os
import glob
import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_SBL import SupportSBL

SIO = SupportFileIO()
SC = SupportCAN()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()
SSBL = SupportSBL()


def swdl_with_modified_vbf_path(dut, modified_vbf_path):
    """
    Read VBF files and download software parts
    Args:
        dut (Dut): An instance of Dut
        modified_vbf_path (str): Modified vbf path
    Returns:
        (bool): True when successfully downloaded software parts
    """
    # Flash Software Part of DATA and EXE
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    variant = odtb_proj_param + modified_vbf_path

    if not glob.glob(variant):
        result = False
    else:
        for f_name in glob.glob(variant):
            result = result and SSBL.sw_part_download(dut, f_name)

    return result


def step_1(dut: Dut):
    """
    action: Verify download of 1st data block (ESS) is rejected
    expected_result: True when download of 1st data block (ESS) is rejected
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Verify programming preconditions
    routinecontrol_result = SE31.routinecontrol_requestsid_prog_precond(dut)
    if not routinecontrol_result:
        logging.error("Test Failed: Programming preconditions are not fulfilled")
        return False

    # Set to programming session
    dut.uds.set_mode(2)

    # Security access
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not sa_result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    # Read VBF files for ESS file (1st logical block)
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_ess_filename())

    # Extract data for ESS
    block_by = SSBL.block_data_extract(data, data_start)[1]

    # Verify request download the 1st data block (ESS) rejected
    SSBL.vbf_header_convert(vbf_header)
    result = SE34.request_block_download(dut, vbf_header, block_by)[0]
    if result:
        logging.error("Test Failed: Downloaded 1st data block (ESS) which is not expected")
        return False

    logging.info("Successfully verified request download for 1st data block (ESS) is rejected")
    return True


def step_2(dut: Dut):
    """
    action: ECU reset and download and activation of SBL
    expected_result: True on SBL activation
    """
    # ECU reset
    result = dut.uds.ecu_reset_1101()
    if not result:
        logging.error("Test Failed: ECU reset failed")
        return False
    time.sleep(1)

    # Download and activate SBL
    sbl_result = SSBL.sbl_dl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify it is possible to download each data file separately without any requirements
            of downloading other data files previously
    expected_result: True when successfully downloaded each data file separately after SBL download
    """
    # Flash software part of EXE
    modified_vbf_result = swdl_with_modified_vbf_path(dut, parameters['modified_vbf_path_data'])
    if not modified_vbf_result:
        return False

    # Download ESS software part
    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    if not result:
        logging.error("Test Failed: ESS download failed")
        return False

    # Flash software part of DATA
    modified_vbf_result = swdl_with_modified_vbf_path(dut, parameters['modified_vbf_path_exe'])
    if not modified_vbf_result:
        return False

    # Verify the complete and compatible routine return 'Not Complete, Compatible'
    result = SSBL.check_complete_compatible_routine(dut, stepno=2)
    result = result and (SSBL.pp_decode_routine_complete_compatible(SC.can_messages\
             [dut["receive"]][0][2])== 'Not Complete, Compatible')
    if not result:
        logging.error("Test Failed: Complete and compatible routine return does not return"
                      " 'Not Complete, Compatible'")
        return False

    # Flash software part of EXE
    modified_vbf_result = swdl_with_modified_vbf_path(dut, parameters['modified_vbf_path_data'])
    if not modified_vbf_result:
        return False

    logging.info("Successfully downloaded each data file separately")
    return True


def step_4(dut: Dut):
    """
    action: Check complete & compatibility and do ECU hard reset
    expected_result: True when ECU is in default session
    """
    # Complete and compatible check
    result = SSBL.check_complete_compatible_routine(dut, stepno=3)
    if not result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    logging.info("Downloaded software is complete and compatible")

    # ECU reset
    result = dut.uds.ecu_reset_1101()
    if not result:
        logging.error("Test Failed: ECU reset failed")
        return False

    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()

    # Verify active diagnostic session
    if active_session.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def run():
    """
    Verify it is possible to download each data file separately without any requirements of
    downloading other data files previously, except SBL.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'modified_vbf_path_exe': '',
                       'modified_vbf_path_data': ''}

    try:
        dut.precondition(timeout=1000)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose='Verify download of 1st data block (ESS) is'
                                               ' rejected')
        if result_step:
            result_step = dut.step(step_2, purpose='Download and activate SBL')
        if result_step:
            result_step = dut.step(step_3, parameters, purpose='Verify it is possible to download'
                                   ' each data file separately without any requirements of'
                                   ' downloading other data files previously')
        if result_step:
            result_step = dut.step(step_4, purpose='Check complete & compatibility and do ECU'
                                                   ' hard reset')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
