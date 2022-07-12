"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68239
version: 8
title: Complete ECU PartSerial Number data record
purpose: >
    To enable readout of the complete set of ECU Part/Serial numbers.

description: >
    A data record (called "composite" data record) with identifier 0xEDA0 shall be implemented.
    The data records shall contain several data items in an arbitrary order. Each data item shall
    consist of a data identifier followed by the record data that is identified by the data
    identifier. The "composite" data record with identifier 0xEDA0 shall contain the following
    data items(the data items is depending of the currently active executing software):

    Description	Identifier
    ---------------------------------------------------------------------
                                               Application   PBL	SBL
    ---------------------------------------------------------------------
    Diagnostic Database Part number    	            F120	F121    F122
    ECU Core Assembly Part Number	                F12A	F12A	F12A
    ECU Delivery Assembly Part Number	            F12B	F12B	F12B
    ECU Serial Number	                            F18C	F18C	F18C
    Software Part Number	                        F12E	F125	F124
    Private ECU(s) or component(s) Serial Number	F13F	  -	      -
    ----------------------------------------------------------------------
    •   The data records shall be implemented exactly as defined in Carcom - Global Master
        Reference Database.
    •   It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    •    Default session
    •    Programming session (which includes both primary and secondary bootloader)
    •    Extended Session

details: >
    Import script - Inherited from older version of requirement
"""

from e_68239_MAIN_7_complete_ecu_partserial_number_data_record import run

if __name__ == '__main__':
    run()
