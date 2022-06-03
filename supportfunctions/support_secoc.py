"""

/*********************************************************************************/


Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

import logging

class SecOCmsgVerification: # pylint: disable=too-few-public-methods
    """
    class for supporting SecOC message Verification
    """

    @staticmethod
    def failed_message_take_no_action(signal):
        """
        Support function to take no action, function to be implemented
        """
        #Logic to be implemented in future
        # Take no Action
        logging.info(" message to take no action on %s",signal)
        response = ''
        return response

    @staticmethod
    def get_secoc_message(signal):
        """
        Return SecOC message
        Function to be implemented to get SecOC message
        """
        logging.info("Need to implement support function to get SecOC message for signal %s"
                     ,signal)
        response = ''
        return response
