# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-14
# version:  2.0
# reqprod:  74450
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
import os
import sys

import ODTB_conf

from support_can import Support_CAN
SC = Support_CAN()

from support_test_odtb2 import Support_test_ODTB2
SuTe = Support_test_ODTB2()

# Global variable:
testresult = True


    
# precondition for test running:
#  BECM has to be kept alive: start heartbeat
def precondition(stub, s, r, ns):
    global testresult
        
    # start heartbeat, repeat every 0.8 second
    #SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    
    #start_periodic(self, stub, per_name, per_id, per_send, per_nspace, per_frame, per_intervall)
    SC.start_periodic(stub, 'heartbeat', True, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)
    time.sleep(4) #wait for ECU startup
    
    #VCU1Front1Fr06, VehSpdLgtSafe
    
    #SC.set_periodic(self, per_name, per_send, per_id, per_nspace, per_frame, per_intervall)
    #SC.set_periodic('heartbeat', True, "EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.4)
    #time.sleep(2)
    
    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 300   #seconds
    timeout = 40   #seconds
    SC.subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, r, s, ns, timeout)
    
    print()
    step_0(stub, s, r, ns)
    
    print ("precondition testok:", testresult, "\n")

    
# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    global testresult
    
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 1
    
    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xED\xA0', "")
    can_mr_extra = ''

    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[r][0][2], title=''))  

# teststep 1: send signal vehicle velocity < 3km/h  
def step_1(stub):  

    stepno = 1
    purpose = "send signal vehicle velocity < 3km/h"
    SuTe.print_test_purpose(stepno, purpose)
    #VCU1Front1Fr06, VehSpdLgtSafe
    SC.start_periodic(stub, 'VehSpdLgtSafe', True, "VCU1Front1Fr06", "Front1CANCfg1", b'\x80\xd5\x00\x00\x00\x00\x00\x00',0.015)

# teststep 2: Change to programming session
def step_2(stub, s, r, ns):
    global testresult
    
    stepno = 2
    purpose = "Change to Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1
    
    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)

# teststep 3: verify programming session
def step_3(stub, s, r, ns):
    global testresult
    
    stepno = 3
    purpose = "Verify programming session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x02'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)
    
# teststep 4: Change to default session
def step_4(stub, s, r, ns):
    global testresult
    
    stepno = 4
    purpose = "Change to default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x01', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    


# teststep 5:  send signal vehicle velocity > 3 km/h   
def step_5():

    stepno = 5
    purpose = "send signal vehicle velocity > 3km/h"
    SuTe.print_test_purpose(stepno, purpose)
    SC.set_periodic('VehSpdLgtSafe', True, "VCU1Front1Fr06", "Front1CANCfg1", b'\x80\xd6\x00\x00\x00\x00\x00\x00',0.015)
    time.sleep(2)

# teststep 6: Change to programming session
def step_6(stub, s, r, ns):
    global testresult
    
    stepno = 6
    purpose = "Change to Programming session"
    timeout = 1
    min_no_messages = -1
    max_no_messages = -1

    can_m_send = SC.can_m_send( "DiagnosticSessionControl", b'\x02', "")
    can_mr_extra = ''
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    #time.sleep(1)
    print(SuTe.PP_Decode_7F_response(SC.can_messages[r][0][2]))

# teststep 7: verify default session
def step_7(stub, s, r, ns):
    global testresult
    
    stepno = 7
    purpose = "Verify default session"
    timeout = 1
    min_no_messages = 1
    max_no_messages = 1

    can_m_send = SC.can_m_send( "ReadDataByIentifier", b'\xF1\x86', "")
    can_mr_extra = b'\x01'
    
    testresult = testresult and SuTe.teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    time.sleep(1)

def run():
    global testresult
    #start logging
    # to be implemented
    
    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg1")

    # Test PreCondition
    #root = logging.getLogger()
    #root.setLevel(logging.DEBUG)
    #
    #ch = logging.StreamHandler(sys.stdout)
    #ch.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #ch.setFormatter(formatter)
    #root.addHandler(ch)
    #root.info('BEGIN:  %s' % os.path.basename(__file__))
    
    
    print ("Testcase start: ", datetime.now())
    starttime = time.time()
    print ("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: # send periodic signal vehicle velocity < 3km/h
    # result: 
    step_1(network_stub)

    # step 2:
    # action: # Change to Programming session
    # result: 
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step 3:
    # action: # Verify programming session
    # result: BECM reports mode
    step_3(network_stub, can_send, can_receive, can_namespace)

    # step 4:
    # action: # Change to Default session
    # result: BECM reports mode
    step_4(network_stub, can_send, can_receive, can_namespace)

    # step 5:
    # action: # send periodic signal vehicle velocity < 3km/h
    # result: 
    step_5()

    # step 6:
    # action: # Request change to Programming session with changed entry condition
    # result: BECM reports NRC
    step_6(network_stub, can_send, can_receive, can_namespace)
    
    # step 7:
    # action: # Verify default session
    # result: BECM reports mode
    step_7(network_stub, can_send, can_receive, can_namespace)


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
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()