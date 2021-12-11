/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
This is a script that starts the didalyzer GUI (pretty print of DIDs).

The didalyzer is a graphical interface to read dids using the hilding hardware.
"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

import supportfunctions.pretty_print_GUI as ppGUI

def run():
    """
    Run - Call other functions from here

    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        #When this time has run out the communication will fail
        dut.precondition(timeout=3600)

        #This is used to start the GUI
        ppGUI.run(dut)

        #This is used to print in console for a certain duration.
        #Basically only using the backend, provide did id and time in seconds.
        #pp.subscribe_to_did(dut, "FD40", duration=5)

        result = True

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        result = False
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
