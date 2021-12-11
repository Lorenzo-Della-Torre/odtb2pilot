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
date:     2020-11-23
version:  2
reqprod:  68264

title:

    DTCs defined by GMRDB

purpose:

    All DTC information shall be supported by VCC tools and must therefore be
    defined in GMRDB.

description:

    Rationale:

    Global Master Reference Data Base (GMRDB) is a part of the central
    diagnostic database that is used by Volvo Car Corporation in order to
    document the implementation of diagnostics in the ECUs. GMRDB is a library
    containing predefined DTCs, DIDs and Control Routines. The definition of
    DTCs (both identifier and description) that are supposed to be used by
    Volvo tools must have its origin in GMRDB. GMRDB holds only the 2-byte base
    DTC.

    Requirement:

    DTCs supported by an ECU shall be implemented in accordance to the
    definition in Global Master Reference Database. Development specific
    implementer specified DTCs are excluded from this requirement.

details:

    We test this requirement by doing negative testing. That is, we attept
    finding one DTC that does not respond appropriately to a snapshot request.
    Appropriately mean that it should not return any error to the request and
    the content of the snapshot should be according the SDDB. Implicitly we
    assume that the information in SDDB corresponds with GMRDB.

"""
import time
from datetime import datetime
from dataclasses import dataclass
import sys
import logging
import inspect

import odtb_conf

from build.dtc import sddb_dtcs

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

def dtc_snapshot(dtc_number: bytes, mask: bytes):
    """ Report DTC Snapshot Record By DTC Number """
    return b'\x19\x04' + dtc_number + mask

@dataclass
class Dtc:
    """ Hybrid/EV Battery Voltage Sense "D" Circuit """
    battery_voltage_d = b'\x0B\x4A\x00'

def step_1(can_p):
    """ Test that all DTC responds appropriately """

    for dtc_id, dtc in sddb_dtcs.items():
        dtc_number = bytearray.fromhex(dtc_id)
        logging.debug('Testing DTC number: %s', dtc_number)

        cpay: CanPayload = {
            "payload": dtc_snapshot(dtc_number, b'\xFF'),
            "extra": ''
        }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
        etp: CanTestExtra = {
            "step_no": 1,
            "purpose": f"Test that the DTC {dtc_number} snapshot request "
                        "responds according to SDDB",
            "timeout": 1,
            "min_no_messages": -1,
            "max_no_messages": -1
        }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

        result = SUTE.teststep(can_p, cpay, etp)
        if not result:
            return False

        message = SC.can_messages[can_p['receive']]

        if message:
            message = message[0][2]
            if "7F" in message:
                logging.error(
                    "DTC %s snapshot request returns an error (7F)", dtc_number)
                logging.error("Expected: %s", dtc)
                return True

            # testing that the snapshots contain dids according to SDDB
            for snapshot in dtc["snapshot_dids"]:
                for _, did in snapshot["did_ref"].items():
                    if not did in message:
                        logging.error(
                            "DTC %s snapshot request does not return a "
                            "snapshot containing the did: %s", dtc_number, did)
                        return True

        else:
            # Currently the ECU stops responding after a while, so in order to
            # keep the test running we need to restart it to keep procerssing
            # the DTCs
            POST.postcondition(can_p, time.time(), True)
            PREC.precondition(can_p, 30)

    return False


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

    # action: Negative testing: request a snapshot for all DTCs defined in SDDB
    # result: Since we are doing negative testing we should get a True result
    # if at least one DTC does not respond to a snapshot request or does not
    # contain the dids accoding to the specification
        result = result and step_1(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
