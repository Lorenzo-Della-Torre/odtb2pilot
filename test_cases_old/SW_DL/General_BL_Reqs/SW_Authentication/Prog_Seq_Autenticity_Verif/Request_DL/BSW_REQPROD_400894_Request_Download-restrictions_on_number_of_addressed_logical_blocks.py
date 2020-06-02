# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-15
# version:  1.0
# reqprod:  400894

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
from datetime import datetime
import sys
import logging

import ODTB_conf
from support_can import Support_CAN, CanMFParam
from support_test_odtb2 import Support_test_ODTB2
from support_SBL import Support_SBL, VbfBlockFormat
from support_SecAcc import Support_Security_Access

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSBL = Support_SBL()
SSA = Support_Security_Access()

def precondition(stub, can_send, can_receive, can_namespace):
    """
    Precondition for test running:
    BECM has to be kept alive: start heartbeat
    """
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "MvcmFront1NMFr", "Front1CANCfg0",
                       b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)

    SC.start_periodic(stub, "Networkeptalive", True, "Vcu1ToAllFuncFront1DiagReqFrame",
                      "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)

    # timeout = more than maxtime script takes
    timeout = 1800   #seconds"

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

    result = step_0(stub, can_send, can_receive, can_namespace)
    logging.info("Precondition testok: %s\n", result)
    return result

def step_0(stub, can_send, can_receive, can_namespace):
    """
    Teststep 0: Complete ECU Part/Serial Number(s)
    """
    stepno = 0
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', ""),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Complete ECU Part/Serial Number(s)",\
                   "timeout" : 1,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1
                  }

    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    logging.info('%s', SUTE.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return result

def step_1(stub, can_send, can_receive, can_namespace):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(stub, can_send, can_receive, can_namespace,
                                 stepno, purpose)
    return result

def step_2(stub, can_send, can_receive, can_namespace):
    """
    Teststep 2: ESS Software Part Download
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    result = SSBL.sw_part_download(stub, SSBL.get_ess_filename(),
                                   can_send, can_receive, can_namespace,
                                   stepno, purpose)
    return result

def step_3(vbf_bl: VbfBlockFormat):
    """
    Teststep 3: Read VBF files for 1st file (1st Logical Block)
    """
    #global BLOCK_1
    stepno = 3
    purpose = "1st files reading"
    #global offset, data, data_format

    SUTE.print_test_purpose(stepno, purpose)
    data_files = SSBL.get_df_filenames()
    vbf_bl['offset'], _, vbf_bl['data'], _, vbf_bl['data_format'], _ =\
        SSBL.read_vbf_file(data_files[0])

def step_4(vbf_bl: VbfBlockFormat):
    """
    Teststep 4: Extract data for the 1st data block from 1st file
    """
    #global BLOCK_1
    stepno = 4
    purpose = "EXtract data for the 1st block from VBF"
    #global block_addr, block_len

    SUTE.print_test_purpose(stepno, purpose)

    _, _, vbf_bl['addr'], vbf_bl['len'], _ =\
        SSBL.block_data_extract(vbf_bl['offset'], vbf_bl['data'])

def step_5(stub, can_send, can_receive, can_namespace, vbf_bl: VbfBlockFormat):
    """
    Teststep 5: Request Download the 1st data block (1nd Logical Block)
    """
    #global BLOCK_1
    stepno = 5
    purpose = "Request Download the 1st data block (1nd Logical Block)"

    SUTE.print_test_purpose(stepno, purpose)

    block_addr_b = vbf_bl['addr'].to_bytes(4, 'big')
    block_len_b = vbf_bl['len'].to_bytes(4, 'big')
    result, _ = SSBL.request_block_download(stub,
                                            can_send, can_receive, can_namespace,
                                            stepno, purpose,
                                            block_addr_b, block_len_b, vbf_bl['data_format'])
    return result

def step_6(vbf_bl: VbfBlockFormat):
    """
    Teststep 6: Read VBF files for 2nd file (2nd Logical Block)
    """
    #global BLOCK_2
    stepno = 6
    purpose = "2nd files reading"

    SUTE.print_test_purpose(stepno, purpose)

    data_files = SSBL.get_df_filenames()
    vbf_bl['offset'], _, vbf_bl['data'], _, vbf_bl['data_format'], _ =\
        SSBL.read_vbf_file(data_files[1])

def step_7(vbf_bl: VbfBlockFormat):
    """
    Teststep 7: Extract data for the 1st data block from 2nd file
    """
    #global BLOCK_2
    stepno = 7
    purpose = "EXtract data for the 1st data block from VBF"

    SUTE.print_test_purpose(stepno, purpose)

    _, _, vbf_bl['addr'], vbf_bl['len'], _ =\
        SSBL.block_data_extract(vbf_bl['offset'], vbf_bl['data'])

def step_8(stub, can_send, can_receive, can_namespace, vbf_bl: VbfBlockFormat):
    """
    Teststep 8: Request Download the 1st data block (2nd Logical Block)
    """
    #global BLOCK_2
    stepno = 8
    block_addr_b = vbf_bl['addr'].to_bytes(4, 'big')
    block_len_b = vbf_bl['len'].to_bytes(4, 'big')
    ts_param = {"stub" : stub,\
                "m_send" : b'\x34' + vbf_bl['data_format'] + b'\x44'+ block_addr_b + block_len_b,\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Request Download the 1st data block",\
                   "timeout" : 0.05,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1
                  }

    # Parameters for FrameControl FC
    can_mf_param: CanMFParam = {
        'block_size' : 0,
        'separation_time' : 0,
        'frame_control_delay' : 0, #no wait
        'frame_control_flag' : 48, #continue send
        'frame_control_auto' : False
        }
    SC.change_MF_FC(can_send, can_mf_param)

    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='7F3431')

    logging.info('%s', SUTE.PP_Decode_7F_response(SC.can_frames[can_receive][0][2]))
    return result

def step_9(stub, can_send, can_receive, can_namespace, vbf_bl: VbfBlockFormat):
    """
    Teststep 9: Request Download again for the 1st data block (1st Logical Block)
    """
    #global block_addr, block_len
    #global BLOCK_1
    stepno = 9
    purpose = "Request Download again for the 1st data block (1st Logical Block)"

    SUTE.print_test_purpose(stepno, purpose)

    block_addr_b = vbf_bl['addr'].to_bytes(4, 'big')
    block_len_b = vbf_bl['len'].to_bytes(4, 'big')
    result, _ = SSBL.request_block_download(stub,
                                            can_send, can_receive, can_namespace,
                                            stepno, purpose,
                                            block_addr_b, block_len_b, vbf_bl['data_format'])
    return result

def step_10(stub, can_send, can_receive, can_namespace):
    """
    Teststep 10: Download SW Parts
    """
    stepno = 10
    purpose = "Download SW"

    result = True
    for i in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(stub, i, can_send, can_receive,
                                                  can_namespace, stepno, purpose)
    return result

def step_11(stub, can_send, can_receive, can_namespace):
    """
    Teststep 11: Check Complete And Compatible
    """
    stepno = 11
    purpose = "verify RoutineControl start are sent for Type 1"

    result = SSBL.check_complete_compatible_routine(stub, can_send, can_receive,
                                                    can_namespace, stepno, purpose)
    result = result and SUTE.test_message(SC.can_messages[can_receive], 'Complete, Compatible')
    return result

def step_12(stub, can_send, can_receive, can_namespace):
    """
    Teststep 12: Reset
    """
    stepno = 12
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ECUResetHardReset", b'', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "ECU Reset",\
                   "timeout" : 1,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1
                  }
    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    result = result and SUTE.test_message(SC.can_messages[can_receive], teststring='025101')
    return result

def step_13(stub, can_send, can_receive, can_namespace):
    """
    Teststep 13: verify session
    """
    stepno = 13
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', ""),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Verify Default session",\
                   "timeout" : 1,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1
                  }
    result = SUTE.teststep(ts_param,\
                           stepno, extra_param)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    block_1: VbfBlockFormat = {}
    block_2: VbfBlockFormat = {}

    ############################################
    # precondition
    ############################################
    result = precondition(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action:
    # result:
    result = result and step_1(network_stub, can_send, can_receive, can_namespace)

    # step 2:
    # action:
    # result:
    result = result and step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3:
    # action:
    # result:
    step_3(block_1)

    # step 4:
    # action:
    # result:
    step_4(block_1)

    # step 5:
    # action:
    # result:
    result = result and step_5(network_stub, can_send, can_receive, can_namespace, block_1)

    # step 6:
    # action:
    # result:
    step_6(block_2)

    # step 7:
    # action:
    # result:
    step_7(block_2)

    # step 8:
    # action:
    # result:
    result = result and step_8(network_stub, can_send, can_receive, can_namespace, block_2)

    # step 9:
    # action:
    # result:
    result = result and step_9(network_stub, can_send, can_receive, can_namespace, block_1)

    # step 10:
    # action:
    # result:
    result = result and step_10(network_stub, can_send, can_receive, can_namespace)

    # step 11:
    # action:
    # result:
    result = result and step_11(network_stub, can_send, can_receive, can_namespace)

    # step 12:
    # action:
    # result:
    result = result and step_12(network_stub, can_send, can_receive, can_namespace)
    time.sleep(1)

    # step 13:
    # action:
    # result:
    result = step_13(network_stub, can_send, can_receive, can_namespace, result)
    time.sleep(1)

    ############################################
    # postCondition
    ############################################

    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    run()
