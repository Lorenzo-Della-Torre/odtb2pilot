"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# project:  Hilding testenvironment using SignalBroker
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

The Python implementation of the grPC route guide client.
"""

#import io
import lzma
import logging

class LzmaEncoder():
    """
    support function for decoding
    LZMA compressed blocks.
    implemented to have same support functions as for LZMA compression
    """

    def __init__(self):
        pass


    @classmethod
    def encode(cls, inpath, outpath):
        """
        Encode file with LZMA
        code snippet from web - not tested yet
        """
        logging.info("LZMA encoding: not implemented yet")
        logging.info("inpath:  %s", inpath)
        logging.info("outpath: %s", outpath)

    @classmethod
    def encode_barray(cls, in_array, out_array):
        """
        Encode binary stream with LZMA
        code snippet from web - not tested yet
        """
        logging.info("LZMA encode_barray: not implemented yet")
        logging.info("in_array:  %s", in_array)
        logging.info("out_array: %s", out_array)

    @classmethod
    def decode(cls, inpath, outpath):
        """
        Decode file with LZMA
        code snippet from web - not tested yet
        """
        logging.info("LZMA decode: not implemented yet")
        logging.info("inpath:  %s", inpath)
        logging.info("outpath: %s", outpath)


    @classmethod
    def decode_barray(cls, in_array):
        # pylint: disable=too-many-locals
        """
        Decode io.BytesIO with LZMA
        """
        return lzma.decompress(in_array)
