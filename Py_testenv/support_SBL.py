# project:  ODTB2 testenvironment using SignalBroker
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-07-11
# version:  1.2

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

from __future__ import print_function
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
class Support_SBL_Download:

    def SBL_Download(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose=""):
        """
        SBL Download 
        """
        testresult = True
        PP_StringTobytes = SUTE.PP_StringTobytes
        unpack = struct.unpack
        purpose = "SBL Download"

        # Parameters for FrameControl FC
        BS=0
        ST=0
        FC_delay = 0 #no wait
        FC_flag = 48 #continue send
        FC_auto = False

        """
        Read vbf file for SBL download
        """
        if len(sys.argv) !=2:
            print('Please specify VBF file')
            quit(-1)

        data = SUTE.main(sys.argv[1])
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
        #print(SUTE.CRC32_from_file(data[offset:len(data)]))
        block_address = unpack('>L', data[offset: offset + 4])[0]
        print(block_address)
        
        """
        Iteration to Download the SBL by blocks
        """
        while offset < len(data):
            [block_addr, block_len] = unpack('>2L', data[offset: offset + 8])
            offset += 8
            block_addr_by = PP_StringTobytes(hex(block_addr),4)
            block_len_by = PP_StringTobytes(hex(block_len),4)

            block_data = data[offset : offset + block_len]
            offset += block_len
        
            crc = unpack('>H', data[offset : offset + 2])[0]
            #print(hex(crc))
            offset += 2
      
            crc_res = 'ok ' if SUTE.crc16(block_data) == crc else 'error'
    
            #print(hex(SUTE.crc16(block_data)))

            print ("Block adr: 0x%X length: 0x%X crc %s" % (block_addr, block_len, crc_res))

            timeout = 0.05
            min_no_messages = -1
            max_no_messages = -1
        
            can_m_send = b'\x34\x10\x44'+ block_addr_by + block_len_by
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
        
            """
            Flash blocks to BECM with transfer data service 0x36
            """
            pad = 0
            for i in range(int(block_len/(NBL-2))+1):
        
                pad = (NBL-2)*i
                i += 1
                ibyte = bytes([i])
                timeout = 0.02
                min_no_messages = -1
                max_no_messages = -1

                can_m_send = b'\x36' + ibyte + block_data[pad:pad + NBL-2]
            
                can_mr_extra = ''
        
                SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
            
                testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                              can_rec, can_nspace, step_no, purpose,
                                              timeout, min_no_messages, max_no_messages)
                testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '76')
                #print(SC.can_messages[can_receive])

            """    
            Transfer data exit with service 0x37
            """
            min_no_messages = 1
            max_no_messages = 1
            can_m_send = b'\x37'
            can_mr_extra = ''    
            testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_rec, can_nspace, step_no, purpose,
                                          timeout, min_no_messages, max_no_messages)
          
        return testresult, sw_signature, call

    def SBL_Activation(self, stub, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose=""):
        """
        verify RoutineControlRequest is sent for Type 1
        """
        testresult = True
        purpose = "verify RoutineControl start are sent for Check Programming Preconditions"
        timeout = 1 #wait a second for reply to be send
        min_no_messages = -1
        max_no_messages = -1

        # Parameters for FrameControl FC
        BS=0
        ST=0
        FC_delay = 0 #no wait
        FC_flag = 48 #continue send
        FC_auto = False

        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x06', b'\x01')
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                        can_rec, can_nspace, step_no, purpose,
                                        timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')

        """
        Teststep 2: Change to Programming session
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
        purpose = "Security Access Request SID"
        timeout = 0.05
        min_no_messages = 1
        max_no_messages = 1

        can_m_send = b'\x27\x01'
        can_mr_extra = ''
    
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)

        R = SSA.SetSecurityAccessPins(SC.can_messages[can_rec][0][2][6:12])

        """
        Security Access Send Key
        """
        purpose = "Security Access Send Key"
        timeout = 0.05
        min_no_messages = -1
        max_no_messages = -1

        can_m_send = b'\x27\x02'+ R
        can_mr_extra = ''
    
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '6702') 

        """
        SBL Download 
        """
        
        purpose = 'SBL Download'
        tresult, sw_signature, call = self.SBL_Download(stub, can_send, can_rec, can_nspace, step_no, purpose)
        testresult = testresult and tresult
    
        """
        Check Memory
        """
       
        purpose = "verify RoutineControl start are sent for Type 1"
        timeout = 1 #wait a second for reply to be send

        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x12' + sw_signature, b'\x01')
        can_mr_extra = ''
        SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
            
        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')
        print(SC.can_messages[can_rec])
    
        """
        Activate SBL
        """
        purpose = "verify RoutineControl start are sent for Type 1"
        timeout = 2 #wait a second for reply to be send

        can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x03\x01' + call, b'\x01')
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_rec, can_nspace, step_no, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
        testresult = testresult and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_rec][0][2], 'Type1,Completed')
        return testresult

