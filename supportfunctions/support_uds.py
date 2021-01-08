"""
Unified diagnostic services (ISO-14229-1)
"""

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra

SUTE = SupportTestODTB2()
SC = SupportCAN()

global_timestamp = b'\xDD\x00'

class UdsEmptyResponse(Exception):
    """ Exception class to indicate that that response was emtpy """

class Uds:
    """ Unified diagnostic services """
    def __init__(self, dut):
        self.dut = dut

    def __make_call(self, payload):
        cpay: CanPayload = {
            "payload": payload,
            "extra": ''
        }
        etp: CanTestExtra = {
            "step_no": 1,
            "purpose": "purpose",
            "timeout": 1,
            "min_no_messages": -1,
            "max_no_messages": -1
        }
        SUTE.teststep(self.dut, cpay, etp)

        response = SC.can_messages[self.dut['receive']]

        if len(response) == 0:
            raise UdsEmptyResponse()

        return response[0][2]


    def dtc_snapshot(self, dtc_number: bytes, mask: bytes):
        """ Report DTC Snapshot Record By DTC Number """
        payload = b'\x19\x04' + dtc_number + mask
        return self.__make_call(payload)


    def read_data_by_identifier(self, did: bytes, mask: bytes = b''):
        """ Read Data by Identifier """
        payload = b'\x22' + did + mask
        return self.__make_call(payload)
