"""
Status of DTC (UDS: ISO-14229-1:2006) and Status Indicators SI30 (Autosar)i

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

class StatusBits:
    """ Base class for status bits """
    def __init__(self, hexstring="", bits=""):
        if hexstring and bits:
            raise Exception("specify either hexstring or bits, not both")
        if bits:
            self._bits = list(bits)
        elif hexstring:
            self._bits = list(format(int(hexstring, 16), '08b'))
        else:
            self._bits = list("00000000")

    @property
    def bits(self):
        """ string representation of the bits """
        return ''.join(self._bits)

    @property
    def int(self):
        """ int representation of the bits """
        return int(''.join(self._bits), 2)

    @property
    def hex(self):
        """ hex string representation of the bits """
        return "{:X}".format(self.int)

    @property
    def bytes(self):
        """ convert bits to bytes """
        return bytes([int(self.bits, 2)])

    def clear(self):
        """ reset all bits to 0 """
        self._bits = list("00000000")

    def set_all(self):
        """ set all bits to 1 """
        self._bits = list("11111111")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.bytes == other.bytes
        if isinstance(other, str):
            return self.bits == other
        if isinstance(other, bytes):
            return self.bytes == other
        raise NotImplementedError("datatype is not supported for equality")

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.hex}")'


class DtcStatus(StatusBits):
    """ dtc status bits """

    def __str__(self):
        __str = repr(self)
        dtc_status_bits = [
            'test_failed',
            'test_failed_this_operation_cycle',
            'pending_dtc',
            'confirmed_dtc',
            'test_not_completed_since_last_clear',
            'test_failed_since_last_clear',
            'test_not_completed_this_operation_cycle',
            'warning_indicator_requested',
        ]
        # note the reverse order of the bits below (see section
        # 11.3.5.2.2 of iso-14229-1:2006). bit 0 is the least
        # significant bit (e.g the right-most bit in the string).
        for bit, name in zip(self.bits[::-1], dtc_status_bits):
            __str += f'\n {bit} {name}'
        return __str

    @property
    def test_failed(self):
        """ dtc failed at the time of the request """
        return bool(int(self._bits[7]))

    @test_failed.setter
    def test_failed(self, value):
        self._bits[7] = bool_to_bit(value)

    # pylint: disable=invalid-name
    @property
    def test_failed_this_operation_cycle(self):
        """ dtc failed on the current operation cycle """
        return bool(int(self._bits[6]))

    @test_failed_this_operation_cycle.setter
    def test_failed_this_operation_cycle(self, value):
        self._bits[6] = bool_to_bit(value)

    @property
    def pending_dtc(self):
        """  dtc failed on the current or previous operation cycle """
        return bool(int(self._bits[5]))

    @pending_dtc.setter
    def pending_dtc(self, value):
        self._bits[5] = bool_to_bit(value)

    @property
    def confirmed_dtc(self):
        """ dtc is confirmed at the time of the request """
        return bool(int(self._bits[4]))

    @confirmed_dtc.setter
    def confirmed_dtc(self, value):
        self._bits[4] = bool_to_bit(value)

    @property
    def test_not_completed_since_last_clear(self):
        """ dtc test has not been completed since last clear """
        return bool(int(self._bits[3]))

    @test_not_completed_since_last_clear.setter
    def test_not_completed_since_last_clear(self, value):
        self._bits[3] = bool_to_bit(value)

    @property
    def test_failed_since_last_clear(self):
        """ dtc test failed at least once since last code clear """
        return bool(int(self._bits[2]))

    @test_failed_since_last_clear.setter
    def test_failed_since_last_clear(self, value):
        self._bits[2] = bool_to_bit(value)

    @property
    def test_not_completed_this_operation_cycle(self):
        """ dtc test has not been completed this operation cycle """
        return bool(int(self._bits[1]))

    @test_not_completed_this_operation_cycle.setter
    def test_not_completed_this_operation_cycle(self, value):
        self._bits[1] = bool_to_bit(value)

    @property
    def warning_indicator_requested(self):
        """ server is requesting warningindicator to be active """
        return bool(int(self._bits[0]))

    @warning_indicator_requested.setter
    def warning_indicator_requested(self, value):
        self._bits[0] = bool_to_bit(value)


class StatusIndicators(StatusBits):
    """
    DTC status indicator bits (SI30)

    Note: These bits are defined by Autosar and are not covered by ISO-14229-1
    """

    def __str__(self):
        __str = repr(self)
        status_indicators = [
            'fdc_threshold_reached',
            'fdc_threshold_reached_toc',
            '_undefined_bit_3',
            'aged_dtc',
            'symptoms_since_last_clear',
            'warning_indicator',
            'emission_related_dtc',
            'test_failed_since_last_clear_aged',
        ]

        # like for DTC status bits, status indicators bits are also counted
        # from right to left
        for bit, name in zip(self.bits[::-1], status_indicators):
            __str += f'\n {bit} {name}'
        return __str

    @property
    def fdc_threshold_reached(self):
        """
        autosar: This bit is set to 1 when debouncing counter reach the value
        DemEventMemoryEntryFdcThresholdStorageValue and reset to 0 when the
        debouncing counter reach the value DemDebounceCounterPassedThreshold

        according to swrs version 4, this bit is N/A and should always be 0
        """
        return bool(int(self._bits[7]))

    @fdc_threshold_reached.setter
    def fdc_threshold_reached(self, value):
        self._bits[7] = bool_to_bit(value)

    @property
    def fdc_threshold_reached_toc(self):
        """
        autosar: The bit is set to 1 when fdc_threshold_reached is set to 1.
        The bit is reset to 0 at the start of the operation cycle
        (DemOperationCycleRef)

        according to swrs version 4, this bit is N/A and should always be 0
        """
        return bool(int(self._bits[6]))

    @fdc_threshold_reached_toc.setter
    def fdc_threshold_reached_toc(self, value):
        self._bits[6] = bool_to_bit(value)

    @property
    def _undefined_bit_3(self):
        """
        undefined bit 3

        according to swrs version 4, this bit is N/A and should always be 0
        """
        # according to swrs version 4, this should always be 0
        return bool(int(self._bits[5]))

    @_undefined_bit_3.setter
    def _undefined_bit_3(self, value):
        self._bits[5] = bool_to_bit(value)

    @property
    def aged_dtc(self):
        """
        The bit is set to 1 when the DTC is aged.
        The bit is reset to 0 when the aged DTC reoccurs.
        """
        return bool(int(self._bits[4]))

    @aged_dtc.setter
    def aged_dtc(self, value):
        self._bits[4] = bool_to_bit(value)

    @property
    def symptoms_since_last_clear(self):
        """
        swrs:
        When implemented, this bit indicates whether the fault detected by the
        DTC-test has caused a customer symptom since DTC information was last
        cleared.

        The bit shall be set to 1 when the FDC10 is in the range [UnconfirmedDTCLimit
        to TestFailedLimit] and specific conditions, that need to be fulfilled in order
        to cause a customer symptom, are satisfied.

        The specific conditions, specified by the implementer, can be that the
        customer use the defect function, ECU takes certain actions due to the
        fault, the ECU is in specific operation or environment condition, etc.

        When not implemented, the bit shall be set to 0
        """
        return bool(int(self._bits[3]))

    @symptoms_since_last_clear.setter
    def symptoms_since_last_clear(self, value):
        self._bits[3] = bool_to_bit(value)

    @property
    def warning_indicator(self):
        """
        autosar:
        This bit is set to 1 when UDS DTC status bit 7 is set to 1 and
        the bit is reset to 0 when a call to ClearDTC is made

        When implemented, this bit indicates the maximum value of DTC status
        bit 7 since DTC information was last cleared.

        swrs:
        The bit is set to 1 when DTC status bit no 7 is set to 1.

        However, the bit may also be set to 1 even when DTC status bit not 7 –
        warningIndicatorRequested is not set to 1 (refer to reference ISO
        14229-1 regarding requirements on set of DTC status bit not 7 to 1)
        according to the following:


        The bit is set to 1 when the same criteria as required by the above
        mention reference on set of DTC status bit not 7 –
        warningIndicatorRequested to 1 is satisfied, but it may also be set to
        1 and warning indicator may be requested before DTC status bit 3 –
        confirmed DTC is set to 1.

        Note that in all cases must FDC10 has reached the value +127, since DTC
        information was latest cleared, before the bit is set to 1 and warring
        indicator is requested (if not otherwise is specified in this
        document).

        When not implemented, the bit shall be set to 0
        """
        return bool(int(self._bits[2]))

    @warning_indicator.setter
    def warning_indicator(self, value):
        self._bits[2] = bool_to_bit(value)

    @property
    def emission_related_dtc(self):
        """
        autosar:
        This bit is set to 1 when the DTC is emission related and set to 0 when
        the DTC is not emission related.

        swrs:
        The bit is set to 0 when the DTC is not emission related.

        The bit is set to 1 when the DTC is emission related.

        Note that a DTC is not emission related as long as the FDC10 has not
        reached the value +127 since DTC information was last cleared and when
        it is aged i.e. the SI30:3 (bit 3 above) is set to1.
        """
        return bool(int(self._bits[1]))

    @emission_related_dtc.setter
    def emission_related_dtc(self, value):
        self._bits[1] = bool_to_bit(value)

    # pylint: disable=invalid-name
    @property
    def test_failed_since_last_clear_aged(self):
        """
        swrs:
        When implemented, this bit indicates DTC test failed since the DTC was
        last aged or, as long as the DTC have not been aged, since the DTC
        information was last cleared.

        The bit is set to set to 1 when DTC test is failed i.e. when the FDC10
        reach the value +127.

        The bit is reset to 0 when DTC is aged i.e. the SI30:3 (bit 3 above) is
        set to1.

        When not implemented, this bit shall be set to 0
        """
        return bool(int(self._bits[0]))

    @test_failed_since_last_clear_aged.setter
    def test_failed_since_last_clear_aged(self, value):
        self._bits[0] = bool_to_bit(value)



def bool_to_bit(value):
    """ convert truth value to bit """
    return "1" if value else "0"


##################################
# Pytest unit tests starts here
##################################

def test_dtc_status():
    """ pytest: test correct operation of the DtcStatus class """
    bits = DtcStatus("AF")
    other_bits = DtcStatus("AF")
    assert bits == other_bits
    assert bits is not other_bits
    assert bits == "10101111"
    assert bits.bytes == b'\xAF'
    assert bits == b'\xAF'
    assert bits.test_failed
    bits.test_failed = False
    assert not bits.test_failed
    assert bits == b'\xAE'

    # ISO 14229-1:2006 section 11.3.5.2.2 examples:

    table_261_bits = DtcStatus("24")
    assert table_261_bits == "00100100"

    # ensure correct operation of each bit
    assert not table_261_bits.test_failed
    assert not table_261_bits.test_failed_this_operation_cycle
    assert table_261_bits.pending_dtc
    assert not table_261_bits.confirmed_dtc
    assert not table_261_bits.test_not_completed_since_last_clear
    assert table_261_bits.test_failed_since_last_clear
    assert not table_261_bits.test_not_completed_this_operation_cycle
    assert not table_261_bits.warning_indicator_requested

    table_262_bits = DtcStatus("02")
    assert table_262_bits == "00000010"

    # ensure correct operation of each bit
    assert not table_262_bits.test_failed
    assert table_262_bits.test_failed_this_operation_cycle
    assert not table_262_bits.pending_dtc
    assert not table_262_bits.confirmed_dtc
    assert not table_262_bits.test_not_completed_since_last_clear
    assert not table_262_bits.test_failed_since_last_clear
    assert not table_262_bits.test_not_completed_this_operation_cycle
    assert not table_262_bits.warning_indicator_requested

    table_263_bits = DtcStatus("2F")
    assert table_263_bits == "00101111"

    # ensure correct operation of each bit
    assert table_263_bits.test_failed
    assert table_263_bits.test_failed_this_operation_cycle
    assert table_263_bits.pending_dtc
    assert table_263_bits.confirmed_dtc
    assert not table_263_bits.test_not_completed_since_last_clear
    assert table_263_bits.test_failed_since_last_clear
    assert not table_263_bits.test_not_completed_this_operation_cycle
    assert not table_263_bits.warning_indicator_requested

def test_status_indicators():
    """ ensure the correct operation of status indicators """
    si = StatusIndicators("01")
    assert si.bits == "00000001"
    assert si.fdc_threshold_reached

    si = StatusIndicators("03")
    assert si.bits == "00000011"
    assert si.fdc_threshold_reached
    assert si.fdc_threshold_reached_toc

    si = StatusIndicators("21")
    assert si.bits == "00100001"
    assert si.fdc_threshold_reached
    assert si.warning_indicator

    si = StatusIndicators("23")
    assert si.bits == "00100011"
    assert si.fdc_threshold_reached
    assert si.fdc_threshold_reached_toc
    assert si.warning_indicator
