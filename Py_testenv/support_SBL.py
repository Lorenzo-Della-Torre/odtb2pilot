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

from datetime import datetime
import time

import logging
import os, fnmatch 
import sys
import struct

from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
from support_SecAcc import Support_Security_Access

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSA = Support_Security_Access()

#class for supporting Secondary Bootloader Download
class Support_SBL:
    
    # Support Function for flashing Secondary Bootloader SW  
    def SBL_Download(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose="", file_N = 1):
        """
        SBL Download 
        """
        testresult = True
        purpose = "SBL Download"
        """
        Read vbf file for SBL download
        """
        offset, data, sw_signature, call, data_format = self.Read_vbf_file_SBL(file_N)
        
        """
        Iteration to Download the SBL by blocks
        """
        while offset < len(data):
            """
            Extract data block
            """
            offset, block_data, block_addr_by, block_len_by, block_addr, block_len = self.Block_data_extract(offset, data)

            #print(self.crc_calculation(data, offset, block_data, block_addr, block_len))
            """
            Request Download
            """
            testresultt, NBL = self.Request_Block_Download(stub, can_send, can_rec, can_nspace, step_no, purpose, block_addr_by, block_len_by, data_format)
            testresult = testresult and testresultt
            """
            Flash blocks to BECM with transfer data service 0x36
            """
            testresult = testresult and self.Flash_blocks(NBL, stub, can_send, can_rec, can_nspace, step_no, purpose, block_len, block_data)

            """    
            Transfer data exit with service 0x37
            """
            testresult = testresult and self.Transfer_data_exit(stub, can_send, can_rec, can_nspace, step_no, purpose)

        """
        Check memory
        """
        testresult = testresult and self.Check_Memory(stub, can_send, can_rec, can_nspace, step_no, purpose, sw_signature)    
          
        return testresult, call
    
    # Support Function for flashing SW Parts
    def SW_Part_Download(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose="", file_N=2):
        """
        Software Download
        """
        testresult = True
        purpose = "Software Download"
        """
        Read vbf file for SBL download
        """
        offset, off, data, sw_signature1, data_format, erase = self.Read_vbf_file(file_N)
        
        """
        Erase Memory
        """   
        testresult = testresult and self.Flash_Erase(stub, can_send, can_rec, can_nspace, step_no, purpose, erase, data, off)
        """
        Iteration to Download the Software by blocks
        """
    
        while offset < len(data):

            """
            Extract data block
            """
            offset, block_data, block_addr_by, block_len_by, block_addr, block_len = self.Block_data_extract(offset, data)

            #print(self.crc_calculation(data, offset, block_data, block_addr, block_len))
            """
            Request Download
            """
            resultt, NBL = self.Request_Block_Download(stub, can_send, can_rec, can_nspace, step_no, purpose, block_addr_by, block_len_by, data_format)
            testresult = testresult and resultt
            """
            Flash blocks to BECM with transfer data service 0x36
            """
            testresult = testresult and self.Flash_blocks(NBL, stub, can_send, can_rec, can_nspace, step_no, purpose, block_len, block_data)

            """    
            Transfer data exit with service 0x37
            """
            testresult = testresult and self.Transfer_data_exit(stub, can_send, can_rec, can_nspace, step_no, purpose)

        """
        Check memory
        """
        testresult = testresult and self.Check_Memory(stub, can_send, can_rec, can_nspace, step_no, purpose, sw_signature1)
        
        return testresult
        
    # Support Function for flashing SW Parts without Check
    def SW_Part_Download_No_Check(self, stub, can_send="", can_rec="", can_nspace="", step_no='', purpose="", file_N=2):
        """
        Software Download
        """
        testresult = True
        purpose = "Software Download"
        """
        Read vbf file for SBL download
        """
        offset, off, data, sw_signature, data_format, erase = self.Read_vbf_file(file_N)
        
        """
        Erase Memory
        """   
        testresult = testresult and self.Flash_Erase(stub, can_send, can_rec, can_nspace, 
                                                     step_no, purpose, erase, data, off)
        """
        Iteration to Download the Software by blocks
        """
    
        while offset < len(data):

            """
            Extract data block
            """
            offset, block_data, block_addr_by, block_len_by, _, block_len = self.Block_data_extract(offset, data)

            #print(self.crc_calculation(data, offset, block_data, block_addr, block_len))
            """
            Request Download
            """
            resultt, NBL = self.Request_Block_Download(stub, can_send, can_rec, can_nspace, 
                                                       step_no, purpose, block_addr_by, 
                                                       block_len_by, data_format)
            testresult = testresult and resultt
            """
            Flash blocks to BECM with transfer data service 0x36
            """
            testresult = testresult and self.Flash_blocks(NBL, stub, can_send, can_rec, can_nspace, 
                                                          step_no, purpose, block_len, block_data)

            """    
            Transfer data exit with service 0x37
            """
            testresult = testresult and self.Transfer_data_exit(stub, can_send, can_rec, 
                                                                can_nspace, step_no, purpose)
        
        return testresult, sw_signature

    # Support Function for Flashing and activate Secondary Bootloader from Default session
    def SBL_Activation_Def(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose=""):
        """
        function used for BECM in Default or Extended mode
        """
        testresult = True
        min_no_messages = -1
        max_no_messages = -1

        """
        verify RoutineControlRequest is sent for Type 1
        """
        purpose = "verify RoutineControl start are sent for Check Programming Preconditions"
        timeout = 0.05 #wait a second for reply to be send
        
        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x06', b'\x01')
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                        can_rec, can_nspace, step_no, purpose,
                                        timeout, min_no_messages, max_no_messages)
        print(SC.can_messages[can_rec])
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')

        """
        Change to Programming session
        """
        purpose = "Change to Programming session(01) from default"
        timeout = 1

        can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
        can_mr_extra = ''
    
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        """
        Security Access Request SID
        """
        testresult = testresult and SSA.Activation_Security_Access(stub, can_send, can_rec, can_nspace, step_no, purpose)

        """
        SBL Download 
        """
        purpose = 'SBL Download'
        tresult, call = self.SBL_Download(stub, can_send, can_rec, can_nspace, step_no, purpose)
        testresult = testresult and tresult
    
        """
        Activate SBL
        """
        purpose = "Activation of SBL"
        testresult = testresult and self.Activate_SBL(stub, can_send, can_rec, can_nspace, step_no, purpose,call)

        return testresult

    # Support Function for Flashing and activate Secondary Bootloader from Programming session
    def SBL_Activation_Prog(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose=""):
        """
        function used for BECM in forced Programming mode
        """
        testresult = True
        
        """
        Security Access Request SID
        """
        testresult = testresult and SSA.Activation_Security_Access(stub, can_send, can_rec, can_nspace, step_no, purpose)

        """
        SBL Download 
        """
        purpose = 'SBL Download'
        tresult, call = self.SBL_Download(stub, can_send, can_rec, can_nspace, step_no, purpose)
        testresult = testresult and tresult
    
        """
        Activate SBL
        """
        purpose = "Activation of SBL"
        testresult = testresult and self.Activate_SBL(stub, can_send, can_rec, can_nspace, step_no, purpose,call)

        return  testresult
    
    # Support Function to select Support functions to use for activating SBL based on actual mode
    def SBL_Activation(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose=""):
        """
        Function used to activate the Secondary Bootloader
        """
        testresult = True

        """
        Teststep 11: verify session
        """
        purpose = "Verify Session"
        timeout = 1
        min_no_messages = -1
        max_no_messages = -1

        can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
        can_mr_extra = ''
    
        SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                        can_rec, can_nspace, step_no, purpose,
                        timeout, min_no_messages, max_no_messages)

        print(SC.can_messages[can_rec])

        if SUTE.test_message(SC.can_messages[can_rec], '62F18601') or SUTE.test_message(SC.can_messages[can_rec], '62F18603'):
            testresult = self.SBL_Activation_Def(stub, can_send, can_rec, can_nspace, step_no, purpose)
        elif SUTE.test_message(SC.can_messages[can_rec], '62F18602'):
            testresult = self.SBL_Activation_Prog(stub, can_send, can_rec, can_nspace, step_no, purpose)
        else:
            print("error message: ", SC.can_messages[can_rec])
        time.sleep(1)
        return testresult

    
#------------------------------Support Support SWDL Functions-------------------------------

    #support function for Extracting Completed and compatible Routine Control Response 
    def PP_Decode_Routine_Complete_Compatible (self, message):
        mess_len = len(message)
        if (mess_len == 0):
            val_C = "PP_Decode_Routine_Control_response: missing message"
        else:
            pos = message.find ('0205')
            res = message[pos+6:pos+16]
            val = "{0:40b}".format(int(res, 16))
            if val[38] == '0' or '':
                val_Ca = 'Compatible'
            elif val[38] == '1':
                val_Ca = 'Not Compatible'
            else:
                val_Ca = 'Wrong Decoding'

            if val[39] == '0':
                val_Cl = 'Complete, '
            elif val[39] == '1':
                val_Cl = 'Not Complete, '
            else:
                val_Cl = 'Wrong Decoding'
                
            val_C = val_Cl + val_Ca
        return val_C
        
    #support function for Extracting Check Memory Routine Control Response
    def PP_Decode_Routine_Check_Memory(self, message):
        mess_len = len(message)
        if mess_len == 0:
            val_C = "PP_Decode_Routine_Control_response: missing message"
        else:
            pos = message.find('0212')
            res = message[pos+7:pos+8]
            #val = "{0:8b}".format(int(res, 16))
            if res == '0' or '':
                val_C = 'The verification is passed'
            elif res == '1':
                val_C = 'The signed data could not be authenticated'
                #testresult=False
            elif res == '2':
                val_C = 'The public key integrity check failed'
            elif res == '3':
                val_C = 'Invalid format of length of th eVerification Block Table'
            elif res == '4':
                val_C = 'The address of hash values of the downloaded data blocks does not match the expected values'
            elif res == '5':
                val_C = 'The blank check failed'
            elif res == '6':
                val_C = 'No data downloaded at all, nothing to verify'
            elif res == '7':
                val_C = 'Read error during hash calculation over memory content'
            elif res == '8':
                val_C = 'ESS content is not valid'
            elif res == '9':
                val_C = 'Additional processor failed verification'
            elif res == 'A':
                val_C = 'Error storing vaildity status information'
            elif res == 'B':
                val_C = 'Certioficate verification failed'
            elif res == 'C':
                val_C = 'User definable'
            else:
                val_C = 'Wrong Decoding'
        return val_C
    
    #Support function for Routine Complete & Compatible
    def Check_Complete_Compatible_Routine(self, stub, can_send, can_rec, can_nspace, step_no, purpose):
        testresult = True
        timeout = 1 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1

        # Parameters for FrameControl FC
        BS=0
        ST=0
        FC_delay = 0 #no wait
        FC_flag = 48 #continue send
        FC_auto = True

        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x05', b'\x01')
        can_mr_extra = ''

        SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')
        testresult = testresult and self.PP_Decode_Routine_Complete_Compatible (SC.can_messages[can_rec][0][2])
        print(SC.can_messages[can_rec][0][2])
        return testresult

    #Read and decode vbf files for Secondary Bootloader
    def Read_vbf_file_SBL(self, file_N = 1):
        unpack = struct.unpack
        data = SUTE.read_f(sys.argv[file_N])
        find = data.find
        header_len = find(b'\x3B\x0D\x0A\x7D') + 4
        #print ('Header length: 0x%04X' % header_len)

        if header_len < 100:
            print ('Unknown format')
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
        print(data_format)
        #print(SUTE.CRC32_from_file(data[offset:len(data)]))
        block_address = unpack('>L', data[offset: offset + 4])[0]
        print(block_address)
        return offset, data, sw_signature, call, data_format
    
    #Read and decode vbf files for Software Parts
    def Read_vbf_file(self, file_N):
        unpack = struct.unpack
        data = SUTE.read_f(sys.argv[file_N])
        find = data.find 
        header_len = find(b'\x3B\x0D\x0A\x7D') + 4
        #print ('Header length: 0x%04X' % header_len)
    
        off = data.find(b'erase = ') + 12
        memory_add = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1],4)
        off += 12
        memory_size = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1],4)
        off += 8
        off1 = data.find(b'sw_signature_dev = 0x') + 21
        off2 = data.find(b'data_format_identifier = 0x') + 27
        end = data.find(b';\r\n}')
        print(data[off1:end])
        sw_signature = bytes.fromhex(str(data[off1 : end])[2:-1])
        data_format = bytes.fromhex(str(data[off2 : off2+2])[2:-1])
        print(sw_signature)
        offset = header_len
        print(SUTE.CRC32_from_file(data[offset:len(data)]))
        block_address = unpack('>L', data[offset: offset + 4])[0]
        erase = memory_add + memory_size
        return offset, off, data, sw_signature, data_format, erase
    
    #Support function for Routine Flash Erase
    def Flash_Erase(self, stub, can_send, can_rec, can_nspace, step_no, purpose, erase, data, off):
        testresult = True
        timeout = 15 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1
        # Parameters for FrameControl FC
        BS=0
        ST=0
        FC_delay = 0 #no wait
        FC_flag = 48 #continue sends
        FC_auto = False

        can_m_send = SC.can_m_send( "RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')
        can_mr_extra = ''

        SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
        time.sleep(1)
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')

        """
        Erase Memory
        """
        while data[off + 24 : off + 25] == b'x':
            off += 25
            memory_add = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1],4)
            off += 12
            memory_size = SUTE.PP_StringTobytes(str(data[off : off + 8])[2:-1],4)
            off += 8
            erase = memory_add + memory_size
            timeout = 15 #wait a second for reply to be send
            min_no_messages = -1
            max_no_messages = -1

            can_m_send = SC.can_m_send( "RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')
            can_mr_extra = ''

            SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
            time.sleep(1)
            testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_rec, can_nspace, step_no, purpose,
                                          timeout, min_no_messages, max_no_messages)
    
            testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')
        return testresult
    
    #Extraction of block data from vbf file
    def Block_data_extract(self, offset, data):
        PP_StringTobytes = SUTE.PP_StringTobytes
        unpack = struct.unpack
        [block_addr, block_len] = unpack('>2L', data[offset: offset + 8])
        offset += 8
        block_addr_by = PP_StringTobytes(hex(block_addr),4)
        block_len_by = PP_StringTobytes(hex(block_len),4)

        block_data = data[offset : offset + block_len]
        offset += block_len
        offset +=2
        return offset, block_data, block_addr_by, block_len_by, block_addr, block_len
    
    #crc calculation for each block
    def crc_calculation(self, data, offset, block_data, block_addr, block_len):
        unpack = struct.unpack
        crc = unpack('>H', data[offset : offset + 2])[0]
        #print(hex(crc))
        offset += 2
      
        crc_res = 'ok ' if SUTE.crc16(block_data) == crc else 'error'

        return "Block adr: 0x%X length: 0x%X crc %s" % (block_addr, block_len, crc_res)
    
    #Support function for Request Download
    def Request_Block_Download(self, stub, can_send, can_rec, can_nspace, step_no, purpose, block_addr_by, block_len_by, data_format):
        testresult = True
        PP_StringTobytes = SUTE.PP_StringTobytes
        unpack = struct.unpack
        # Parameters for FrameControl FC
        BS=0
        ST=0
        FC_delay = 0 #no wait
        FC_flag = 48 #continue sends
        FC_auto = False

        timeout = 0.05
        min_no_messages = -1
        max_no_messages = -1
        
        can_m_send = b'\x34' + data_format + b'\x44'+ block_addr_by + block_len_by
        can_mr_extra = ''

        SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
    
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_rec, can_nspace, step_no, purpose,
                                          timeout, min_no_messages, max_no_messages)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '74')

        NBL = PP_StringTobytes(SC.can_frames[can_rec][0][2][6:10],2)
        #print(SC.can_frames[can_receive][0][2])
        NBL = unpack('>H', NBL)[0]
        print("NBL: ",NBL)
        return testresult, NBL
    
    # Support function for Transfer Data
    def Flash_blocks(self, NBL, stub, can_send, can_rec, can_nspace, step_no, purpose, block_len, block_data):
        testresult = True
        pad = 0
        
        for i in range(int(block_len/(NBL-2))+1):
        
            pad = (NBL-2)*i
            i += 1
            ibyte = bytes([i])
            timeout = 0.02
            min_no_messages = -1
            max_no_messages = -1
            # Parameters for FrameControl FC
            BS=0
            ST=0
            FC_delay = 0 #no wait
            FC_flag = 48 #continue sends
            FC_auto = False

            can_m_send = b'\x36' + ibyte + block_data[pad:pad + NBL-2]
            
            can_mr_extra = ''
        
            SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
            
            testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                              can_rec, can_nspace, step_no, purpose,
                                              timeout, min_no_messages, max_no_messages)
            testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '76')
                #print(SC.can_messages[can_receive])
        return testresult
    
    #Support function for Request Transfer Exit
    def Transfer_data_exit(self, stub, can_send, can_rec, can_nspace, step_no, purpose): 
        testresult = True
        min_no_messages = 1
        max_no_messages = 1
        timeout = 0.02
        can_m_send = b'\x37'
        can_mr_extra = ''    
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_rec, can_nspace, step_no, purpose,
                                          timeout, min_no_messages, max_no_messages)

        return testresult  
    
    #Support function for Check Memory
    def Check_Memory(self, stub, can_send, can_rec, can_nspace, step_no, purpose, sw_signature1):
        testresult = True
        timeout = 2
        min_no_messages = -1
        max_no_messages = -1
        # Parameters for FrameControl FC
        BS=0
        ST=0
        FC_delay = 0 #no wait
        FC_flag = 48 #continue sends
        FC_auto = False
        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x12' + sw_signature1, b'\x01')
        can_mr_extra = ''
        SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
        time.sleep(1)
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')
        print(SC.can_messages[can_rec])
        return testresult
    
    #Support function for Routine Control Activate Secondary Bootloader
    def Activate_SBL(self, stub, can_send, can_rec, can_nspace, step_no, purpose,call):
        testresult = True
        timeout = 2 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1
        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x03\x01' + call, b'\x01')
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')
        return testresult
