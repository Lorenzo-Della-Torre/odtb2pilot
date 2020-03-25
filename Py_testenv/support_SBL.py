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

from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
from support_SecAcc import Support_Security_Access

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSA = Support_Security_Access()

#class for supporting Secondary Bootloader Download
class Support_SBL:
    """
    class for supporting Secondary Bootloader Download
    """

    # Support Function for flashing Secondary Bootloader SW
    def sbl_download(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                     purpose="", file_n=1):
        """
        SBL Download
        """
        testresult = True
        purpose = "SBL Download"
        # Read vbf file for SBL download
        offset, data, sw_signature, call, data_format = self.read_vbf_file_sbl(file_n)

        # Iteration to Download the SBL by blocks
        while offset < len(data):
            # Extract data block
            offset, block_data, block_addr_by, block_len_by, _, block_len = (
                self.block_data_extract(offset, data))

            #print(self.crc_calculation(data, offset, block_data, block_addr, block_len))
            # Request Download
            testresultt, nbl = self.request_block_download(stub, can_send, can_rec,
                                                           can_nspace, step_no, purpose,
                                                           block_addr_by, block_len_by, data_format)
            testresult = testresult and testresultt
            # Flash blocks to BECM with transfer data service 0x36
            testresult = testresult and self.flash_blocks(nbl, stub, can_send, can_rec, can_nspace,
                                                          step_no, purpose, block_len, block_data)

            #Transfer data exit with service 0x37
            testresult = testresult and self.transfer_data_exit(stub, can_send, can_rec, can_nspace,
                                                                step_no, purpose)

        #Check memory
        testresult = testresult and self.check_memory(stub, can_send, can_rec, can_nspace, step_no,
                                                      purpose, sw_signature)

        return testresult, call

    # Support Function for flashing SW Parts
    def sw_part_download(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                         purpose="", file_n=2):
        """
        Software Download
        """
        testresult = True
        purpose = "Software Download"
        # Read vbf file for SBL download
        offset, off, data, sw_signature1, data_format, erase = self.read_vbf_file(file_n)

        # Erase Memory
        testresult = testresult and self.flash_erase(stub, can_send, can_rec, can_nspace, step_no,
                                                     purpose, erase, data, off)
        # Iteration to Download the Software by blocks

        while offset < len(data):

            # Extract data block
            offset, block_data, block_addr_by, block_len_by, _, block_len = (
                self.block_data_extract(offset, data))

            #print(self.crc_calculation(data, offset, block_data, block_addr, block_len))
            # Request Download
            resultt, nbl = self.request_block_download(stub, can_send, can_rec,
                                                       can_nspace, step_no,
                                                       purpose, block_addr_by,
                                                       block_len_by, data_format)
            testresult = testresult and resultt
            # Flash blocks to BECM with transfer data service 0x36
            testresult = testresult and self.flash_blocks(nbl, stub, can_send, can_rec,
                                                          can_nspace, step_no, purpose,
                                                          block_len, block_data)

            # Transfer data exit with service 0x37
            testresult = testresult and self.transfer_data_exit(stub, can_send, can_rec, can_nspace,
                                                                step_no, purpose)

        # Check memory
        testresult = testresult and self.check_memory(stub, can_send, can_rec, can_nspace, step_no,
                                                      purpose, sw_signature1)

        return testresult

    # Support Function for flashing SW Parts without Check
    def sw_part_download_no_check(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                                  purpose="", file_n=2):
        """
        Software Download
        """
        testresult = True
        purpose = "Software Download"
        # Read vbf file for SBL download
        offset, off, data, sw_signature, data_format, erase = self.read_vbf_file(file_n)

        # Erase Memory
        testresult = testresult and self.flash_erase(stub, can_send, can_rec, can_nspace,
                                                     step_no, purpose, erase, data, off)
        # Iteration to Download the Software by blocks

        while offset < len(data):

            # Extract data block
            offset, block_data, block_addr_by, block_len_by, _, block_len = (
                self.block_data_extract(offset, data))

            #print(self.crc_calculation(data, offset, block_data, block_addr, block_len))
            # Request Download
            resultt, nbl = self.request_block_download(stub, can_send, can_rec, can_nspace,
                                                       step_no, purpose, block_addr_by,
                                                       block_len_by, data_format)
            testresult = testresult and resultt
            # Flash blocks to BECM with transfer data service 0x36
            testresult = testresult and self.flash_blocks(nbl, stub, can_send, can_rec, can_nspace,
                                                          step_no, purpose, block_len, block_data)

            #Transfer data exit with service 0x37
            testresult = testresult and self.transfer_data_exit(stub, can_send, can_rec,
                                                                can_nspace, step_no, purpose)

        return testresult, sw_signature

    # Support Function for Flashing and activate Secondary Bootloader from Default session
    def sbl_activation_def(self, stub, can_send="", can_rec="", can_nspace="", step_no='',
                           purpose=""):
        """
        function used for BECM in Default or Extended mode
        """
        testresult = True
        min_no_messages = -1
        max_no_messages = -1


        # verify RoutineControlRequest is sent for Type 1

        purpose = "verify RoutineControl start are sent for Check Programming Preconditions"
        timeout = 0.05 #wait a second for reply to be send

        can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\x02\x06', b'\x01')
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)
        logging.info(SC.can_messages[can_rec])
        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))

        # Change to Programming session
        purpose = "Change to Programming session(01) from default"
        timeout = 1

        can_m_send = SC.can_m_send("DiagnosticSessionControl", b'\x02', "")
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

        # Security Access Request SID
        testresult = testresult and SSA.activation_security_access(stub, can_send, can_rec,
                                                                   can_nspace, step_no, purpose)

        # SBL Download
        purpose = 'SBL Download'
        tresult, call = self.sbl_download(stub, can_send, can_rec, can_nspace, step_no, purpose)
        testresult = testresult and tresult

        # Activate SBL
        purpose = "Activation of SBL"
        testresult = testresult and self.activate_sbl(stub, can_send, can_rec, can_nspace,
                                                      step_no, purpose, call)

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
        tresult, call = self.sbl_download(stub, can_send, can_rec, can_nspace, step_no, purpose)
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
        purpose = "Verify Session"
        timeout = 1
        min_no_messages = -1
        max_no_messages = -1

        can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', "")
        can_mr_extra = ''

        SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                      can_rec, can_nspace, step_no, purpose,
                      timeout, min_no_messages, max_no_messages)

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
        time.sleep(1)
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
        testresult = True
        timeout = 1 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1

        # Parameters for FrameControl FC
        block_size = 0
        separation_time = 0
        frame_control_delay = 0 #no wait
        frame_control_flag = 48 #continue send
        frame_control_auto = True

        can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\x02\x05', b'\x01')
        can_mr_extra = ''

        SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay, frame_control_flag,
                        frame_control_auto)

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))
        testresult = testresult and (
            self.pp_decode_routine_complete_compatible(SC.can_messages[can_rec][0][2]))
        logging.info(SC.can_messages[can_rec][0][2])
        return testresult

    #Read and decode vbf files for Secondary Bootloader
    def read_vbf_file_sbl(self, file_n=1):
        """
        Read and decode vbf files for Secondary Bootloader
        """
        data = SUTE.read_f(sys.argv[file_n])
        find = data.find
        header_len = find(b'\x3B\x0D\x0A\x7D') + 4
        #print ('Header length: 0x%04X' % header_len)

        if header_len < 100:
            logging.info('Unknown format')
            quit(-1)

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
    def read_vbf_file(self, file_n):
        """
        Read and decode vbf files for Software Parts
        """
        data = SUTE.read_f(sys.argv[file_n])
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
        testresult = True
        timeout = 15 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1
        # Parameters for FrameControl FC
        block_size = 0
        separation_time = 0
        frame_control_delay = 0 #no wait
        frame_control_flag = 48 #continue send
        frame_control_auto = False

        can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')
        can_mr_extra = ''

        SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay,
                        frame_control_flag, frame_control_auto)
        time.sleep(1)
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

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
            timeout = 15 #wait a second for reply to be send
            min_no_messages = -1
            max_no_messages = -1

            can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')
            can_mr_extra = ''

            SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay,
                            frame_control_flag, frame_control_auto)
            time.sleep(1)
            testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                      can_rec, can_nspace, step_no, purpose,
                                                      timeout, min_no_messages, max_no_messages)

            testresult = testresult and (
                SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                        'Type1,Completed'))
        return testresult

    #Extraction of block data from vbf file
    def block_data_extract(self, offset, data):
        """
        Extraction of block data from vbf file
        """
        block_addr_by = data[offset: offset + 4]
        print("block_address: {}".format(block_addr_by))
        block_len_by = data[offset+4: offset + 8]
        block_addr = int.from_bytes(block_addr_by, 'big')
        block_len = int.from_bytes(block_len_by, 'big')
        offset += 8

        block_data = data[offset : offset + block_len]
        offset += block_len
        offset += 2
        return offset, block_data, block_addr_by, block_len_by, block_addr, block_len

    #crc calculation for each block
    def crc_calculation(self, data, offset, block_data, block_addr, block_len):
        """
        crc calculation for each block
        """
        crc = int.from_bytes(a, 'big')
        #print(hex(crc))
        offset += 2

        crc_res = 'ok ' if SUTE.crc16(block_data) == crc else 'error'

        return "Block adr: 0x%X length: 0x%X crc %s" % (block_addr, block_len, crc_res)

    #Support function for Request Download
    def request_block_download(self, stub, can_send, can_rec, can_nspace, step_no, purpose,
                               block_addr_by, block_len_by, data_format):
        """
        Support function for Request Download
        """
        testresult = True
        # Parameters for FrameControl FC
        block_size = 0
        separation_time = 0
        frame_control_delay = 0 #no wait
        frame_control_flag = 48 #continue send
        frame_control_auto = False

        timeout = 0.05
        min_no_messages = -1
        max_no_messages = -1

        can_m_send = b'\x34' + data_format + b'\x44'+ block_addr_by + block_len_by
        can_mr_extra = ''

        SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay,
                        frame_control_flag, frame_control_auto)

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '74')
        nbl = SUTE.PP_StringTobytes(SC.can_frames[can_rec][0][2][6:10], 4)
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
        testresult = True
        pad = 0

        for i in range(int(block_len/(nbl-2))+1):

            pad = (nbl-2)*i
            i += 1
            ibyte = bytes([i])
            timeout = 0.02
            min_no_messages = -1
            max_no_messages = -1
            # Parameters for FrameControl FC
            block_size = 0
            separation_time = 0
            frame_control_delay = 0 #no wait
            frame_control_flag = 48 #continue send
            frame_control_auto = False

            can_m_send = b'\x36' + ibyte + block_data[pad:pad + nbl-2]

            can_mr_extra = ''

            SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay,
                            frame_control_flag, frame_control_auto)

            testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                      can_rec, can_nspace, step_no, purpose,
                                                      timeout, min_no_messages, max_no_messages)
            testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '76')
                #print(SC.can_messages[can_receive])
        return testresult

    #Support function for Request Transfer Exit
    def transfer_data_exit(self, stub, can_send, can_rec, can_nspace, step_no, purpose):
        """
        Support function for Request Transfer Exit
        """
        testresult = True
        min_no_messages = 1
        max_no_messages = 1
        timeout = 0.1
        can_m_send = b'\x37'
        can_mr_extra = ''
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

        return testresult

    #Support function for Check Memory
    def check_memory(self, stub, can_send, can_rec, can_nspace, step_no, purpose, sw_signature1):
        """
        Support function for Check Memory
        """
        testresult = True
        timeout = 2
        min_no_messages = -1
        max_no_messages = -1
        # Parameters for FrameControl FC
        block_size = 0
        separation_time = 0
        frame_control_delay = 0 #no wait
        frame_control_flag = 48 #continue send
        frame_control_auto = False
        can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\x02\x12' + sw_signature1, b'\x01')
        can_mr_extra = ''
        SC.change_MF_FC(can_send, block_size, separation_time, frame_control_delay,
                        frame_control_flag, frame_control_auto)
        time.sleep(1)
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

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
        testresult = True
        timeout = 2 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1
        can_m_send = SC.can_m_send("RoutineControlRequestSID", b'\x03\x01' + call, b'\x01')
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

        testresult = testresult and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2],
                                                    'Type1,Completed'))
        return testresult
