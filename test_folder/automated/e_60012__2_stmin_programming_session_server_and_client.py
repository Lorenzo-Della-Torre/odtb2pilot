"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-19
# version:  1.0
# reqprod:  60012

# #inspired by https://grpc.io/docs/tutorials/basic/python.html
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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_SBL import SupportSBL
from hilding.conf import Conf


SSA = SupportSecurityAccess()
SSBL = SupportSBL()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE34 = SupportService34()
conf = Conf()

def step_3():
    """
    Teststep 3: Read VBF files for SBL file (1st Logical Block)
    """
    stepno = 3
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    SSBL.vbf_header_convert(vbf_header)
    return vbf_header, vbf_data, vbf_offset

def step_4(vbf_offset, vbf_data):
    """
    Teststep 4: Extract data for the 1st block from SBL VBF
    """
    stepno = 4
    purpose = "Extract data for the 1st block from SBL VBF"

    SUTE.print_test_purpose(stepno, purpose)
    vbf_offset, vbf_block, _ = SSBL.block_data_extract(vbf_data, vbf_offset)
    logging.debug("block_data_extract - vbf_block('Length') : {0:08X}".format\
                  (vbf_block['Length']))
    logging.debug("block_Startaddress:              {0:08X}".format(vbf_block['StartAddress']))
    return vbf_block

def step_5(can_p, vbf_header, vbf_block):
    """
    Teststep 5: Send multi frame request verify ST is 0
    """
    addr_b = vbf_block['StartAddress'].to_bytes(4, 'big')
    len_b = vbf_block['Length'].to_bytes(4, 'big')
    cpay: CanPayload = {"payload" : b'\x34' +\
                                    vbf_header["data_format_identifier"].to_bytes(1, 'big') +\
                                    b'\x44'+\
                                    addr_b +\
                                    len_b,
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 5,
                         "purpose" : "Send multi frame request verify ST is 0",
                         "timeout" : 0.05,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }
    result = SUTE.teststep(can_p, cpay, etp)

    logging.info("Control Frame from Server: %s", SC.can_cf_received[can_p["receive"]][0][2])

    #test if ST is 0 ms: get ST from saved Control Frame
    result = result and (int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16) == 0)
    if int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16) == 0:
        logging.info("ST is 0 ms")
    else:
        logging.info("ST is not 0 ms")
    return result

def step_6(can_p):
    """
    Teststep 6: verify session PBL
    """
    result = SE22.read_did_eda0(can_p, stepno=6)
    logging.info("Complete Part/serial received: %s", SC.can_messages[can_p["receive"]])

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
                                          teststring='F121')
    return result

def run():
    """
    Run - Call other functions from here
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "Vcu1ToBecmFront1DiagReqFrame",
        'receive': "BecmToVcu1Front1DiagResFrame",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    #Read YML parameter for current function (get it from stack)
    logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action: # Change to programming session
        # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode2(can_p, 1)

        # step2:
        # action: Request Security Access to be able to unlock the server(s)
        #         and run the primary bootloader.
        # result: Positive reply from support function if Security Access to server is activated.
        result = result and SE27.activate_security_access_fixedkey(can_p, conf.default_rig_config)

        # step3:
        # action: read SBL
        # result: header, data, offset of VBF
        vbf_header, vbf_data, vbf_offset = step_3()

        # step4:
        # action: extract data of first block in SBL
        # result:
        vbf_block = step_4(vbf_offset, vbf_data)

        # step5:
        # action:
        # result:
        result = result and step_5(can_p, vbf_header, vbf_block)

        # step6:
        # action: verify session PBL
        # result:
        result = result and step_6(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
