"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68264
version: 1
title: DTCs defined by GMRDB
purpose: >
	All DTC information shall be supported by VCC tools and must therefore be defined in GMRDB.

description: >
    Rationale-
    Global Master Reference Data Base (GMRDB) is a part of the central diagnostic database that
    is used by Volvo Car Corporation in order to document the implementation of diagnostics in the
    ECUs. GMRDB is a library containing predefined DTCs, DIDs and Control Routines. The definition
    of DTCs (both identifier and description) that are supposed to be used by Volvo tools must
    have its origin in GMRDB. GMRDB holds only the 2-byte base DTC.

    Requirement-
    DTCs supported by an ECU shall be implemented in accordance to the definition in Global Master
    Reference Database. Development specific implementer specified DTCs are excluded from this
    requirement.

details: >
    Verify positive response of all DTCs or DTC snapshot DIDs are identical according to SDDB DIDs
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM

SC_CARCOM = SupportCARCOM()


def step_1(dut: Dut):
    """
    action: Verify positive response of all DTCs or DTC snapshot DIDs are identical according
            to SDDB DIDs
    expected_result: True when received positive response for all DTCs or DTC snapshot DIDs are
                     identical according to SDDB DIDs
    """
    results = []
    # Test all the DTCs are appropriate according to SDDB
    sddb_dtcs = dut.conf.rig.sddb_dtcs["sddb_dtcs"]
    failed_dtc = []
    for dtc, dtc_data in sddb_dtcs.items():
        payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                        bytearray.fromhex(dtc), bytes.fromhex('FF'))

        dtc_response = dut.uds.generic_ecu_call(payload)

        # Compare the DTC snapshot positive response
        if dtc_response.raw[2:4] == '59':
            logging.info("DTC %s snapshot request returns positive response %s as expected", dtc,
                         dtc_response.raw[2:4])
            results.append(True)

            # Compare the DTC snapshot DIDs are according to SDDB
            if dtc_data['snapshot_dids'] != dtc_response.data['details']['snapshot_dids']:
                logging.error("DTC snapshot did response are not equal with SDDB DIDs which is not"
                             " expected for DTC %s", dtc)
                results.append(False)
                failed_dtc.append(dtc)
            else:
                logging.info("DTC snapshot did response are equal with SDDB DIDs as expected"
                              " for DTC %s", dtc)
                results.append(True)
        else:
            logging.error("DTC %s snapshot request returns negative response %s",
                           dtc, dtc_response.raw[2:4])
            results.append(False)
            failed_dtc.append(dtc)

    if all(results) and len(results) != 0:
        logging.info("Successfully verified all the DTCs are identical according to SDDB DIDs")
        return True

    logging.error("Test Failed: DTC DIDs %s are not identical according to SDDB DIDs",
                  ", ".join(failed_dtc))
    return False


def run():
    """
    Verify positive response of all DTCs or DTC snapshot DIDs are identical according to SDDB DIDs
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=500)

        result = dut.step(step_1, purpose='Verify positive response of all DTCs or DTC snapshot'
                                          ' DIDs are identical according to SDDB DIDs')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
