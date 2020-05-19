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

from support_can import Support_CAN, CanMFParam
from support_test_odtb2 import Support_test_ODTB2
from support_SecAcc import Support_Security_Access

from support_LZSS import LZSS_Encoder

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSA = Support_Security_Access()

LZSS = LZSS_Encoder()

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

    def transfer_data_block(self, offset, data, data_format,\
                            stub, can_send, can_rec, can_nspace,\
                            step_no, purpose):
        """
            transfer_data_block
            support function to transfer
            data with given offset and data_format to
            intended destination, given by
            stub, can_send, can_rec, can_nspace

            step_no, purpose:
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
                    self.request_block_download(stub, can_send, can_rec,
                                                can_nspace, step_no, purpose,
                                                block_addr_b, block_len_b, data_format)
                #testresult = testresult and testresultt
                # Flash blocks to BECM with transfer data service 0x36
                testresult = testresult and\
                             self.flash_blocks(nbl, stub, can_send, can_rec, can_nspace,
                                               step_no, purpose, block_len, block_data)

                #Transfer data exit with service 0x37
                testresult = testresult and\
                             self.transfer_data_exit(stub, can_send, can_rec, can_nspace,
                                                     step_no, purpose)
            else:
                print("CRC doesn't match after decompression")
                print("Header       CRC16 block_data:  {0:04X}".format(block_crc16))
                print("Decompressed CRC16 calculation: {0:04X}".format(SUTE.crc16(decompr_data)))
                print("Header       block length: {0:08X}".format(block_len))
                print("Decompressed block length: {0:08X}".format(len(decompr_data)))
                testresult = False
        return testresult

    # Support Function for flashing Secondary Bootloader SW
    def sbl_download(self, stub, file_n, can_send="", can_rec="", can_nspace="", step_no='',
                     purpose=""):
        """
        SBL Download
        """
        testresult = True
        purpose = "SBL Download"
        # Read vbf file for SBL download
        offset, data, sw_signature, call, data_format = self.read_vbf_file_sbl(file_n)

        testresult = testresult and self.transfer_data_block(offset, data, data_format,\
                                                            stub, can_send, can_rec, can_nspace,\
                                                            step_no, purpose)
        #Check memory
        testresult = testresult and self.check_memory(stub, can_send, can_rec, can_nspace, step_no,
                                                      purpose, sw_signature)

        return testresult, call

    # Support Function for flashing SW Parts
    def sw_part_download(self, stub, file_n, can_send="", can_rec="", can_nspace="", step_no='',
                         purpose=""):
        """
        Software Download
        """
        #testresult = True

        print("sw_part_download filename: ", file_n)
        testresult, sw_signature =\
            self.sw_part_download_no_check(stub, file_n, can_send, can_rec, can_nspace,\
                                           step_no, purpose\
                                          )

        # Check memory
        testresult = testresult and self.check_memory(stub, can_send, can_rec, can_nspace,\
                                                      step_no, purpose,\
                                                      sw_signature)
        return testresult

    # Support Function for flashing SW Parts without Check
    def sw_part_download_no_check(self, stub, file_n,\
                                  can_send="", can_rec="", can_nspace="",\
                                  step_no='', purpose=""):
        """
        Software Download
        """
        #testresult = True
        purpose = "Software Download"
        # Read vbf file for SBL download
        print("sw_part_download_no_check filename: ", file_n)
        offset, off, data, sw_signature, data_format, erase = self.read_vbf_file(file_n)

        # Erase Memory
        testresult = self.flash_erase(stub, can_send, can_rec, can_nspace,
                                      step_no, purpose, erase, data, off)
        # Iteration to Download the Software by blocks

        testresult = testresult and self.transfer_data_block(offset, data, data_format,\
                                                            stub, can_send, can_rec, can_nspace,\
                                                            step_no, purpose)

        return testresult, sw_signature

    # Support Function for Flashing and activate Secondary Bootloader from Default session
    def sbl_activation_def(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                           purpose=""):
        """
        function used for BECM in Default or Extended mode
        """


        # verify RoutineControlRequest is sent for Type 1

        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("RoutineControlRequestSID", b'\x02\x06', b'\x01'),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : "verify RC start sent for Check Prog Precond",\
                       "timeout" : 0.05,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)
        #testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
        #                                          can_rec, can_nspace, step_no, purpose,
        #                                          timeout, min_no_messages, max_no_messages)
        logging.info(SC.can_messages[can_rec])
        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))

        # Change to Programming session

        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("DiagnosticSessionControl", b'\x02', ""),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                }
        extra_param = {"purpose" : "Change to Programming session(02) from default",\
                       "timeout" : 1,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = testresult and SUTE.teststep(ts_param,\
                                                  step_no, extra_param)
        testresult = testresult and SUTE.teststep(ts_param,\
                                                  step_no, extra_param)

        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', ""),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : "Verify Session after SessionControl to Prog",\
                       "timeout" : 1,\
                       "min_no_messages" : 1,\
                       "max_no_messages" : 1
                      }

        SUTE.teststep(ts_param,\
                      step_no, extra_param)

        testresult = testresult and self.sbl_activation_prog(stub, can_send, can_rec, can_nspace,\
                                            step_no, purpose)

        return testresult

    # Support Function for Flashing and activate Secondary Bootloader from Programming session
    def sbl_activation_prog(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                            purpose=""):
        """
        function used for BECM in forced Programming mode
        """
        testresult = True

        # Security Access Request SID
        testresult = testresult and SSA.activation_security_access(stub, can_send, can_rec,
                                                                   can_nspace, step_no, purpose)

        # SBL Download
        purpose = 'SBL Download'
        tresult, call = self.sbl_download(stub, self._sbl,\
                                          can_send, can_rec, can_nspace,\
                                          step_no, purpose)
        testresult = testresult and tresult

        # Activate SBL
        purpose = "Activation of SBL"
        testresult = testresult and self.activate_sbl(stub, can_send, can_rec, can_nspace,
                                                      step_no, purpose, call)

        return  testresult

    # Support Function to select Support functions to use for activating SBL based on actual mode
    def sbl_activation(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                       purpose=""):
        """
        Function used to activate the Secondary Bootloader
        """
        testresult = True


        # verify session

        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', ""),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : "Verify Session",\
                       "timeout" : 1,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        SUTE.teststep(ts_param,\
                      step_no, extra_param)


        logging.info(SC.can_messages[can_rec])

        if SUTE.test_message(SC.can_messages[can_rec],
                             '62F18601') or SUTE.test_message(SC.can_messages[can_rec],
                                                              '62F18603'):
            testresult = self.sbl_activation_def(stub, can_send, can_rec, can_nspace,
                                                 step_no, purpose)
        elif SUTE.test_message(SC.can_messages[can_rec], '62F18602'):
            testresult = self.sbl_activation_prog(stub, can_send, can_rec, can_nspace,
                                                  step_no, purpose)
        else:
            logging.info("error message: %s\n", SC.can_messages[can_rec])
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

    def check_complete_compatible_routine(self, stub, can_send, can_rec, can_nspace,
                                          step_no, purpose):
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
        SC.change_MF_FC(can_send, can_mf_param)

        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("RoutineControlRequestSID", b'\x02\x05', b'\x01'),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : purpose,\
                       "timeout" : 1,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)

        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))
        testresult = testresult and (
            self.pp_decode_routine_complete_compatible(SC.can_messages[can_rec][0][2]))
        logging.info(SC.can_messages[can_rec][0][2])
        return testresult

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
        logging.info(data_format)
        #print(SUTE.CRC32_from_file(data[offset:len(data)]))
        block_address = int.from_bytes(data[offset: offset + 4], 'big')
        logging.info(block_address)
        return offset, data, sw_signature, call, data_format

    #Read and decode vbf files for Software Parts
    def read_vbf_file(self, f_path_name):
        """
        Read and decode vbf files for Software Parts
        """
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
    def flash_erase(self, stub, can_send, can_rec, can_nspace, step_no, purpose, erase, data, off):
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
        SC.change_MF_FC(can_send, can_mf_param)
        time.sleep(1)
        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("RoutineControlRequestSID", b'\xFF\x00'\
                                             + erase, b'\x01'),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : purpose,\
                       "timeout" : 15,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)

        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))

        # Erase Memory
        while data[off + 24 : off + 25] == b'x':
            off += 25
            memory_add = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1], 4)
            off += 12
            memory_size = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1], 4)
            off += 8
            erase = memory_add + memory_size

            SC.change_MF_FC(can_send, can_mf_param)
            time.sleep(1)
            ts_param = {"stub" : stub,\
                        "m_send" : SC.can_m_send("RoutineControlRequestSID", b'\xFF\x00'\
                                                 + erase, b'\x01'),\
                        "mr_extra" : '',\
                        "can_send" : can_send,\
                        "can_rec"  : can_rec,\
                        "can_nspace" : can_nspace\
                       }
            extra_param = {"purpose" : purpose,\
                           "timeout" : 15,\
                           "min_no_messages" : -1,\
                           "max_no_messages" : -1
                          }

            testresult = SUTE.teststep(ts_param,\
                                       step_no, extra_param)
            testresult = testresult and (
                SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                        'Type1,Completed'))
        return testresult

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

    #Support function for Request Download
    def request_block_download(self, stub, can_send, can_rec, can_nspace, step_no, purpose,
                               block_addr_by, block_len_by, data_format):
        """
        Support function for Request Download
        """
        #testresult = True
        # Parameters for FrameControl FC

        can_mf_param: CanMFParam = {
            'block_size' : 0,
            'separation_time' : 0,
            'frame_control_delay' : 0, #no wait
            'frame_control_flag' : 48, #continue send
            'frame_control_auto' : False
            }
        SC.change_MF_FC(can_send, can_mf_param)

        ts_param = {"stub" : stub,\
                    "m_send" : b'\x34' + data_format + b'\x44'+ block_addr_by + block_len_by,\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : purpose,\
                       "timeout" : 0.05,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '74')
        nbl = SUTE.PP_StringTobytes(SC.can_frames[can_rec][0][2][6:10], 4)
        if self._debug:
            print("NBL: {}".format(nbl))
        #nbl = int.from_bytes(SC.can_frames[can_rec][0][2][6:10])
        nbl = int.from_bytes(nbl, 'big')
        return testresult, nbl

    # Support function for Transfer Data
    def flash_blocks(self, nbl, stub, can_send, can_rec, can_nspace, step_no, purpose, block_len,
                     block_data):
        """
        Support function for Transfer Data
        """
        #testresult = True
        pad = 0

        for i in range(int(block_len/(nbl-2))+1):

            pad = (nbl-2)*i
            i += 1
            ibyte = bytes([i])
            # Parameters for FrameControl FC
            can_mf_param: CanMFParam = {
                'block_size' : 0,
                'separation_time' : 0,
                'frame_control_delay' : 0, #no wait
                'frame_control_flag' : 48, #continue send
                'frame_control_auto' : False
                }
            SC.change_MF_FC(can_send, can_mf_param)

            ts_param = {"stub" : stub,\
                        "m_send" : b'\x36' + ibyte + block_data[pad:pad + nbl-2],\
                        "mr_extra" : '',\
                        "can_send" : can_send,\
                        "can_rec"  : can_rec,\
                        "can_nspace" : can_nspace\
                       }
            extra_param = {"purpose" : purpose,\
                           "timeout" : 0.02,\
                           "min_no_messages" : -1,\
                           "max_no_messages" : -1
                          }

            testresult = SUTE.teststep(ts_param,\
                                       step_no, extra_param)
            #testresult = SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
            #                           can_rec, can_nspace, step_no, purpose,
            #                           timeout, min_no_messages, max_no_messages)
            testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '76')
                #print(SC.can_messages[can_receive])
        return testresult

    #Support function for Request Transfer Exit
    def transfer_data_exit(self, stub, can_send, can_rec, can_nspace, step_no, purpose):
        """
        Support function for Request Transfer Exit
        """
        #testresult = True
        ts_param = {"stub" : stub,\
                    "m_send" : b'\x37',\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : purpose,\
                       "timeout" : 0.2,\
                       "min_no_messages" : 1,\
                       "max_no_messages" : 1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)
        return testresult

    #Support function for Check Memory
    def check_memory(self, stub, can_send, can_rec, can_nspace, step_no, purpose, sw_signature1):
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
        SC.change_MF_FC(can_send, can_mf_param)

        time.sleep(1)
        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("RoutineControlRequestSID", b'\x02\x12'\
                                             + sw_signature1, b'\x01'),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : purpose,\
                       "timeout" : 2,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)

        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))
        logging.info(SC.can_messages[can_rec])
        return testresult

    #Support function for Routine Control Activate Secondary Bootloader
    def activate_sbl(self, stub, can_send, can_rec, can_nspace, step_no, purpose, call):
        """
        Support function for Routine Control Activate Secondary Bootloader
        """

        ts_param = {"stub" : stub,\
                    "m_send" : SC.can_m_send("RoutineControlRequestSID",\
                                             b'\x03\x01' + call, b'\x01'),\
                    "mr_extra" : '',\
                    "can_send" : can_send,\
                    "can_rec"  : can_rec,\
                    "can_nspace" : can_nspace\
                   }
        extra_param = {"purpose" : purpose,\
                       "timeout" : 2,\
                       "min_no_messages" : -1,\
                       "max_no_messages" : -1
                      }

        testresult = SUTE.teststep(ts_param,\
                                   step_no, extra_param)
        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))
        return testresult
