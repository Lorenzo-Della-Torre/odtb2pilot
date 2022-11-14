"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72185
version: 0
title: Activate Secondary Bootloader routine
purpose: >
    All ECUs must support routines defined for SWDL.

description: >
    Rationale:
    The routine shall be used to activate the Secondary Bootloader after it has been downloaded to
    volatile memory. The ECU shall start executing the secondary bootloader from the memory
    address defined in the data file containing the Secondary Bootloader.

    Req: The Activate Secondary Bootloader routine with routine identifier as specified in the
    table below shall be implemented as defined in Carcom - Global Master Reference
    Database (GMRDB).
    ------------------------------------------------------------
    Description	                                Identifier
    ------------------------------------------------------------
    Activate Secondary Bootloader	               0301
    ------------------------------------------------------------

    •   It shall be possible to execute the control routine with service as specified in
        Ref[LC : VCC - UDS Services - Service 0x31 (RoutineControl) Reqs].
    •   The final positive response message from the Activate Secondary Bootloader routine shall
        be sent when the SBL has been activated, i.e. from the SBL. If the SBL is already
        activated at the time of the request the ECU shall respond with a positive response
        message with Routine Completed = 0.
    •   The routine shall be implemented as a type 1 routine.

    The ECU shall support the identifier in the following sessions:
    •   Programming session (which includes both primary and secondary bootloader)

details: >
    Verify SBL activation using the routine identifier (0x0301) in programming session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_service27 import SupportService27

SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()


def step_1(dut: Dut):
    """
    action: Verify SBL activation using the routine identifier (0x0301) in programming session
    expected result: True on received 'Type1,Completed'
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

   # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Aborting SBL activation due to problems when loading VBFs")
        return False

    # Security access
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not sa_result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    logging.info("Security access successful in programming session")

    # Download SBL
    result, vbf_sbl_header = SSBL.sbl_download(dut, SSBL.get_sbl_filename(), stepno='1')
    if not result:
        logging.error("Test Failed: SBL download failed")
        return False

    # Activate SBL with RoutineControlRequest with routine identifier 0x0301
    call = vbf_sbl_header['call'].to_bytes((vbf_sbl_header['call'].bit_length()+7) // 8, 'big')
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID",b'\x03\x01' + call, b'\x01')
    response = dut.uds.generic_ecu_call(payload)

    result = SUTE.pp_decode_routine_control_response(response.raw, 'Type1,Completed')

    if result:
        logging.info("Received routine identifier response 'Type1,Completed' as expected")
        return True

    logging.error("Test Failed: Routine identifier response 'Type1,Completed' not received")
    return False


def run():
    """
    Verify SBL activation using the routine identifier (0x0301) in programming session
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=90)

        result = dut.step(step_1, purpose='Verify SBL activation using the routine '
                                          'identifier (0x0301) in programming session')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
