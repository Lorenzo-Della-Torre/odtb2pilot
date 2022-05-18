"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 113861
version: 1
title: Diagnostic Read out #1 to #4 data record
purpose: >
    To support quality tracking of the ECU.

description: >
    A data record(s) with identifiers as specified in the table below may be implemented. The data
    record(s) intended for quality tracking of the ECU is defined by the implementer. The data
    record(s) shall only consist of other record data than the record data read by the generic
    standard read out sequence.

    Description	                                Identifier
    ---------------------------------------------------------
    Diagnostic Read out #1 to #4	            EDC0 - EDC3
    ---------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
        •	Default session
        •	Extended Session

details: >
    Import script - Inherited from older version of requirement
"""

from e_113861_MAIN_0_diagnostic_readout import run

if __name__ == '__main__':
    run()
