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
from build.dtc import dtcs

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra
from supportfunctions.dtc_status import DtcStatus


SUTE = SupportTestODTB2()
SC = SupportCAN()



global_timestamp_dd00 = bytes.fromhex('DD00')

@dataclass
class EicDid:
    """
    ECU Identification and Configuration

    EDA0-EDFF, ED20-ED7F
    """
    complete_ecu_part_number_eda0 = bytes.fromhex('EDA0')

# maybe move this to a different file since it's volvo specific
@dataclass
class IoVmsDid:
    """
    Identification Option - Vehicle Manufacturer Specific

    F100-F17F, F1A0-F1EF
    """
    # pylint: disable=too-many-instance-attributes,invalid-name
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
        self.data['details'] = {}
        self.all_defined_dids = {}
        self.__did_regex = {}
        self.__process_message()

    def __process_message(self):
        # check for negative reply
        response_patterns = [
            (r'.{2}7F(?P<service_id>.{2})(?P<nrc>.{2})', self.__negative_response),
            (r'.{2,4}(?P<sid>59|62|6F|71)(?P<body>.*)', self.__positive_response)
        ]
        for pattern, processor in response_patterns:
            match = re.match(pattern, self.raw)
            if match:
                self.data.update(match.groupdict())
                processor()
                # only one pattern should match so we must stop here
                return
        raise LookupError("Unrecognizable response format")

    def __negative_response(self):
        # we should get these from the sddb file instead
        negative_response_codes = {
            "00": "positiveResponse",
            "10": "generalReject",
            "11": "serviceNotSupported",
            "12": "subFunctionNotSupported",
            "13": "incorrectMessageLengthOrInvalidFormat",
            "14": "responseTooLong",
            "21": "busyRepeatRequest",
            "22": "conditionsNotCorrect",
            "24": "requestSequenceError",
            "25": "noResponseFromSubnetComponent",
            "26": "failurePreventsExecutionOfRequestedAction",
            "31": "requestOutOfRange",
            "33": "securityAccessDenied",
            "35": "invalidKey",
            "36": "exceedNumberOfAttempts",
            "37": "requiredTimeDelayNotExpired",
            "70": "uploadDownloadNotAccepted",
            "71": "transferDataSuspended",
            "72": "generalProgrammingFailure",
            "73": "wrongBlockSequenceCounter",
            "78": "requestCorrectlyReceived-ResponsePending",
            "7E": "subFunctionNotSupportedInActiveSession",
            "7F": "serviceNotSupportedInActiveSession",
            "81": "rpmTooHigh",
            "82": "rpmTooLow",
            "83": "engineIsRunning",
            "84": "engineIsNotRunning",
            "85": "engineRunTimeTooLow",
            "86": "temperatureTooHigh",
            "87": "temperatureTooLow",
            "88": "vehicleSpeedTooHigh",
            "89": "vehicleSpeedTooLow",
            "8A": "throttle/PedalTooHigh",
            "8B": "throttle/PedalTooLow",
            "8C": "transmissionRangeInNeutral",
            "8D": "transmissionRangeInGear",
            "8F": "brakeSwitch(es)NotClosed (Brake Pedal not pressed or not applied)",
            "90": "shifterLeverNotInPark",
            "91": "torqueConverterClutchLocked",
            "92": "voltageTooHigh",
            "93": "voltageTooLow"
        }
        nrc = self.data["nrc"]
        if nrc in negative_response_codes:
            self.data["nrc_name"] = negative_response_codes[nrc]

    def __positive_response(self):
        # actually, this is not a good idea since we have to use different
        # definitions depending on the mode of the ecu, but let's add that
        # functionality when we need it
        self.all_defined_dids = get_all_dids()
        for did, item in self.all_defined_dids.items():
            # each byte takes two hexadecimal characters
            length = int(item['sddb_size']) * 2
            self.__did_regex[did] = r'{}(.{{{}}})'.format(did, length)

        service_types = {
            "59": "ReadDTCInformation",
            "62": "ReadDataByIdentifier",
            "6F": "InputOutputControlByIdentifier",
            "71": "RoutineControl",
        }
        sid = self.data["sid"]
        if sid in service_types:
            service = service_types[sid]
            self.data["service"] = service

            if service == "ReadDataByIdentifier":
                self.__process_dids()
            if service == "ReadDTCInformation":
                self.__process_dtc()


    def __process_dids(self):
        did = self.data["body"][0:4]
        item = self.data["body"][4:]
        info = self.all_defined_dids[did]
        self.data['did'] = did
        self.details.update(info)
        self.details['item'] = item
        self.validate_part_num(did, item)

        # execute did specific handler if it's defined
        for did_method in dir(self):
            if did_method.endswith(self.data["did"].lower()):
                getattr(self, did_method)()

    def __process_dtc(self):
        report_type = self.data["body"][0:2]
        content = self.data["body"][2:]

        if report_type == '02':
            dtc_status_list_match = re.match(
                r'(?P<dtc_status_availability_mask>.{2})(?P<dtc_status_list>)$',
                content)
            if dtc_status_list_match:
                list_group = dtc_status_list_match.groupdict()
                dtc_status_bits_pattern = re.compile(
                    r'(?P<dtc>.{6})(?P<dtc_status_bits>.{2})')
                dtc_list = []
                for record in textwrap.wrap(
                        list_group['dtc_status_list'], width=8):
                    dtc_status_match = dtc_status_bits_pattern.match(record)
                    if dtc_status_match:
                        status_group = dtc_status_match.groupdict()
                        bits = DtcStatus(status_group["dtc_status_bits"])
                        dtc_list.append({status_group["dtc"]: bits})
                        self.data['dtcs'] = dtc_list
                        self.data['count'] = len(dtc_list)
            return
        if report_type == '03':
            # process list of dtc and snapshot ids
            snapshot_ids = []
            pattern = re.compile(r'(?P<dtc>.{6})(?P<snapshot_id>.{2})')
            for record in textwrap.wrap(content, width=8):
                match = pattern.match(record)
                if match:
                    group = match.groupdict()
                    snapshot_ids.append({group["snapshot_id"]: group["dtc"]})
            self.data['snapshot_ids'] = snapshot_ids
            self.data['count'] = len(snapshot_ids)
            return
        if report_type == '04':
            match = re.match(r'(?P<dtc>.{6})(?P<dtc_status_bits>.{2})', content)
            if match:
                dtc = match.groupdict()["dtc"]
                self.data['dtc'] = dtc
                if dtc in dtcs:
                    self.details.update(dtcs[dtc])
                self.data["dtc_status_bits"] = DtcStatus(
                    match.groupdict()["dtc_status_bits"])
                return
        if report_type == '06':
            match = re.match(
                r'(?P<dtc>.{6})(?P<dtc_status_bits>.{2})01(?P<occ1>..)' + \
                r'02(?P<occ2>..)03(?P<occ3>..)04(?P<occ4>..)05(?P<occ5>..)' + \
                r'06(?P<occ6>..)07(?P<unknown07>..)10(?P<fdc10>..)' + \
                r'12(?P<unknown12>..)20(?P<ts20>.{8})' + \
                r'21(?P<ts21>.{8})30(?P<si30>..)',
                content)
            if match:
                self.data.update(match.groupdict())
                dtc = match.groupdict()["dtc"]
                self.data['dtc'] = dtc
                if dtc in dtcs:
                    self.details.update(dtcs[dtc])
                self.data["dtc_status_bits"] = DtcStatus(
                    match.groupdict()["dtc_status_bits"])
                return
        logging.warning("dtc report type not supported by UdsResponse")


    @property
    def details(self):
        """ convenience property for getting response details """
        return self.data["details"]


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
                self.details[did] = item
                self.details[did] = item
                self.details[did+'_info'] = info
                self.validate_part_num(did, item)


    def validate_part_num(self, did, item):
        """ validate part number and add convert it to text format """
        if did in ['F120', 'F121', 'F122', 'F125', 'F12A', 'F12B',
                   'F12C', 'F12E']:
            if SupportTestODTB2.validate_part_number_record(item):
                self.details[did+'_valid'] = \
                    SupportTestODTB2.pp_partnumber(item)


    def __str__(self):
        s = (
            f"{self.__class__.__name__}:\n"
            f"  raw = {self.raw}\n"
            f"  data = \n"
        )
        for key, item in self.data.items():
            if isinstance(item, dict):
                s += f"    {key}: \n"
                for k, v in item.items():
                    s += f"      {k}: {v}\n"
            elif isinstance(item, DtcStatus):
                dtc_status_bits = textwrap.indent(str(item), "      ")
                s += f"    {key}: \n{dtc_status_bits}\n"
            else:
                s += f"    {key}: {item}\n"
        return s


    def __ecu_software_structure_part_number_f12c(self):
        item = self.details['item']
        if SupportTestODTB2.validate_part_number_record(item):
            self.details['valid'] = \
                SupportTestODTB2.pp_partnumber(item)


    def __complete_ecu_part_number_eda0(self):
        self.extract_dids(self.details['item'])

        if not 'F12E' in self.details:
            logging.error('No F12E part numbers found')
            return

        remaining = self.details['F12E']

        # each part number is 7 bytes and each byte is represented as two
        # hexadecimal characters
        part_num_len = 7 * 2

        records = int(remaining[0:2])
        self.details['F12E_info']['records'] = records
        remaining = remaining[2:]

        if not records * part_num_len == len(remaining):
            logging.warning(
                "Record length of F12E in EDA0 appears incorrect in SDDB file")
            # attempting to recover by ignoreing SDDB record for F12E
            match = re.search(r'F12E\d\d(.{{{}}})'.format(
                records * part_num_len), self.data['body'])
            remaining = match.groups()[0]

        part_nums = textwrap.wrap(remaining, part_num_len)
        self.details['F12E_list'] = part_nums

        # validate the part numbers
        f12e_valid = []
        for pn in part_nums:
            if SupportTestODTB2.validate_part_number_record(pn):
                f12e_valid.append(SupportTestODTB2.pp_partnumber(pn))
            else:
                f12e_valid.append(False)
        self.details['F12E_valid'] = f12e_valid


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


    def dtc_by_status_mask_1902(self, mask: bytes):
        """ Read dtc by status mask """
        payload = bytes([0x19, 0x02]) + mask
        return self.__make_call(payload)

    def dtc_snapshot_ids_1903(self):
        """ Read snapshot id and DTC pairs currently in the ECU """
        payload = bytes([0x19, 0x03])
        return self.__make_call(payload)

    def dtc_snapshot_1904(self, dtc_number: bytes, record: bytes = b'\xff'):
        """ Report DTC snapshot record by DTC Number """
        payload = bytes([0x19, 0x04]) + dtc_number + record
        return self.__make_call(payload)

    def dtc_extended_1906(self, dtc_number: bytes, record: bytes = b'\xff'):
        """ Report DTC extended data record by DTC number """
        payload = bytes([0x19, 0x06]) + dtc_number + record
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
    assert response.data['did'] == "F12C"
    assert response.data['details']['valid'] == "32263666 AA"
    eda0 = "104A62EDA0F12032299361204142F12A32290749202020F12BFFFFFFFFFFFFFF" + \
    "F12E053229942520414532299427204143322994292041453229943020414132263666204141" + \
    "F18C30400011"
    response = UdsResponse(eda0)
    assert response.data['details']['F12E_valid'][-1] == "32263666 AA"

def test_did():
    """ pytest: make sure get_all_dids works properly """
    did = get_all_dids()
    assert did['EDA0']['sddb_size'] == '64'
    assert did['EDA0']['sddb_name'] == 'Complete ECU Part/Serial Number(s)'

def test_dtc_snapshot():
    """ pytest: test parsing of dtc snapshots """

    dtc_snapshot = \
        "116859040B4A00AF2019DD0000000000DD01000000DD0200DD0A00DD0B000000" + \
        "DD0C004028FFEF25074802000001480300004947000649FA00" + \
        "4A2A00000000000000000000000000000000000000000000000000000000FFFF" + \
        "4B1900000000000000004B1A00000000000000004B1B0000000000000000" + \
        "D02102D9010110D96007D007D007D0DAD00000DB755817E8DB9F2000" + \
        "DBA400040000DBB400000000FFFF000000000000000000000000000000000000" + \
        "F40D00F4463C2119DD0000000000DD01000000DD0200DD0A00DD0B000000" + \
        "DD0C004028FFF2095A4802000001480300004947000049FA0" + \
        "04A2A00000000000000000000000000000000000000000000000000000000FFFF" + \
        "4B1900000000000000004B1A00000000000000004B1B0000000000000000" + \
        "D02102D9010110D96007D007D007D0DAD00000DB75581590DB9F2000" + \
        "DBA400040000DBB400000000FFFF000000000000000000000000000000000000" + \
        "F40D00F4463C"

    res = UdsResponse(dtc_snapshot)
    assert "dtc" in res.data
    assert res.data["dtc"] == "0B4A00"
    assert res.data["sid"] == "59"
    assert res.data["service"] == "ReadDTCInformation"

def test_negative_response():
    """ pytest: test negative responses """
    negative_response = "037F191300000000"
    res = UdsResponse(negative_response)
    assert res.data["nrc"] == "13"
    assert res.data["nrc_name"] == "incorrectMessageLengthOrInvalidFormat"

def test_dtc_snapshot_ids():
    """ pytest: test call for listing dtc snapshot ids from the ECU """
    raw = \
        '105A59030D150021C29A00211C4068201C406821C64A00210C4500210CD800' + \
        '210B3B00200B3B00210B4000200B4000210B4A00200B4A00210B4F00200B4F' + \
        '00210B4500210B5400210B5900210B5E00210B63002150605721D0640021'
    res = UdsResponse(raw)
    assert res.data["sid"] == "59"
    assert res.data["service"] == "ReadDTCInformation"
    assert res.data["count"] == 22
    snapshot_id0 = res.data["snapshot_ids"][0]
    assert '21' in snapshot_id0
    assert snapshot_id0['21'] == '0D1500'

def test_dtc_extended_data_record():
    """ pytest: test parsing of extended data records """
    raw = \
        '102459060B4A00AF01FF020003FF04FF0500060007FF107F127F2000000000' + \
        '21000000003023'
    res = UdsResponse(raw)
    assert res.data["occ1"] == "FF"
    assert res.data["fdc10"] == "7F"
    assert res.data["ts20"] == "00000000"
    assert res.data["ts21"] == "00000000"
    assert res.data["si30"] == "23"
