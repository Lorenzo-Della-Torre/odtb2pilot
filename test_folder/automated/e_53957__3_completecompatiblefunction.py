"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53957
version: 3
title: Complete Compatible Function
purpose: >
    To define the functionality of the CompleteCompatibleFunction()

description: >
    The CompleteCompatibleFunction() is invoked from the bootloader via either the routine
    (Check Complete & Compatible) or during the Init phase. The CompleteCompatibleFunction()
    shall be implemented in a way that allows new or modified software part without an updated
    application(EXE). The CompleteCompatibleFunction() shall detect if any of the software parts
    are not as expected, missing, broken (partly downloaded), altered etc. The function is also
    responsible to decide whether the combination of stored software parts are compatible to
    each other.

details: >
    Check complete & compatibility function
"""

import os
import logging
import inspect
import glob
import hilding.flash as swdl
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_file_io import SupportFileIO

SSBL = SupportSBL()
SE11 = SupportService11()
SE22 = SupportService22()
SIO = SupportFileIO()


def step_1(dut: Dut):
    """
    action: Download and activation of SBL
    expected_result: True on SBL activation
    """
    # Loads the rig specific VBF files
    vbf_result = swdl.load_vbf_files(dut)
    if not vbf_result:
        return False

    # Download and activate SBL on the ECU
    sbl_result = swdl.activate_sbl(dut)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_2(dut: Dut):
    """
    action: Download ESS, DATA and EXE software parts
    expected_result: True on successful download
    """
    result = True
    # Download the ESS file to the ECU
    ess_result = swdl.download_ess(dut)
    if not ess_result:
        logging.error("Test Failed: ESS Download failed")
        return False

    logging.info("ESS download successful")
    for swp in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, swp, stepno=2)

    return result


def step_3(dut: Dut):
    """
    action: Check complete & compatibility and perform ECU hardreset
    expected_result: True when ECU reset successfully
    """
    # Complete and compatible check
    result = SSBL.check_complete_compatible_routine(dut, stepno=105)
    if not result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    logging.info("Downloaded software is complete and compatible")

    # ECU reset use 1101
    result = dut.uds.ecu_reset_1101()
    if not result:
        logging.error("Test Failed: ECU reset Failed")
        return False

    return True


def step_4(dut: Dut):
    """
    action: Activate SBL
    expected_result: True on SBL activation
    """
    # Loads the rig specific VBF files
    vbf_result = swdl.load_vbf_files(dut)
    if not vbf_result:
        logging.error("Test Failed: Unable to Load vbf files")
        return False

    # Download and activate SBL on the ECU
    sbl_result = swdl.activate_sbl(dut)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_5(dut: Dut, parameters):
    """
    action: Download different SW parts variant
    expected_result: True when download different SW parts variant complete
    """
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    modified_vbf_path = parameters['modified_vbf_path']
    # By default we get files from VBF_Reqprod directory
    # REQ_53957_32325411XC_SWP1variant.vbf

    variant = odtb_proj_param + modified_vbf_path
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), variant)
    if not glob.glob(variant):
        result = False
    else:
        for f_name in glob.glob(variant):
            result = result and SSBL.sw_part_download(dut, f_name,
                                                      stepno=5, purpose= "Download SWP1 variant")
    return result


def step_6(dut: Dut):
    """
    action: Check complete & compatibility and perform ECU hardreset
    expected_result: True when ECU is in default session
    """
    # Complete and compatible check
    result = SSBL.check_complete_compatible_routine(dut, stepno=105)
    if not result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    logging.info("Downloaded software is complete and compatible")

    # ECU reset
    result = dut.uds.ecu_reset_1101()
    if not result:
        logging.error("Test Failed: ECU reset Failed")
        return False

    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()

    # confirming active session
    if active_session.data["details"]["mode"] == 1:
        logging.info("ECU is in Default session")
        return True

    logging.error("Test Failed: ECU Not in Default session")
    return False


def run():
    """
    Check complete & compatibility function
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'modified_vbf_path': ''}

    try:
        dut.precondition(timeout=1000)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose="Download and activation of SBL")
        if result_step:
            result_step = dut.step(step_2, purpose="Download ESS, DATA and EXE software parts")
        if result_step:
            result_step = dut.step(step_3, purpose="Check complete & compatibility and perform ECU"
                                                   " hardreset")
        if result_step:
            result_step = dut.step(step_4, purpose="Activate SBL")
        if result_step:
            result_step = dut.step(step_5, parameters, purpose="Download Different SW Parts"
                                                               " variant")
        if result_step:
            result_step = dut.step(step_6, purpose="Check complete & compatibility and perform"
                                                   " ECU hardreset")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
