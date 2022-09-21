"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 72203
version: 2
title: Erase Memory routine
purpose: >
    All ECUs must support routines defined for SWDL

description: >
    Rationale:
    The routine shall perform a non-volatile memory erase of the memory blocks defined by the
    memoryAddress and memorySize request parameters. The ECU does not need to support the
    routine if the ECU has file system data storage and implements an alternative method e.g
    RequestFileTransfer - modeOfOperation parameter DeleteFile or ReplaceFile.

    Req:
    If the ECU supports a non-file system data storage SWDL option, the ECU shall implement
    the Erase Memory routine with routine identifier as specified in the table below. The ECU
    shall implement the routine exactly as defined in Carcom - Global Master Reference Database
    (GMRDB)
        ------------------------------------------
            Description             Identifier
        ------------------------------------------
            Erase Memory            FF00
        ------------------------------------------

        • It shall be possible to execute the control routine with service as specified in
          Ref[LC : VCC - UDS Services - Service 0x31 (RoutineControl) Reqs].
        • The ECU shall implement the routine as a type 1 routine.
    The ECU shall support the identifier in the following sessions:
        • Programming session (which includes secondary bootloader)

details: >
    Import script - Inherited from older version of requirement
"""

import logging
import sys
from e_72203_MAIN_1_erase_memory_routine import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
