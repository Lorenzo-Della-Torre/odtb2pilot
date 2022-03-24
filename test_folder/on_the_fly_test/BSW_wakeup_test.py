"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

details: >
    Verify if the ECU wakes up or not after the NM frames are stopped sending.
    The timing value used here ranges between 3s to 30s

"""

import sys
import logging
import time

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanParam,PerParam
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27

SC = SupportCAN()
CNF = Conf()
SSBL = SupportSBL()
SE27 = SupportService27()
STO = SupportTestODTB2()

def heart_beat(self, timeout=36000):
    """Run preconditions and start heartbeat

    Args:
        timeout (int, optional): Decides for how long the test is allowed to run.
        Defaults to 30.
    """

    self.uds.step = 100
    # start heartbeat, repeat every 0.8 second
    heartbeat_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : self.conf.rig.signal_periodic,
        "nspace" : self.namespace.name,
        "protocol" : "can",
        "framelength_max" : 8,
        "padding" : True,
        "frame" : bytes.fromhex(self.conf.rig.wakeup_frame),
        "intervall" : 0.4
        }
    logging.debug("heartbeat_param %s", heartbeat_param)


    # start heartbeat, repeat every x second
    SC.start_heartbeat(self.network_stub, heartbeat_param)

    # start testerpresent without reply
    #tp_name = self.conf.rig.signal_tester_present
    #SupportService3e.start_periodic_tp_zero_suppress_prmib(self, tp_name)

    # record signal we send as well
    SC.subscribe_signal(self, timeout)
    logging.debug("precondition can_p2 %s", self)

    # record signal we send as well. Do notice the reverse order of the
    # send and receive signals!
    can_p2: CanParam = {"netstub": self.network_stub,
                        "send": self.conf.rig.signal_receive,
                        "receive": self.conf.rig.signal_send,
                        "namespace": self.namespace,
                        "protocol": self.protocol,
                        "framelength_max": self.framelength_max,
                        "padding" : self.padding
                        }
    SC.subscribe_signal(can_p2, timeout)


def run():
    """
    DD0A verification in  Default and Ext Session
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()

    result = False

    payload = b'\x22\xf1\x86'

    timelist = list()

    cpay: CanPayload = {
            "payload": payload,
            "extra": ''
        }
    etp: CanTestExtra = {
            "step_no": 280,
            "purpose": "To Test ECU Wakeup",
            "timeout": 1,
            "min_no_messages": -1,
            "max_no_messages": -1
        }

    try:

        timing =3

        # This while loop runs infinitely. Need to add conditions based on
        # the test requirements.
        while 1:

            print("============================================================")

            heart_beat(dut)

            STO.teststep(dut, cpay, etp)

            response = SC.can_messages[dut['receive']]

            if len(response) == 0:
                timelist.append(timing-3)
                logging.error(" ECU did not wake up for the time difference of : %d  ",timing-3)

            else:
                logging.info(" ECU wakes up for time diff : %d",timing-3)

            SC.stop_heartbeat()
            time.sleep(timing)

            if timing > 30:
                timing = 0

            timing = timing +3

            logging.info('All Error list in seconds: %s', timelist)

        if len(timelist) == 0:
            result = True

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        if result:
            logging.info("PASSED")
        else:
            logging.info("FAILED")

if __name__ == '__main__':
    run()
