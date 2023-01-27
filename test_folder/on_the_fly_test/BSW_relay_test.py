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

from supportfunctions.support_relay import Relay

relay = Relay()


# A sequence of action to test that the relay is working or not.
# Listen to the LEDs and the click sound in the relay boards.

relay.power_on()

relay.power_off()

relay.psr_on()

relay.psr_off()

relay.ecu_on()

relay.ecu_off()

relay.toggle_power()

relay.toggle_power()

relay.relay_all_on()

relay.relay_all_off()
 