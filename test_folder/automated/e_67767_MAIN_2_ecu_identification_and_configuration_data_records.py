"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-10-30
# version:  1.0
# reqprod:  67767
#
# inspired by https://grpc.io/docs/tutorials/basic/python.html
#
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
import inspect

from datetime               import datetime
import sys
import logging

import odtb_conf
from build.did                              import app_did_dict
from supportfunctions.support_can           import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2    import SupportTestODTB2
from supportfunctions.support_carcom        import SupportCARCOM
from supportfunctions.support_file_io       import SupportFileIO
from supportfunctions.support_precondition  import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22     import SupportService22

SIO         = SupportFileIO
SC          = SupportCAN()
SUTE        = SupportTestODTB2()
SC_CARCOM   = SupportCARCOM()
PREC        = SupportPrecondition()
POST        = SupportPostcondition()
SE22        = SupportService22()


def test_did(can_p, stepno, did_byte, did_hex):
    '''
    Checks a single DID with ReadDataByIdentifier and return True if it's available.
    '''
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        did_byte, b''),
                        "extra" : ''
                    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,
                        "purpose" : "Test DID: %s" % did_hex.upper(),
                        "timeout" : 2,
                        "min_no_messages" : -1,
                        "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],
                                            teststring=did_hex.upper())
    logging.info("ReadDataByIdentifier(%s): %s", did_hex.upper(),
                                                SC.can_messages[can_p["receive"]][0][2])
    return result

def step_1():
    '''
    Compare the range 0xEDA0-0xEDFF to the SDDB and return a list of available DID:s in the range.
    '''
    did_int=0x22EDA0
    didarray = []
    for _ in range(96):
        did_hex = hex(did_int)[2:].upper()

        if did_hex in app_did_dict:
            didarray.append([did_int-0x220000, did_hex[2:]])

        did_int = did_int + 1

    return didarray

def step_2(can_p, didarray):
    '''
    Verify that all DID:s defined by step_1 are available and readable by service 22.
    '''
    resultarray = []
    counter = 0
    for did in didarray:
        did_int=did[0]
        did_hex=did[1]
        did_byte = did_int.to_bytes(length=2, byteorder='big', signed=False)

        result = test_did(can_p, stepno=counter+200, did_byte=did_byte, did_hex=did_hex)
        resultarray.append([did_hex.upper(), result])
        counter = counter + 1

    return resultarray

def step_3():
    '''
    Compare the range 0xED20-0xED7F to the SDDB and return a list of available DID:s in the range.
    '''
    did_int=0x22ED20
    didarray = []
    for _ in range(96):
        did_hex = hex(did_int)[2:].upper()

        if did_hex in app_did_dict:
            didarray.append([did_int-0x220000, did_hex[2:]])

        did_int = did_int + 1

    return didarray

def step_4(can_p, didarray):
    '''
    Verify that all DID:s defined by step_3 are available and readable by service 22.
    '''
    resultarray = []
    counter = 0
    for did in didarray:
        did_int=did[0]
        did_hex=did[1]
        did_byte = did_int.to_bytes(length=2, byteorder='big', signed=False)

        result = test_did(can_p, stepno=counter+200, did_byte=did_byte, did_hex=did_hex)
        resultarray.append([did_hex.upper(), result])
        counter = counter + 1

    return resultarray


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
    timeout = 300
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action:   Compare the range 0xEDA0-0xEDFF to the SDDB.
        # result:   Returns a list of available DID:s in the range.
        didarray_step1 = step_1()

        # step 2:
        # action:   Verify available DID:s in the range 0xEDA0-0xEDFF.
        # result:   ECU sends a valid response for all DID:s in dictionary.
        resultarray_step2 = step_2(can_p, didarray_step1)

        # step 3:
        # action:   Compare the range 0xED20-0xED7F to the SDDB.
        # result:   Returns a list of available DID:s in the range.
        didarray_step3 = step_3()

        # step 4:
        # action:   Verify available DID:s in the range 0xED20-0xED7F.
        # result:   ECU sends a valid response for all DID:s in dictionary.
        resultarray_step4 = step_4(can_p, didarray_step3)

        # step 5:
        # action:   Summarize results
        # result:   Pass if non-zero length and all tested cases return True.
        resultarray = resultarray_step2 + resultarray_step4
        if len(resultarray) > 0:
            logging.info('[DID:  , Result:]')
            for didresult in resultarray:
                logging.info("%s", didresult)
                result = result and didresult[1]
        else:
            result = False
            logging.info("Test failed. No valid DID:s in SDDB.")

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
