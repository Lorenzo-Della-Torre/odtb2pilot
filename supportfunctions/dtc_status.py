"""
DTC status bits implementation according to ISO-14229-1
"""

class DtcStatus:
    """
    DTC status bits
    """

    # pylint: disable=invalid-name, missing-function-docstring
    def __init__(self, hexstring=""):
        if hexstring:
            self.__bits = list(format(int(hexstring, 16), '08b'))
        else:
            self.__bits = list('00000000')

    def clear(self):
        """
        reset all bits to 0
        """
        self.__bits = list("00000000")

    def set_all(self):
        """
        set all bits to 1
        """
        self.__bits = list("11111111")

    def to_bytes(self):
        """
        convert bits to bytes
        """
        return bytes([int(''.join(self.__bits), 2)])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.to_bytes() == other.to_bytes()
        if isinstance(other, str):
            return ''.join(self.__bits) == other
        raise NotImplementedError("datatype is not supported for equality")


    def __repr__(self):
        bits = ''.join(self.__bits)
        bits = self.__bits
        return f'{self.__class__.__name__}({bits})'

    def __str__(self):
        # note the reverse order compared to the listing in ISO-14229-1. bit 0
        # is the least significant bit (e.g the right-most bit in the string)
        dtc_status_bits = [
            'warning_indicator_requested'
            'test_not_completed_this_operation_cycle',
            'test_failed_since_last_clear',
            'test_not_completed_since_last_clear',
            'confirmed_dtc',
            'pending_dtc',
            'test_failed_this_operation_cycle',
            'test_failed',
        ]

        return str([dtc_status_bits[i]
                for i, x in enumerate(self.__bits) if x == '1'])

    @property
    def test_failed(self):
        return bool(int(self.__bits[7]))

    @test_failed.setter
    def test_failed(self, value):
        self.__bits[7] = bool_to_bit(value)

    @property
    def test_failed_this_operation_cycle(self):
        return bool(self.__bits[6])

    @test_failed_this_operation_cycle.setter
    def test_failed_this_operation_cycle(self, value):
        self.__bits[6] = bool_to_bit(value)

    @property
    def pending_dtc(self):
        return bool(self.__bits[5])

    @pending_dtc.setter
    def pending_dtc(self, value):
        self.__bits[5] = bool_to_bit(value)

    @property
    def confirmed_dtc(self):
        return bool(self.__bits[4])

    @confirmed_dtc.setter
    def confirmed_dtc(self, value):
        self.__bits[4] = bool_to_bit(value)

    @property
    def test_not_completed_since_last_clear(self):
        return bool(self.__bits[3])

    @test_not_completed_since_last_clear.setter
    def test_not_completed_since_last_clear(self, value):
        self.__bits[3] = bool_to_bit(value)

    @property
    def test_failed_since_last_clear(self):
        return bool(self.__bits[2])

    @test_failed_since_last_clear.setter
    def test_failed_since_last_clear(self, value):
        self.__bits[2] = bool_to_bit(value)

    @property
    def test_not_completed_this_operation_cycle(self):
        return bool(self.__bits[1])

    @test_not_completed_this_operation_cycle.setter
    def test_not_completed_this_operation_cycle(self, value):
        self.__bits[1] = bool_to_bit(value)

    @property
    def warning_indicator_requested(self):
        return bool(self.__bits[0])

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
    """ pytest: test correct operation of DtcStatus class """
    bits1 = DtcStatus("AF")
    bits2 = DtcStatus("AF")
    assert bits1 == bits2
    assert bits1 == "10101111"
    assert bits1.to_bytes() == b'\xAF'
    assert bits1.test_failed
    bits1.test_failed = False
    print(bits1)
    assert not bits1.test_failed
    assert bits1.to_bytes() == b'\xAE'
