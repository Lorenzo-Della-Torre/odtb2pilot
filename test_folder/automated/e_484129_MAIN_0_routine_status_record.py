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

description: >
	The control routine may support data parameter routineStatusRecord (RSR). If implemented,
    the routineStatusRecord shall at least be included in the positive response for:
	sub-function startRoutine if the routine type = 1 (short routine) and the routine does not
    support sub-function requestRoutineResults
	sub-function requestRoutineResults
	The routineStatusRecord shall contain information regarding:
	Result from the routine (if the routine was successful)
	Detailed exit information (in the case the routine was stopped due to entry or exit conditions
    or if the routine failed its completion due to other reasons)


details: >
    Verify Check Memory operation services routine 0x31,
    and get the RoutineType and RoutineStatus for security
    access in programming session and extended session
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

CNF = Conf()
SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()


def get_yml_parameters(dut: Dut, parameters):
    """
    Get yml parameters to Dut object
    Args:
		dut (class object): dut instance
        parameters(dict): rid and subfunctions

    Returns: True
    """
    try:
        dut.rid = parameters['rid']
        dut.subfunctions = parameters['subfunctions']
    except KeyError:
        logging.error("Test Failed: rid or subfunctions not present in the yml file")
        return False
    return True

def get_vbf_header(dut:Dut):
    """
    To Extract vbf headers from VBF file
    Args:
        dut (class object): dut instance

    Returns:
      vbf_header(dict): dictionary containing vbf header
    """

    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_paths = glob(str(rig_vbf_path) + "/*.vbf")
    if len(vbf_paths) == 0:
        msg = "No vbf file found in path: {}".format(rig_vbf_path)
        logging.error(msg)
        return False, None

    vbf_header = SSBL.read_vbf_file(vbf_paths[0])[1]
    SSBL.vbf_header_convert(vbf_header)
    return vbf_header


def check_memory_session_routine_type_status(dut:Dut, vbf_header, stepno, prog_rid):
    """
    To get Routine type  and Routine status
    Args:
        dut (class object): dut instance
        vbf_header : dictionary containing vbf header
        step no : stepno
        prog_rid : rid from yml file for specific session
    Returns:
        bool: True if data extraction is completed
    """
    result = []
    sw_signature = vbf_header['sw_signature_dev'].to_bytes(256, 'big')
    for index_sf in range(len(dut.subfunctions)):
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",
                             prog_rid + sw_signature, bytes(dut.subfunctions[index_sf], 'utf-8')),
                            "extra" : ''
                            }
        etp: CanTestExtra = {"step_no": stepno,
                                "purpose" : "SE31 CheckMemory",
                                "timeout" : 2,
                                "min_no_messages" : -1,
                                "max_no_messages" : -1
                            }
        result.append(SE31.routinecontrol_request_sid(dut, cpay, etp))
    if all(result):
        return True
    logging.error('Test Failed: routine control request not successful')
    return False


def step_1(dut: Dut):
    """
    action: Read yml file and get neccessary parameters
    expected_result: True
    """
    parameters = dut.get_platform_yml_parameters(__file__)
    if parameters is None:
        raise DutTestError("Cannot read yml file or file not exist")

    return get_yml_parameters(dut, parameters)

def step_2(dut: Dut):
    """
    action: set programming session , security access to ECU and
    verify check memory with routine control 0x31 service
    to get the routine type and Routine status
    expected_result: positive response

    """
    vbf_header = get_vbf_header(dut)
    dut.uds.set_mode(2)
    if dut.uds.mode == 2:
        response = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config, 2,
                                                         'Security Access')
        if response is None:
            logging.error("Test Failed: Security Access Failed")
            return False
        result = check_memory_session_routine_type_status(
            dut,vbf_header,2,bytes.fromhex(dut.rid["programming"][0]))
    if result:
        return True
    logging.error('Test Failed: routine control request not successful for programming session')
    return False

def step_3(dut: Dut):
    """
    action: set extended session , security access to ECU and
    verify check memory with routine control 0x31 service
    to get the routine type and Routine status
    expected_result: positive response

    """
    vbf_header = get_vbf_header(dut)
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    result = []
    if dut.uds.mode == 3:
        #line no 225 line to be removed when Security access is supported
        logging.error("Test Failed: Security access not supported in extended sesssion")
        response = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config, 3,
                                                         'Security Access')
        if response is None:
            logging.error("Test Failed: Security access Failed")
            return False
        for index in range (len(dut.rid["extended"])):
            result.append(check_memory_session_routine_type_status(
                dut,vbf_header,3,bytes.fromhex(dut.rid["extended"][index])))
    if len (result) != 0 and all(result):
        return True
    logging.error('Test Failed: routine control request not successful for Extended session')
    return False


def run():
    """
    Verifying positive response for service routineControl (0x31)
    request, regardless of sub-functione with service
    to get the routine type and Routine status to check Routine Status Record.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=60)
        result = dut.step(step_1, purpose="Read the data from yml file")

        if result:
            result = dut.step(step_2, purpose='Verifying routine with service 0x31 to get'
                            ' the routine type and Routine status in programming session'
                            ' to check Routine Status Record')

        if result:
            result = dut.step(step_3, purpose='Verifying routine with service 0x31 to get'
                            ' the routine type and Routine status in Extended session'
                            ' to check Routine Status Record')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
