"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/


reqprod: 484129
version: 0
title: RoutineStatusRecord (RSR)

purpose: >
    nil

description: >
	The control routine may support data parameter routineStatusRecord (RSR). If implemented,
    the routineStatusRecord shall at least be included in the positive response for:
    	> sub-function startRoutine if the routine type = 1 (short routine) and the routine does
          not support sub-function requestRoutineResults
	    > sub-function requestRoutineResults
	The routineStatusRecord shall contain information regarding:
	    > Result from the routine (if the routine was successful)
	    > Detailed exit information (in the case the routine was stopped due to entry or exit
          conditions or if the routine failed its completion due to other reasons)

details: >
    Verify Check Memory operation services routine 0x31, and get the RoutineType and RoutineStatus
    for security access in programming session and extended session
"""


import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_SBL import S_CARCOM, SupportSBL
from supportfunctions.support_can import  CanPayload, CanTestExtra
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_file_io import SupportFileIO

CNF = Conf()
SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()
SIO = SupportFileIO


def get_sw_signature_dev(dut:Dut):
    """
    To Extract sw_signature from vbf headers of VBF file
    Args:
        dut (class obj): dut instance
    Returns:
        sw_signature (bytes): bytes of sw signature
    """
    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_file_paths) > 0:
        for vbf_file_path in vbf_file_paths:
            vbf_header = SSBL.read_vbf_file(vbf_file_path)[1]
            SSBL.vbf_header_convert(vbf_header)
            sw_signature_dev = vbf_header['sw_signature_dev'].to_bytes(256, 'big')
            return sw_signature_dev

    logging.error("No VBF file found in %s", rig_vbf_path)
    return False, None


def check_memory_session_routine_type_status(dut:Dut, sw_signature_dev, stepno, parameters,
                                             rid_index):
    """
    To get Routine type and Routine status
    Args:
        dut (class object): dut instance
        sw_signature_dev (bytes) : sw_signature_dev
        step no : stepno
        prog_rid (list): rid_programming/rid_extended from yml file for specific session
        subfunctions (list): subfunction values from yml
    Returns:
        bool: True if data extraction is completed
    """
    result = []
    for index_sf in range(len(parameters['subfunctions'])):

        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",
                             bytes.fromhex(rid_index) + sw_signature_dev,
                             bytes.fromhex(parameters['subfunctions'][index_sf])), "extra" : ''
                            }

        etp: CanTestExtra = {"step_no": stepno,
                                "purpose" : "SE31 CheckMemory",
                                "timeout" : 2,
                                "min_no_messages" : -1,
                                "max_no_messages" : -1
                            }
        result.append(SE31.routinecontrol_request_sid(dut, cpay, etp))

    if len(result) != 0 and all(result):
        return True
    logging.error('Test Failed: routine control request not successful')
    return False


def step_1(dut: Dut):
    """
    action: Read yml file to get necessary parameters and Set programming session,
            security access to ECU
    expected_result: ECU is in programming session and security access is granted
    """
    # Define did from yml file
    parameters_dict = { 'rid_programming': '',
                        'rid_extended':'',
                        'subfunctions':''
                     }
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Setting Programming session
    dut.uds.set_mode(2)

    response = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if response is None:
        logging.error("Test Failed: Security access Failed")
        return False, None
    return True, parameters


def step_2(dut: Dut, parameters):
    """
    action: Verify check memory with routine control 0x31 service
            to get the routine type and Routine status
    expected_result: Positive response

    """
    sw_signature_dev = get_sw_signature_dev(dut)
    result = []
    for rid_programming in parameters["rid_programming"]:
        result.append(check_memory_session_routine_type_status(dut, sw_signature_dev, 2,
             parameters, rid_programming))


    if len(result) != 0 and all(result):
        return True
    logging.error('Test Failed: routine control request not successful for Extended session')
    return False


def step_3(dut: Dut):
    """
    action: Set Extended session, security access to ECU
    expected_result: ECU is in programming session and security access is granted

    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    #line no 178 line to be removed when Security access is supported in extended session
    logging.error("Test Failed: Security access not supported in extended session")
    response = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if response is None:
        logging.error("Test Failed: Security access Failed")
        return False
    return True

def step_4(dut: Dut, parameters):
    """
    action: Verify check memory with routine control 0x31 service
    to get the routine type and Routine status
    expected_result: Positive response

    """
    sw_signature_dev = get_sw_signature_dev(dut)
    result = []
    for rid_extended in parameters["rid_extended"]:
        result.append(check_memory_session_routine_type_status(dut, sw_signature_dev, 2,
             parameters, rid_extended))

    if len(result) != 0 and all(result):
        return True
    logging.error('Test Failed: routine control request not successful for Extended session')
    return False


def run():
    """
    Verifying positive response for service routineControl (0x31)
    request, regardless of sub-function with service
    to get the routine type and Routine status to check Routine Status Record.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, parameters = dut.step(step_1, purpose="Read the data from yml file and set "
                                           " programming session & security access to ECU")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verifying routine with service '
                                    '0x31 to get the routine type and Routine status to check '
                                    'Routine Status Record')

        if result_step:
            result_step = dut.step(step_3, purpose='Set Extended session & security access to ECU')

        if result_step:
            result_step = dut.step(step_4, parameters, purpose='Verifying routine with service '
                                    '0x31 to get the routine type and Routine status to check '
                                    'RoutineStatus Record')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
