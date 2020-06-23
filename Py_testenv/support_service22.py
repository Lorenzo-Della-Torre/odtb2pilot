# project:  ODTB2 testenvironment using SignalBroker
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-05-29
# version:  1.0

# Initial version:
# version 1.0:
#   teststep    Common teststeps moved into support for dedicated service
#   pep8        coding is changed to confirm to pep8 (some code left, though)

# inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC route guide client."""

import logging

from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()

class SupportService22:
    """
    class for supporting Service#22
    """


    #@classmethod
    @staticmethod
    def read_did_eda0(can_p: CanParam, stepno=220):
        """
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUTE.teststep(can_p, cpay, etp)
        if not len(SC.can_messages[can_p["receive"]]) == 0:
            logging.info('%s',\
                         SUTE.pp_combined_did_eda0(SC.can_messages[can_p["receive"]][0][2],\
                                                    title='')
                        )
        else:
            logging.info('%s', "No messages received for request Read DID EDA0")
            logging.info("Frames received: %s", SC.can_frames[can_p["receive"]])
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            result = False
        return result

    #@classmethod
    @staticmethod
    #def read_did_f186(self, stub, can_send, can_receive, can_namespace, dsession=b''):
    def read_did_f186(can_p: CanParam, dsession=b'', stepno=221):
        """
        Read DID F186: Active Diagnostic Session
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x86', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Active Diagnostic Session",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUTE.teststep(can_p, cpay, etp)
        #time.sleep(1)
        return result

    #@classmethod
    @staticmethod
    def read_did_fd35_pressure_sensor(can_p: CanParam, dsession=b'', stepno=222):
        """
        Read DID FD35: pressure sensor

        return:
        result: True/False
        pressure: pressure value as int
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xFD\x35', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Read Pressure Sensor FD35",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUTE.teststep(can_p, cpay, etp)
        pressure = 0
        if not len(SC.can_messages[can_p["receive"]]) == 0 and\
           SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='0662FD35'):
            #position 6-9: 2bytes for pressure value (uint)
            press = SC.can_messages[can_p["receive"]][0][2][6:10]
            pressure = int(press, 16)
            logging.info('Read Pressure Sensor (raw): 0x%s', press)
            logging.info('Read Pressure Sensor (kPa): %s', pressure)
        else:
            logging.info("Could not read pressure sensor (DID FD35)")

        #time.sleep(1)
        return result, pressure

    #@classmethod
    @staticmethod
    def read_did_4a28_pressure_sensor(can_p: CanParam, dsession=b'', stepno=223):
        """
        Read DID 4A28: pressure sensor

        return:
        result: True/False
        pressure: pressure value as int
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\x4A\x28', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Read Pressure Sensor 4A28",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUTE.teststep(can_p, cpay, etp)
        pressure = 0
        if not len(SC.can_messages[can_p["receive"]]) == 0 and\
            SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='07624A28'):
            #position 26 bits for pressure value, temperature and flags
            raw4a28 = SC.can_messages[can_p["receive"]][0][2][6:14]
            #position 12 bits for pressure value (uint)
            pressure = int(raw4a28[0:4], 16)
            logging.info('Read 4A28 return value (raw): 0x%s', raw4a28)
            logging.info('Read Pressure Sensor (kPa): %s', pressure)
        else:
            logging.info("Could not read pressure sensor (DID 4A28)")

        #time.sleep(1)
        return result, pressure

    #@classmethod
    @staticmethod
    def read_did_eda0_mep2(can_p: CanParam, stepno=220):
        """
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }

        result = SUTE.teststep(can_p, cpay, etp)
        if not len(SC.can_messages[can_p["receive"]]) == 0:
            logging.info('%s',\
                         SUTE.pp_combined_did_eda0_mep2(SC.can_messages[can_p["receive"]][0][2],\
                                                    title='')
                        )
        else:
            logging.info('%s', "No messages received for request Read DID EDA0")
            logging.info("Frames received: %s", SC.can_frames[can_p["receive"]])
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            result = False
        return result
