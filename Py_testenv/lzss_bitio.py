"""
    LZSS bitio taken from
    #https://stackoverflow.com/a/10691412

    Demo simple implementation of LZSS using Python.
"""
class BitWriter:
    """
    LZSS bitio taken from
    #https://stackoverflow.com/a/10691412

    Demo simple implementation of LZSS using Python.
    """
    def __init__(self, f):
        self.accumulator = 0
        self.bcount = 0
        self.out = f

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

    def __del__(self):
        try:
            self.flush()
        except ValueError:   # I/O operation on closed file.
            pass

    def _writebit(self, bit):
        if self.bcount == 8:
            self.flush()
        if bit > 0:
            self.accumulator |= 1 << 7-self.bcount
        self.bcount += 1

    def writebits(self, bits, num_of_bits):
        """
            writes
                num_of_bits taken from
                bits
        """
        while num_of_bits > 0:
            self._writebit(bits & 1 << num_of_bits-1)
            num_of_bits -= 1

    def flush(self):
        """
            writes number of bits in buffer
            flushes buffer after writing it
        """
        #print("flush write: ", self.accumulator, "bytearray: ", bytearray([self.accumulator]))
        self.out.write(bytearray([self.accumulator]))
        #self.out.write(self.accumulator)
        self.accumulator = 0
        self.bcount = 0


class BitReader:
    """
    LZSS bitio taken from
    #https://stackoverflow.com/a/10691412

    Demo simple implementation of LZSS using Python.
    """
    def __init__(self, f):
        self.input = f
        self.accumulator = 0
        self.bcount = 0
        self.read = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _readbit(self):
        if not self.bcount:
            a_byte = self.input.read(1) #one byte like b'I'
            if a_byte:
                self.accumulator = ord(a_byte) #a_byte as int
            self.bcount = 8 #bitcount
            self.read = len(a_byte)
        ret_value = (self.accumulator & (1 << self.bcount-1)) >> self.bcount-1
        self.bcount -= 1
        return ret_value

    def readbits(self, num_of_bits):
        """
            readbits
                reads num_of_bits from self
            returns
                bits read as string containing '01'
        """
        v_bits = 0
        while num_of_bits > 0:
            v_bits = (v_bits << 1) | self._readbit()
            num_of_bits -= 1
        return v_bits
