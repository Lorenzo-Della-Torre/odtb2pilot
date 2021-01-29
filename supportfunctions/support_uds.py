"""
Unified diagnostic services (ISO-14229-1)
"""

import re
import logging
import textwrap
from dataclasses import dataclass

from build.did import pbl_did_dict
from build.did import sbl_did_dict
from build.did import app_did_dict

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra


SUTE = SupportTestODTB2()
SC = SupportCAN()


global_timestamp_dd00 = bytes.fromhex('DD00')

# maybe move this to a different file since it's volvo specific
@dataclass
class VccDid:
    """
    Identification Option - Vehicle Manufacturer Specific

    F100-F17F, F1A0-F1EF
    """
    # pylint: disable=too-many-instance-attributes,invalid-name
    complete_ecu_part_number_eda0 = bytes.fromhex('EDA0')
    app_diag_part_num_f120 = bytes.fromhex('F120')
    pbl_diag_part_num_f121 = bytes.fromhex('F121')
    sbl_diag_part_num_f122 = bytes.fromhex('F122')
    pbl_software_part_num_f125 = bytes.fromhex('F125')
    ecu_core_assembly_part_num_f12a = bytes.fromhex('F12A')
    ecu_delivery_assembly_part_num_f12b = bytes.fromhex('F12B')
    ecu_software_structure_part_number_f12c = bytes.fromhex('F12C')
    ecu_software_part_number_f12e = bytes.fromhex('F12E')

class UdsEmptyResponse(Exception):
    """ Exception class to indicate that that response was empty """

class UdsResponse:
    """ UDS response """
    def __init__(self, raw):
        self.raw = raw
        self.data = {}
        self.__did_regex = {}
        self.__process_message()

    def __process_message(self):
        service_types = {
            "59": "ReadDTCInformation",
            "62": "ReadDataByIdentifier",
            "6F": "InputOutputControlByIdentifier",
            "71": "RoutineControl",
        }

        pattern = r'.{2,4}(?P<sid>59|62|6F|71)(?P<body>.*)'
        match = re.match(pattern, self.raw)
        if not match:
            raise LookupError("Unrecognizable response format")

        self.data = match.groupdict()

        self.sid = self.data["sid"]
        if self.sid in service_types:
            self.service = service_types[self.sid]

        # actually, this is not a good idea since we have to use different
        # definitions depending on the mode of the ecu, but let's att that
        # functionality when we need it
        self.all_defined_dids = get_all_dids()
        for did, item in self.all_defined_dids.items():
            # each byte takes two hexadecimal characters
            length = int(item['sddb_size']) * 2
            self.__did_regex[did] = r'{}(.{{{}}})'.format(did, length)


        did = self.data["body"][0:4]
        item = self.data["body"][4:]
        info = self.all_defined_dids[did]
        self.data['did'] = did
        self.data['details'] = {}
        self.data['details'].update(info)
        self.data['details']['item'] = item
        self.validate_part_num(did, item)

        # execute did specific handler if it's defined
        for did_method in dir(self):
            if did_method.endswith(self.data["did"].lower()):
                getattr(self, did_method)()

    def empty(self):
        """ Check if the response is empty """
        return len(self.raw) == 0


    def extract_dids(self, content):
        """ find all the defined dids in the content """
        for did, regex in self.__did_regex.items():
            match = re.search(regex, content)
            if match:
                item = match.groups()[0]
                info = self.all_defined_dids[did]
                self.data['details'][did] = item
                self.data['details'][did+'_info'] = info
                self.validate_part_num(did, item)


    def validate_part_num(self, did, item):
        """ validate part number and add convert it to text format """
        if did in ['F120', 'F121', 'F122', 'F125', 'F12A', 'F12B',
                   'F12C', 'F12E']:
            if SupportTestODTB2.validate_part_number_record(item):
                self.data['details'][did+'_valid'] = \
                    SupportTestODTB2.pp_partnumber(item)


    def __str__(self):
        s = (
            f"{self.__class__.__name__}:\n"
            f"  raw = {self.raw}\n"
            f"  service = {self.service} (sid={self.sid})\n"
            f"  data = \n"
        )
        for key, item in self.data.items():
            if isinstance(item, dict):
                s += f"    {key}: \n"
                for k, v in item.items():
                    s += f"      {k}: {v}\n"
            else:
                s += f"    {key}: {item}\n"
        return s


    def __ecu_software_structure_part_number_f12c(self):
        item = self.data['details']['item']
        if SupportTestODTB2.validate_part_number_record(item):
            self.data['details']['valid'] = \
                SupportTestODTB2.pp_partnumber(item)


    def __complete_ecu_part_number_eda0(self):
        self.extract_dids(self.data['details']['item'])
        remaining = self.data['details']['F12E']

        # each part number is 7 bytes and each byte is represented as two
        # hexadecimal characters
        part_num_len = 7 * 2

        records = int(remaining[0:2])
        self.data['details']['F12E_info']['records'] = records
        remaining = remaining[2:]

        if not records * part_num_len == len(remaining):
            logging.warning(
                "Record length of F12E in EDA0 appears incorrect in SDDB file")
            # attempting to recover by ignoreing SDDB record for F12E
            match = re.search(r'F12E\d\d(.{{{}}})'.format(
                records * part_num_len), self.data['body'])
            remaining = match.groups()[0]

        part_nums = textwrap.wrap(remaining, part_num_len)
        self.data['details']['F12E_list'] = part_nums

        # validate the part numbers
        f12e_valid = []
        for pn in part_nums:
            if SupportTestODTB2.validate_part_number_record(pn):
                f12e_valid.append(SupportTestODTB2.pp_partnumber(pn))
            else:
                f12e_valid.append(False)
        self.data['details']['F12E_valid'] = f12e_valid


class Uds:
    """ Unified diagnostic services """
    def __init__(self, dut):
        self.dut = dut
        self.step = 0
        self.purpose = ""

    def __make_call(self, payload):
        cpay: CanPayload = {
            "payload": payload,
            "extra": ''
        }
        etp: CanTestExtra = {
            "step_no": self.step,
            "purpose": self.purpose,
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


def get_all_dids():
    """ collect all dids defined in sddb in one dictionary """
    dids = {}
    for did_dict in [pbl_did_dict, sbl_did_dict, app_did_dict]:
        for key, item in did_dict.items():
            dids[key[2:]] = {"sddb_" + k.lower(): v
                             for k, v in item.items() if k in ['Name', 'Size']}
    return dids


##################################
# Pytest unit tests starts here
##################################

def test_uds_response():
    """ pytest: UdsResponse """
    f12c_response = "100A62F12C32263666204141"
    response = UdsResponse(f12c_response)
    print(response)
    assert response.data['did'] == "F12C"
    assert response.data['details']['valid'] == "32263666 AA"
    eda0 = "104A62EDA0F12032299361204142F12A32290749202020F12BFFFFFFFFFFFFFF" + \
    "F12E053229942520414532299427204143322994292041453229943020414132263666204141" + \
    "F18C30400011"
    response = UdsResponse(eda0)
    print(response)
    assert response.data['details']['F12E_valid'][-1] == "32263666 AA"

def test_did():
    """ pytest: make sure get_all_dids works properly """
    did = get_all_dids()
    assert did['EDA0']['sddb_size'] == '64'
    assert did['EDA0']['sddb_name'] == 'Complete ECU Part/Serial Number(s)'
