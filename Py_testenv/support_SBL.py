# project:  ODTB2 testenvironment using SignalBroker
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-11
# version:  0.1

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

"""The Python implementation of the gRPC route guide client."""

import time
import logging
import sys
import glob
from typing import Dict

from support_carcom import SupportCARCOM
from support_can import SupportCAN, CanMFParam, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_sec_acc import SupportSecurityAccess
from support_LZSS import LzssEncoder
from support_service10 import SupportService10
from support_service22 import SupportService22
from support_service31 import SupportService31
from support_service34 import SupportService34
from support_service36 import SupportService36
from support_service37 import SupportService37
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSA = SupportSecurityAccess()
LZSS = LzssEncoder()

SE10 = SupportService10()
SE22 = SupportService22()
SE31 = SupportService31()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


class VbfBlockFormat(Dict): # pylint: disable=inherit-non-class
    """
        Parameters used in VBF blocks
    """
    offset: int
    data: int
    data_format: bytes
    #addr: int
    len: int
    b_addr: int
    b_len: int
    b_data: bytes


    @classmethod
    def vbf_block_init(cls, block):
        """
            init of VbfBlockFormat with empty values
        """
        block['offset'] = 0
        block['data'] = 0
        block['data_format'] = b''
        #block['addr'] = 0
        block['len'] = 0
        block['b_addr'] = 0
        block['b_len'] = 0
        block['b_data'] = b''


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
        print("SBL: ", self._sbl)
        print("ESS: ", self._ess)
        print("DF:  ", self._df)


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


    def read_vbf_param(self):
        """
        read filenames used for transer as args to testscript
        """
        # read arguments for files to DL:
        f_sbl = ''
        f_ess = ''
        f_df = []
        for f_name in sys.argv:
            if not f_name.find('.vbf') == -1:
                print("Filename to DL: ", f_name)
                if not f_name.find('sbl') == -1:
                    f_sbl = f_name
                elif not f_name.find('ess') == -1:
                    f_ess = f_name
                else:
                    f_df.append(f_name)
        self.__init__(f_sbl, f_ess, f_df)
        self.show_filenames()
        time.sleep(10)


    def set_vbf_default_param(self):
        """
        read default filenames used for transer when no args were given
        """
        f_sbl = ''
        f_ess = ''
        f_df = []
        for f_name in glob.glob("./VBF/*.vbf"):
            if not f_name.find('.vbf') == -1:
                print("Filename to DL: ", f_name)
                if not f_name.find('sbl') == -1:
                    f_sbl = f_name
                elif not f_name.find('ess') == -1:
                    f_ess = f_name
                else:
                    f_df.append(f_name)
        self.__init__(f_sbl, f_ess, f_df)
        self.show_filenames()
        time.sleep(10)

    def get_vbf_files(self):
        """
        read filenames used for transfer to ECU
        """
        print("Length sys.argv: ", len(sys.argv))
        if len(sys.argv) != 1:
            self.read_vbf_param()
        else:
            self.set_vbf_default_param()


    #def transfer_data_block(self, data: VbfBlockFormat, can_p: CanParam, step_no, purpose):
    def transfer_data_block(self, data: VbfBlockFormat, can_p: CanParam):
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
        if self._debug:
            print("offset: ", data["offset"], "len(data): ", len(data["data"]))
        while data["offset"] < len(data["data"]):
            # Extract data block
            # new offset!
            data["offset"], data["b_data"], data["b_addr"], data["b_len"], block_crc16 = (
                self.block_data_extract(data["offset"], data["data"]))

            #print("FileHeader   CRC calculation CRC16: {0:04X}".format(SUTE.crc16(data["b_data"])))

            #decompress data["b_data"] if needed
            if self._debug:
                print("DataFormat block: ", data["data_format"].hex())
            if data["data_format"].hex() == '00':
                decompr_data = data["b_data"]
            elif data["data_format"].hex() == '10':
                decompr_data = b''
                decompr_data = LZSS.decode_barray(data["b_data"])
            else:
                print("Unknown compression format:", data["data_format"].hex())

            if self._debug:
                print("Header       CRC16 block_data:  {0:04X}".format(block_crc16))
                print("Decompressed CRC16 calculation: {0:04X}".format(SUTE.crc16(decompr_data)))
                print("Length block from header:  {0:08X}".format(data["b_len"]))
                print("Length block decompressed: {0:08X}".format(len(decompr_data)))

            if SUTE.crc16(decompr_data) == block_crc16:
                # Request Download
                #result, nbl = SE34.request_block_download(can_p, data, step_no, purpose)
                result, nbl = SE34.request_block_download(can_p, data)
                #result = result and resultt
                # Flash blocks to BECM with transfer data service 0x36
                #result = result and SE36.flash_blocks(nbl, can_p, data, step_no, purpose)
                result = result and SE36.flash_blocks(nbl, can_p, data)
                #Transfer data exit with service 0x37
                #result = result and SE37.transfer_data_exit(can_p, step_no, purpose)
                result = result and SE37.transfer_data_exit(can_p)
            else:
                print("CRC doesn't match after decompression")
                print("Header       CRC16 block_data:  {0:04X}".format(block_crc16))
                print("Decompressed CRC16 calculation: {0:04X}".format(SUTE.crc16(decompr_data)))
                print("Header       block length: {0:08X}".format(data["b_len"]))
                print("Decompressed block length: {0:08X}".format(len(decompr_data)))
                result = False
        return result


    # Support Function for flashing Secondary Bootloader SW
    #def sbl_download_no_check(self, can_p: CanParam, file_n, step_no,\
    #                          purpose="SBL Download no check"):
    def sbl_download_no_check(self, can_p: CanParam, file_n):
        """
        SBL Download
        """
        testresult = True

        data = dict()

        # Read vbf file for SBL download
        data["offset"], data["data"], _, call, data["data_format"] = self.read_vbf_file_sbl(file_n)

        #testresult = testresult and self.transfer_data_block(data, can_p, step_no, purpose)
        testresult = testresult and self.transfer_data_block(data, can_p)
        return testresult, call


    # Support Function for flashing Secondary Bootloader SW
    def sbl_download(self, can_p: CanParam, file_n, stepno='',\
                     purpose="SBL Download transfer block"):
        """
        Support Function for flashing Secondary Bootloader SW
        """
        data = dict()

        # Read vbf file for SBL download
        data["offset"], data["data"], sw_signature, call, data["data_format"] =\
            self.read_vbf_file_sbl(file_n)

        #testresult = self.transfer_data_block(data, can_p, stepno, purpose)
        testresult = self.transfer_data_block(data, can_p)

        #Check memory
        #testresult = testresult and self.check_memory(can_param, step_no, purpose, sw_signature)
        #testresult = testresult and self.transfer_data_block(data, can_p, stepno, purpose)
        testresult = testresult and self.transfer_data_block(data, can_p)
        #Check memory
        testresult = testresult and self.check_memory(can_p, sw_signature, stepno, purpose)
        return testresult, call


    # Support Function for flashing SW Parts

    def sw_part_download(self, can_p: CanParam, file_n, stepno='',
                         purpose="sw_part_download filename"):
        """
        Software Download
        """
        print("sw_part_download filename: ", file_n)
        #result, sw_signature =\
        #    self.sw_part_download_no_check(can_p, file_n, stepno, purpose)
        result, sw_signature = self.sw_part_download_no_check(can_p, file_n, stepno)

        # Check memory
        result = result and self.check_memory(can_p, sw_signature,
                                              stepno, purpose
                                             )
        return result


    # Support Function for flashing SW Parts without Check
    #def sw_part_download_no_check(self, can_p: CanParam, file_n, stepno='',\
    #                              purpose="sw_part_download_no_check"):
    def sw_part_download_no_check(self, can_p: CanParam, file_n, stepno=''):
        """
        Software Download
        """
        data = dict()

        # Read vbf file for SBL download
        print("sw_part_download_no_check filename: ", file_n)
        data["offset"], off, data["data"], sw_signature,\
            data["data_format"], erase = self.read_vbf_file(file_n)

        # Erase Memory
        result = self.flash_erase(can_p, erase, data["data"], off, stepno)
        # Iteration to Download the Software by blocks

        #result = result and self.transfer_data_block(data, can_p, stepno, purpose)
        result = result and self.transfer_data_block(data, can_p)
        return result, sw_signature


    # Support Function for Flashing and activate Secondary Bootloader from Default session
    def sbl_activation_def(self, can_p: CanParam, stepno='',\
                           purpose="sbl_activation_default/ext mode"):
        """
        function used for BECM in Default or Extended mode
        """

        # verify RoutineControlRequest is sent for Type 1
        result = SE31.routinecontrol_requestsid_prog_precond(can_p, stepno)

        # Change to Programming session
        # done two times: first request doesn't give reply
        # second one gives reply with timings, but not in all versions (issue on BECM?)
        result = SE10.diagnostic_session_control_mode2(can_p)
        result = SE10.diagnostic_session_control_mode2(can_p)

        # Verify Session changed
        SE22.read_did_f186(can_p, dsession=b'\x02')
        result = result and self.sbl_activation_prog(can_p, stepno, purpose)
        return result


    # Support Function for Flashing and activate Secondary Bootloader from Programming session
    def sbl_activation_prog(self, can_p: CanParam, stepno='',\
                            purpose="sbl_activation_prog"):
        """
        Function used for BECM in forced Programming mode
        """
        # Security Access Request SID
        result = SSA.activation_security_access(can_p, stepno, purpose)

        # SBL Download
        tresult, call = self.sbl_download(can_p, self._sbl, stepno)
        result = result and tresult

        # Activate SBL
        result = result and self.activate_sbl(can_p, call, stepno)
        return result


    # Support Function to select Support functions to use for activating SBL based on actual mode
    def sbl_activation(self, can_p: CanParam, stepno='', purpose=""):
        """
        Function used to activate the Secondary Bootloader
        """
        testresult = True

        # verify session
        SE22.read_did_f186(can_p, dsession=b'')
        logging.info(SC.can_messages[can_p["receive"]])

        if SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18601')\
            or SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18603'):
            testresult = self.sbl_activation_def(can_p, stepno, purpose)
        elif SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18602'):
            testresult = self.sbl_activation_prog(can_p, stepno, purpose)
        else:
            logging.info("error message: %s\n", SC.can_messages[can_p["receive"]])
        time.sleep(0.1)
        return testresult


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
            val = "{0:40b}".format(int(res, 16))
            if val[38] == '0' or ' ':
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

        # Parameters for FrameControl FC
        can_mf_param: CanMFParam = {
            'block_size' : 0,
            'separation_time' : 0,
            'frame_control_delay' : 0, #no wait
            'frame_control_flag' : 48, #continue send
            'frame_control_auto' : True
            }
        SC.change_mf_fc(can_p["send"], can_mf_param)

        result = SE31.routinecontrol_requestsid_complete_compatible(can_p, stepno)
        result = result and (
            self.pp_decode_routine_complete_compatible(SC.can_messages[can_p["receive"]][0][2]))
        logging.info(SC.can_messages[can_p["receive"]][0][2])
        return result


    @classmethod
    def read_vbf_file_sbl(cls, f_path_name):
        """
        Read and decode vbf files for Secondary Bootloader
        """
        print("File to read: ", f_path_name)
        data = SUTE.read_f(f_path_name)
        find = data.find
        header_len = find(b'\x3B\x0D\x0A\x7D') + 4
        #print ('Header length: 0x%04X' % header_len)
        if header_len < 100:
            logging.info('Unknown format')
            sys.exit() #quit(-1)

        off1 = find(b'sw_signature_dev = 0x') + 21
        end = find(b';\r\n}')
        #print(data[off1:end])
        sw_signature = bytes.fromhex(str(data[off1 : end])[2:-1])
        #print(sw_signature)
        off2 = find(b'call = 0x') + 9
        call = bytes.fromhex(str(data[off2 : off2 + 8])[2:-1])
        offset = header_len
        #print data format
        off3 = find(b'data_format_identifier = 0x') + 27
        data_format = bytes.fromhex(str(data[off3 : off3+2])[2:-1])
        logging.info("VBF_data_format %s", str(data_format))
        #print(SUTE.CRC32_from_file(data[offset:len(data)]))
        block_address = int.from_bytes(data[offset: offset + 4], 'big')
        logging.info("VBF_block_adress {0:08X}".format(block_address))
        return offset, data, sw_signature, call, data_format


    @classmethod
    def read_vbf_file(cls, f_path_name):
        # Disable too-many-locals violations in this function.
        # Should be rewritten, maybe using regexp
        # pylint: disable=too-many-locals
        """
        Read and decode vbf files for Software Parts
        """
        print("File to read: ", f_path_name)
        data = SUTE.read_f(f_path_name)
        find = data.find
        header_len = find(b'\x3B\x0D\x0A\x7D') + 4

        off = data.find(b'erase = ') + 12
        memory_add = SUTE.pp_string_to_bytes(str(data[off : off + 8])[2:-1], 4)
        off += 12
        memory_size = SUTE.pp_string_to_bytes(str(data[off : off + 8])[2:-1], 4)
        off += 8
        off1 = data.find(b'sw_signature_dev = 0x') + 21
        off2 = data.find(b'data_format_identifier = 0x') + 27
        end = data.find(b';\r\n}')
        logging.info(data[off1:end])
        sw_signature = bytes.fromhex(str(data[off1 : end])[2:-1])
        data_format = bytes.fromhex(str(data[off2 : off2+2])[2:-1])
        logging.info(sw_signature)
        offset = header_len
        logging.info(SUTE.crc32_from_file(data[offset:len(data)]))
        erase = memory_add + memory_size
        return offset, off, data, sw_signature, data_format, erase


    @classmethod
    def flash_erase(cls, can_p: CanParam, erase, data, off, stepno):
        # Don't have a suitable object for these arguments, need to investigate
        # pylint: disable=too-many-arguments
        """
        Support function for Routine Flash Erase
        """
        # Parameters for FrameControl FC
        can_mf_param: CanMFParam = {
            'block_size' : 0,
            'separation_time' : 0,
            'frame_control_delay' : 0, #no wait
            'frame_control_flag' : 48, #continue send
            'frame_control_auto' : False
            }
        SC.change_mf_fc(can_p["send"], can_mf_param)
        time.sleep(1)

        result = SE31.routinecontrol_requestsid_flash_erase(can_p, erase, stepno)

        # Erase Memory
        while data[off + 24 : off + 25] == b'x':
            off += 25
            memory_add = SUTE.pp_string_to_bytes(str(data[off : off + 8])[2:-1], 4)
            off += 12
            memory_size = SUTE.pp_string_to_bytes(str(data[off : off + 8])[2:-1], 4)
            off += 8
            erase = memory_add + memory_size

            SC.change_mf_fc(can_p["send"], can_mf_param)
            time.sleep(1)
            result = result and SE31.routinecontrol_requestsid_flash_erase(can_p, erase, stepno)
        return result


    def block_data_extract(self, offset, data):
        """
        Extraction of block data from vbf file
        """
        block_addr = int.from_bytes(data[offset: offset + 4], 'big')
        offset += 4
        if self._debug:
            print("block_Startaddress:              {0:08X}".format(block_addr))
        block_len = int.from_bytes(data[offset: offset + 4], 'big')
        offset += 4
        if self._debug:
            print("block_data_extract - block_len : {0:08X}".format(block_len))
        block_data = data[offset : offset + block_len]
        offset += block_len
        crc16 = int.from_bytes(data[offset: offset + 2], 'big')
        if self._debug:
            print("CRC16 in blockdata              {0:04X}".format(crc16))
        offset += 2
        return offset, block_data, block_addr, block_len, crc16


    #crc calculation for each block
    def crc_calculation(self, offset, block_data, block_addr, block_len):
        """
        crc calculation for each block
        """
        if self._debug:
            print("CRC calculation - offset:     {0:08X}".format(offset))
            print("CRC calculation - block_data:        ", block_data)
            print("CRC calculation - block_addr: {0:08X}".format(block_addr))
            print("CRC calculation - block_len:  {0:04X}".format(block_len))
        offset += 2

        if self._debug:
            print("CRC calculation CRC16: {0:04X}".format(SUTE.crc16(block_data)))
        crc_res = 'ok'
        return "Block adr: 0x%X length: 0x%X crc %s" % (block_addr, block_len, crc_res)

    # Moved?
    # def request_block_download(self, can_param, step_no, purpose, data_param):
        # """
        # Support function for Request Download

        # Replaced:
        # can_param["stub"] = stub
        # can_param["can_nspace"] = can_nspace
        # can_param["can_send"] = can_send
        # can_param["can_rec"] = can_rec''
        # data_param["block_addr_by"] = block_addr_by
        # data_param["block_len_by"] = block_len_by
        # data_param["data_format"] = data_format
        # """
        # #testresult = True
        # # Parameters for FrameControl FC

        # can_mf_param: CanMFParam = {
            # 'block_size' : 0,
            # 'separation_time' : 0,
            # 'frame_control_delay' : 0, #no wait
            # 'frame_control_flag' : 48, #continue send
            # 'frame_control_auto' : False
            # }
        # SC.change_mf_fc(can_param["can_send"], can_mf_param)

        # ts_param = {"stub" : can_param["stub"],
                    # "payload" : b'\x34' + data_param["data_format"] + b'\x44'+\
                    # data_param["block_addr_by"] + data_param["block_len_by"],
                    # "extra" : '',
                    # "can_send" : can_param["can_send"],
                    # "can_rec"  : can_param["can_rec"],
                    # "can_nspace" : can_param["can_nspace"]
                   # }
        # extra_param = {"purpose" : purpose,
                       # "timeout" : 0.05,
                       # "min_no_messages" : -1,
                       # "max_no_messages" : -1
                      # }

        # testresult = SUTE.teststep(ts_param, step_no, extra_param)
        # testresult = testresult and SUTE.test_message(SC.can_messages[can_param["can_rec"]], '74')
        # nbl = SUTE.pp_string_to_bytes(SC.can_frames[can_param["can_rec"]][0][2][6:10], 4)
        # if self._debug:
            # print("NBL: {}".format(nbl))
        # nbl = int.from_bytes(nbl, 'big')
        # return testresult, nbl


    # @classmethod
    # def flash_blocks(cls, can_param, step_no, purpose, data_param):
        # """
        # Support function for Transfer Data

        # Replaced:
        # can_param["stub"] = stub
        # can_param["can_nspace"] = can_nspace
        # can_param["can_send"] = can_send
        # can_param["can_rec"] = can_rec
        # data_param["block_len"] = block_len
        # data_param["block_data"] = block_data
        # data_param["nbl"] = nbl
        # """

        # pad = 0
        # for i in range(int(data_param["block_len"]/(data_param["nbl"]-2))+1):

            # pad = (data_param["nbl"]-2)*i
            # i += 1
            # ibyte = bytes([i])
            # # Parameters for FrameControl FC

            # can_mf_param: CanMFParam = {
                # 'block_size' : 0,
                # 'separation_time' : 0,
                # 'frame_control_delay' : 0, #no wait
                # 'frame_control_flag' : 48, #continue send
                # 'frame_control_auto' : False
                # }
            # SC.change_mf_fc(can_param["can_send"], can_mf_param)

            # ts_param = {"stub" : can_param["stub"],
                        # "m_send" : b'\x36' + ibyte + data_param["block_data"][pad:pad +\
                            # data_param["nbl"]-2],
                        # "mr_extra" : '',
                        # "can_send" : can_param["can_send"],
                        # "can_rec"  : can_param["can_rec"],
                        # "can_nspace" : can_param["can_nspace"]
                       # }
            # extra_param = {"purpose" : purpose,
                           # "timeout" : 0.02,
                           # "min_no_messages" : -1,
                           # "max_no_messages" : -1
                          # }

            # testresult = SUTE.teststep(ts_param, step_no, extra_param)
            # testresult = testresult and SUTE.test_message(SC.can_messages[can_param["can_rec"]],
                                                          # '76')
        # return testresult


    # @classmethod
    # def transfer_data_exit(cls, can_param, step_no, purpose):
        # """
        # Support function for Request Transfer Exit

        # Replaced:
        # can_param["stub"] = stub
        # can_param["can_nspace"] = can_nspace
        # can_param["can_send"] = can_send
        # can_param["can_rec"] = can_rec
        # """
        # ts_param = {"stub" : can_param["stub"],
                    # "m_send" : b'\x37',
                    # "mr_extra" : '',
                    # "can_send" : can_param["can_send"],
                    # "can_rec"  : can_param["can_rec"],
                    # "can_nspace" : can_param["can_nspace"]
                   # }
        # extra_param = {"purpose" : purpose,
                       # "timeout" : 0.2,
                       # "min_no_messages" : 1,
                       # "max_no_messages" : 1
                      # }

        # testresult = SUTE.teststep(ts_param, step_no, extra_param)
        # return testresult


    @classmethod
    def check_memory(cls, can_p: CanParam, sw_signature1, stepno, purpose):
        """
        Support function for Check Memory

        Replaced:
        can_param["stub"] = stub
        can_param["can_nspace"] = can_nspace
        can_param["can_send"] = can_send
        can_param["can_rec"] = can_rec
        """
        # Parameters for FrameControl FC

        can_mf_param: CanMFParam = {
            'block_size' : 0,
            'separation_time' : 0,
            'frame_control_delay' : 0, #no wait
            'frame_control_flag' : 48, #continue send
            'frame_control_auto' : False
            }
        SC.change_mf_fc(can_p["send"], can_mf_param)

        time.sleep(1)
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",\
                                             b'\x02\x12' + sw_signature1, b'\x01'),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : purpose,\
                             "timeout" : 2,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        testresult = SUTE.teststep(can_p, cpay, etp)
        testresult = testresult and (
            SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
                                                    'Type1,Completed'))
        logging.info(SC.can_messages[can_p["receive"]])
        return testresult


    @classmethod
    def activate_sbl(cls, can_p: CanParam, call, stepno,\
                     purpose="RoutineControl activate_sbl"):
        """
        Support function for Routine Control Activate Secondary Bootloader

        Replaced:
        can_param["stub"] = stub
        can_param["can_nspace"] = can_nspace
        can_param["can_send"] = can_send
        can_param["can_rec"] = can_rec
        """
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
        testresult = testresult and (
            SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
                                                    'Type1,Completed'))
        return testresult
