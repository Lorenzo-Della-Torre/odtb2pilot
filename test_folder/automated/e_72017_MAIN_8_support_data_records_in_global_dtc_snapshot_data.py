"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72017

title:>
    Supported data records in global DTC snapshot data ; 10

purpose:>
    To define the criteria for sampling of snapshot data record 20

definition:>
    For all DTCs stored and supported by the ECU, global DTC snapshot data
    records shall include the following data, as defined in Carcom - Global
    Master Reference Database (GMRDB).

    0xDD00 – Global Real Time
    0xDD01 – Total Distance
    0xDD02 – Vehicle Battery Voltage
    0xDD05 – Outside Temperature
    0xDD06 – Vehicle Speed
    0xDD0A – Usage Mode

details:>
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

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO

def step_1(dut : Dut):
    '''
    Verify global DTC snapshot data records contains all data.
    '''

    result = True
    dtc = ""

    yml_dids = {"list_dids" : []}
    yml_dids = SIO.parameter_adopt_teststep(yml_dids)

    response = dut.uds.dtc_snapshot_ids_1903()

    if response.data["snapshot_ids"]:
        dtc = response.data["snapshot_ids"][0][1]
    else:
        result = False
        logging.error("No DTCs in the ECU to test snapshot data")

    if result:
        logging.info("First DTC in the list is %s ", dtc)
        message = dut.uds.dtc_snapshot_1904(bytes.fromhex(dtc))
        logging.info("Global DTC snapshot data response : %s", message.raw)

        #Verify data available for all the Ids
        for did in yml_dids["list_dids"]:
            if not did in message.raw:
                logging.error("The ID %s is not in the reply", did)
                result = False
            else:
                logging.info("The ID %s is available in the reply", did)

    return result


def run():
    """
    Run - Verify Global snapshot data
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        # Communication with ECU lasts 60 seconds.
        dut.precondition(timeout=60)

        # Verify the DID values in DTC snapshot
        result = dut.step(step_1, purpose="Verify that the ECU sends DTC snapshot values")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
