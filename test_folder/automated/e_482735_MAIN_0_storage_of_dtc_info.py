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

"""
reqprod: 482735
version: 0
title:
    Storage of DTC information

purpose:
    To ensure that the amount of DTCs that shall be stored in long-term memory.

description:
    The ECU shall store supported DTC information in the long-term memory.

    DTC information:
     * Status bits
     * Snapshot data
     * Status indicators (SI)
     * Operation cycle counters (OCC)
     * Time stamps

details:
    Look for DTC that has the DTC status bit "confirmed" set. If it is set,
    then we can be certain that the snapshot is in long-term memory. Verify
    then that it has, dtc status bits, snapshot data, operation cycle counters,
    and time stamps.

    The test is an existence test making sure that at lease one DTC has been
    stored in the long-term memory.
"""

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.status_bits import DtcStatus

def step_1(dut):
    """
    action:
        get all dtc snapshots with id and dtc number

    expected_result: >
        ECU: positive response with dtcs data
    """

    # create a DTC status mask with confirmed_dtc set, since that is the bit
    # that we want to be true to get DTCs that are stored in the long-term
    # memory.
    dtc_status_mask = DtcStatus()
    dtc_status_mask.confirmed_dtc = True

    logging.info(dtc_status_mask)

    res = dut.uds.dtc_by_status_mask_1902(dtc_status_mask)

    if res.empty():
        raise DutTestError(
            "The ECU did not give us any response to the snapshot ids request")

    logging.info(res)

    if not "dtcs" in res.data:
        raise DutTestError("No DTC snapshots are present on the ECU")

    return res.data["dtcs"]

def step_2(dut, dtcs):
    """
    action:
        test dtc extended data records for one snapshot per DTC

    expected_result:
        ECU: positive response with all OCCs, time stamps, and status
        indicators present
    """

    si30_records = []
    for dtc, dtc_status_bits in dtcs:
        res = dut.uds.dtc_extended_1906(bytes.fromhex(dtc), b'\xFF')

        logging.info(res)

        if not dtc_status_bits.confirmed_dtc:
            logging.error(dtc_status_bits)
            raise DutTestError(
                "DTC retrieved with status bits, that do not correspond " + \
                "to the DTC status mask request")

        if dtc_status_bits != res.data['dtc_status_bits']:
            logging.error("From DTC by status mask request (1902): %s",
                          dtc_status_bits)
            logging.error("From extended data records (1906): %s",
                          res.data['dtc_status_bits'])
            raise DutTestError("DTC status bits does not match")

        for field in ['occ2', 'occ2', 'occ3', 'occ4', 'occ5', 'occ6', 'fdc10',
                      'ts20', 'ts21', 'si30']:
            if field not in res.data:
                raise DutTestError(
                    f"Field '{field}' not present in DTC extended data record")

        # the bit format of si30 is abit unclear, so let's collect them and
        # inspect them. It appears that the format is in the reverse order of
        # the DTC status bits with bit zero being the left most bit as opposed
        # to the right most. Furthermore, it appears to be returned in decimal
        # format from the ECU whereas everything else in the hexstring is in
        # hex. Otherwise, the first three bits will not be zero as by the
        # specification in the swrs document.
        si30_records.append(
            {k: v for k, v in res.data.items() if k.startswith('si30')})

    logging.info(si30_records)
    num_si30_records = len(si30_records)
    logging.info('A total number of %s si30 records found.', num_si30_records)

def run():
    """ Storage of DTC information """
    logging.basicConfig(
        format=" %(message)s", stream=sys.stdout, level=logging.DEBUG)

    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition(timeout=2000)

        dtcs = step_1(dut)
        step_2(dut, dtcs)

        result = True
    except DutTestError as error:
        logging.error("The test encountered an error: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
