#pylint: disable=too-many-lines
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
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-11
# version:  0.1

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-07-06
# version:  1.0
# changes:  parameters in VBF are parsed now

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-10-08
# version:  1.1
# changes:  update for fit comments added in VBF

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-10-15
# version:  1.2
# changes:  update better handling of ECU-mode when activating SBL

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2021-08-13
# version:  1.3
# changes:  support SecAcc_Gen2

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

The Python implementation of the gRPC route guide client.
"""

import time
import logging
import os
import sys
import glob
from typing import Dict
import traceback

from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_lzss import LzssEncoder
from supportfunctions.support_lzma import LzmaEncoder
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
LZSS = LzssEncoder()
LZMA = LzmaEncoder()

SE10 = SupportService10()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


class VbfHeader(Dict): # pylint: disable=inherit-non-class
    """
        Parameters used in VBF header
        For keywords see Volvo Document 31808832 Rev 015
        SWRS Versatile Binary Format Specification
    """
    description: list
    sw_part_number: str
    sw_version: str
    sw_part_type: str
    sw_current_part_number: str
    sw_current_version: str
    data_format_identifier: int
    ecu_address: int
    erase: list #used in other VBF files
    call: int   #used in SBL
    verification_block_root_hash: int
    verification_block_start: int
    verification_block_length: int
    sw_signature_dev: int
    sw_signature: int
    parameter_settings: list
    file_checksum: int

    @classmethod
    def vbf_header_read(cls, vbf_header):
        """
            return vbf_header
        """
        return vbf_header

class VbfBlock(Dict): # pylint: disable=inherit-non-class
    """
        Parameters used in VBF blocks
        For keywords see Volvo Document 31808832 Rev 015
        SWRS Versatile Binary Format Specification
    """
    StartAddress: int
    Length: int
    Checksum: int


    @classmethod
    def vbf_block_read(cls, block):
        """
            return block
        """
        return block


class SupportSBL:
    # Disable the too-many-public-methods violation. Not sure how to split it
    # pylint: disable=too-many-public-methods
    """
    class for supporting Secondary Bootloader Download
    """
    #_debug = True
    _debug = False

    def __init__(self, sbl='', ess='', df=''):
        self._sbl = sbl
        self._ess = ess
        if df == '':
            self._df = []
        else:
            self._df = df


    def show_filenames(self):
        """
        print filenames used for SWDL
        """
        result = True
        # Some ECU like HLCM don't include ESS vbf
        # if so, state that in project or testscript parameters (yml file)
        ess_needed = True
        new_ess_needed = SIO.parameter_adopt_teststep('ess_needed')
        if new_ess_needed != '':
            assert isinstance(new_ess_needed, bool)
            ess_needed = new_ess_needed
        else:
            logging.info("Support_SBL: new_ess_needed is empty. Leave True.")
        logging.info("Support_SBL: ess_needed after YML: %s", ess_needed)

        if (len(self._sbl) == 0) or\
            (ess_needed and (len(self._ess) == 0)) or (len(self._df) == 0):
            logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            logging.info("!!!!! VBF files not as expected / incomplete! !!!!!")
            logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            logging.info("len SBL: %s", len(self._sbl))
            logging.info("len ESS: %s", len(self._ess))
            logging.info("len DF: %s", len(self._df))

        logging.info("SBL:  %s", self._sbl)
        logging.info("ESS: %s", self._ess)
        logging.info("DF: %s", self._df)
        if (len(self._sbl) == 0) or\
            (ess_needed and (len(self._ess) == 0)) or (len(self._df) == 0):
            logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            logging.info("!!!!! VBF files not as expected / incomplete! !!!!!")
            logging.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            result = False
        return result

    def get_sbl_filename(self):
        """
        return filename used for SBL in SWDL
        """
        return self._sbl


    def get_ess_filename(self):
        """
        return filename used for ESS in SWDL
        """
        return self._ess


    def get_df_filenames(self):
        """
        return filenames used for data in SWDL
        """
        return self._df


    def read_vbf_param(self, f_names):
        """
        read filenames used for transer as args to testscript
        """
        # read arguments for files to DL:
        f_sbl = ''
        f_ess = ''
        f_df = []
        for f_name in f_names:
            if not f_name.find('.vbf') == -1:
                logging.info("Filename to DL:  %s", f_name)

                vbf_version, vbf_header, _, _ = self.read_vbf_file(f_name)
                self.vbf_header_convert(vbf_header)
                logging.debug("VBF version: %s", vbf_version)
                logging.debug('VBF_header: %s', vbf_header)

                if vbf_header["sw_part_type"] == 'SBL':
                    f_sbl = f_name
                elif vbf_header["sw_part_type"] == 'ESS':
                    f_ess = f_name
                else:
                    f_df.append(f_name)
        self.__init__(f_sbl, f_ess, f_df)
        result = self.show_filenames()
        #time.sleep(10)
        return result


    def get_vbf_files_wo_argv(self):
        """
        read filenames used for transfer to ECU
        sets filenames found in dict vbf_header
        This can be used if you want to avoid the sys.argv part
        """
        odtb_proj_param = os.environ.get('ODTBPROJPARAM')
        if odtb_proj_param is None:
            odtb_proj_param = '.'
        f_names = glob.glob(odtb_proj_param + "/VBF/*.vbf")
        result = self.read_vbf_param(f_names)
        return result


    def get_vbf_files(self):
        """
        read filenames used for transfer to ECU
        sets filenames found in dict vbf_header
        """
        logging.debug("Length sys.argv: %s", len(sys.argv))
        if len(sys.argv) != 1:
            f_names = sys.argv
            result = self.read_vbf_param(f_names)
        else:
            result = self.get_vbf_files_wo_argv()
        return result


    def display_data_block(self,# pylint: disable=too-many-branches too-many-statements
                           vbf_header: VbfHeader,
                           vbf_data, vbf_offset):
        """
            display_data_block
            support function to transfer
            data with given offset and data_format to
            intended destination, given by
            stub, can_send, can_rec, can_nspace

            stepno, purpose:
                used for logging purposes
        """
        result = True
        # Iteration to Download the SBL by blocks
        logging.info("vbf_offset: %s len(data): %s", vbf_offset, len(vbf_data))
        while vbf_offset < len(vbf_data):
            # Extract data block
            # new offset!
            vbf_offset, vbf_block, vbf_block_data = (
                self.block_data_extract(vbf_data, vbf_offset))

            decompress_block = True
            new_decompress_block =\
                SIO.parameter_adopt_teststep('decompress_block')
            if new_decompress_block != '':
                assert isinstance(new_decompress_block, bool)
                decompress_block = new_decompress_block
            else:
                logging.debug("Support_SBL: new_decompress_block is empty. Leave True.")
            #show data block after decompress
            logging.debug("Support_SBL: decompress_block after YML: %s", decompress_block)

            #show header details
            logging.info("vbf_header:  %s", vbf_header)
            logging.info("data_format_identifier %s", vbf_header['data_format_identifier'])
            logging.info("DataFormat block: {0:02X}".format(vbf_header['data_format_identifier']))

            if decompress_block:
                if vbf_header['data_format_identifier'] == 0: # format '0x00':
                    decompr_data = vbf_block_data
                elif vbf_header['data_format_identifier'] == 16: # format '0x10':
                    logging.info("Compression method 1: LZSS")
                    decompr_data = LZSS.decode_barray(vbf_block_data)
                elif vbf_header['data_format_identifier'] == 32: # format '0x20':
                    logging.info("Compression method 2: LZMA")
                    decompr_data = LZMA.decode_barray(vbf_block_data)
                else:
                    logging.warning("Unknown compression format: {0:02X}".format\
                                    (vbf_header['data_format_identifier']))

            logging.debug("Header       CRC16 block_data:  {0:04X}".format(vbf_block['Checksum']))
            if decompress_block:
                logging.debug("Decompressed CRC16 calculation: {0:04X}".format\
                              (SUTE.crc16(decompr_data)))
            else:
                logging.debug("Block not decompress. No compare of CRC16.")
            logging.debug("Length block from header:  {0:08X}".format(vbf_block['Length']))
            if decompress_block:
                logging.debug("Length block decompressed: {0:08X}".format\
                              (len(decompr_data)))
            else:
                logging.debug("Block not decompress. No compare of Block length.")

            logging.info("Compare compress / uncompressed data:")
            logging.info("Compressed: vbf_block_data")
            logging.info("HEX: %s", vbf_block_data.hex())
            logging.info("Uncompressed: decompr_data")
            logging.info("HEX: %s", decompr_data.hex())
            logging.info("\n")

            if (decompress_block and SUTE.crc16(decompr_data) == vbf_block['Checksum'])\
               or not decompress_block:
                # Request Download
                #result, nbl = SE34.request_block_download(can_p, vbf_header, vbf_block)
                logging.info("When transfer: SE34.request_block_download.")
                result = True
                if not result:
                    logging.info("Support SBL, DL block request failed")
                    logging.info("DL block request - vbf_header: %s", vbf_header)
                # Flash blocks to BECM with transfer data service 0x36
                #result = result and SE36.flash_blocks(can_p, vbf_block_data, vbf_block, nbl)
                logging.info("When transfer: SE36.flash_blocks.")
                result = True
                if not result:
                    logging.info("Support SBL, SE36, flash_blocks failed")
                    logging.info("DL block request - vbf_header: %s", vbf_header)
                #Transfer data exit with service 0x37
                #result = result and SE37.transfer_data_exit(can_p)
                logging.info("When transfer: SE37.transfer_data_exit.")
                result = True
                if not result:
                    logging.info("Support SBL, SE37, transfer_data_exit failed")
                    logging.info("DL block request - vbf_header: %s", vbf_header)
            else:
                logging.info("CRC doesn't match after decompression")
                logging.info("Header       CRC16 block_data:  {0:04X}".format\
                                (vbf_block['Checksum']))
                logging.info("Decompressed CRC16 calculation: {0:04X}".format\
                                (SUTE.crc16(decompr_data)))
                logging.info("Header       block length:  {0:08X}".format(vbf_block['Length']))
                logging.info("Decompressed block length: {0:08X}".format(len(decompr_data)))
                result = False
        return result

    def transfer_data_block(self,# pylint: disable=too-many-branches too-many-statements
                            can_p: CanParam, vbf_header: VbfHeader,
                            vbf_data, vbf_offset):
        """
            transfer_data_block
            support function to transfer
            data with given offset and data_format to
            intended destination, given by
            stub, can_send, can_rec, can_nspace

            stepno, purpose:
                used for logging purposes
        """
        result = True
        # Iteration to Download the SBL by blocks
        logging.debug("vbf_offset: %s len(data): %s", vbf_offset, len(vbf_data))
        while vbf_offset < len(vbf_data):
            # Extract data block
            # new offset!
            vbf_offset, vbf_block, vbf_block_data = (
                self.block_data_extract(vbf_data, vbf_offset))

            decompress_block = True
            new_decompress_block =\
                SIO.parameter_adopt_teststep('decompress_block')
            if new_decompress_block != '':
                assert isinstance(new_decompress_block, bool)
                decompress_block = new_decompress_block
            else:
                logging.info("Support_SBL: new_decompress_block is empty. Leave True.")
            logging.info("Support_SBL: decompress_block after YML: %s", decompress_block)

            #decompress data["b_data"] if needed
            logging.debug("vbf_header:  %s", vbf_header)
            logging.debug("data_format_identifier %s", vbf_header['data_format_identifier'])
            logging.debug("DataFormat block: {0:02X}".format(vbf_header['data_format_identifier']))

            if decompress_block:
                if vbf_header['data_format_identifier'] == 0: # format '0x00':
                    decompr_data = vbf_block_data
                elif vbf_header['data_format_identifier'] == 16: # format '0x10':
                    decompr_data = LZSS.decode_barray(vbf_block_data)
                elif vbf_header['data_format_identifier'] == 32: # format '0x20':
                    decompr_data = LZMA.decode_barray(vbf_block_data)
                else:
                    logging.info("Unknown compression format: {0:02X}".format\
                                 (vbf_header['data_format_identifier']))

            logging.debug("Header       CRC16 block_data:  {0:04X}".format(vbf_block['Checksum']))
            if decompress_block:
                logging.debug("Decompressed CRC16 calculation: {0:04X}".format\
                              (SUTE.crc16(decompr_data)))
            else:
                logging.debug("Block not decompress. No compare of CRC16.")
            logging.debug("Length block from header:  {0:08X}".format(vbf_block['Length']))
            if decompress_block:
                logging.debug("Length block decompressed: {0:08X}".format\
                              (len(decompr_data)))
            else:
                logging.debug("Block not decompress. No compare of Block length.")

            if (decompress_block and SUTE.crc16(decompr_data) == vbf_block['Checksum'])\
               or not decompress_block:
                # Request Download
                result, nbl = SE34.request_block_download(can_p, vbf_header, vbf_block)
                if not result:
                    logging.info("Support SBL, DL block request failed")
                    logging.info("DL block request - vbf_header: %s", vbf_header)
                # Flash blocks to BECM with transfer data service 0x36
                result = result and SE36.flash_blocks(can_p, vbf_block_data, vbf_block, nbl)
                if not result:
                    logging.info("Support SBL, SE36, flash_blocks failed")
                    logging.info("DL block request - vbf_header: %s", vbf_header)
                #Transfer data exit with service 0x37
                result = result and SE37.transfer_data_exit(can_p)
                if not result:
                    logging.info("Support SBL, SE37, transfer_data_exit failed")
                    logging.info("DL block request - vbf_header: %s", vbf_header)
            else:
                logging.info("CRC doesn't match after decompression")
                logging.info("Header       CRC16 block_data:  {0:04X}".format\
                                (vbf_block['Checksum']))
                logging.info("Decompressed CRC16 calculation: {0:04X}".format\
                                (SUTE.crc16(decompr_data)))
                logging.info("Header       block length:  {0:08X}".format(vbf_block['Length']))
                logging.info("Decompressed block length: {0:08X}".format(len(decompr_data)))
                result = False
        return result


    def sbl_download_no_check(self, can_p: CanParam, file_n):
        """
        Support Function for flashing Secondary Bootloader SW
        SBL Download
        """
        # Read vbf file for SBL download
        vbf_version, vbf_header, vbf_data, vbf_offset = self.read_vbf_file(file_n)
        #convert vbf header so values can be used directly
        self.vbf_header_convert(vbf_header)
        logging.info("VBF version: %s", vbf_version)

        testresult = self.transfer_data_block(can_p, vbf_header, vbf_data, vbf_offset)
        return testresult, vbf_header


    def sbl_download(self, can_p: CanParam, file_n, stepno=''):
        """
        Support Function for flashing Secondary Bootloader SW
        """

        # Read vbf file for SBL download
        vbf_version, vbf_header, vbf_data, vbf_offset = self.read_vbf_file(file_n)
        #convert vbf header so values can be used directly
        self.vbf_header_convert(vbf_header)
        logging.info("VBF version: %s", vbf_version)

        testresult = self.transfer_data_block(can_p, vbf_header, vbf_data, vbf_offset)
        #Check memory
        testresult = testresult and SE31.check_memory(can_p, vbf_header, stepno)
        return testresult, vbf_header


    def sw_part_download(self, can_p: CanParam, file_n, stepno='',
                         purpose="sw_part_download filename"):
        """
        Software Download
        Support Function for flashing SW Parts
        """
        logging.info("sw_part_download: %s", purpose)
        logging.info("sw_part_download filename: %s", file_n)
        result, vbf_header = self.sw_part_download_no_check(can_p, file_n, stepno)

        # Check memory
        result = result and SE31.check_memory(can_p, vbf_header,
                                              stepno
                                             )
        return result


    # Support Function for flashing SW Parts without Check
    def sw_part_download_no_check(self, can_p: CanParam, file_n, stepno=''):
        """
        Software Download
        """
        #data = dict()

        # Read vbf file for SBL download
        logging.info("sw_part_download_no_check filename: %s", file_n)
        vbf_version, vbf_header, vbf_data, vbf_offset = self.read_vbf_file(file_n)
        #convert vbf header so values can be used directly
        self.vbf_header_convert(vbf_header)
        logging.info("VBF version: %s", vbf_version)

        # Erase Memory
        result = self.flash_erase(can_p, vbf_header, stepno)
        # Iteration to Download the Software by blocks
        result = result and self.transfer_data_block(can_p, vbf_header, vbf_data, vbf_offset)
        return result, vbf_header


    # Support Function for Flashing and activate Secondary Bootloader from Default session
    def sbl_activation_def(self, can_p: CanParam,\
                           sa_keys,\
                           stepno='',\
                           purpose="sbl_activation_default/ext mode"):
        """
        function used for BECM in Default or Extended mode
        sa_keys in SA Gen1: fixed_key='0102030405'
                   SA Gen2: auth_key, proof_key
        """

        # verify RoutineControlRequest is sent for Type 1
        result = SE31.routinecontrol_requestsid_prog_precond(can_p, stepno)

        #result = SE22.read_did_appl_dppn(can_p)
        result = SE22.read_did_pbl_pn(can_p)
        # Change to Programming session
        # done two times: first request doesn't give reply
        # second one gives reply with timings, but not in all versions (issue on BECM?)
        result = SE10.diagnostic_session_control_mode2(can_p)
        result = SE10.diagnostic_session_control_mode2(can_p)

        # Verify Session changed
        SE22.read_did_f186(can_p, dsession=b'\x02')
        result = result and self.sbl_activation_prog(can_p, sa_keys, stepno, purpose)
        return result


    # Support Function for Flashing and activate Secondary Bootloader from Programming session
    def sbl_activation_prog(self, can_p: CanParam,\
                            sa_keys,\
                            stepno='',\
                            purpose="sbl_activation_prog"):
        """
        Function used for BECM in forced Programming mode
        sa_keys in SA Gen1: fixed_key='0102030405'
                   SA Gen2: auth_key, proof_key
        """
        result = True

        ecu_mode = SE22.get_ecu_mode(can_p)
        if ecu_mode == 'PBL':
            # Security Access Request SID
            result = result and SE27.activate_security_access_fixedkey(can_p,
                                                                       sa_keys,
                                                                       stepno, purpose)

            # SBL Download
            tresult, vbf_sbl_header = self.sbl_download(can_p, self._sbl, stepno)
            result = result and tresult

            # Activate SBL
            result = result and self.activate_sbl(can_p, vbf_sbl_header, stepno)
        elif ecu_mode == 'SBL':
            logging.info("SBL already active. Don't take any actions")
        elif ecu_mode in ('DEF', 'EXT'):
            logging.warning("ECU does not seem to be in PROG mode: %s", ecu_mode)
        else:
            logging.warning("sbl_activation: unknown ECU mode: %s", ecu_mode)
            logging.info("sbl_activation: use PBL while EDA0 not implemented in PBL/SBL")
            ### remove when EDA0 implemented in MEP2
            # use ecu_mode == 'PBL' as default while EDA0 not implemented in MEP2 SA_GEN2
            # Security Access Request SID
            result = result and SE27.activate_security_access_fixedkey(can_p,
                                                                       sa_keys,
                                                                       stepno, purpose)

            # SBL Download
            tresult, vbf_sbl_header = self.sbl_download(can_p, self._sbl, stepno)
            result = result and tresult

            # Activate SBL
            result = result and self.activate_sbl(can_p, vbf_sbl_header, stepno)
            #result = False
        return result


    # Support Function to select Support functions to use for activating SBL based on actual mode
    def sbl_activation(self, can_p: CanParam,\
                       sa_keys, stepno='', purpose=""):
        """
        Function used to activate the Secondary Bootloader
        """
        result = True

        # verify session
        ecu_mode = SE22.get_ecu_mode(can_p)
        if ecu_mode in ('DEF', 'EXT'):
            result = self.sbl_activation_def(can_p, sa_keys, stepno, purpose)
        #elif '62F18602' in rec_messages:
        elif ecu_mode == 'PBL':
            result = self.sbl_activation_prog(can_p, sa_keys, stepno, purpose)
        elif ecu_mode == 'SBL':
            logging.info("sbl_activation: SBL already active")
        else:
            logging.info("sbl_activation: unknown ECU mode")
            logging.info("sbl_activation: use PBL while EDA0 not implemented in PBL/SBL")
            ### remove when EDA0 implemented in MEP2
            # use ecu_mode == 'PBL' as default while EDA0 not implemented in MEP2 SA_GEN2
            result = self.sbl_activation_prog(can_p, sa_keys, stepno, purpose)
            #result = False
        time.sleep(0.1)
        return result

    # Support Function to select Support functions to use for activating SBL based on actual mode
    def sbl_dl_activation(self, can_p: CanParam, sa_keys, stepno='', purpose=""):
        """
        Function used to download and activate the Secondary Bootloader

        function allows to change sa_keys via YML parameter.
        This is done by making a copy of sa_keys to not change those.
        (would happen as sa_keys is dict)
        """
        sa_keys_new = sa_keys
        sa_keys_new = SIO.parameter_adopt_teststep(sa_keys_new)

        result = self.sbl_activation(can_p, sa_keys_new, stepno, purpose)
        return result


#------------------------------Support Support SWDL Functions-------------------------------

    @classmethod
    def pp_decode_routine_complete_compatible(cls, message):
        """
        Support function for Extracting Completed and compatible Routine Control Response
        """
        mess_len = len(message)
        if mess_len == 0:
            val_c = "PP_Decode_Routine_Control_response: missing message"
        else:
            pos = message.find('0205')
            res = message[pos+6:pos+16]
            val = "{:040b}".format(int(res, 16))
            if val[38] == '0':
                val_ca = 'Compatible'
            elif val[38] == '1':
                val_ca = 'Not Compatible'
            else:
                val_ca = 'Wrong Decoding'
            if val[39] == '0':
                val_cl = 'Complete, '
            elif val[39] == '1':
                val_cl = 'Not Complete, '
            else:
                val_cl = 'Wrong Decoding'
            val_c = val_cl + val_ca
        return val_c

    @classmethod
    def pp_decode_routine_check_memory(cls, message):
        """
        Support function for Extracting Check Memory Routine Control Response
        """
        mess_len = len(message)
        if mess_len == 0:
            val_c = "PP_Decode_Routine_Control_response: missing message"
        else:
            pos = message.find('0212')
            res = message[pos+7:pos+8]
            switcher = {
                '0' or '': 'The verification is passed',
                '1': 'The signed data could not be authenticated',
                '2': 'The public key integrity check failed',
                '3': 'Invalid format of length of th eVerification Block Table',
                '4': '', # The address of hash values of the downloaded data blocks
                         # does not match the expected values''',
                '5': 'The blank check failed',
                '6': 'No data downloaded at all, nothing to verify',
                '7': 'Read error during hash calculation over memory content',
                '8': 'ESS content is not valid',
                '9': 'Additional processor failed verification',
                'A': 'Error storing vaildity status information',
                'B': 'Certioficate verification failed',
                'C': 'User definable',
            }
            val_c = switcher.get(res, 'Wrong Decoding')
        return val_c

    def check_complete_compatible_routine(self, can_p: CanParam, stepno):
        """
        Support function for Routine Complete & Compatible
        """

        result = SE31.routinecontrol_requestsid_complete_compatible(can_p, stepno)
        result = result and (
            self.pp_decode_routine_complete_compatible(SC.can_messages[can_p["receive"]][0][2]))
        logging.info(SC.can_messages[can_p["receive"]][0][2])
        return result

    @classmethod
    def vbf_header_convert(cls, header):
        """
        take 'header' as read from vbf file and convert values
        so they get usable directly in python
        """
        logging.debug("vbf_header_convert:")
        logging.debug("Header before convert: %s", header)
        for keys in header:
            #elements contains a list of elements
            #convert into a python list
            if header[keys][0] == '{' and header[keys][-1] == '}':
                #convert multiple values into python list
                cvert = header[keys].replace('{', '[')
                cvert = cvert.replace('}', ']')
                header[keys] = cvert

            try:
                if keys != 'sw_part_type':
                    header[keys] = eval(header[keys]) # pylint: disable=eval-used
            except: # pylint: disable=bare-except
                traceback.print_exc()
                logging.info("Oops! Value in header that can't be evaluated")
        logging.debug("Header after convert: %s", header)

    @classmethod
    def vbf_cm_filter(cls, cm_str):
        """
        vbf_cm_filter
        filter out comment from string
        return: input string with comments removed
        """
        #logging.info("look for comments starting with '//': ")
        str_ret = cm_str
        comm = cm_str.find(b'//')
        while comm != -1:
            #comm = cm_str.find(b'//')
            #if not comm == -1:
            #logging.info("position comment: %s", comm)
            #logging.info("found single line comment. Remove upp till cr/eol")
            #comment line ends with LF (REQ 64698)
            comm_end = cm_str.find(b'\n', comm)
            str_ret = cm_str[0:comm] + cm_str[comm_end:]
            cm_str = str_ret
            comm = cm_str.find(b'//')
            #else:
            #    logging.info("nothing found, do nothing")
            #    str_ret = cm_str
        #logging.info("string to return: %s", str_ret)
        return str_ret

    @classmethod
    def vbf_ws_filtered(cls, p_str):
        """
        remove whitespace chars as defined for vbf2.6 in str
        """
        # [WS/CM]identifier[WS/CM]=[WS/CM]IdentifierValue[WS/CM];[WS/CM]
        # WS chars in vbf 2.6
        w_space = b'\x09\x0A\x0B\x0C\x0D\x20'
        #logging.debug("vbf_ws_filter - in %s ", p_str)
        for bchar in w_space:
            #logging.debug("bchar to check: %s", bchar)
            #p_str = p_str.replace(bchar, b'')
            p_str = p_str.replace(bytes([bchar]), b'')
        #logging.info("vbf_ws_filter - out %s", p_str)
        return p_str

    @classmethod
    def vbf_parse(cls, p_str):
        """
        parse line for key and argument
        delimiters: '=' for key/arg
                    ';' for end of arg
        """
        logging.debug("vbf_parse to parse: %s", p_str)
        vbf_key = p_str[0: p_str.find(b'=')]
        vbf_nam = p_str[1+p_str.find(b'='):p_str.find(b';')]
        logging.debug("key found: %s", cls.vbf_ws_filtered(vbf_key))
        logging.debug("nam found: %s", cls.vbf_ws_filtered(vbf_nam))
        return (cls.vbf_ws_filtered(vbf_key), cls.vbf_ws_filtered(vbf_nam))

    @classmethod
    def read_vbf_header_filtered(cls, data, start_pos):
        """
        starts reading data from start_pos
        continous reading until next closing bracker cbrack
        return: data_filtererd: data until next closing bracket, without comments
                start_pos: position in data reached
        """
        data_filtered = b''
        next_cbrack = data.find(b'}', start_pos)

        # C++ style comment in header data before next closing bracket
        next_comm_line = data.find(b'//', start_pos, next_cbrack +1)

        #filter out comment(s),
        while not next_comm_line == -1:
            #read until comment:
            data_filtered = data_filtered + data[start_pos:next_comm_line]
            start_pos = next_comm_line + 2

            #now filter out comment, set new start_pos for searching
            next_comm_stop = data.find(b'\n', next_comm_line)
            start_pos = next_comm_stop +1
            #look for next semicolon / cbracket after comment / comment line
            #next_scol = data.find(b';', next_comm_stop +1)
            next_cbrack = data.find(b'}', next_comm_stop +1)
            next_comm_line = data.find(b'//', start_pos, next_cbrack +1)

        #no more comment lines, add data until cbrack
        data_filtered = data_filtered + data[start_pos:next_cbrack +1]
        start_pos = next_cbrack +1

        #look if more comments in buffer
        next_comm_line = data.find(b'//', start_pos +1, next_cbrack)
        return data_filtered, start_pos

    @classmethod
    def read_vbf_file(cls, f_path_name):
        # Disable too-many-locals violations in this function.
        # Should be rewritten, maybe using regexp
        # pylint: disable=too-many-locals
        """
        Read and decode vbf files for Software Parts
        """
        logging.info("File to read: %s", f_path_name)
        # read to EOF:
        data = SUTE.read_f(f_path_name)
        vers_pos = data.find(b'vbf_version')
        if not vers_pos == 0:
            logging.info("Warning: version not at expected position: %s", vers_pos)
        #logging.debug("Version vers_pos: %s", vers_pos)

        # look for first semicolon
        semi_pos = data.find(b';')
        if not semi_pos == -1:
            semi_pos += 1
        logging.debug("to filter: %s", data[vers_pos:semi_pos])

        # remove CM in string to parse
        # if no semicolon contained take semicolon in file
        str_cm_filtered = cls.vbf_cm_filter(data[vers_pos:semi_pos])
        logging.debug("str_cm_filtered: %s", str_cm_filtered)
        while not str_cm_filtered.find(b';'):
            semi_pos = data.find(b';', semi_pos)
            str_cm_filtered = cls.vbf_cm_filter(data[vers_pos:semi_pos])

        v_key, v_arg = cls.vbf_parse(str_cm_filtered)
        #logging.debug("VBF Version read: %s = %s", v_key.decode('utf-8'), v_arg.decode('utf-8'))
        version = v_arg.decode('utf-8')

        logging.debug("Now starting to read Header")
        #Start to read header data
        #store all key, arg in dict
        header: VbfHeader = {}
        head_pos = data.find(b'header', semi_pos)
        logging.debug("Header head_pos: %s", head_pos)

        head_pos = data.find(b'{', head_pos) + 1

        # header data without comments, position where to continue reading
        data_filtered, head_pos = cls.read_vbf_header_filtered(data, head_pos)

        #only cbrack in buffer: header completely read
        while not (data_filtered.find(b'}') != -1 and data_filtered.find(b'=') == -1):

        #Read on until next keyword / data pair
            while data_filtered.find(b';') == -1:
                #logging.debug("No ';' found anymore, read further.")
                #logging.debug("Data read: %s %s", data.find(b'}', next_cbrack+1))

                #fill up data_filtered
                data_filtered2, head_pos = cls.read_vbf_header_filtered(data, head_pos)
                data_filtered = data_filtered + data_filtered2

            # Now I should have next keyword read
            # filter away white spaces
            str_filtered = cls.vbf_ws_filtered(data_filtered)
            logging.debug("expr WS filtered: %s", str_filtered)
            v_key, v_arg = cls.vbf_parse(str_filtered)
            header[v_key.decode('utf-8')] = v_arg.decode('utf-8')

            data_filtered = data_filtered[data_filtered.find(b';')+1:]
        # header read now, start data
        data_start = head_pos
        logging.info("vbf_version: %s", version)
        logging.info('Header: %s', header)
        logging.info("Data_Start: %s", data_start)

        ### optional to add:
        ### check for not allowed keywords in header

        return version, header, data, data_start

    @classmethod
    def flash_erase(cls, can_p: CanParam, vbf_header, stepno):
        # Don't have a suitable object for these arguments, need to investigate
        # pylint: disable=too-many-arguments
        """
        Support function for Routine Flash Erase
        """
        result = SE31.routinecontrol_requestsid_flash_erase(can_p, vbf_header, stepno)
        logging.info("SSBL: flash_erase requestsid, result: %s", result)
        logging.info("SSBL: flash_erase EraseMemory, result: %s", result)
        return result

    def block_data_extract(self, vbf_data, vbf_offset):
        """
        Extraction of block data from vbf file
        See Volvo Document 31808832 Rev 015
        Chapter 6.3.3 REQPROD 64727 Data section structure
        """
        vbf_block: VbfBlock = dict()
        #Chapter 6.3.3 REQPROD 64727 Data section structure
        #   4-byte start address, physical addr in ECU memory, range 0x00000000 to 0xFFFFFFFF
        vbf_block['StartAddress'] = int.from_bytes(vbf_data[vbf_offset: vbf_offset + 4], 'big')
        vbf_offset += 4
        logging.debug("block_Startaddress:              {0:08X}".format(vbf_block['StartAddress']))
        #   4-byte length, number of data bytes in block, range 0x00000001 to 0xFFFFFFFF
        #   If data compression used: compressed length
        vbf_block['Length'] = int.from_bytes(vbf_data[vbf_offset: vbf_offset + 4], 'big')
        vbf_offset += 4
        logging.debug("block_data_extract - vbf_block('Length') : {0:08X}".format\
                        (vbf_block['Length']))
        vbf_block_data = vbf_data[vbf_offset : vbf_offset + vbf_block['Length']]
        vbf_offset += vbf_block['Length']
        #   2-byte checksum of data block (excluding Start addr and Length), range 0x0000 to 0xFFFF
        vbf_block['Checksum'] = int.from_bytes(vbf_data[vbf_offset: vbf_offset + 2], 'big')
        if self._debug:
            logging.info("CRC16 in blockdata              {0:04X}".format(vbf_block['Checksum']))
        vbf_offset += 2
        return vbf_offset, vbf_block, vbf_block_data

    @staticmethod
    def crc_calculation(vbf_offset, vbf_block, vbf_block_data):
        """
        crc calculation for each block
        """
        logging.debug("CRC calculation - offset:     {0:08X}".format(vbf_offset))
        logging.debug("CRC calculation - block_data: %s", vbf_block_data)
        logging.debug("CRC calculation - block_addr: {0:08X}".format(vbf_block('StartAddress')))
        logging.debug("CRC calculation - block_len:  {0:04X}".format(vbf_block('Length')))
        vbf_offset += 2
        logging.debug("CRC calculation CRC16: {0:04X}".format(SUTE.crc16(vbf_block_data)))
        crc_res = 'ok'
        return "Block adr: 0x%X length: 0x%X crc %s" % (vbf_block('StartAddress'),\
               vbf_block('Length'), crc_res)

    @classmethod
    def activate_sbl(cls, can_p: CanParam, vbf_sbl_header, stepno,\
                     purpose="RoutineControl activate_sbl"):
        """
        Support function for Routine Control Activate Secondary Bootloader
        """
        # In VBF sbl header call was stored as hex, Python converts that into int.
        # It has to be converted to bytes to be used as payload
        call = vbf_sbl_header['call'].to_bytes((vbf_sbl_header['call'].bit_length()+7) // 8, 'big')
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",\
                                             b'\x03\x01' + call, b'\x01'),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : purpose,\
                             "timeout" : 2,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        testresult = SUTE.teststep(can_p, cpay, etp)
        logging.info("support_SBL, activate_sbl: RC ReqSID 0301 %s sent", call)
        logging.info("support_SBL, activate_sbl: Decode RC response")
        logging.info("support_SBL, activate_sbl: received frames %s",\
                     SC.can_frames[can_p["receive"]])
        logging.info("support_SBL, activate_sbl: received messages %s",\
                     SC.can_messages[can_p["receive"]])
        testresult = testresult and (
            SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
                                                    'Type1,Completed'))
        return testresult
