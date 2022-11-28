"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76621
version: 2
title: RoutineControl (31) - routineControlOptionRecord (RCEOR)
purpose: >
    To have the optional ability to define control parameters for a control routine. The control
    parameters can be used in one, several or all sub-functions supported by the control routine.

description: >
    The ECU may support the data parameter routineControlOptionRecord in one or several of the
    implemented sub-functions for a control routine. The data parameter is defined by the
    implementer.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76621_MAIN_1_rc31_option_record import run

if __name__ == '__main__':
    run()
