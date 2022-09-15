"""
Unified diagnostic services (ISO-14229-1)
Response handling

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
import re
import sys
import logging
import textwrap
import string

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from hilding.status_bits import DtcStatus
from hilding import get_conf

log = logging.getLogger('uds_response')

class UdsResponse:
    """ UDS response, this is a class that handles one response
    """
    def __init__(self, raw, incoming_mode=None):
        self.raw = raw
        self.incoming_mode = incoming_mode
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
            (r'.{2,4}(?P<sid>50|51|59|62|63|6F|71|67|74|76|75|77|54)(?P<body>.*)',
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
        if not self.incoming_mode:
            self.all_defined_dids.update(self.__sddb_dids["app_did_dict"])
            self.all_defined_dids.update(self.__sddb_dids["pbl_did_dict"])
            self.all_defined_dids.update(self.__sddb_dids["sbl_did_dict"])
        elif self.incoming_mode in [1, 3]:
            self.all_defined_dids.update(self.__sddb_dids["app_did_dict"])
        elif self.incoming_mode == 2:
            # it would be good to separate these two and we can do that if we
            # add a state to the class indicating which programming mode it's
            # in.
            self.all_defined_dids.update(self.__sddb_dids["pbl_did_dict"])
            self.all_defined_dids.update(self.__sddb_dids["sbl_did_dict"])
        else:
            sys.exit(f"Incorrect incoming_mode set: {self.incoming_mode}. "
                     f"Exiting...")

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
        self.details['session_parameter_record'] = self.data["body"][2:]

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
        """Convenience property for getting response details

        Returns:
            dict: Dictionary containing details
        """
        return self.data["details"]

    def extract_from_did(self,attribute,get_data=True):
        """[This method extracts information about an attribute within a did.

        Ex. If info about "TotalNumberOfReportedEvents" is requested supply
        attribute name. A dictionary containing the info will
        be returned.

        If get_data is True the returned dictionary will contain the information]

        Args:
            attribute ([string]): [Name of requested attribute]
            get_data (bool, optional): [If True the data belonging to the attribute will be\
            returned]. Defaults to True.

        Returns:
            [return_dictionary]: [Dictionary containing size and offset. If get_data is true
            and data related to the attribute could be retrieved this will also be included
            in the dictionary with key "data". If get_data is False dict["data"] will be None]
        """
        if "did" in self.data:
            if self.data["did"] in self.__sddb_dids["resp_item_dict"]:
                did_info = self.__sddb_dids["resp_item_dict"][self.data["did"]]
            else:
                logging.error("Did not in sddb dictionary, make sure it is implemented and that the\
 sddb dictionary is updated")
                return {}
        else:
            logging.error("The response from the ECU does not have the correct format,\
 make sure it is implemented in the ECU SW")
            return {}

        for ent in did_info:
            if ent["name"].lower() == attribute.lower():
                offset = ent["offset"]
                size = ent["size"]
                return_dictionary = {"offset" : offset,
                                "size" : size}
                if get_data is True:
                    item = self.details["item"]
                    attribute_data = item[int(offset, base=16)*2:\
                        int(offset, base=16)*2+int(size, base=16)*2]
                    return_dictionary["data"] = attribute_data
                else:
                    return_dictionary["data"] = None

                return return_dictionary
        logging.error("The attribute %s could not be found for the did %s",
        attribute,
        self.data["did"])
        return {}

    def empty(self):
        """Check if the response is empty

        Returns:
            boolean: True if raw is empty, otherwise False
        """
        return len(self.raw) == 0


    def extract_dids(self, content):
        """Find all the defined DIDs in the content

        Args:
            content (content): Content to search through
        """
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
        """Validate part number and add convert it to test format

        Args:
            did (string): [description]
            item (string): [description]
        """
        if did in ['F120', 'F121', 'F122', 'F124', 'F125', 'F12A', 'F12B',
                   'F12C', 'F12E']:

            # F12E contains more than one part number and therefore must be divided
            items = []
            if did == "F12E":
                number_of_part_numbers = int(item[0:2]) # Defined in the SWRS
                item = item[2:] # Since the first two chars are
                                # "Total number of ECU Software Part Numbers"

                # Used to extract size of part number from sddb. Letters and _ use one byte,
                # digits use one. Note: One byte = 2 hex chars
                part_number = self.__sddb_dids["pbl_diag_part_num"]
                part_number_size = 0
                for char in part_number:
                    if char in string.ascii_uppercase + "_":
                        part_number_size += 2
                    if char in string.digits:
                        part_number_size += 1

                for i in range(number_of_part_numbers):
                    items.append(item[i*part_number_size:part_number_size+i*part_number_size])
            else:
                items.append(item)

            for itm in items:
                if SupportTestODTB2.validate_part_number_record(itm):
                    self.details[did+'_valid'] = \
                        SupportTestODTB2.pp_partnumber(itm)
                else:
                    did_name = ""
                    if did in self.__sddb_dids['app_did_dict']:
                        did_name = self.__sddb_dids['app_did_dict'][did]['name']
                    logging.info("^^^^^^^^^ The previous line is related to DID %s (%s) ^^^^^^^^",
                        did,
                        did_name)

    def add_response_items(self, did, payload):
        """Add response items

        This methods extracts all attributes in the sddb from the can response to
        details['response_items']

        Args:
            did (string): DID to find response items for
            payload ([type]): Can payload
        """
        if did in self.__sddb_dids["resp_item_dict"]:
            resp_item_dict = self.__sddb_dids["resp_item_dict"]
            response_items = []
            unscaleable_values = str()
            if resp_item_dict[did]:
                # Used to find entries with containing compare values that are only False.
                # (See the explanation below for more info)
                compare_variables = {'previous_resp_item_name' : resp_item_dict[did][0]['name'],
                        'previous_resp_item_value' : False,
                        'previous_compare_value' : resp_item_dict[did][0].get('compare_value')}

            for resp_item in resp_item_dict[did]:
                offset = resp_item['offset']
                size = resp_item['size']
                formula = resp_item.get('formula', '')
                sub_payload = get_sub_payload(payload, offset, size)
                scaled_value = 0
                try:
                    scaled_value = get_scaled_value(resp_item, sub_payload)
                except ValueError:
                    unscaleable_values += '\n' + resp_item.get('name')
                    if sub_payload == '':
                        unscaleable_values += " - because payload is to short"

                if 'compare_value' in resp_item:
                    compare_result = compare(scaled_value, resp_item['compare_value'])

                    # Used to keep track of entries where everything is False.
                    # Ex: If
                    # Voltage Sense 1                         |   Disable = False
                    # Voltage Sense 1                         |   Module = False
                    # Voltage Sense 1                         |   Busbar = False
                    # the the following will be added to response_items for Voltage Sense 1:
                    # Voltage Sense 1                         |   False

                    if resp_item['name'] != compare_variables['previous_resp_item_name']:
                        if compare_variables['previous_resp_item_value'] is False and\
                                compare_variables['previous_compare_value'] is not None:
                            item = {}
                            item['name'] = compare_variables['previous_resp_item_name']
                            item['scaled_value'] = "False"
                            response_items.append(item)

                        compare_variables['previous_resp_item_value'] = False

                    if compare_result:
                        item = {}
                        item['name'] = resp_item.get('name', '')
                        item['scaled_value'] = resp_item.get('unit', '')
                        response_items.append(item)

                        compare_variables['previous_resp_item_value'] = True

                    compare_variables['previous_resp_item_name'] = resp_item['name']

                    continue

                item = {k: v for k, v in resp_item.items() if k in
                        ['name', 'software_label', 'unit']}
                item['sub_payload'] = sub_payload
                item['scaled_value'] = scaled_value
                item['formula'] = formula

                response_items.append(item)

            if unscaleable_values:
                log.error("The following response items could not be extracted\
                    \nfrom the payload received from the ECU: %s", unscaleable_values)

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

        logging.debug("Part nums: %s", part_nums)

        # validate the part numbers. This is also done in self.extract_dids()...
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


def extract_fields(hexstring, regex_fields: list):
    """Match regex_fields against the hexstring, add them to the fields
    dictionary, and remove the record from the original string representation.

    Args:
        hexstring ([type]): [description]
        regex_fields (list): [description]

    Returns:
        dict: [description]
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
    """Returns the chosen sub part of the payload based on the offset and size
    Payload, offset and size is hexadecimal (16 base)
    Every byte is two characters (multiplying with two)

    Args:
        payload ([type]): Can payload
        offset ([type]): Attributes offset
        size ([type]): Attribute size

    Returns:
        [type]: Part of payload that was extracted using offset and size
    """
    start = int(offset, 16)*2
    end = start+(int(size, 16)*2)

    # Making sure the end is inside the payload
    if len(payload) >= end:
        sub_payload = payload[start:end]
    else:
        end = start + len(payload)
        sub_payload = payload[start:end]

    log.debug('----------------')
    log.debug('payload: %s', payload)
    log.debug('payload len: %s', len(payload))
    log.debug('offset: %s', offset)
    log.debug('size: %s', size)
    log.debug('start: %s', start)
    log.debug('end: %s', end)
    log.debug('sub_payload: %s', sub_payload)
    log.debug('----------------')
    return sub_payload


def populate_formula(formula, value, size):
    """Replaces X in a formula with a value.
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

    Args:
        formula ([type]): The formula that is to be used. Usually found in sddb
        value ([type]): Value that is used as input to formula
        size ([type]): [description]

    Returns:
        [type]: Whatever is calculated using the formula
    """

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
    """ Input - Response Item with at least formula
            Value which should converted from raw data
    Returns the string with converted data

    Args:
        resp_item ([type]): An entry from response_items
        sub_payload ([type]): Part of can payload

    Raises:
        RuntimeError: Raised if formula is not found

    Returns:
        string: String containing converted data
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
    """Comparing two values. Returns boolean.
    If the compare value contains '=' and if condition is not >= or <=, then we add an '='
    Example:    Scaled value:    0x40
                Compare value:  =0x40
                Result: eval('0x40==0x40') which gives True

    Args:
        scaled_value ([type]): [description]
        compare_value ([type]): [description]

    Returns:
        boolean: Result from the comparison between the two inputs
    """
    improved_compare_value = compare_value
    result = False # If not True, then default is False
    # To be able to compare we need to change '=' to '==', if condition is not >= or <=
    if '=' in compare_value and ">" not in compare_value and "<" not in compare_value:
        improved_compare_value = compare_value.replace('=', '==')
    try:
        # pylint: disable=eval-used
        result = eval(str(scaled_value) + str(improved_compare_value))
    except NameError as name_error:
        log.error(name_error)
    except SyntaxError as syntax_error:
        log.error(syntax_error)
    return result
