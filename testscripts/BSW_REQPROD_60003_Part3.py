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
import threading
from threading import Thread

import random
import time

import grpc
import string

import logging
import os
import sys
sys.path.append('generated')

import volvo_grpc_network_api_pb2
import volvo_grpc_network_api_pb2_grpc
import volvo_grpc_functional_api_pb2
import volvo_grpc_functional_api_pb2_grpc
import common_pb2

# Global variable:
testresult = True
_heartbeat = False

#Global: Buffer for receives CAN frames and messages
#ToDo: Move to class after Pilot
can_frames = dict()
can_messages = dict()

#Global: Frame control handling
#ToDo: Move to class after Pilot
global FC_flag
global FC_responses
global FC_delay #in ms
global BS
global ST

def fill_payload(payload_value):
    #print ("payload to complete: ", str(payload_value))
    payload_value = bytes([len(payload_value)]) + payload_value
    while len(payload_value) < 8:
        payload_value = payload_value + bytes([0])
    #print ("new payload: ", payload_value)
    return(payload_value)

    
def signal2message( sigtime, mysignal):
    # format signal to be better readable
    #print ("mysignal in signal2message: ", mysignal.signal)
    return ([sigtime, mysignal.signal[0].id.name, "{0:016X}".format(mysignal.signal[0].integer)])
    
    
# subscribe to signal sig in namespace nsp
def subscribe_to_sig(stub, send, sig, nsp, timeout = 5):
    #time_start = time.time()
    source = common_pb2.ClientId(id="app_identifier")
    signal = volvo_grpc_network_api_pb2.SignalId(name=sig, namespace=nsp)
    sub_info = volvo_grpc_network_api_pb2.SubscriberConfig(name=source, signals=volvo_grpc_network_api_pb2.SignalIds(signal_id=[signal]), on_change=False)
    # add signal to dictionary, empty list of messages
    global can_frames
    global can_messages
    
    global FC_flag
    global FC_responses
    global FC_delay
    global BS
    global ST
    
    # create a new element for sig in dictionary
    can_frames[sig] = list()
    can_messages[sig] = list()
    
    print ("subscribe: new can_frames list", can_frames)
    #while True:
    try:
         #print ("list response in sub_info ", [stub.SubscribeToSignals(sub_info, timeout)])
        for response in stub.SubscribeToSignals(sub_info, timeout):
            #if multiframe detected prepare answer and send it
            det_mf = response.signal[0].integer>>60
            if (det_mf == 1): 
                ###FC_flag = 48 # 48=0x30 continue to send
                ###BS = 0           # send remaining frames without flow control
                ###ST = 0           # no separation time needed between frames
                ###FC_responses = 0 # number of FC responses already sent for current FC frame
                ###FC_delay = 0 # delay to send FC response in ms
                # send wanted reply with delay
                #print ("parameters for thread: ")
                #print ('Delay ', FC_delay/1000)
                #print ("send ", send, "NSP: ", nsp, "FC_flag ", FC_flag, " BS ", BS, " ST ", ST)
                
                #if (FC_delay == 0):
                #    send_FC_frame(stub, send, nsp, FC_flag, BS, ST)
                #else:
                time.sleep(FC_delay/1000)
                send_FC_frame(stub, send, nsp, FC_flag, BS, ST)
                #print ("FC_responses ", FC_responses)
                FC_responses += 1
                #print ("FC_responses ", FC_responses)
                
                #print ("Multiframe First")
                #print ("Length: ", "{0:03X}".format((response.signal[0].integer >> 48) & 0x0FFF))
                ### prepare and send FC frame
                #FC_flag = 48 #continue to send: b'\x30'
                #BS = 0 #no delay for remaining frames
                #ST = 0 #no separation time for remaining blocks
                #send_FC_frame(stub,send, nsp, FC_flag, BS, ST)
            
            #print ("formatting response: ", response)
            can_frames[sig].append(signal2message(time.time(), response)) 
            #print ("received: ", can_frames[sig])
    except grpc._channel._Rendezvous as err:
        # suppress 'Deadline Exceeded', show other errors
        if not err._state.details == "Deadline Exceeded":
            print(err)
        #print(err)
        #print("err_status: ", err._state.code)
        #print("err_details:", err._state.details)

def subscribe_signal(stub, can_send, can_rec, can_nspace, timeout):
    # start every subscribe as extra thread as subscribe is blocking
    t1 = Thread (target=subscribe_to_sig, args = (stub, can_send, can_rec, can_nspace, timeout))
    t1.deamon = True
    t1.start()


# make sure you have Front1CANCfg1 namespace in interfaces.json
#BO_ 1305 BecmFront1NMFr: 8 BECM
# SG_ InfotainmentAndHMI_BECM : 22|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCCharging_BECM : 25|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCPreClimatization_BECM : 26|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCDriving_BECM : 27|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCGlobal_BECM : 29|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCGSD_BECM : 30|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCStart_BECM : 24|1@0+ (1,0) [0|0] "" VCU1
# SG_ PNCHVEnergyStorage_BECM : 35|1@0+ (1,0) [0|0] "" VCU1
# SG_ NM_PNI_BECM : 14|1@0+ (1,0) [0|0] "" VCU1
# SG_ NM_AW_BECM : 12|1@0+ (1,0) [0|0] "" VCU1
# SG_ NM_CS_BECM : 11|1@0+ (1,0) [0|0] "" VCU1
# SG_ NM_RMR_BECM : 8|1@0+ (1,0) [0|0] "" VCU1
# SG_ NM_NodeID_BECM : 7|8@0+ (1,0) [0|0] "" VCU1
def subscribe_to_Heartbeat(stub):
    source = common_pb2.ClientId(id="app_identifier")
    signal = volvo_grpc_network_api_pb2.SignalId(name="BecmFront1NMFr", namespace="Front1CANCfg1")
    sub_info = volvo_grpc_network_api_pb2.SubscriberConfig(name=source, signals=volvo_grpc_network_api_pb2.SignalIds(signal_id=[signal]), on_change=False)
    while True:
        try:
            for response in stub.SubscribeToSignals(sub_info):
                print("Response start: \n", response)
                print("Response stop")
        except grpc._channel._Rendezvous as err:
                print(err)


# make sure you have Lin namespace in interfaces.json
def send_heartbeat(stub, signal_name, namespace, payload_value, intervall_sec):
    source = common_pb2.ClientId(id="app_identifier")
    #print ("Heartbeat: ", _heartbeat)
    while _heartbeat:
        try:
            #print ("send heartbeat signal_name: ", signal_name, " namespace: ", namespace)
            t_send_signal_hex(stub, signal_name, namespace, payload_value)
            time.sleep(intervall_sec)
        except grpc._channel._Rendezvous as err:
            print(err)


# make sure you have Lin namespace in interfaces.json
def t_send_signal(stub, signal_name, namespace, payload_value):
    #print ("t_send signal")
    source = common_pb2.ClientId(id="app_identifier")

    signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
    signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
    signal_with_payload.integer = payload_value
    publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
    try:
        stub.PublishSignals(publisher_info)
    except grpc._channel._Rendezvous as err:
        print(err)


# add offset \x40 to first byte
# add can_extra to message
def can_receive(can_send, can_extra):
    #print ("can_receive can_send ", can_send)
    #print ("can_receive can_extra ", can_extra)
    #print ("len can_send ", len(can_send))
    can_ret = ''
    
    #print ("Conditions:  len(can_send):", len(can_send), "len(can_extra):", len(can_extra), "can_send0 ", can_send[0]) 
    # check if receive frame/message can be build
    if (len(can_send) > 0) and (len(can_send)+len(can_extra) < 7) and (can_send[0] < 192):
        can_ret = bytes([can_send[0]+ 0x40 ])
        for c in range(len(can_send)-1):
            can_ret = can_ret + bytes([can_send[c+1]])
        for c in range(len(can_extra)):
            can_ret = can_ret + bytes([can_extra[c]])            
    print ("payload to receive: ", str(can_ret))
    return(can_ret)
    

# send GPIO message  with raw (hex) payload
def t_send_GPIO_signal_hex(stub, signal_name, namespace, payload_value):
    #print ("t_send GPIO signal_hex")
    source = common_pb2.ClientId(id="app_identifier")
    signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
    signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
    signal_with_payload.raw = payload_value
    #print ("source: ", source, " signal_with_PL: ",  payload_value)
    publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
    try:
        stub.PublishSignals(publisher_info)
    except grpc._channel._Rendezvous as err:
        print(err)
    
# send CAN message (8 bytes load) with raw (hex) payload
def t_send_signal_hex(stub, signal_name, namespace, payload_value):
    #print ("t_send signal_hex")
    source = common_pb2.ClientId(id="app_identifier")
    signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
    signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
    signal_with_payload.raw = payload_value
    #print ("source: ", source, " signal_with_PL: ",  payload_value)
    publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
    try:
        stub.PublishSignals(publisher_info)
    except grpc._channel._Rendezvous as err:
        print(err)


# similar to t_send_signal_hex, but payload is filled with length of payload, and fillbytes to 8 bytes
def t_send_signal_raw(stub, signal_name, namespace, payload_value):
    #print ("t_send signal_raw")

    source = common_pb2.ClientId(id="app_identifier")
    signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
    signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)

    signal_with_payload.raw = fill_payload(payload_value)
    publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]),  frequency = 0)
    try:
        stub.PublishSignals(publisher_info)
    except grpc._channel._Rendezvous as err:
        print(err)

# build FlowControl frame and send
def send_FC_frame(stub, signal_name, namespace, FC_flag, BS, ST):
    #print ("send_FC_frame")
    
    #print ("send_FC_frame parameters: SigName ", signal_name," NSP ",namespace," FC_flag ", FC_flag," BS ",BS, " ST ",ST)
    #payload = (FC_flag << 8) + BS
    #payload = (payload << 8) + ST
    if (FC_flag < 48) | (FC_flag > 50):
        print ("CAN Flowcontrol: Error FC_flag: Out_of_range ", FC_flag)
    if (BS > 255):
        print ("CAN Flowcontrol: Blocksize ouf_of_range ", BS)
    #if(ST < b'\xf1') | (ST > b'\xf9'):
    if(ST > 127) & ((ST < 241) | (ST > 249)):
        print ("CAN Flowcontrol: separationtime out_of_range", ST)
    #payload =  b'\x30\x00\x00\x00\x00\x00\x00\x00'
    #print ("payload FC ", FC_flag +1, "to_bytes ", FC_flag.to_bytes(1,'big'))
    #print ("payload BS ", BS, " to_bytes ", BS.to_bytes(1,'big'))
    #print ("payload ST ", ST, " to_bytes ", ST.to_bytes(1,'big'))
    
    payload = FC_flag.to_bytes(1,'big')+BS.to_bytes(1,'big')+ST.to_bytes(1,'big')+b'\x00\x00\x00\x00\x00'
    #print ("Payload FC frame", payload)
    t_send_signal_hex(stub, signal_name, namespace, payload)
    #can_messages[signal_name].append(list(payload)) #add to list of sent frames

# update list of messages for a given can_rec
def update_can_messages(stub, can_rec):
    global can_frames
    global can_messages
    # default message_status = 0 - single frame message
    message_status = 0
    mf_CF_count = 0
    mf_mess_size = 0
    #print ("update_can_messages")
    #can_messages[can_rec] = list()
    temp_message = [] #empty list as default
    
    #print ("number of frames ", len(can_frames[can_rec]))
    for i in can_frames[can_rec]:
    #print ("can frame  ", i[2].upper())
    #print ("test against ", can_answer.hex().upper())
        if (message_status == 0):
            #print ("message to handle: ", i[2])
            #print ("message to handle: ", i[2][0:1])
            #det_mf = i[2].integer >>60
            det_mf = int(i[2][0:1], 16)
            if (det_mf == 0):
                #Single frame message, add frame as message
                #can_messages[can_rec].append(i)
                temp_message = i
                #print ("Single frame message received")
            elif (det_mf == 1):
                # First frame of MF-message, change to status=2 consective frames to follow
                message_status = 2
                mf_CF_count = 32
                # get size of message to receive:
                #mf_mess_size = (i.integer >> 48) & 0x0FFF
                mf_mess_size = int(i[2][1:4], 16)
                #print ("update_can_message: message_size ", mf_mess_size)
                # add first payload
                #print ("update_can_message: whole frame ", i[2])
                #print ("update_can_message firstpayload ", i[2][10:])
                #temp_message = i[2][10:]
                temp_message = i[:]
                #temp_message = i[2]
                mf_size_remain = mf_mess_size - 6
                mf_CF_count = ((mf_CF_count + 1) & 0xF) + 32
            elif (det_mf == 2):
                print ("consecutive frame not expected without FC")
            elif (det_mf == 3):
                print ("Flow control received - not expected")
            else:
                print ("Reserved CAN-header")
        elif (message_status == 1):
            print ("message not expected")
        elif (message_status == 2):
            #print ("update_can_message: handling of CS frame")
            CF_count = int(i[2][0:2], 16)
            #print ("update_can_message: secure no frames dropped via CF count:", CF_count, "/", mf_CF_count)
            if (mf_size_remain > 7): 
                temp_message[2] = temp_message[2] + i[2][2:16]
                mf_size_remain -= 7
                mf_CF_count = ((mf_CF_count + 1) & 0xF) + 32
            else:
                temp_message[2] = temp_message[2] + i[2][2:(2+mf_size_remain*2)]
                mf_size_remain = 0
            #print ("temp_message    ", temp_message)
            #print ("can_frames      ", can_frames)
            #print ("mf_size_remain= ", mf_size_remain)
        else:
            print ("unexpected message status in can_frames")
    # don't add empty messages
    if (len(temp_message) > 0):
        can_messages[can_rec].append(list(temp_message))
    #print ("all can messages : ", can_messages)

def print_test_purpose(stub, stepno, purpose):
    print ("\nStep     ", stepno, ":")
    print ("Purpose: ", purpose)

    
# precondition for test running:
#  BECM has to be kept alive: start heartbeat
def precondition(stub, s, r, ns):
    global testresult
    global _heartbeat

    global FC_flag
    global FC_responses
    global FC_delay
    global BS
    global ST
    # start heartbeat, repeat every 0.8 second
    _heartbeat = True
    t = Thread (target=send_heartbeat, args = (stub,"EcmFront1NMFr", "Front1CANCfg1", b'\x20\x40\x00\xFF\x00\x00\x00\x00',0.8))
    t.daemon = True
    t.start()
    # wait for BECM to wake up
    time.sleep(5)
    # Register signals
    
    #messages = list()
    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_rec = "BecmToVcu1Front1DiagResFrame"
    can_nspace = "Front1CANCfg1"
    
    # Set default for CAN MF handling
    FC_flag = 48    # 48=0x30 continue to send
    BS = 0          # send remaining frames without flow control
    ST = 0          # no separation time needed between frames
    FC_responses = 0 # number of FC responses already sent for current FC frame
    FC_delay = 0    # delay to send FC response in ms

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    timeout = 300   #seconds
    #timeout = 40   #seconds
    subscribe_signal(stub, s, r, ns, timeout)
    #record signal we send as well
    subscribe_signal(stub, s, r, ns, timeout)
    
    print()
    step_0(stub, s, r, ns)
    
    print ("precondition testok:", testresult, "\n")

def test_message(messagelist, teststring=''):
    global testresult
    
    #print ("Messagelist: ", messagelist)
    if (messagelist == ''):
        print ("Empty messagelist")
    else:
        for i in messagelist:
        #print ("can frame  ", i[2].upper())
        #print ("test against ", teststring)
            if (teststring == ''):
                print ("Nothing expected. Received ", i[2].upper())
            elif teststring in i[2].upper():
                print ("Good: Expected: ", teststring, " received: ", i[2].upper())
                #continue
            else:
                testresult = False
                print ("Bad: Expected: ", teststring, " received: ", i[2].upper())

def teststep(stub, m_send, m_receive_extra, can_send = "", can_rec = "", can_nspace="", step_no = '', purpose="", timeout = 5, min_no_messages = 1, max_no_messages = 0, clear_old_mess= True):
    global testresult
    
    #clear old messages
    global can_messages
    if clear_old_mess: 
        can_frames[can_rec] = list()
        can_messages[can_rec] = list()
    
    print_test_purpose(stub, step_no, purpose)
    
    # wait for messages
    # define answer to expect
    can_answer = can_receive(m_send, m_receive_extra)
    #print ("can_frames to receive", can_answer)
    # message to send
    print ("To send:   [", time.time(), ", ", can_send, ", ", fill_payload(m_send).hex().upper(),"]")
    t_send_signal_raw(stub, can_send, can_nspace, m_send)
    #wait timeout for getting subscribed data
    time.sleep(timeout)
       
    #print ("all can frames for receiver : ", can_frames[can_rec])
    #print ("all rec can messages : ", can_messages[can_rec])
    update_can_messages(stub, can_rec)
    #print ("all can messages : ", can_messages)
    print ("rec can messages : ", can_messages[can_rec])
    if (len(can_messages[can_rec]) < min_no_messages):
        print ("Bad: min_no_messages not reached: ", len(can_messages[can_rec]))
        testresult = False
    elif max_no_messages > 0 and (len(can_messages[can_rec]) > max_no_messages):
        print ("Bad: max_no_messages ", len(can_messages[can_rec]))
    else:
        print ("number messages ", len(can_messages[can_rec]))
        test_message(can_messages[can_rec], can_answer.hex().upper())
    print ("Step ", step_no, " teststatus:", testresult, "\n")

    
# teststep 0: Complete ECU Part/Serial Number(s)
def step_0(stub, s, r, ns):
    can_m_send = b'\x22\xED\xA0'
    #can_mr_extra = b'\x01'
    can_mr_extra = ''
    
    stepno = 0
    purpose = "Complete ECU Part/Serial Number(s)"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 0
    
    teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    

# teststep 1: verify session
def step_1(stub, s, r, ns):
    can_m_send = b'\x22\xF1\x86'
    can_mr_extra = b'\x01'
    
    stepno = 1
    purpose = "Verify default session"
    timeout = 5
    min_no_messages = 1
    max_no_messages = 0
    
    teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)

    
# teststep 2: request EDA0 - complete ECU part/serial number default session
def step_2(stub, s, r, ns):
    global FC_flag
    #global FC_responses
    global FC_delay #in ms
    #global BS
    #global ST

    FC_flag = 49 #Wait
    FC_delay = 990 #wait 900ms before sending FC frame back
    
    can_m_send = b'\x22\xED\xA0'
    can_mr_extra = ''
    #can_mr_extra = b'\x02'
    
    stepno = 2
    purpose = "request EDA0 - complete ECU part/serial number to get MF reply"
    timeout = 0.1 #Don't wait - need to send FC frames
    min_no_messages = 0
    max_no_messages = 0
    
    teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)


# teststep 3: wait maxtime to send reply for first frame, send reply
def step_3(stub, s, r, ns):
    
    global FC_flag
    global FC_responses
    global FC_delay #in ms
    global BS
    global ST
    
    global can_frames

    stepno = 3
    purpose = "Verify FC with max number of WAIT frames"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    
    print ("Step ", stepno, ":")
    print ("Purpose: ", purpose)

    # do a loop:
    # send intended number of FC Wait frames
    #
    # controll number of frames sent from ECU

    FC_flag = 49    # b'\x31'
    BS = 0          # b'\x00'
    ST = 0          # b'\x00'
    FC_delay = 990  # requirement: wait max 900ms before sending FC frame back
    
    max_delay = 254   #number of delays wanted
    #max_delay = 24   #number of delays wanted
    
    # delay for TS in ms: if TS_delay < 127, if TS_delay between 0xF1 and 0xF9 then 100-900 usec
    # this one will allow delay bigger than 127 ms as needed for testing purposes
    #if ((TS_delay > 0xF1) & (TS_delay < 0xFA)):
    #    TSdelay = (TS_delay & 0x0F) / 10000
    #else:
    #    TSdelay = TS_delay / 1000
    
    for count in range(max_delay):
        time.sleep(FC_delay/1000)
        send_FC_frame(stub,s,ns,FC_flag,BS,ST)
        #FC = threading.Timer(FC_delay/1000, send_FC_frame, (stub,can_send,can_namespace,FC_flag,BS,ST)).start()
        FC_responses += 1
        print ("DelayNo.: ", FC_responses-1, ", Number of can_frames received: ", len(can_frames[r]))

        
# teststep 4: send flow control with WAIT flag (0x31), BS=0, ST=0
def step_4(stub, s, r, ns):
    global FC_flag
    global FC_responses
    global BS
    global ST

    #can_m_send = b'\x31\x00\x00\x00\x00\x00\x00\x00'
    #can_mr_extra = ''

    FC_flag = 48    # b'\x30'
    BS = 0          # b'\x00'
    ST = 0          # b'\x00'
   
    stepno = 4
    purpose = "Change FC to continue (0x30)"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    
    print_test_purpose(stub, stepno, purpose)
    print()
    print ("\nStep ", stepno, ":")
    print ("Purpose: ", purpose)
    
    time.sleep(FC_delay / 1000)
    send_FC_frame(stub,s,ns,FC_flag,BS,ST)


# teststep 5: update received messages and frames, display
def step_5(stub, s, r, ns):
    global can_frames
    global can_messages
#can_m_send = b'\x10\x02'
    #can_mr_extra = ''
    #
    stepno = 5
    purpose = "update received messages and frames, display"
    #timeout = 5
    #min_no_messages = 1
    #max_no_messages = 0
    #
    #teststep(stub, can_m_send, can_mr_extra, s, r, ns, stepno, purpose, timeout, min_no_messages, max_no_messages)
    
    print_test_purpose(stub, step_no, purpose)
    
    time.sleep(1)
    update_can_messages(stub, r)
    print ("Step5: messages received ", len(can_messages))
    print ("Step5: messages: ", can_messages, "\n")
    print ("Step5: frames received ", len(can_frames))
    print ("Step5: frames: ", can_frames, "\n")
    print("Test if string contains all IDs expected:")
    test_message(can_messages[r], teststring='62EDA0')
    test_message(can_messages[r], teststring='F120')
    test_message(can_messages[r], teststring='F12A')
    test_message(can_messages[r], teststring='F12B')
    test_message(can_messages[r], teststring='F12E')
    test_message(can_messages[r], teststring='F18C')
    

def run():
    global testresult
    global _heartbeat
    #start logging
    # to be implemented
    
    # where to connect to signal_broker
    #channel = grpc.insecure_channel('localhost:50051')
    
    # old Raspberry board Rpi 3B#channel
    #channel = grpc.insecure_channel('10.247.249.204:50051')
    
    # new Raspberry-board Rpi 3B+
    # ToDo: get IP via DNS
    channel = grpc.insecure_channel('10.246.47.27:50051')
    functional_stub = volvo_grpc_functional_api_pb2_grpc.FunctionalServiceStub(channel)
    network_stub = volvo_grpc_network_api_pb2_grpc.NetworkServiceStub(channel)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = "Front1CANCfg1"

    # Test PreCondition
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    root.info('BEGIN:  %s' % os.path.basename(__file__))
    
    
    print ("Testcase start: ", datetime.now())
    starttime = time.time()
    print ("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)
    #print ("after precond active threads ", threading.active_count())
    #print ("after precond thread enumerate ", threading.enumerate())

    #subscribe_to_BecmFront1NMFr(network_stub)
    
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    step_1(network_stub, can_send, can_receive, can_namespace)
    
    # step2:
    # action: check current session
    # result: BECM reports programmin session
    step_2(network_stub, can_send, can_receive, can_namespace)

    # step3:
    # action: send 'hard_reset' to BECM
    # result: BECM acknowledges message
    step_3(network_stub, can_send, can_receive, can_namespace)
    
    # step4:
    # action: check current session
    # result: BECM reports default session
    step_4(network_stub, can_send, can_receive, can_namespace)
   
    step_5(network_stub, can_send, can_receive, can_namespace)
    
    ############################################
    # postCondition
    ############################################
            
    print()
    print ("time ", time.time())
    print ("Testcase end: ", datetime.now())
    print ("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print ("Do cleanup now...")
    time.sleep(5)
    _heartbeat = False
    time.sleep(5)
    print ("waiting for threads to finish")

    #cleanup
    #postcondition(network_stub)
    while threading.active_count() > 1:
        item =(threading.enumerate())[-1]
        print ("thread to join ", item)
        item.join(5)
        time.sleep(5)
        #item2 = (threading.enumerate()) [-2]
        #print ("thread to join2 ", item2)
        #item2.join(5)
        #time.sleep
        print ("active thread after join ", threading.active_count() )
        print ("thread enumerate ", threading.enumerate())
            
    print()
    #print ("time ", time.time())
    #print ("Testcase end: ", datetime.now())
    #print ("Time needed for testrun (seconds): ", time.time() - starttime)
    if testresult:
        print ("Testcase result: PASSED")
    else:
        print ("Testcase result: FAILED")

    
if __name__ == '__main__':
    run()
