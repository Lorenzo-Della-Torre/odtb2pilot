# project:  ODTB2 testenvironment using SignalBroker
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-04-20
# version:  1.0

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 grPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WArrANTIES Or CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the grPC route guide client."""

import io
import supportfunctions.lzss_bitio
from supportfunctions.lzss_helpers import CircularBuffer, Reference, SmartOpener

class LzssEncoder():
    """
    support function for decoding
    LZSS compressed blocks.

    For details concerning algorithm see
    VOLVO document no. 31827960-006 (or newer)
    LZSS is not completely followed.
    """
    LZSS_INDEX_BIT_COUNT = 10
    LZSS_LENGTH_BIT_COUNT = 4
    LZSS_WINDOW_SIZE = (1 << LZSS_INDEX_BIT_COUNT)     #10 bits for position pointer
    #LZSS_BREAK_EVEN = 2
    LZSS_BREAK_EVEN = int((1 + LZSS_INDEX_BIT_COUNT + LZSS_LENGTH_BIT_COUNT) / 9)
    MAX_MATCH_SIZE = (1 << LZSS_LENGTH_BIT_COUNT) -1   #max value is 15
    #ENCODED_FLAG = 0b1
    ENCODED_FLAG = 0b0 #Volvo choosed to use 0b0
    LZSS_END_OF_STREAM = 0

    def __init__(self):
        pass

    @staticmethod
    def _byte2int(byte) -> int:
        assert len(byte) == 1
        return int.from_bytes(byte, byteorder="big")

    def _read_next(self, buffer: CircularBuffer, dictionary: CircularBuffer, infile) -> bool:
        """Read next to buffer, return false if there is nothing to read"""
        dictionary.put_byte(buffer.get_byte_at(0))
        last_byte = infile.read(1)
        if last_byte:
            buffer.put_byte(self._byte2int(last_byte))  # read another byte to buffer
            ret_v = True
        else: # EOF?
            buffer.pop()
            ret_v = buffer.get_fill() > 0
        return ret_v

    def encode(self, inpath, outpath):
        """
        Encode file with LZSS
        code snippet from web - not tested yet
        """
        dictionary = CircularBuffer(self.LZSS_WINDOW_SIZE)
        buffer = CircularBuffer(self.MAX_MATCH_SIZE)
        with SmartOpener.smart_read(inpath) as infile, SmartOpener.smart_write(outpath) as outfile:
            with lzss_bitio.BitWriter(outfile) as writer:
                for _ in range(0, self.MAX_MATCH_SIZE): #max match as initial buffer value
                    buffer.put_byte(self._byte2int(infile.read(1)))
                is_there_something_to_read = True
                while is_there_something_to_read:
                    longest_match_ref = dictionary.get_longest_match(self.MAX_MATCH_SIZE, buffer)
                    if longest_match_ref.get_length() > self.LZSS_BREAK_EVEN:
                        writer.writebits(self.ENCODED_FLAG, 1)
                        writer.writebits(longest_match_ref.get_bits(), 16)
                        #print("Writing ref: " + str(bin(longest_match_ref.get_bits())))
                        for _ in range(0, longest_match_ref.get_length()):
                            # go forward since only match reference is written
                            is_there_something_to_read = self._read_next(buffer, dictionary, infile)
                    else:
                        writer.writebits(0, 1)
                        #print("Writing raw: " + str(bin(buffer.get_byte_at(0))))
                        writer.writebits(buffer.get_byte_at(0), 8) #write original byte
                        is_there_something_to_read = self._read_next(buffer, dictionary, infile)
    def encode_barray(self, in_array, out_array):
        """
        Encode binary stream with LZSS
        code snippet from web - not tested yet
        """
        dictionary = CircularBuffer(self.LZSS_WINDOW_SIZE)
        buffer = CircularBuffer(self.MAX_MATCH_SIZE)
        #with in_array as infile, out_array as outfile:
        with io.BytesIO(in_array) as infile, io.BytesIO(out_array) as outfile:
            with lzss_bitio.BitWriter(outfile) as writer:
                for _ in range(0, self.MAX_MATCH_SIZE): #max match as initial buffer value
                    buffer.put_byte(self._byte2int(infile.read(1)))
                is_there_something_to_read = True
                while is_there_something_to_read:
                    longest_match_ref = dictionary.get_longest_match(self.MAX_MATCH_SIZE, buffer)
                    if longest_match_ref.get_length() > self.LZSS_BREAK_EVEN:
                        writer.writebits(self.ENCODED_FLAG, 1)
                        writer.writebits(longest_match_ref.get_bits(), 16)
                        #print("Writing ref: " + str(bin(longest_match_ref.get_bits())))
                        for _ in range(0, longest_match_ref.get_length()):
                            # go forward since only match reference is written
                            is_there_something_to_read = self._read_next(buffer, dictionary, infile)
                    else:
                        writer.writebits(0, 1)
                        #print("Writing raw: " + str(bin(buffer.get_byte_at(0))))
                        writer.writebits(buffer.get_byte_at(0), 8) #write original byte
                        is_there_something_to_read = self._read_next(buffer, dictionary, infile)

    def decode(self, inpath, outpath):
        # pylint: disable=too-many-locals
        """
        Decode file with LZSS
        code snippet from web - not tested yet
        """
        eos_reached = False
        dictionary = CircularBuffer(self.LZSS_WINDOW_SIZE)
        with SmartOpener.smart_read(inpath) as infile, SmartOpener.smart_write(outpath) as outfile:
            with lzss_bitio.BitReader(infile) as reader, lzss_bitio.BitWriter(outfile) as writer:
                while not eos_reached:
                    bit = reader.readbits(1)
                    if bit == self.ENCODED_FLAG:
                        reference_pos_bits = reader.readbits(self.LZSS_INDEX_BIT_COUNT)
                        if reference_pos_bits == self.LZSS_END_OF_STREAM:
                            eos_reached = True
                        else:
                            reference_length_bits = reader.readbits(self.LZSS_LENGTH_BIT_COUNT)
                            reference_length_bits = reference_length_bits + self.LZSS_BREAK_EVEN +1
                            #Python array starts at 0, correct position:
                            #Correct length to be loop+1
                            reference = Reference(reference_pos_bits-1, reference_length_bits)
                            for i in range(0, reference.get_length()):
                                byte = dictionary.get_byte_at((reference.get_pos() + i)\
                                                            % self.LZSS_WINDOW_SIZE)
                                dictionary.put_byte(byte)
                                writer.writebits(byte, 8)
                            if not reader.read:
                                print("Not reader.read - break in encoded")
                                break
                    else:
                        byte = reader.readbits(8)
                        if not reader.read:
                            print("Not reader.read - break in else")
                            break
                        dictionary.put_byte(byte)
                        writer.writebits(byte, 8)


    def decode_barray(self, in_array):
        # pylint: disable=too-many-locals
        """
        Decode io.BytesIO with LZSS
        modified to fit Volvo, tested with VBF files
        """
        eos_reached = False
        dictionary = CircularBuffer(self.LZSS_WINDOW_SIZE)
        # no out_array here, wouldn't be returned
        with io.BytesIO(in_array) as infile, io.BytesIO() as outfile:
            with lzss_bitio.BitReader(infile) as reader, lzss_bitio.BitWriter(outfile) as writer:
                while not eos_reached:
                    bit = reader.readbits(1)
                    if bit == self.ENCODED_FLAG:
                        reference_pos_bits = reader.readbits(self.LZSS_INDEX_BIT_COUNT)
                        if reference_pos_bits == self.LZSS_END_OF_STREAM:
                            eos_reached = True
                        else:
                            reference_length_bits = reader.readbits(self.LZSS_LENGTH_BIT_COUNT)
                            reference_length_bits = reference_length_bits + self.LZSS_BREAK_EVEN +1
                            #print("New length: ", reference_length_bits)
                            #Python array starts at 0, correct position:
                            #Correct length to be loop+1
                            reference = Reference(reference_pos_bits-1, reference_length_bits)
                            for i in range(0, reference.get_length()):
                                byte = dictionary.get_byte_at((reference.get_pos() + i)\
                                                            % self.LZSS_WINDOW_SIZE)
                                dictionary.put_byte(byte)
                                writer.writebits(byte, 8)
                            if not reader.read:
                                print("Not reader.read - break in encoded")
                                break
                    else:
                        byte = reader.readbits(8)
                        if not reader.read:
                            print("Not reader.read - break in else")
                            break
                        dictionary.put_byte(byte)
                        writer.writebits(byte, 8)
            out_array = outfile.getvalue()
        return out_array
