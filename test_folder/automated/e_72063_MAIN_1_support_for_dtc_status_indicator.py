# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-11-20
# version:  1.0
# reqprod:  72063

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
import sys
import logging
import inspect

from datetime   import datetime

import odtb_conf
from supportfunctions.support_can           import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2    import SupportTestODTB2
from supportfunctions.support_carcom        import SupportCARCOM
from supportfunctions.support_file_io       import SupportFileIO
from supportfunctions.support_precondition  import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition

SIO         = SupportFileIO
SC          = SupportCAN()
SUTE        = SupportTestODTB2()
SC_CARCOM   = SupportCARCOM()
PREC        = SupportPrecondition()
POST        = SupportPostcondition()


def step_1(can_p):
    """
    Teststep 1: Verify that ReadDTCInfoExtDataRecordByDTCNumber replies positive for a DTC,
    with DTCExtendedDataRecordNumber = 30. Verify that record value is 1 byte long.
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoExtDataRecordByDTCNumber",
                                        b'\x0D\x15\x00', b'\x30'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "verify that Read DTC Extent Info reply positively",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    teststring = '0D1500'
    teststring_yml = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'teststring')
    if len(teststring_yml) > 0:
        teststring = teststring_yml

    result = SUTE.teststep(can_p, cpay, etp)
    can_reply_message = SC.can_messages[can_p["receive"]]
    result = result and SUTE.test_message(can_reply_message, teststring)

    if result:
        reply = can_reply_message[0][2]
        index = reply.index(teststring)+len(teststring)
        ext_data_record = reply[index:]

        # Second byte in ext_data_record should be 0x30
        if ext_data_record[2:4] != "30":
            logging.info("Error: Wrong data record number: %s\n Expected 30",
                            ext_data_record[2:4])
            logging.info("Received message: %s\n", reply)
            result = False

        # Data record value should be exactly 1 byte long.
        record_value_len = len(ext_data_record)-4
        if record_value_len != 2:
            logging.info("Error: Wrong length of data record value: %s\n Expected 2",
                            record_value_len)
            logging.info("Received message: %s\n", reply)
            result = False

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
    timeout = 50
    result = PREC.precondition(can_p, timeout)

    if result:

        ############################################
        # teststeps
        ############################################
        # step1:
        # action:   Send ReadDTCInfoExtDataRecordByDTCNumber, with DTCExtendedDataRecordNumber = 30.
        #           Verify that record value is 1 byte long.
        # result:   BECM replies with the DTC, data record value in response is 1 byte long.
        result = step_1(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
