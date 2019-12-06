# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-11-06
# version:  1.0
# #inspired by https://grpc.io/docs/tutorials/basic/python.html
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
from datetime import datetime
import sys
import binascii
import intelhex
import struct

import ODTB_conf
from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2

SC = Support_CAN()
SUTE = Support_test_ODTB2()

def precondition(stub, can_send, can_receive, can_namespace, result):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """
        
    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0", b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)
    
    SC.start_periodic(stub,"Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame", "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)
    
    # timeout = more than maxtime script takes
    timeout = 90   #seconds"

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    print()
    result = step_0(stub, can_send, can_receive, can_namespace, result)
    print("precondition testok:", result, "\n")
    return result

def step_0(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """

    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    print(SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result

def step_1(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 1: verify RoutineControlRequest is sent for Type 1
    """
    stepno = 1
    purpose = "verify RoutineControl start are sent for Check Programming Preconditions"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x06', b'\x01')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_frames[can_receive][0][2], 'Type1,Completed')
    return result

def step_2(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 2: Change to Programming session
    """
    
    stepno = 2
    purpose = "Change to Programming session(01) from default"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    return result

def step_3(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 3: Security Access Request SID
    """
    global R
    stepno = 3
    purpose = "Security Access Request SID"
    timeout = 0.05
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = b'\x27\x01'
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    R = SUTE.SetSecurityAccessPins(SC.can_messages[can_receive][0][2][6:12])
    return result

def step_4(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 4: Security Access Send Key
    """
    global R
    stepno = 4
    purpose = "Security Access Send Key"
    timeout = 0.05
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x27\x02'+ R
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    result = result and SUTE.test_message(SC.can_messages[can_receive], '6702') 
    return result 

def step_5(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 5:Flash Erase in PBL reply with Aborted
    """
    stepno = 5
    purpose = "Flash Erase Routine reply Aborted in PBL"

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False
    
    memory_add = SUTE.PP_StringTobytes(str('80000000'),4)
    
    memory_size = SUTE.PP_StringTobytes(str('0000C000'),4)

    erase = memory_add + memory_size
        
    timeout = 1 #wait a second for reply to be send

    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')
    can_mr_extra = ''

    SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
    time.sleep(1)
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_frames[can_receive][0][2], 'Type1,Aborted')
    
    return result

def step_6(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 6: SBL Download 
    """
    global call
    global sw_signature
    stepno = 6
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
    out_hex = intelhex.IntelHex()
    offset = header_len
    
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

        print ("Block adr: 0x%X length: 0x%X crc %s" % (block_addr, block_len, crc_res))

        timeout = 0.05
        min_no_messages = -1
        max_no_messages = -1
        
        can_m_send = b'\x34\x10\x44'+ block_addr_by + block_len_by
        can_mr_extra = ''

        SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
    
        result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_receive, can_namespace, stepno, purpose,
                                          timeout, min_no_messages, max_no_messages)
        result = result and SUTE.test_message(SC.can_messages[can_receive], '74')

        NBL = PP_StringTobytes(SC.can_frames[can_receive][0][2][6:10],2)
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
            
            result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                              can_receive, can_namespace, stepno, purpose,
                                              timeout, min_no_messages, max_no_messages)
            result = result and SUTE.test_message(SC.can_messages[can_receive], '76')

        """    
        Transfer data exit with service 0x37
        """
        min_no_messages = 1
        max_no_messages = 1
        can_m_send = b'\x37'
        can_mr_extra = ''    
        result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                          can_receive, can_namespace, stepno, purpose,
                                          timeout, min_no_messages, max_no_messages)      
    return result

def step_7(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 7: Check Memory
    """
    global sw_signature
    stepno = 7
    purpose = "verify RoutineControl start are sent for Type 1"
    timeout = 1 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x02\x12' + sw_signature, b'\x01')
    can_mr_extra = ''
    SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
            
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_receive][0][2], 'Type1,Completed')
    print(SC.can_messages[can_receive])
    return result

def step_8(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 8: Activate SBL
    """
    global call
    stepno = 8
    purpose = "verify RoutineControl start are sent for Type 1"
    timeout = 2 #wait a second for reply to be send
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID",b'\x03\x01' + call, b'\x01')
    can_mr_extra = ''

    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    
    result = result and SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_receive][0][2], 'Type1,Completed')
    return result

def step_9(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 9:Flash Erase of PBL memory address is not allowed
    """
    stepno = 9
    purpose = "Flash Erase of PBL memory address is not allowed"

    # Parameters for FrameControl FC
    BS=0
    ST=0
    FC_delay = 0 #no wait
    FC_flag = 48 #continue send
    FC_auto = False

    #memory address of PBL: PBL start with the address 80000000 for all ECU
    memory_add = SUTE.PP_StringTobytes(str('80000000'),4)
    #memory size to erase
    memory_size = SUTE.PP_StringTobytes(str('0000C000'),4)
    
    erase = memory_add + memory_size
        
    timeout = 5 #wait a second for reply to be send

    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01')
    can_mr_extra = ''

    SC.change_MF_FC(can_send, BS, ST, FC_delay, FC_flag, FC_auto)
    time.sleep(1)
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='7F3131')
    print(SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
    return result

def step_10(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 10: Reset
    """
    
    stepno = 10
    purpose = "ECU Reset"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = b'\x11\x01'
    can_mr_extra = ''
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)

    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    time.sleep(1)
    return result

def step_11(stub, can_send, can_receive, can_namespace, result):
    """
    Teststep 11: verify session
    """
    
    stepno = 11
    purpose = "Verify Default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIdentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    result = result and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                      can_receive, can_namespace, stepno, purpose,
                                      timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    return result
    
def run():
    """
    Run
    """

    test_result = True

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    print("Testcase start: ", datetime.now())
    starttime = time.time()
    print("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    test_result = precondition(network_stub, can_send, can_receive, can_namespace,test_result)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    #test_result = step_1(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 2:
    # action:
    # result: BECM sends positive reply
    test_result = step_2(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 3:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = step_3(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 4:
    # action: 
    # result: BECM sends positive reply
    test_result = step_4(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 5:
    # action: 
    # result: BECM sends positive reply
    test_result = step_5(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 6:
    # action: 
    # result: BECM sends positive reply
    test_result = step_6(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 7:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = step_7(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 8:
    # action: 
    # result: BECM sends positive reply
    test_result = step_8(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 9:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = step_9(network_stub, can_send, can_receive, can_namespace, test_result)

    # step 10:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply
    test_result = step_10(network_stub, can_send, can_receive, can_namespace, test_result)
    
    # step 11:
    # action: 
    # result: BECM sends positive reply
    test_result = step_11(network_stub, can_send, can_receive, can_namespace, test_result)
   
    ############################################
    # postCondition
    ############################################
            
    print()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print ("Do cleanup now...")
    print ("Stop all periodic signals sent")
    #SC.stop_heartbeat()
    SC.stop_periodic_all()
    #time.sleep(5)

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them 
    SC.thread_stop()
            
    print ("Test cleanup end: ", datetime.now())
    print()
    if test_result:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")
  
if __name__ == '__main__':
    run()
