"""
Testscript Hilding MEPII
project:  BECM basetech MEPII
author:   DHJELM (Daniel Hjelm)
date:     2020-11-19
version:  5
reqprod:  72041

title:

    Support for DTC time stamp #20 ; 5

purpose:

    To provide enhanced information about the occurrence of a fault, that may
    be useful in the analysis of the fault.

description:

    For all DTCs supported by the ECU a data record identified by
    DTCExtendedDataRecordNumber=20 shall be implemented according to the
    following definition:

    - The record value shall be equal to the global real time (data record
      0xDD00) that is taken the first time FDC10 reaches a value that is equal
      to or greater than UnconfirmedDTCLimit, since DTC information was last
      cleared.

    - The stored data record shall be reported as a 4 byte value.


Make sure the DTC snapshot has a time record
"""
import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()

def step_1(can_p):
    """
    Teststep 1: Get the global time
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                        b'\x0B\x4A\x00', b'\x20'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Make sure the DTC snapshot has a time record",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    if not SUTE.teststep(can_p, cpay, etp):
        return False

    message = SC.can_messages[can_p["receive"]][0][2]
    pos1 = message.find("DD00")
    if pos1 == -1:
        # No time record was found in the DTC snapshot
        return False

    time_stamp = message[pos1+4: pos1+12]

    # Since we currently can't trigger any DTC on the raspberry pi testbench,
    # this test should be seen more as a stub to build future tests. The ODTB
    # is not connected to a any other ecu, hence we do not get any .
    # This is not a very sensible test, but it gives us something to build on
    return time_stamp == "00000000"


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
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

    # step1:
    # action: Get time data from DTC snapshoot
    # result: We should be able to retrieve a timestamp from the response
        result = result and step_1(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
