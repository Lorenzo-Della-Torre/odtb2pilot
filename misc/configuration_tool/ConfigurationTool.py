"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

This is a script that starts the the hilding configuration tool.

"""

import misc.configuration_tool.main_GUI as ctGUI

def run():
    """
    Run - Call other functions from here

    """

    #This is used to start the GUI
    ctGUI.run()


if __name__ == '__main__':
    run()