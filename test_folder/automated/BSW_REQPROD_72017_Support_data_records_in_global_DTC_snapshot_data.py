"""
reqprod: 72017

title:
    Supported data records in global DTC snapshot data ; 10

purpose:
    To define the criteria for sampling of snapshot data record 20

definition:
    For all DTCs stored and supported by the ECU, global DTC snapshot data
    records shall include the following data, as defined in Carcom - Global
    Master Reference Database (GMRDB).

    0xDD00 – Global Real Time
    0xDD01 – Total Distance
    0xDD02 – Vehicle Battery Voltage
    0xDD05 – Outside Temperature
    0xDD06 – Vehicle Speed
    0xDD0A – Usage Mode

details:
    Note: 1) That the above requirement is for SPA2. For SPA1 we will use the
    following list of DIDs to check against as it is corresponding to an
    earlier version of this requirement.

    0xDD00 – Global Real Time
    0xDD01 – Total Distance
    0xDD02 – Vehicle Battery Voltage
    0xDD0A – Usage Mode

    Note: 2) When we request the global DTC snapshot data, the response can
    also include local DTCs so there is a risk that by doing this testing that
    we get false positives. That is, one or more of the DID might actually not
    be part of the global snapshot, but rather the local. Unfortunatly, there
    seems not to exist any good way to distinguish between the two, so we will
    have to live with that for now.

"""


import os
import time
from datetime import datetime
import sys
import logging
import inspect
import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam,CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE10 = SupportService10()


def step_1(can_p):
    '''
    Verify global DTC snapshot data records contains all data.
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",\
                                            b'\x0B\x4A\x00', b"\xFF"),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 1,
        "purpose": "Verify global snapshot data ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    message = SC.can_messages[can_p['receive']][0][2]
    logging.info("Global DTC Snapshot data: %s", message)

    did_check = True
    platform = os.environ.get("ODTBPROJ")
    if platform == "MEP2_SPA1":
        snapshot_dids = ['DD00', 'DD01', 'DD02', 'DD0A']
    elif platform == "MEP2_SPA2":
        snapshot_dids = ['DD00', 'DD01', 'DD02', 'DD05', 'DD06', 'DD0A']
    else:
        raise EnvironmentError("ODTBPROJ is not set")

    for did in snapshot_dids:
        if not did in message:
            logging.error("The following DID is not in the reply: %s", did)
            did_check = False

    return result and did_check


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
    SSBL.get_vbf_files()
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################

        # step 1:
        # action: Verify global snapshot data contains expected DID's
        # result: Check if expected DiD's are contained in reply
        result = result and step_1(can_p)

   ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
