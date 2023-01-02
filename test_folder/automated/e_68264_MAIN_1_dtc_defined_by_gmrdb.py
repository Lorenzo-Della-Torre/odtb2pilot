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
    We test this requirement by doing negative testing. That is, we attempt finding one DTC that
    does not respond appropriately to a snapshot request. Appropriately mean that it should not
    return any error to the request and the content of the snapshot should be according the SDDB.
    Implicitly we assume that the information in SDDB corresponds with GMRDB.
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
    dtcs_not_in_sddb = []
    failed_dtc = []

    # DTCs from ReadDTCByStatusMask
    response = dut.uds.generic_ecu_call(bytes.fromhex('1902FF'))
    response_dtcs = response.data['dtcs']

    # DTCs from SDDB
    sddb_dtcs = dut.conf.rig.sddb_dtcs["sddb_dtcs"]

    # Test all the DTCs are appropriate according to SDDB
    for _, response_data in enumerate(response_dtcs):
        dtc = response_data[0]
        if dtc in sddb_dtcs.keys():
            payload = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                            bytearray.fromhex(dtc), bytes.fromhex('FF'))
            dtc_response = dut.uds.generic_ecu_call(payload)

            # Compare the DTC snapshot positive response
            if dtc_response.raw[2:4] == '59' or dtc_response.raw[4:6] == '59':
                logging.info("DTC %s snapshot request returns positive response %s as expected",
                              dtc, dtc_response.raw)
                results.append(True)

                # Compare the DTC snapshot DIDs are according to SDDB
                if sddb_dtcs[dtc]['snapshot_dids'] != dtc_response.data['details']['snapshot_dids']:
                    logging.error("DTC snapshot did response are not equal with SDDB DIDs which is "
                                  "not expected for DTC %s", dtc)
                    results.append(False)
                    failed_dtc.append(["DTC snapshot did response are not equal with SDDB DIDs "
                                       "which is not expected for DTC "+dtc])
                else:
                    logging.info("DTC snapshot did response are equal with SDDB DIDs as expected"
                                 " for DTC %s", dtc)
                    results.append(True)
            else:
                logging.error("DTC %s snapshot request returns negative response %s",
                              dtc, dtc_response.raw)
                results.append(False)
                failed_dtc.append(["DTC "+dtc+" snapshot request returns negative response "+
                                  dtc_response.raw])
        else:
            dtcs_not_in_sddb.append(dtc)

    if all(results) and len(results) != 0:
        if len(dtcs_not_in_sddb) != 0:
            logging.error("Test Failed: DTCs not found in SDDB: %s", dtcs_not_in_sddb)
            return False
        logging.info("Successfully verified all the DTCs are identical according to SDDB DIDs")
        return True

    if len(dtcs_not_in_sddb) != 0:
        logging.error("Test Failed: DTCs not found in SDDB: %s", dtcs_not_in_sddb)
    logging.error("Test Failed: Failed DTCs = %s", '\n'.join(map(str, failed_dtc)))
    logging.error("Test Failed: Some or one of the DIDs are not identical according to SDDB DIDs")
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
