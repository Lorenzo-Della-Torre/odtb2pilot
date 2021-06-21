"""
Unified diagnostic services (ISO-14229-1)
"""

import re
import sys
import time
import logging
import textwrap
from dataclasses import dataclass

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra
from supportfunctions.support_SBL import SupportSBL

from hilding.status_bits import DtcStatus
from hilding import get_conf

SC = SupportCAN()

log = logging.getLogger('uds')

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
    sbl_software_part_num_f124 = bytes.fromhex('F124')
    pbl_software_part_num_f125 = bytes.fromhex('F125')
    ecu_core_assembly_part_num_f12a = bytes.fromhex('F12A')
    ecu_delivery_assembly_part_num_f12b = bytes.fromhex('F12B')
    ecu_software_structure_part_number_f12c = bytes.fromhex('F12C')
    ecu_software_part_number_f12e = bytes.fromhex('F12E')

@dataclass
class IoSssDid:
    """
    Identification Options-System Supplier Specific

    F1F0-F1FF
    """
    git_hash_f1f2 = bytes.fromhex('F1F2')

class UdsEmptyResponse(Exception):
    """ Exception class to indicate that that response was empty """

class UdsError(Exception):
    """ General exception class for Uds """

class UdsResponse:
    """ UDS response """
    def __init__(self, raw, mode=None):
        self.raw = raw
        self.mode = mode
        self.data = {}
        self.data['details'] = {}
        self.all_defined_dids = {}
        self.__did_regex = {}
        self.__sddb_dids = get_conf().rig.sddb_dids
        self.__sddb_dtcs = get_conf().rig.sddb_dtcs.get("sddb_dtcs")
        self.__process_message()


    def __process_message(self):

        response_patterns = [
            (r'.{2}7F(?P<service_id>.{2})(?P<nrc>.{2})',
             self.__negative_response),
            (r'.{2,4}(?P<sid>50|51|59|62|6F|71)(?P<body>.*)',
             self.__positive_response)
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
        self.all_defined_dids = {}
        if not self.mode:
            self.all_defined_dids.update(self.__sddb_dids["app_did_dict"])
            self.all_defined_dids.update(self.__sddb_dids["pbl_did_dict"])
            self.all_defined_dids.update(self.__sddb_dids["sbl_did_dict"])
        elif self.mode in [1, 3]:
            self.all_defined_dids.update(self.__sddb_dids["app_did_dict"])
        elif self.mode == 2:
            # it would be good to separate these two and we can do that if we
            # add a state to the class indicating which programming mode it's
            # in.
            self.all_defined_dids.update(self.__sddb_dids["pbl_did_dict"])
            self.all_defined_dids.update(self.__sddb_dids["sbl_did_dict"])
        else:
            sys.exit(f"Incorrect mode set: {self.mode}. Exiting...")

        for did, item in self.all_defined_dids.items():
            # each byte takes two hexadecimal characters
            length = int(item['size']) * 2
            # For F120 with a length of 14 the resulting regex should be
            # r'F120(.{14})' in the raw string below. The first replacement is
            # trivial, but the second one requires some explanation. Python
            # `format` will consume any curly braces pairs, but we want to have
            # {14} in the resulting string there is a way around that. By
            # doubling the curly braces `format` will then not do any variable
            # replacement and will add a single curly brace in the output
            # instead which is what we want.
            # see:
            # https://docs.python.org/3/library/string.html#format-string-syntax
            # for more details
            self.__did_regex[did] = r'{}(.{{{}}})'.format(did, length)

        service_types = {
            "50": "DiagnosticSessionControl",
            "51": "ECUReset",
            "59": "ReadDTCInformation",
            "62": "ReadDataByIdentifier",
            "6F": "InputOutputControlByIdentifier",
            "71": "RoutineControl",
        }
        sid = self.data["sid"]
        if sid in service_types:
            service = service_types[sid]
            self.data["service"] = service

            if service == "DiagnosticSessionControl":
                self.__mode_change()
            if service == "ReadDataByIdentifier":
                self.__process_dids()
            if service == "ReadDTCInformation":
                self.__process_dtc_report()

    def __mode_change(self):
        mode = self.data["body"][:2]
        self.details['mode'] = int(mode)

    def __process_dids(self):
        did = self.data["body"][0:4]
        item = self.data["body"][4:]
        info = self.all_defined_dids[did]
        self.data['did'] = did
        self.details.update(info)
        self.details['item'] = item
        self.validate_part_num(did, item)
        self.add_response_items(did, item)

        # execute did specific handler if it's defined
        for did_method in dir(self):
            if did_method.endswith(self.data["did"].lower()):
                getattr(self, did_method)()

    def __process_dtc_report(self):
        report_type = self.data["body"][0:2]
        content = self.data["body"][2:]

        if report_type == '02':
            self.__process_dtc_by_status_mask(content)
        elif report_type == '03':
            self.__process_dtc_snapshot_ids(content)
        elif report_type == '04':
            self.__process_dtc_snapshot(content)
        elif report_type == '06':
            self.__process_dtc_extended_data_records(content)
        else:
            log.warning("dtc report type not supported by UdsResponse")

    def __process_dtc_by_status_mask(self, content):
        dtc_status_list_match = re.match(
            r'(?P<dtc_status_availability_mask>.{2})(?P<dtc_status_list>.*)$',
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
                    dtc_list.append((status_group["dtc"], bits))
                    self.data['dtcs'] = dtc_list
                    self.data['count'] = len(dtc_list)

    def __process_dtc_snapshot_ids(self, content):
        """ process list of dtc and snapshot ids """
        snapshot_ids = []
        pattern = re.compile(r'(?P<dtc>.{6})(?P<snapshot_id>.{2})')
        for record in textwrap.wrap(content, width=8):
            match = pattern.match(record)
            if match:
                group = match.groupdict()
                snapshot_ids.append((group["snapshot_id"], group["dtc"]))
        self.data['snapshot_ids'] = snapshot_ids
        self.data['count'] = len(snapshot_ids)

    def __process_dtc_snapshot(self, content):
        match = re.match(
            r'(?P<dtc>.{6})(?P<dtc_status_bits>.{2})(?P<snapshot>.*)$', content)
        if match:
            dtc = match.groupdict()["dtc"]
            self.data['dtc'] = dtc
            if dtc in self.__sddb_dtcs:
                self.details.update(self.__sddb_dtcs[dtc])
            self.data["dtc_status_bits"] = DtcStatus(
                match.groupdict()["dtc_status_bits"])

    def __process_dtc_extended_data_records(self, content):
        match = re.match(
            r'(?P<dtc>.{6})(?P<dtc_status_bits>.{2})(?P<ext_records>.*)$',
            content)

        if match:
            # self.data.update(match.groupdict())
            group = match.groupdict()
            dtc = group["dtc"]
            self.data['dtc'] = dtc
            if dtc in self.__sddb_dtcs:
                self.details.update(self.__sddb_dtcs[dtc])

            self.data["dtc_status_bits"] = DtcStatus(
                group["dtc_status_bits"])

            regex_fields = [
                '.*?(01)(?P<occ1>..)',
                '.*?(02)(?P<occ2>..)',
                '.*?(03)(?P<occ3>..)',
                '.*?(04)(?P<occ4>..)',
                '.*?(05)(?P<occ5>..)',
                '.*?(06)(?P<occ6>..)',
                '.*?(10)(?P<fdc10>..)',
                '.*?(20)(?P<ts20>.{8})',
                '.*?(21)(?P<ts21>.{8})',
                '.*?(30)(?P<si30>..)'
            ]
            fields = extract_fields(group["ext_records"], regex_fields)
            if "si30" in fields:
                fields["si30_bits"] = "{:08b}".format(int(fields["si30"], 16))
                fields["si30_decimal_bits"] = "{:08b}".format(int(fields["si30"], 10))
            self.data.update(fields)

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
                self.details[did+'_info'] = info
                self.validate_part_num(did, item)
                self.add_response_items(did, item)


    def validate_part_num(self, did, item):
        """ validate part number and add convert it to text format """
        if did in ['F120', 'F121', 'F122', 'F124', 'F125', 'F12A', 'F12B',
                   'F12C', 'F12E']:
            if SupportTestODTB2.validate_part_number_record(item):
                self.details[did+'_valid'] = \
                    SupportTestODTB2.pp_partnumber(item)

    def add_response_items(self, did, payload):
        """ add response items """
        if did in self.__sddb_dids["resp_item_dict"]:
            resp_item_dict = self.__sddb_dids["resp_item_dict"]
            response_items = []
            for resp_item in resp_item_dict[did]:
                offset = resp_item['offset']
                size = resp_item['size']
                sub_payload = get_sub_payload(payload, offset, size)
                scaled_value = get_scaled_value(resp_item, sub_payload)
                if 'compare_value' in resp_item:
                    compare_value = resp_item['compare_value']
                    if compare(scaled_value, compare_value):
                        log.debug('Equal! Comparing %s with %s', str(compare_value),
                                      scaled_value)
                    continue


                resp_item['sub_payload'] = sub_payload
                resp_item['scaled_value'] = scaled_value

                response_items.append(resp_item)

            self.details['response_items'] = response_items


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
            log.error('No F12E part numbers found')
            return

        remaining = self.details['F12E']

        # each part number is 7 bytes and each byte is represented as two
        # hexadecimal characters
        part_num_len = 7 * 2

        records = int(remaining[0:2])
        self.details['F12E_info']['records'] = records
        remaining = remaining[2:]

        if not records * part_num_len == len(remaining):
            log.warning(
                "Record length of F12E in EDA0 appears incorrect in SDDB file")
            # attempting to recover by ignoreing SDDB record for F12E
            # `format` will replace the two outer most curly braces with a single
            # curly braces pair (i.e. F12E\d\d(.{length}))
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


    def __active_diag_session_f186(self):
        details = self.data['details']
        item = details['item']
        length = int(details['size']) * 2
        if len(item) >= length:
            self.details['mode'] = int(item[:length])


class Uds:
    """ Unified diagnostic services """
    def __init__(self, dut):
        self.dut = dut
        self.step = 0
        self.purpose = ""
        self.mode = None

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
        log.info("Request with payload: %s", payload.hex())
        SupportTestODTB2().teststep(self.dut, cpay, etp)

        response = SC.can_messages[self.dut['receive']]

        if len(response) == 0:
            raise UdsEmptyResponse()

        return UdsResponse(response[0][2], self.mode)


    def ecu_reset_1101(self, delay=1):
        """ Reset the ECU """
        payload = bytes([0x11, 0x01])
        reply =  self.__make_call(payload)
        time.sleep(delay)
        return reply

    def ecu_reset_noreply_1181(self, delay=1):
        """ Reset the ECU with no reply """
        payload = bytes([0x11, 0x81])
        reply =  self.__make_call(payload)
        time.sleep(delay)
        return reply

    def dtc_by_status_mask_1902(self, mask: DtcStatus):
        """ Read dtc by status mask """
        payload = bytes([0x19, 0x02]) + mask.bytes
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

    def active_diag_session_f186(self):
        """ Read active diagnostic session/mode """
        return self.read_data_by_id_22(b'\xf1\x86')

    def generic_ecu_call(self, payload: bytes = b''):
        """
        Generic ECU call
        Use the service specific methods if you can instead of this method
        """
        return self.__make_call(payload)

    def milliseconds_since_request(self):
        """
        Elapsed time since last sent frame to first received frame with
        millisecond resolution.
        """
        t_sent = float(SC.can_frames[self.dut['send']][0][0])
        t_received = float(SC.can_frames[self.dut['receive']][0][0])
        return int((t_received - t_sent) * 1000)

    def set_mode(self, mode=1, change_check=True):
        """ Read Data by Identifier """

        if change_check and mode == 3 and self.mode == 2:
            raise UdsError(
                "You can not change directly from mode 2 to mode 3. Use the "
                "mode order 1, 3, 2 if you want to implement at testcase "
                "covering all modes instead")

        modes = {
            1: "default session/mode",
            2: "programming session/mode",
            3: "extended session/mode"
        }
        assert mode in modes.keys()
        payload = bytes([0x10, mode])
        log.info(
            "Set %s with payload %s", modes[mode], payload.hex())

        try:
            res = self.__make_call(payload)
        except UdsEmptyResponse:
            # set mode 1 and 2 calls might not give us any response, so this is
            # fine
            res = None

        if not res or not "mode" in res.details:
            # mode change can take a little while so let's sleep a bit before
            # we request the active diagnostic session number
            time.sleep(2)
            res = self.active_diag_session_f186()
            if not "mode" in res.details:
                raise UdsError(f"Failure occurred when setting mode: {mode}")
        self.mode = res.details["mode"]


    def enter_sbl(self):
        """ enter the secondary bootloader """
        if self.mode != 2:
            UdsError(
                "You need to be in programming mode to change from pbl to sbl")

        sbl = SupportSBL()
        rig = get_conf().rig
        vbf_files = [str(f.resolve()) for f in rig.vbf_path.glob("*.vbf")]
        log.info(vbf_files)
        if not sbl.read_vbf_param(vbf_files):
            UdsError("Could not load vbf files")
        if not sbl.sbl_activation(
            self.dut, fixed_key=rig.fixed_key, stepno=self.dut.step,
                purpose="Activate Secondary bootloader"):
            UdsError("Could not set ecu in sbl mode")


def extract_fields(hexstring, regex_fields: list):
    """
    Match regex_fields against the hexstring, add them to the fields
    dictionary, and remove the record from the original string representation.
    """
    fields = {}
    for regex in regex_fields:
        match = re.match(regex, hexstring)
        if match:
            fields.update(match.groupdict())
            hexstring = hexstring[:match.start(1)] + hexstring[match.end(2):]
    fields["unmatched_data"] = hexstring
    return fields


def get_sub_payload(payload, offset, size):
    """
    Returns the chosen sub part of the payload based on the offset and size
    Payload, offset and size is hexadecimal (16 base)
    Every byte is two characters (multiplying with two)
    """
    start = int(offset, 16)*2
    end = start+(int(size, 16)*2)

    # Making sure the end is inside the payload
    if len(payload) >= end:
        sub_payload = payload[start:end]
    else:
        raise RuntimeError('Payload is to short!')
    return sub_payload


def populate_formula(formula, value, size):
    '''
    Replaces X in a formula with a value.
    Input:  formula = Example: X*1
            value   = Any value
            size    = size of bitmask/payload when it was in hex

    Output: The formula with X replaced.

    If there is "bitwise AND" in the formula;
    - '&amp;' is replaced with '&'.
    - '0x' is removed from the hex value.
    - The bitmask is translated from hex to decimal

    Example 1:  Input:  Formula: X/100
                        Value: 56
                        Size: 1 (doesn't matter in this example)
                Output: 56/100

    Example 2:  Input:  Formula: X&amp;0xFFFE/2
                        Value: 56
                        Size: 2 (doesn't matter in this example)
                Output: (56 & 65534)/2
    '''

    # Check for "Bitwise AND"
    # Removing characters we don't want
    formula = formula.replace('&amp;0x', '&0x')
    and_pos_hex = formula.find('&0x')
    and_pos_bit = formula.find('&0b')

    # It is a bitwise-and HEX
    if and_pos_hex != -1:
        log.debug('Formula = %s and_pos_hex = %s', formula, and_pos_hex)
        hex_value = formula[and_pos_hex + 1:and_pos_hex + 3 + int(size) * 2]
        formula = formula.replace(hex_value, str(int(hex_value, 16)) + ')')
        populated_formula = formula.replace('X', '(' +str(value))
    # It is a bitwise-and bit-mapping
    elif and_pos_bit != -1:
        log.debug('Formula = %s and_pos_bit = %s', formula, and_pos_bit)
        bit_value = bin(value)
        populated_formula = formula.replace('X', '(' +str(bit_value) + ')')
    else:
        log.debug('Value = %s', value)
        populated_formula = formula.replace('X', str(value))
    return populated_formula


def get_scaled_value(resp_item, sub_payload):
    """
    Input - Response Item with at least formula
            Value which should converted from raw data
    Returns the string with converted data
    """
    if 'outdatatype' in resp_item and resp_item['outdatatype'] == '06':
        sub_payload = sub_payload.rstrip("0") # Removing trailing zeros
        utf8_text = bytearray.fromhex(sub_payload).decode() # decode from hex to utf-8
        return utf8_text

    int_value = int(sub_payload, 16)
    if 'formula' in resp_item:
        size = resp_item['size']
        formula = resp_item['formula']
        log.debug('Formula = %s', formula)
        populated_formula = populate_formula(formula, int_value, size)
        log.debug('Populated formula = %s', populated_formula)

        try:
            result = str(eval(populated_formula)) # pylint: disable=eval-used
            int_result = int(float(result))
            log.debug('Formula = %s => %s', formula, result)
            return int_result
        except RuntimeError as runtime_error:
            log.fatal(runtime_error)
        except SyntaxError as syntax_error:
            log.fatal(syntax_error)
        except OverflowError as overflow_error:
            log.fatal(overflow_error)
    else:
        # If we reach this, then there is no formula.
        # That is an issue, formula should be mandatory
        log.fatal('No formula!')
        log.fatal(resp_item)
        log.fatal(sub_payload)
        raise RuntimeError('No formula!')
    return int_value


def compare(scaled_value, compare_value):
    """
    Comparing two values. Returns boolean.
    If the compare value contains '=', then we add an '='
    Example:    Scaled value:    0x40
                Compare value:  =0x40
                Result: eval('0x40==0x40') which gives True
    """
    improved_compare_value = compare_value
    result = False # If not True, then default is False
    # To be able to compare we need to change '=' to '=='
    if '=' in compare_value:
        improved_compare_value = compare_value.replace('=', '==')
    try:
        # pylint: disable=eval-used
        result = eval(str(scaled_value) + str(improved_compare_value))
    except NameError as name_error:
        log.error(name_error)
    except SyntaxError as syntax_error:
        log.error(syntax_error)
    return result
