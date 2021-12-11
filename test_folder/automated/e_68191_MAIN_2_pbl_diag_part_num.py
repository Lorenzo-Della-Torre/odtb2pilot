"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
Testscript Hilding MEPII
project:  BECM basetech MEPII
author:   DHJELM (Daniel Hjelm)
date:     2020-12-21
version:  3
reqprod:  68191

title:

    Primary Bootloader Diagnostic Database Part Number ; 3

purpose:

    To enable readout of a database key for the diagnostic database used by the
    ECU's primary bootloader SW.

description:

    The data record Primary Bootloader Diagnostic Database Part Number with
    identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database (GMRDB).

    Description: Primary Bootloader Diagnostic Database Part Number
    Identifier: F121

      - It shall be possible to read the data record by using the diagnostic
        service specified in Ref[LC : Volvo Car Corporation - UDS Services -
        Service 0x22 (ReadDataByIdentifier) Reqs].

      - It is allowed to change the value of the data record one time in
        secondary bootloader by diagnostic service as specified in Ref[LC : VCC
        - UDS Services - Service 0x2E (WriteDataByIdentifier) Reqs].

    The ECU shall support the identifier in the following sessions:

      - Programming session (which includes both primary and secondary bootloader)

"""
import time
from datetime import datetime
import sys
import logging
import inspect
from dataclasses import dataclass

import odtb_conf

from build.did import pbl_diag_part_num

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_rpi_gpio import SupportRpiGpio

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SGPIO = SupportRpiGpio()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE31 = SupportService31()


def read_data_by_id(identifier: bytes):
    """ Read Data by Identifier """
    return b'\x22' + identifier

@dataclass
class Id:
    """ Primary Bootloader Diagnostic Database Part Number """
    pbl_diag_part_num = b'\xF1\x21'


def extract_db_part_num(can_p, stepno=0):
    """ Extract DB Part Number for PBL """
    cpay: CanPayload = {
        "payload" : read_data_by_id(Id.pbl_diag_part_num),
        "extra" : ""
    }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Extract DB Part Number for PBL",
        "timeout": 5,
        "min_no_messages": -1,
        "max_no_messages": -1
    }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("PBL DB part number message: %s", SC.can_messages[can_p["receive"]])
    db_part_num = SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:])
    logging.info("Step %s: %s", stepno, db_part_num)
    pbl_part_number = SUTE.pp_partnumber(SC.can_messages[can_p["receive"]][0][2][10:])
    return result, pbl_part_number


def compare_part_numbers(pbl_part_number, stepno=0):
    """ Compare PBL DB Part Numbers from Data Base and PBL """

    purpose = "Compare PBL DB Part Numbers from Data Base and PBL"
    SUTE.print_test_purpose(stepno, purpose)

    pbl_part_number = pbl_part_number.replace(" ", "_")
    logging.info("pbl_diag_part_num: %s", pbl_diag_part_num)
    logging.info("pbl_part_number: %s", pbl_part_number)
    result = bool(pbl_diag_part_num == pbl_part_number)
    if result:
        logging.info('PBL DB Part Numbers are equal! Continue')
    else:
        logging.info('PBL DB Part Numbers are NOT equal! Test FAILS')

    return result


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)
    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 500
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step 1:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=1)
        time.sleep(1)

        # step 2:
        # action: verify ECU in programming session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x02', stepno=2)

        # step 3:
        # action: Extract SWP Number for PBL
        # result: ECU sends positive reply
        result_step3, pbl_part_number = extract_db_part_num(can_p, stepno=3)
        result = result and result_step3

        # step 4:
        # action: Compare the PBL Part Numbers from Data Base and PBL
        # result: The Part Numbers shall be equal
        result = result and compare_part_numbers(pbl_part_number, stepno=4)


    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
