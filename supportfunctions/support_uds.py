"""
Unified diagnostic services (ISO-14229-1)
"""

import re
import logging

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra

SUTE = SupportTestODTB2()
SC = SupportCAN()

global_timestamp_dd00 = bytes.fromhex('DD00')

# maybe move this to a different file since it's volvo specific
complete_ecu_part_number_eda0 = bytes.fromhex('EDA0')
ecu_software_structure_part_number_f12c = bytes.fromhex('F12C')
software_part_number_f12e = bytes.fromhex('F12E')

class UdsEmptyResponse(Exception):
    """ Exception class to indicate that that response was empty """

class UdsResponse:
    """ UDS response """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, raw):
        self.raw = raw
        self.__process_message()

    def __process_message(self):
        service_types = {
            "59": "ReadDTCInformation",
            "62": "ReadDataByIdentifier",
            "6F": "InputOutputControlByIdentifier",
            "71": "RoutineControl",
        }

        pattern = re.compile(r'.{4}(?P<sid>.{2})(?P<did>.{4})(?P<content>.*)')
        match = pattern.match(self.raw)
        if not match:
            raise LookupError("Unrecognizable response format")

        g = match.groupdict()
        self.sid = g["sid"]
        if not self.sid in service_types:
            raise LookupError("Unknown service type in response")

        self.service = service_types[self.sid]
        self.did = g["did"]
        self.content = g["content"]

        # execute did specific handler if it's defined
        for did_method in dir(self):
            if did_method.endswith(self.did.lower()):
                getattr(self, did_method)()

    def empty(self):
        """ Check if the response is empty """
        return len(self.raw) == 0

    def __str__(self):
        s = f"{self.__class__.__name__}:\n"
        s = s + f"  raw = {self.raw}\n"
        s = s + f"  sid = {self.sid}\n"
        s = s + f"  service = {self.service}\n"
        s = s + f"  did = {self.did}\n"
        s = s + f"  content = {self.content}\n"
        if hasattr(self, "match"):
            s = s + f"  match = {self.match} \n"

        # TODO: this should be made general
        if hasattr(self, "ecu_sw_struct_part_num"):
            s = s + "  ecu_sw_struct_part_num = " + \
                f"{self.ecu_sw_struct_part_num} "
        return s

    def __ecu_software_structure_part_number_f12c(self):
        self.ecu_sw_struct_part_num = \
            SupportTestODTB2.pp_partnumber(self.content)

    def __complete_ecu_part_number_eda0(self):
        r = ''.join([
            r'F120(?P<app_diag_part_num>.{14})'
            r'F12A(?P<ecu_core_assembly_part_num>.{14})'
            r'F12B(?P<ecu_delivery_assembly_part_num>.{14})'
            r'F12E(?P<software_part_nums>.{72})'
        ])
        pattern = re.compile(r)
        match = pattern.match(self.content)
        if not match:
            raise LookupError("Unrecognizable response format")
        self.match = match.groupdict()
        self.ecu_sw_struct_part_num = \
            SupportTestODTB2.pp_partnumber(
                re.search(r'(.{14})$',
                          self.match['software_part_nums']).group())


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

        return UdsResponse(response[0][2])


    def dtc_snapshot(self, dtc_number: bytes, mask: bytes):
        """ Report DTC Snapshot Record By DTC Number """
        payload = b'\x19\x04' + dtc_number + mask
        payload = bytes([0x19, 0x04]) + dtc_number + mask
        return self.__make_call(payload)


    def read_data_by_id_22(self, did: bytes, mask: bytes = b''):
        """ Read Data by Identifier """
        payload = b'\x22' + did + mask
        return self.__make_call(payload)


    def set_mode(self, mode=1):
        """ Read Data by Identifier """
        modes = {
            1: "default session/mode",
            2: "programming session/mode",
            3: "extended session/mode"
        }
        assert mode in modes.keys()
        payload = bytes([0x10, mode])
        logging.info(
            "Set %s with payload %s", modes[mode], payload.hex())
        try:
            self.__make_call(payload)
        except UdsEmptyResponse:
            # set mode calls does not give us any response, so this is fine
            pass


##################################
# Pytest unit tests starts here
##################################

def test_uds_response():
    """ pytest: UdsResponse """
    f12c_response = "100A62F12C32263666204141"
    response = UdsResponse(f12c_response)
    assert response.ecu_sw_struct_part_num == "32263666 AA"
    eda0 = "104A62EDA0F12032299361204142F12A32290749202020F12BFFFFFFFFFFFFFF" + \
    "F12E053229942520414532299427204143322994292041453229943020414132263666204141" + \
    "F18C30400011"
    response = UdsResponse(eda0)
    assert response.ecu_sw_struct_part_num == "32263666 AA"
