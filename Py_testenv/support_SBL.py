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
#from typing import Dict, NewType

from support_can import Support_CAN, CanMFParam, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import Support_test_ODTB2
from support_SecAcc import Support_Security_Access

from support_LZSS import LZSS_Encoder

from support_service10 import SupportService10
from support_service22 import SupportService22
from support_service31 import SupportService31
from support_service34 import SupportService34
from support_service36 import SupportService36
from support_service37 import SupportService37
SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSA = Support_Security_Access()

LZSS = LZSS_Encoder()
SE10 = SupportService10()
SE22 = SupportService22()
SE31 = SupportService31()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


class VbfBlockFormat(Dict):
    """
        Parameters used in VBF blocks
    """
    offset: int
    data: int
    data_format: bytes
    addr: int
    len: int

    @staticmethod
    def vbf_block_init(block):
        """
            init of VbfBlockFormat with empty values
        """
        block['offset'] = 0
        block['data'] = 0
        block['data_format'] = b''
        block['addr'] = 0
        block['len'] = 0

    @staticmethod
    def vbf_block_read(block):
        """
            return block
        """
        return block

#class for supporting Secondary Bootloader Download
class Support_SBL:
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

    def read_VBF_param(self):
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

    def set_VBF_default_param(self):
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
            self.read_VBF_param()
        else:
            self.set_VBF_default_param()

    def transfer_data_block(self, offset, data, data_format,\
                            can_p: CanParam,\
                            stepno, purpose):
        """
            transfer_data_block
            support function to transfer
            data with given offset and data_format to
            intended destination, given by
            stub, can_send, can_rec, can_nspace

            stepno, purpose:
                used for logging purposes
        """
        # Iteration to Download the SBL by blocks
        if self._debug:
            print("offset: ", offset, "len(data): ", len(data))
        while offset < len(data):
            # Extract data block
            offset, block_data, block_addr, block_len, block_crc16 = (
                self.block_data_extract(offset, data))

            #block_addr_x = int.from_bytes(block_addr_by, 'big')
            #block_len_x = int.from_bytes(block_len_by, 'big')
            block_addr_b = block_addr.to_bytes(4, 'big')
            block_len_b = block_len.to_bytes(4, 'big')

            #print("FileHeader   CRC calculation CRC16: {0:04X}".format(SUTE.crc16(block_data)))

            #decompress block_data if needed
            if self._debug:
                print("DataFormat block: ", data_format.hex())
            if data_format.hex() == '00':
                decompr_data = block_data
            elif data_format.hex() == '10':
                decompr_data = b''
                decompr_data = LZSS.decode_barray(block_data)
            else:
                print("Unknown compression format:", data_format.hex())

            if self._debug:
                print("Header       CRC16 block_data:  {0:04X}".format(block_crc16))
                print("Decompressed CRC16 calculation: {0:04X}".format(SUTE.crc16(decompr_data)))
                print("Length block from header:  {0:08X}".format(block_len))
                print("Length block decompressed: {0:08X}".format(len(decompr_data)))

            if SUTE.crc16(decompr_data) == block_crc16:
                # Request Download
                testresult, nbl =\
                    SE34.request_block_download(can_p, stepno, purpose,
                                                block_addr_b, block_len_b, data_format)
                #testresult = testresult and testresultt
                # Flash blocks to BECM with transfer data service 0x36
                testresult = testresult and\
                             SE36.flash_blocks(nbl, can_p,
                                               stepno, purpose, block_len, block_data)

                #Transfer data exit with service 0x37
                testresult = testresult and\
                             SE37.transfer_data_exit(can_p,
                                                     stepno, purpose)
            else:
                print("CRC doesn't match after decompression")
                print("Header       CRC16 block_data:  {0:04X}".format(block_crc16))
                print("Decompressed CRC16 calculation: {0:04X}".format(SUTE.crc16(decompr_data)))
                print("Header       block length: {0:08X}".format(block_len))
                print("Decompressed block length: {0:08X}".format(len(decompr_data)))
                testresult = False
        return testresult

    # Support Function for flashing Secondary Bootloader SW
    def sbl_download_no_check(self, can_p: CanParam, file_n, stepno='', purpose=""):
        """
        SBL Download
        """
        testresult = True
        purpose = "SBL Download"
        # Read vbf file for SBL download
        #offset, data, sw_signature, call, data_format = self.read_vbf_file_sbl(file_n)
        offset, data, _, call, data_format = self.read_vbf_file_sbl(file_n)

        testresult = testresult and self.transfer_data_block(offset, data, data_format,\
                                                            can_p,\
                                                            stepno, purpose)
        #Check memory
        #testresult = testresult and self.check_memory(stub, can_send, can_rec, can_nspace, stepno,
        #                                              purpose, sw_signature)

        return testresult, call

    # Support Function for flashing Secondary Bootloader SW
    def sbl_download(self, can_p: CanParam, file_n, stepno='', purpose=""):
        """
        SBL Download
        """
        testresult = True
        purpose = "SBL Download"
        # Read vbf file for SBL download
        offset, data, sw_signature, call, data_format = self.read_vbf_file_sbl(file_n)

        testresult = testresult and self.transfer_data_block(offset, data, data_format,\
                                                            can_p,\
                                                            stepno, purpose)
        #Check memory
        testresult = testresult and self.check_memory(can_p, stepno,
                                                      purpose, sw_signature)

        return testresult, call

    # Support Function for flashing SW Parts
    def sw_part_download(self, can_p: CanParam, file_n, stepno='',
                         purpose=""):
        """
        Software Download
        """

        print("sw_part_download filename: ", file_n)
        testresult, sw_signature =\
            self.sw_part_download_no_check(can_p, file_n, stepno, purpose\
                                          )

        # Check memory
        testresult = testresult and self.check_memory(can_p,\
                                                      stepno, purpose,\
                                                      sw_signature)
        return testresult

    # Support Function for flashing SW Parts without Check
    def sw_part_download_no_check(self, can_p: CanParam, file_n,\
                                  stepno='', purpose=""):
        """
        Software Download
        """
        #testresult = True
        purpose = "Software Download"
        # Read vbf file for SBL download
        print("sw_part_download_no_check filename: ", file_n)
        offset, off, data, sw_signature, data_format, erase = self.read_vbf_file(file_n)

        # Erase Memory
        testresult = self.flash_erase(can_p,
                                      stepno, purpose, erase, data, off)
        # Iteration to Download the Software by blocks

        testresult = testresult and self.transfer_data_block(offset, data, data_format,\
                                                            can_p,\
                                                            stepno, purpose)

        return testresult, sw_signature

    # Support Function for Flashing and activate Secondary Bootloader from Default session
    def sbl_activation_def(self, can_p: CanParam, stepno='',
                           purpose=""):
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
    def sbl_activation_prog(self, can_p: CanParam, stepno='', purpose=""):
        """
        function used for BECM in forced Programming mode
        """

        # Security Access Request SID
        result = SSA.activation_security_access(can_p, stepno, purpose)

        # SBL Download
        purpose = 'SBL Download'
        tresult, call = self.sbl_download(can_p, self._sbl,\
                                          stepno, purpose)
        result = result and tresult

        # Activate SBL
        purpose = "Activation of SBL"
        result = result and self.activate_sbl(can_p,
                                              stepno, purpose, call)
        return result

    # Support Function to select Support functions to use for activating SBL based on actual mode
    def sbl_activation(self, can_p: CanParam, stepno='',
                       purpose=""):
        """
        Function used to activate the Secondary Bootloader
        """
        testresult = True

        # verify session
        SE22.read_did_f186(can_p, dsession=b'')
        logging.info(SC.can_messages[can_p["rec"]])

        if SUTE.test_message(SC.can_messages[can_p["rec"]], '62F18601')\
            or SUTE.test_message(SC.can_messages[can_p["rec"]], '62F18603'):
            testresult = self.sbl_activation_def(can_p, stepno, purpose)
        elif SUTE.test_message(SC.can_messages[can_p["rec"]], '62F18602'):
            testresult = self.sbl_activation_prog(can_p, stepno, purpose)
        else:
            logging.info("error message: %s\n", SC.can_messages[can_p["rec"]])
        time.sleep(0.1)
        return testresult


#------------------------------Support Support SWDL Functions-------------------------------

    #support function for Extracting Completed and compatible Routine Control Response
    def pp_decode_routine_complete_compatible(self, message):
        """
        support function for Extracting Completed and compatible Routine Control Response
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

    #support function for Extracting Check Memory Routine Control Response
    def pp_decode_routine_check_memory(self, message):
        """
        support function for Extracting Check Memory Routine Control Response
        """
        mess_len = len(message)
        if mess_len == 0:
            val_c = "PP_Decode_Routine_Control_response: missing message"
        else:
            pos = message.find('0212')
            res = message[pos+7:pos+8]
            #val = "{0:8b}".format(int(res, 16))
            if res == '0' or '':
                val_c = 'The verification is passed'
            elif res == '1':
                val_c = 'The signed data could not be authenticated'
                #testresult=False
            elif res == '2':
                val_c = 'The public key integrity check failed'
            elif res == '3':
                val_c = 'Invalid format of length of th eVerification Block Table'
            elif res == '4':
                val_c = '''The address of hash values of the downloaded data blocks
                           does not match the expected values'''
            elif res == '5':
                val_c = 'The blank check failed'
            elif res == '6':
                val_c = 'No data downloaded at all, nothing to verify'
            elif res == '7':
                val_c = 'Read error during hash calculation over memory content'
            elif res == '8':
                val_c = 'ESS content is not valid'
            elif res == '9':
                val_c = 'Additional processor failed verification'
            elif res == 'A':
                val_c = 'Error storing vaildity status information'
            elif res == 'B':
                val_c = 'Certioficate verification failed'
            elif res == 'C':
                val_c = 'User definable'
            else:
                val_c = 'Wrong Decoding'
        return val_c

    def check_complete_compatible_routine(self, can_p: CanParam,
                                          stepno, purpose):
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
        SC.change_MF_FC(can_p["send"], can_mf_param)

        result = SE31.routinecontrol_requestsid_complete_compatible(can_p, stepno)
        result = result and (
            self.pp_decode_routine_complete_compatible(SC.can_messages[can_p["rec"]][0][2]))
        logging.info(SC.can_messages[can_p["rec"]][0][2])
        return result

    #Read and decode vbf files for Secondary Bootloader
    def read_vbf_file_sbl(self, f_path_name):
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
        logging.info("VBF_data_format " + str(data_format))
        #print(SUTE.CRC32_from_file(data[offset:len(data)]))
        block_address = int.from_bytes(data[offset: offset + 4], 'big')
        logging.info("VBF_block_adress {0:08X}".format(block_address))
        return offset, data, sw_signature, call, data_format

    #Read and decode vbf files for Software Parts
    def read_vbf_file(self, f_path_name):
        """
        Read and decode vbf files for Software Parts
        """
        print("File to read: ", f_path_name)
        data = SUTE.read_f(f_path_name)
        find = data.find
        header_len = find(b'\x3B\x0D\x0A\x7D') + 4
        #print ('Header length: 0x%04X' % header_len)

        off = data.find(b'erase = ') + 12
        memory_add = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1], 4)
        off += 12
        memory_size = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1], 4)
        off += 8
        off1 = data.find(b'sw_signature_dev = 0x') + 21
        off2 = data.find(b'data_format_identifier = 0x') + 27
        end = data.find(b';\r\n}')
        logging.info(data[off1:end])
        sw_signature = bytes.fromhex(str(data[off1 : end])[2:-1])
        data_format = bytes.fromhex(str(data[off2 : off2+2])[2:-1])
        logging.info(sw_signature)
        offset = header_len
        logging.info(SUTE.CRC32_from_file(data[offset:len(data)]))
        #block_address = unpack('>L', data[offset: offset + 4])[0]
        erase = memory_add + memory_size
        return offset, off, data, sw_signature, data_format, erase

    #Support function for Routine Flash Erase
    def flash_erase(self, can_p: CanParam, stepno, purpose, erase, data, off):
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
        SC.change_MF_FC(can_p["send"], can_mf_param)
        time.sleep(1)
        
        result = SE31.routinecontrol_requestsid_flash_erase(can_p, erase, stepno)

        # Erase Memory
        while data[off + 24 : off + 25] == b'x':
            off += 25
            memory_add = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1], 4)
            off += 12
            memory_size = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1], 4)
            off += 8
            erase = memory_add + memory_size

            SC.change_MF_FC(can_p["send"], can_mf_param)
            time.sleep(1)
            result = result and SE31.routinecontrol_requestsid_flash_erase(can_p, erase, stepno)
        return result

    #Extraction of block data from vbf file
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



    #Support function for Check Memory
    def check_memory(self, can_p: CanParam, stepno, purpose, sw_signature1):
        """
        Support function for Check Memory
        """
        # Parameters for FrameControl FC

        can_mf_param: CanMFParam = {
            'block_size' : 0,
            'separation_time' : 0,
            'frame_control_delay' : 0, #no wait
            'frame_control_flag' : 48, #continue send
            'frame_control_auto' : False
            }
        SC.change_MF_FC(can_p["send"], can_mf_param)

        time.sleep(1)
        cpay: CanPayload = {"m_send" : SC.can_m_send("RoutineControlRequestSID",\
                                             b'\x02\x12' + sw_signature1, b'\x01'),\
                            "mr_extra" : ''
                           }
        etp: CanTestExtra = {"purpose" : purpose,\
                             "timeout" : 2,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        testresult = SUTE.teststep(can_p, cpay, stepno, etp)
        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_p["rec"]][0][2],
                                                    'Type1,Completed'))
        logging.info(SC.can_messages[can_p["rec"]])
        return testresult

    #Support function for Routine Control Activate Secondary Bootloader
    def activate_sbl(self, can_p: CanParam, stepno, purpose, call):
        """
        Support function for Routine Control Activate Secondary Bootloader
        """

        cpay: CanPayload = {"m_send" : SC.can_m_send("RoutineControlRequestSID",\
                                             b'\x03\x01' + call, b'\x01'),\
                            "mr_extra" : ''
                           }
        etp: CanTestExtra = {"purpose" : purpose,\
                             "timeout" : 2,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        testresult = SUTE.teststep(can_p, cpay, stepno, etp)
        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_p["rec"]][0][2],
                                                    'Type1,Completed'))
        return testresult
