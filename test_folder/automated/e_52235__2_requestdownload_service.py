"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-02-12
# version:  1.0
# reqprod:  52235

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-25
# version:  1.1
# reqprod:  52235

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC route guide client."""

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam
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
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

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
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()

def step_4():
    """
    Teststep 4: Read VBF files for SBL file (1st Logical Block)
    """
    stepno = 4
    purpose = "SBL files reading"

    SUTE.print_test_purpose(stepno, purpose)
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    return vbf_header, data, data_start

def step_5(data, data_start):
    """
    Teststep 5: Extract data for SBL
    """
    stepno = 5
    purpose = "EXtract data for SBL"

    SUTE.print_test_purpose(stepno, purpose)

    _, block_by, _ = SSBL.block_data_extract(data, data_start)
    return block_by

def step_6(can_p, block_by, vbf_header):
    """
    Teststep 6: get maxNumberOfBlockLenght from request download service
    """
    SSBL.vbf_header_convert(vbf_header)
    _, nbl = SE34.request_block_download(can_p, vbf_header, block_by, stepno=6, purpose=\
                                        "get maxNumberOfBlockLenght from request download service")
    #verify min maxNumberOfBlockLenght is >2kB
    result = nbl > 2000
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
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step 1:
        # action: Verify programming preconditions
        # result: ECU sends positive reply
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)
        time.sleep(1)

        # step 2:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)

        # step 3:
        # action: Security Access Request SID
        # result: ECU sends positive reply
        result = result and SE27.activate_security_access(can_p, 3)

        # step 4:
        # action: Read VBF files for SBL
        # result:
        vbf_header, data, data_start = step_4()

        # step 5:
        # action: Extract data for the 1st data block from SBL
        # result:
        block_by = step_5(data, data_start)

        # step 6:
        # action: get maxNumberOfBlockLenght from request download service
        # result: ECU sends positive reply
        result = result and step_6(can_p, block_by, vbf_header)

        # step 7:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=7)
        time.sleep(1)

        # step 8:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=8)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
