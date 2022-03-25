"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

testscript: Hilding MEPII
project:   BECM basetech MEPII
author:    GANDER10 (Gustav Andersson)
date:      2020-12-28
version:   1.0
reqprod:   68225

title:
    Primary Bootloader Software Part Number Data Record ; 3

purpose:
    To enable readout of the part number of the Primary Bootloader SW.

description:
    A data record with identifier as specified in the table
    below shall be implemented exactly as defined in Carcom
    - Global Master Reference Database (GMRDB).

    Description	Identifier
    Primary Bootloader Software Part Number data record	F125
    •	It shall be possible to read the data record by using
        the diagnostic service specified in Ref
        [LC : Volvo Car Corporation - UDS Services -
        Service 0x22 (ReadDataByIdentifier) Reqs].

    •	It is allowed to change the value of the data record
        one time in secondary bootloader by diagnostic service
        as specified in Ref[LC : VCC - UDS Services -
        Service 0x2E (WriteDataByIdentifier) Reqs].

    The ECU shall support the identifier in the following sessions:
    •	Programming session
        (which includes both primary and secondary bootloader)

details:
    1. Steps down to programming session in primary bootloader.
    2. Sends ReadDataByIdentifier(F125) in primary bootloader.
    3. Flashes the secondary bootloader and activates it.
    4. Sends ReadDataByIdentifier(F125) in secondary bootloader.
    5. Compares the data from primary and secondary bootloaders.
        a. They must equal.
    Done.
"""

from datetime import datetime
import sys
import time
import logging

import odtb_conf

from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanParam
from supportfunctions.support_can import CanTestExtra
from supportfunctions.support_can import CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam

SSBL = SupportSBL()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def read_data_by_identifier(can_p, boot, step):
    """
    Step read data by identifier (F125).
    Read and verify positive response from programming sesion.
    """
    etp: CanTestExtra = {
        "step_no": step,
        "purpose" : f"ReadDataByIdentifier (Id: F125) in {boot}.",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.parameter_adopt_teststep(etp)

    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xF1\x25',
                                        b''),
        "extra": ''
    }
    SIO.parameter_adopt_teststep(cpay)

    # Send message
    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)

    # Extract part number from response.
    pbl_part_num = SC.can_messages[can_p["receive"]][0][2][10:]

    # Evaluate result (Verify positive response).
    result = result and evaluate_response(can_p, '100A62F125')

    if result:
        # Validate the format of part the number.
        result = result and SUTE.validate_part_number_record(pbl_part_num)

    return result, pbl_part_num

def print_nrc(can_p):
    """
    Get and log NRC (Negative return code).
    """
    logging.info("NRC: %s",
                 SUTE.pp_can_nrc(
                 SC.can_messages[can_p["receive"]][0][2][6:8]))

def evaluate_response(can_p, valid_data):
    """
    Log result of data comparison (true/false)
    If it was a NRC - pretty print number and corresponding string
    If comparison is false and data does not contain a NRC log as unexpected.
    Finally, return result.
    """
    # Check if empty
    if not can_p["receive"]:
        logging.info("No data in can_p['receive']")
        return False

    nrc = SC.can_messages[can_p["receive"]][0][2][0:4] == '037F'
    result = SUTE.test_message(SC.can_messages[can_p["receive"]],
                               teststring=valid_data)
    # Log result
    logging.info("Result: %s\n", result)

    # Check if it was a negative return code. If so, print.
    if nrc:
        print_nrc(can_p)

    # If its not result and not a NRC possible corrupt message.
    if not result and not nrc:
        logging.info("Unexpected data received: %s\n",
                     SC.can_messages[can_p["receive"]][0][2])
    return result

def compare_part_num(part_num1, part_num2, step):
    """
    Compare two part numbers and return the result (true/false).
    """
    purpose = "Compare the part numbers read from PBL and SBL."
    SUTE.print_test_purpose(step, purpose)

    result = (part_num1 == part_num2)
    logging.info("Result: %s\n", result)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # Where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(
            odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.parameter_adopt_teststep(can_p)

    #Init parameter for SecAccess Gen1/Gen2
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen1',
        "fixed_key": 'FFFFFFFFFF',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.parameter_adopt_teststep(sa_keys)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    # read VBF param when testscript is started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 200
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # Step 1:
        # Action: Change to programming session.
        # Result: ECU responds with positive message.
        result = result and SE10.diagnostic_session_control_mode2(can_p, 1)

        # Step 2:
        # Action: Read data by identifier F125
        # Result: ECU responds with a positive message and valid part num. format.
        result, part_num_from_pbl = result and read_data_by_identifier(
            can_p, 'Primary bootloader', 2)

        # Step 3:
        # Action: Activate secondary bootloader.
        # Result: ECU responds with a positive message.
        sa_keys = {
            "SecAcc_Gen": 'Gen1',
            "fixed_key": '0102030405',
            "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
            "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        }
        sa_keys = SIO.parameter_adopt_teststep(sa_keys)
        result = result and SSBL.sbl_activation(
            can_p, sa_keys=sa_keys, stepno='3', purpose="Activate secondary bootloader")
        # Step 4:
        # Action: Read data by identifier F125
        # Result: ECU responds with a positive message and valid part num. format.
        result, part_num_from_sbl = result and read_data_by_identifier(
            can_p, 'Secondary bootloader', 4)

        # Step 5:
        # Action: Compare part numbers from pbl and from sbl.
        # Result: They are equal.
        result = result and compare_part_num(
            part_num_from_pbl, part_num_from_sbl, 5)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
