"""
Status of DTC (ISO-14229-1:2006)
"""

class DtcStatus:
    """ DTC status bits """

    def __init__(self, hexstring="", bits=""):
        if hexstring and bits:
            raise Exception("specify either hexstring or bits, not both")
        if bits:
            self.__bits = list(bits)
        elif hexstring:
            self.__bits = list(format(int(hexstring, 16), '08b'))
        else:
            self.__bits = list("00000000")

    @property
    def bits(self):
        """ string representation of the bits """
        return ''.join(self.__bits)

    def clear(self):
        """ reset all bits to 0 """
        self.__bits = list("00000000")

    def set_all(self):
        """ set all bits to 1 """
        self.__bits = list("11111111")

    def to_bytes(self):
        """ convert bits to bytes """
        return bytes([int(self.bits, 2)])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.to_bytes() == other.to_bytes()
        if isinstance(other, str):
            return self.bits == other
        if isinstance(other, bytes):
            return self.to_bytes() == other
        raise NotImplementedError("datatype is not supported for equality")

    def __repr__(self):
        return f'{self.__class__.__name__}(bits="{self.bits}")'

    def __str__(self):
        s = f'{self.__class__.__name__}:\n'
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
        # 11.3.5.2.2 of ISO-14229-1:2006). bit 0 is the least
        # significant bit (e.g the right-most bit in the string).
        for bit, name in zip(self.bits[::-1], dtc_status_bits):
            s += f' {bit} {name}\n'
        return s

    @property
    def test_failed(self):
        """ DTC failed at the time of the request """
        return bool(int(self.__bits[7]))

    @test_failed.setter
    def test_failed(self, value):
        self.__bits[7] = bool_to_bit(value)

    # pylint: disable=invalid-name
    @property
    def test_failed_this_operation_cycle(self):
        """ DTC failed on the current operation cycle """
        return bool(int(self.__bits[6]))

    @test_failed_this_operation_cycle.setter
    def test_failed_this_operation_cycle(self, value):
        self.__bits[6] = bool_to_bit(value)

    @property
    def pending_dtc(self):
        """  DTC failed on the current or previous operation cycle """
        return bool(int(self.__bits[5]))

    @pending_dtc.setter
    def pending_dtc(self, value):
        self.__bits[5] = bool_to_bit(value)

    @property
    def confirmed_dtc(self):
        """ DTC is confirmed at the time of the request """
        return bool(int(self.__bits[4]))

    @confirmed_dtc.setter
    def confirmed_dtc(self, value):
        self.__bits[4] = bool_to_bit(value)

    @property
    def test_not_completed_since_last_clear(self):
        """ DTC test has not been completed since last clear """
        return bool(int(self.__bits[3]))

    @test_not_completed_since_last_clear.setter
    def test_not_completed_since_last_clear(self, value):
        self.__bits[3] = bool_to_bit(value)

    @property
    def test_failed_since_last_clear(self):
        """ DTC test failed at least once since last code clear """
        return bool(int(self.__bits[2]))

    @test_failed_since_last_clear.setter
    def test_failed_since_last_clear(self, value):
        self.__bits[2] = bool_to_bit(value)

    @property
    def test_not_completed_this_operation_cycle(self):
        """ DTC test has not been completed this operation cycle """
        return bool(int(self.__bits[1]))

    @test_not_completed_this_operation_cycle.setter
    def test_not_completed_this_operation_cycle(self, value):
        self.__bits[1] = bool_to_bit(value)

    @property
    def warning_indicator_requested(self):
        """ Server is requesting warningIndicator to be active """
        return bool(int(self.__bits[0]))

    @warning_indicator_requested.setter
    def warning_indicator_requested(self, value):
        self.__bits[0] = bool_to_bit(value)


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
    assert bits.to_bytes() == b'\xAF'
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
