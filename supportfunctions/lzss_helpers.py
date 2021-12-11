"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
    LZSS helpers taken from
    #https://stackoverflow.com/a/10691412

    Demo simple implementation of LZSS using Python.
"""
import sys
import contextlib
import array

class Reference():
    """Just a wrapper - no data validation"""

    def __init__(self, position: int, length: int):
        self._position = position
        self._length = length

    def get_length(self) -> int:
        """
            get_length
                returns length of object
        """
        return self._length

    def get_pos(self) -> int:
        """
            param: self
            returns: argument _position from param
        """
        return self._position

    def get_bits(self) -> int:
        """
            get_bits
                param: self
                returns: number of bits in self
        """
        # 12 bits for position = max pos is 4096
        # 4 bits for length = max match size is 16
        return self._position << 4 | self._length

    @staticmethod
    def from_bytes(f_bytes: bytes):
        """
            from_bytes
                param: f_bytes
                returns: last 4 bits
        """
        assert len(f_bytes) == 2
        position = (f_bytes[0] << 4) | (f_bytes[1] & ~0b1111)
        length = f_bytes[1] & 0b1111
        return Reference(position, length)

    def __str__(self):
        return "reference: {0}, {1}".format(self._position, self._length)

class CircularBuffer():
    """
        LZSS helpers taken from
        #https://stackoverflow.com/a/10691412
        CircularBuffer implements a sliding window
        slightly changed from LZSS helpers to fit Volvo implementation

        Demo simple implementation of LZSS using Python.
    """

    def __init__(self, max_buffer_size: int):
        self._buffer = array.array('B', bytes(max_buffer_size))
        self._max_buffer_size = max_buffer_size
        self._startpos = 0
        self._putpos = 0
        #self._buffer_size = 0
        self._fill = 0

    def put_byte(self, num_of_bits: int):
        """
            put_byte
            writes #num_of_bits from self
        """
        self._buffer[self._putpos] = num_of_bits
        self._putpos = (self._putpos+1) % self._max_buffer_size
        if self._fill < self._max_buffer_size:
            self._fill = self._fill +1
        if self._fill == self._max_buffer_size:
            self._startpos = self._putpos

    def get_byte_at(self, pos: int) -> int:
        """
            get_byte
            reads byte from buffer at position pos
        """
        npos = pos % self._max_buffer_size
        return self._buffer[npos]

    #def get_match(self, start_pos: int, length: int) -> [int]:
    #    return self._buffer[start_pos : start_pos + length]

    def get_fill(self) -> int:
        """
            get_fill
            returns number of bytes buffer is filled with
        """
        return len(self._fill)

    def get_longest_match(self, max_allowable_match_length: int, buffer) -> Reference:
        """
            get_longest_match
            get the longest match from look_ahead_buffereturns
            returns Reference to match
        """
        # walk it
        longest_match_length = 0
        longest_match_pos = -1
        for i in range(0, self.get_fill()):
            j = 0
            # is there still some symbols left to compare with?
            while(((i + j)% self._max_buffer_size) < self.get_fill() and
                  j < buffer.get_fill() and
                  buffer.get_byte_at(j) == self.get_byte_at(i + j)):
                # if there are, check another
                j += 1
                if j > max_allowable_match_length:
                    print("max_allowable_match_length overflow")
            if j > longest_match_length:
                longest_match_length = j
                longest_match_pos = i
        return Reference(longest_match_pos, longest_match_length)

    def __str__(self):
        return str(self._buffer)

    def pop(self):
        """remove first element and return it"""
        return self._buffer.pop(0)


class SmartOpener():
    """
        taken from:
        #https://stackoverflow.com/a/17603000

    """
    @staticmethod
    @contextlib.contextmanager
    def smart_write(filename=None, mode='wb'):
        """
            smart_write
            opens file,
            stores file_handle
            writes to file
        """
        if filename and filename != '-':
            # to fix pylint warning: consider-using-with
            # pylint: disable=E0012, R1732
            file_h = open(file=filename, mode=mode)
        else:
            file_h = sys.stdout.buffer

        try:
            yield file_h
        finally:
            if file_h is not sys.stdout:
                file_h.close()

    @staticmethod
    @contextlib.contextmanager
    def smart_read(filename=None, mode='rb'):
        """
            smart_write
            opens file,
            stores file_handle
            reads from file
        """
        if filename and filename != '-':
            # to fix pylint warning: consider-using-with
            # pylint: disable=E0012, R1732
            file_h = open(file=filename, mode=mode)
        else:
            file_h = sys.stdin.buffer

        try:
            yield file_h
        finally:
            if file_h is not sys.stdin.buffer:
                file_h.close()
