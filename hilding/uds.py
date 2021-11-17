"""
Unified diagnostic services (ISO-14229-1)
"""

import time
import logging
from dataclasses import dataclass

from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanPayload
from supportfunctions.support_can import CanTestExtra
from supportfunctions.support_SBL import SupportSBL

from hilding.uds_response import UdsResponse
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

        return UdsResponse(response[0][2], incoming_mode=self.mode)


    def ecu_reset_1101(self, delay=1):
        """Reset the ECU

        Args:
            delay (int, optional): Delay just before method returns. Defaults to 1.

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = bytes([0x11, 0x01])
        reply =  self.__make_call(payload)
        time.sleep(delay)
        return reply

    def ecu_reset_noreply_1181(self, delay=1):
        """Reset the ECU with no reply

        Args:
            delay (int, optional): Delay before method returns. Defaults to 1.

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = bytes([0x11, 0x81])
        reply =  self.__make_call(payload)
        time.sleep(delay)
        return reply

    def dtc_by_status_mask_1902(self, mask: DtcStatus):
        """Read DTC by status mask

        Args:
            mask (DtcStatus): [description]

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = bytes([0x19, 0x02]) + mask.bytes
        return self.__make_call(payload)

    def dtc_snapshot_ids_1903(self):
        """Read snapshot id and DTC pairs currently in the ECU

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = bytes([0x19, 0x03])
        return self.__make_call(payload)

    def dtc_snapshot_1904(self, dtc_number: bytes, record: bytes = b'\xff'):
        """Resport the DTC snapshot recorded by the DTC number

        Args:
            dtc_number (bytes): [description]
            record (bytes, optional): [description]. Defaults to 0xff.

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = bytes([0x19, 0x04]) + dtc_number + record
        return self.__make_call(payload)

    def dtc_extended_1906(self, dtc_number: bytes, record: bytes = b'\xff'):
        """Report the DTC extended data record by DTC number

        Args:
            dtc_number (bytes): [description]
            record (bytes, optional): [description]. Defaults to 0xff.

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = bytes([0x19, 0x06]) + dtc_number + record
        return self.__make_call(payload)

    def read_data_by_id_22(self, did: bytes, mask: bytes = b''):
        """Read data by identifier

        Args:
            did (bytes): DID to be read
            mask (bytes, optional): [description]. Defaults to 0.

        Returns:
            UdsResponse: This is a response from the ECU
        """
        payload = b'\x22' + did + mask
        return self.__make_call(payload)

    def active_diag_session_f186(self):
        """Read active diagnostic session/mode (DID F186)

        Returns:
            UdsResponse: This is a response from the ECU
        """
        return self.read_data_by_id_22(b'\xf1\x86')

    def generic_ecu_call(self, payload: bytes = b''):
        """Generic ECU call
        Use the service specific methods if you can instead of this method

        Args:
            payload (bytes, optional): Payload that is to be sent to the ECU. Defaults to 0.

        Returns:
            UdsResponse: This is a response from the ECU
        """
        return self.__make_call(payload)

    def milliseconds_since_request(self):
        """Elapsed time since last sent frame to first received frame with
        millisecond resolution.

        Returns:
            int: Time delta between last sent and last received frame
        """
        t_sent = float(SC.can_frames[self.dut['send']][0][0])
        t_received = float(SC.can_frames[self.dut['receive']][0][0])
        return int((t_received - t_sent) * 1000)

    def set_mode(self, mode=1, change_check=True):
        """Set the mode of the ECU to one of the following:

            1: "default session/mode",
            2: "programming session/mode",
            3: "extended session/mode"

        Args:
            mode (int, optional): Mode the ECU should be set to. Defaults to 1.
            change_check (bool, optional): Check if requested change is legal. Defaults to True.

        Raises:
            UdsError: If requested change is illegal
            UdsError: If failure occurred when setting mode
        """

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
            try:
                res = self.active_diag_session_f186()
            except UdsEmptyResponse as uds_error:
                log.error(uds_error)
                raise

            if not "mode" in res.details:
                raise UdsError(f"Failure occurred when setting mode: {mode}")
        self.mode = res.details["mode"]


    def enter_sbl(self):
        """Enter the secondary bootloader
        """
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
            self.dut, sa_keys=rig.sa_keys, stepno=self.step,
                purpose="Activate Secondary bootloader"):
            UdsError("Could not set ecu in sbl mode")
