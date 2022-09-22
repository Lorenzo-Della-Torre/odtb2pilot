"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53959
version: 4
title: Complete and Compatible sequence diagram
purpose: >
    Definition in which order the ECU shall validate the stored software(s).

description: >
    The ECU shall first check that all software parts are complete prior to the compatibility
    check is performed. If the ECU contains incomplete software(s) it shall not check whether
    the software(s) is compatible. Hence, the ECU cannot indicate that both the complete and
    compatible check has failed. The software parts shall be checked in the order defined in
    Figure - CompleteCompatibleFunction() sequence diagram

details: >
    Verify complete and compatible sequence
"""

import os
import logging
import inspect
import glob
import hilding.flash as swdl
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SSBL = SupportSBL()
SE11 = SupportService11()
SIO = SupportFileIO()


def step_1(dut: Dut):
    """
    action: Download SBL, ESS and activate SBL
    expected_result: True on successful download of SBL, ESS and activation SBL
    """
    # Loads the rig specific VBF files
    vbf_result = swdl.load_vbf_files(dut)
    if not vbf_result:
        return False

    # Download and activate SBL
    sbl_result = swdl.activate_sbl(dut)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")

    # Download the ESS file to the ECU
    ess_result = swdl.download_ess(dut)
    if not ess_result:
        logging.error("Test Failed: ESS Download failed")
        return False

    logging.info("ESS Download successful")
    return True


def step_2(dut: Dut, modified_vbf_path):
    """
    action: Software download with modified vbf file
    expected_result: True on successful software download
    """
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    if not glob.glob(odtb_proj_param + modified_vbf_path):
        result = False
    else:
        for f_name in glob.glob(odtb_proj_param + modified_vbf_path):
            result = result and SSBL.sw_part_download(dut, f_name)
    return result


def step_3(dut: Dut):
    """
    action: Verify downloaded software is 'Not Complete, Compatible'
    expected_result: True on recieving 'Not Complete, Compatible'
    """
    # time_stamp = [0]
    result_str = SSBL.check_complete_compatible_routine(dut, stepno=3)
    result = (result_str  == 'Not Complete, Compatible')

    logging.info("Check(%s == Not Complete, Compatible) :%s",
                     result_str, result)

    time_stamp_send = SC.can_frames[dut["send"]][0][0]
    time_stamp_recieve = SC.can_frames[dut["receive"]][0][0]
    result = result and ((time_stamp_recieve - time_stamp_send)*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_stamp_recieve - time_stamp_send)*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_stamp_recieve - time_stamp_send)*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_stamp_send), 3), frame_type,
            frame_byte])

    return result


def step_4(dut: Dut, modified_vbf_path):
    """
    action: Software download with modified vbf file
    expected_result: True on successful software downlaod
    """
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    swps = odtb_proj_param + modified_vbf_path
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swps)
    if not glob.glob(swps):
        result = False
    else:
        for f_name in glob.glob(swps):
            result = result and SSBL.sw_part_download(dut, f_name)
    return result


def step_5(dut: Dut):
    """
    action: Verify downloaded software is 'Complete, Not Compatible'
    expected_result: True on recieving 'Complete, Not Compatible'
    """
    result_str = SSBL.check_complete_compatible_routine(dut, stepno=5)
    result = (result_str  == 'Complete, Not Compatible')

    logging.info("Check(%s == Complete, Not Compatible) :%s",
                     result_str, result)

    time_stamp_send = SC.can_frames[dut["send"]][0][0]
    time_stamp_recieve = SC.can_frames[dut["receive"]][0][0]
    result = result and ((time_stamp_recieve - time_stamp_send)*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_stamp_recieve - time_stamp_send)*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_stamp_recieve - time_stamp_send)*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_stamp_send), 3), frame_type,
            frame_byte])

    return result


def step_6(dut: Dut, modified_vbf_path):
    """
    action: Software download with modified vbf file
    expected_result: True when download different SW parts variant complete
    """

    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    logging.info("\nODTBPROJPARAM: %s", odtb_proj_param)
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    swp = odtb_proj_param + modified_vbf_path
    logging.info(swp)
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swp)
    if not glob.glob(swp):
        result = False
    else:
        for f_name in glob.glob(swp):
            result = result and SSBL.sw_part_download(dut, f_name)
    return result


def step_7(dut: Dut):
    """
    action: Verify downloaded software is 'Complete, Compatible'
    expected_result: True on recieving 'Complete, Compatible'
    """
    result_str = SSBL.check_complete_compatible_routine(dut, stepno=107)
    result = (result_str  == 'Complete, Compatible')

    logging.info("Check(%s == Complete, Compatible) :%s",
                     result_str, result)

    time_stamp_send = SC.can_frames[dut["send"]][0][0]
    time_stamp_recieve = SC.can_frames[dut["receive"]][0][0]
    result = result and ((time_stamp_recieve - time_stamp_send)*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_stamp_recieve - time_stamp_send)*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_stamp_recieve - time_stamp_send)*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_stamp_send), 3), frame_type,
            frame_byte])

    return result


def step_8(dut: Dut):
    """
    action: ECU hard reset and check it is in default session
    expected_result: True when ECU is in default session
    """
    # ECU reset
    result = SE11.ecu_hardreset_5sec_delay(dut, stepno=108)
    if not result:
        logging.error("Test Failed: ECU reset failed")
        return False

    # Check active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    if active_session.data["details"]["mode"] == 1:
        logging.info("ECU is in default session")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def run():
    """
    Verify complete and compatible sequence
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'modified_vbf_path_1': '',
                       'modified_vbf_path_2' : '',
                       'modified_vbf_path_3' : ''}

    try:
        dut.precondition(timeout=1000)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose="Download SBL, ESS and activate SBL")
        if result_step:
            result_step = dut.step(step_2, parameters['modified_vbf_path_1'], purpose="Software"
                                                             " download with modified vbf file")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify downloaded software is 'Not Complete,"
                                                   " Compatible'")
        if result_step:
            result_step = dut.step(step_4, parameters['modified_vbf_path_2'], purpose="Software"
                                                             " download with modified vbf file")
        if result_step:
            result_step = dut.step(step_5, purpose="Verify downloaded software is 'Complete,"
                                                   " Not Compatible'")
        if result_step:
            result_step = dut.step(step_6, parameters['modified_vbf_path_3'], purpose="Software"
                                                             " download with modified vbf file")
        if result_step:
            result_step = dut.step(step_7, purpose="Verify downloaded software is 'Complete,"
                                                   " Compatible'")
        if result_step:
            result_step = dut.step(step_8, purpose="ECU hard reset and check it is in default"
                                                   " session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
