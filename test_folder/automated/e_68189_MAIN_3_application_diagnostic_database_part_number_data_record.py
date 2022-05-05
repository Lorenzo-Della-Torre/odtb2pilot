"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68189
version: 3
title: Application Diagnostic Database Part Number data record
purpose: >
    To enable readout of a database key for the diagnostic database used by the ECU application SW.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database.

    Description	                                    Identifier
    ----------------------------------------------------------
    Application Diagnostic Database Part Number	    F120
    ----------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
        •	Default session
        •	Extended Session

details: >
    Import script - Inherited from older version of requirement
"""

from e_68189_MAIN_2_application_diagnostic_database_part_number_data_record import run

if __name__ == '__main__':
    run()
