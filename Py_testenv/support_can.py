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


#class for supporting sending/receiving CAN frames
class Support_CAN:

# Buffer for receives CAN frames and messages
    can_frames = dict()
    can_messages = dict()
    can_subscribes = dict()

    _heartbeat = False

    #init array for payload to send
    can_mf_send = dict()
    pl_array = []
    
    def add_pl_length(self, payload_value):
        payload_value = bytes([len(payload_value)]) + payload_value
        #print ("new payload: ", payload_value)
        return(payload_value)

    def fill_payload(self, payload_value, fill_value = 0):
        print ("payload to complete: ", str(payload_value))
        while len(payload_value) < 8:
            payload_value = payload_value + bytes([fill_value])
        print ("new payload: ", payload_value)
        return(payload_value)

    def clear_can_message(self, cm):
        self.can_messages[cm]=list()
    
    def clear_all_can_messages(self):
        for cm in self.can_messages:
            self.can_messages[cm]=list()

    def clear_can_frame(self, cf):
        self.can_frames[cf]=list()
    
    def clear_all_can_frames(self):
        for cf in self.can_frames:
            self.can_frames[cf]=list()
    
    def signal2message(self, sigtime, mysignal):
        # format signal to be better readable
        return ([sigtime, mysignal.signal[0].id.name, "{0:016X}".format(mysignal.signal[0].integer)])
    
    
# subscribe to signal sig in namespace nsp
    def subscribe_to_sig(self, stub, send, sig, nsp, timeout = 5):
        #time_start = time.time()
        source = common_pb2.ClientId(id="app_identifier")
        signal = volvo_grpc_network_api_pb2.SignalId(name=sig, namespace=nsp)
        sub_info = volvo_grpc_network_api_pb2.SubscriberConfig(name=source, signals=volvo_grpc_network_api_pb2.SignalIds(signal_id=[signal]), on_change=False)

        # add signal to dictionary, empty list of messages    
        self.can_frames[sig] = list()
        self.can_messages[sig] = list()
     
# Frame control handling
        #default for each signal to register
        BS = 0          # send remaining frames without flow control
        ST = 0          # no separation time needed between frames
        FC_delay = 0    # delay to send FC response in ms
        FC_flag = 48    # 48=0x30 continue to send
        FC_responses = 0    # number of FC responses sent already (needed for max delay frames)
        FC_auto = True  # send FC frame automatically
   
        #print ("subscribe: new can_frames list", self.can_frames)
        try:
            subscribe_object = stub.SubscribeToSignals(sub_info, timeout)
            print ("Subscribe to signal ", sig)
            self.can_subscribes[sig]=[subscribe_object, BS, ST, FC_delay, FC_flag, FC_responses, FC_auto]
            #print ("list response in sub_info ", [stub.SubscribeToSignals(sub_info, timeout)])
            for response in subscribe_object:
                #if multiframe detected prepare answer and send it
                det_mf = response.signal[0].integer>>60
                #print ("Test if AUTO_FC[",sig,"]: ",self.can_subscribes[sig][6])
                if (det_mf == 1) and (self.can_subscribes[sig][6]==True): 
                    # send wanted reply with delay
                    #print ("send ", send, "NSP: ", nsp, "FC_flag ", FC_flag, " BS ", BS, " ST ", ST)
                    time.sleep(self.can_subscribes[sig][3]/1000)
                    #self.send_FC_frame(stub, send, nsp, FC_flag, BS, ST)
                    ###print ("FC_values: FC_delay",self.can_subscribes[sig][4]," BS:", self.can_subscribes[sig][1]," TS: ", self.can_subscribes[sig][2])
                    self.send_FC_frame(stub, send, nsp, self.can_subscribes[sig][4], self.can_subscribes[sig][1], self.can_subscribes[sig][2])
                    #print ("FC_responses ", self.can_subscribes[sig][5])
                    # increment FC responses sent
                    self.can_subscribes[sig][5] += 1
                    #print ("FC_responses ", self.can_subscribes[sig][5])
                #there is a MF to send, and FC received for it:
                if (det_mf == 3) and (send in self.can_mf_send and self.can_mf_send[send]== []):
                    print ("No CF was expected for ", send)
                self.can_frames[sig].append(self.signal2message(time.time(), response)) 
                #print ("received: ", self.can_frames[sig])
        except grpc._channel._Rendezvous as err:
            # suppress 'Deadline Exceeded', show other errors
            if not err._state.details == "Deadline Exceeded":
                print(err)
                #print("err_status: ", err._state.code)
                #print("err_details:", err._state.details)

    def subscribe_signal(self, stub, can_send, can_rec, can_nspace, timeout):
        # start every subscribe as extra thread as subscribe is blocking
        t1 = Thread (target=self.subscribe_to_sig, args = (stub, can_send, can_rec, can_nspace, timeout))
        t1.deamon = True
        t1.start()


    def unsubscribe_signal(self, stub, signame):
        # start every subscribe as extra thread as subscribe is blocking
        print ("unsubscribe signal") 
        print ("received signals available: ", self.can_subscribes) 


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
    def subscribe_to_Heartbeat(self, stub):
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
    def send_heartbeat(self, stub, signal_name, namespace, payload_value, intervall_sec):
        source = common_pb2.ClientId(id="app_identifier")
        #print ("Heartbeat: ", _heartbeat)
        while self._heartbeat:
            try:
                #print ("send heartbeat signal_name: ", signal_name, " namespace: ", namespace)
                self.t_send_signal_hex(stub, signal_name, namespace, payload_value)
                time.sleep(intervall_sec)
            except grpc._channel._Rendezvous as err:
                print(err)


# make sure you have Lin namespace in interfaces.json
    def t_send_signal(self, signal_name, namespace, payload_value):
        #print ("t_send signal")
        source = common_pb2.ClientId(id="app_identifier")

        signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
        signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
        signal_with_payload.integer = payload_value
        publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
        try:
            self.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)


# add offset \x40 to first byte
# add can_extra to message
    def can_receive(self, can_send, can_extra):
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
        #print ("payload to receive: ", str(can_ret))
        return(can_ret)
    

# send GPIO message  with raw (hex) payload
    def t_send_GPIO_signal_hex(self, stub, signal_name, namespace, payload_value):
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

    def send_FF_CAN(self, stub, s, ns, frequency=0):
        print ("send_FF_CAN")
        
        #print ("Send first frame of MF")
        #print ("payload available: ", self.can_mf_send)
        #print ("payload signal:    ", self.can_mf_send[s])
        #print ("first frame signal ", self.can_mf_send[s][1])
        source = common_pb2.ClientId(id="app_identifier")
        signal = volvo_grpc_network_api_pb2.SignalId(name = s, namespace = ns)
        signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
        signal_with_payload.raw = self.can_mf_send[s][1][0]
        
        #print ("Signal_with_payload : ", self.can_mf_send[s][1][0].hex().upper())
        publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)
        self.can_mf_send[s][0] += 1 # notify frame sent
        print ("Frames sent(FF/SF): ", self.can_mf_send[s][0], "of ", len(self.can_mf_send[s][1]))

    def send_CF_CAN(self, stub, s, r, ns, frequency=0, timeout_ms = 1000):
        print ("send_CF_CAN")
        time_start = time.time()
        last_frame = '00'
        
        source = common_pb2.ClientId(id="app_identifier")
        signal = volvo_grpc_network_api_pb2.SignalId(name = s, namespace = ns)
        signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
        
        # wait for FC frame to arrive (max 1 sec)
        # take last frame received
        if self.can_frames[r]:
            last_frame = self.can_frames[r][-1][2]
        print ("try to get FC frame")
        while ((time.time() - time_start)*1000 < timeout_ms) and (int(last_frame[0:1]) != 3):
            if (self.can_frames[r] != []): 
                last_frame = self.can_frames[r][-1][2]
            #print ("Time till FC: ", (time.time() - time_start)*1000, "last_frame received: ", last_frame)
        
        # continue as stated in FC
            
        #print ("last frame ", last_frame)
        #print ("last frame ", last_frame[0:1])
        #print ("last frame to test : ", int(last_frame[0:1]))
        if int(last_frame[0:1]) == 3:
            # fetch next CAN frames to send
            FC_flag = int(last_frame[1:2],16)
            BS = int(last_frame[2:4],16)
            ST = int(last_frame[4:6],16)
            print ("FC_flag ", FC_flag)
        
            if FC_flag == 1:
                # Wait flag - wait for next FC frame
                self.send_CF_CAN (stub, s, r, ns, frequency, timeout_ms)
            elif FC_flag == 2:
                # overflow / abort
                return ("Error: FC 32 received")
            elif FC_flag == 0:
                # continue sending as stated in FC frame
                print ("continue sending MF message")
                #print ("already sent: ", self.can_mf_send[s][0])
                #print ("length mess:  ", len(self.can_mf_send[s][1]))
                while self.can_mf_send[s][0] < len(self.can_mf_send[s][1]):
                    signal_with_payload.raw = self.can_mf_send[s][1][self.can_mf_send[s][0]]
                    print ("Signal_with_payload : ", signal_with_payload.raw.hex().upper())
                    publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
                    try:
                        stub.PublishSignals(publisher_info)
                        self.can_mf_send[s][0] += 1
                        time.sleep((ST and 0x7F) / 1000) # wait ms, only 0-127 ms allowed, microseconds 0xF1-0xF9 ignored
                        print ("Frames sent(CF): ", self.can_mf_send[s][0], "of ", len(self.can_mf_send[s][1]))
                        BS -= 1
                        if BS == 0: break
                    except grpc._channel._Rendezvous as err:
                        print(err)
            else:
                return ("FAIL: invalid value in FC")
        if (self.can_mf_send[s][0] == len(self.can_mf_send[s][1])):
            print ("MF sent, remove MF")
            #print ("before: can_mf_send[s] ", self.can_mf_send[s])
            self.can_mf_send[s]=[]
            #self.can_mf_send[s].pop(0)
            #print ("after:  can_mf_send[s] ", self.can_mf_send[s])
            print ("remove CF from received frames:")
            print ("before ", self.can_frames[r])
            self.can_frames[r].pop(0)
            print ("after  ", self.can_frames[r])
            return ("OK: MF message sent")
        else:
            return ("FAIL: MF message failed to send")

    def add_canframe_tosend(self, signal_name, frame):
        self.can_mf_send[signal_name][1].append(frame) # SF_Data_Length + payload

            
# send CAN MF message (0-4094 bytes payload hex)
    def t_send_signal_CAN_MF(self, stub, signal_name, rec_name, namespace, payload_value, padding = True, padding_byte = 0x00):
        pl_fcount = 0x21
        
        #self.can_mf_send[signal_name]
        #print ("signals to send: ", self.can_mf_send)
        if signal_name in self.can_mf_send:
            while self.can_mf_send[signal_name]:
                print ("CAN_MF_send: still payload to send. Wait 1sec")
                time.sleep(1)
        else:
            self.can_mf_send[signal_name]=[]
        self.can_mf_send[signal_name] = [0, []] #number of frames to send, array of frames to send
        #print ("signals to send: ", self.can_mf_send)
        #print ("t_send signal_CAN_MF_hex")
        #print ("send CAN_MF payload ", payload_value)
        source = common_pb2.ClientId(id="app_identifier")
        signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
        signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
        
        # ToDo: test if payload can be sent over CAN (payload less then 4096 bytes)

        # build array of frames to send:
        mess_length= len(payload_value)
        pl_work = payload_value
        # if single_frame:
        if mess_length < 8:
            if padding:
                self.add_canframe_tosend(signal_name, self.fill_payload(bytes([mess_length]) + payload_value, padding_byte)) # SF_Data_Length + payload
            else:
                self.add_canframe_tosend(signal_name, bytes([mess_length]) + payload_value, padding_byte) # SF_Data_Length + payload
        # if multi_frame:
        elif mess_length < 4096:
            # add first frame
            #print ("MF pl_append  ", ( int(0x1000 | mess_length).to_bytes(2, 'big') + pl_work[0:6]).hex().upper() )
            self.add_canframe_tosend(signal_name, ( int(0x1000 | mess_length).to_bytes(2, 'big') + pl_work[0:6])) 
            pl_work = pl_work[6:]
            #print ("payload ", payload_value.hex().upper())
            print ("Payload stored: ", self.can_mf_send)
            # add  remaining frames:
            while pl_work:
            # still bytes to take
                #print ("payload rest ", pl_work)
                if len(pl_work) > 7:
                    #print ("MF pl_append  ", ( bytes([pl_fcount]) + pl_work[0:6]).hex().upper() )
                    self.add_canframe_tosend(signal_name, (bytes([pl_fcount]) + pl_work[0:7])) 
                    pl_work = pl_work[7:]
                    pl_fcount = (pl_fcount + 1) & 0x2F
                else:
                    if padding:
                        #print ("MF pl_append  ", (self.fill_payload((bytes([pl_fcount]) + pl_work[0:]), padding_byte)).hex().upper() )
                        self.add_canframe_tosend(signal_name, self.fill_payload((bytes([pl_fcount]) + pl_work[0:]), padding_byte))
                    else:
                        #print ("MF pl_append  ", (bytes([pl_fcount]) + pl_work[0:]).hex().upper() )
                        self.add_canframe_tosend(signal_name, bytes([pl_fcount]) + pl_work[0:])
                    pl_work = []
        print ("PayLoad array as hex: : ")
        for pl_frames in self.can_mf_send[signal_name][1]:
            print (pl_frames.hex().upper())

        if (self.can_mf_send[signal_name][1] == []):
            print ("payload empty: nothing to send")
            # if single_frame:
        elif len(self.can_mf_send[signal_name][1]) == 1:
            #print ("Send first frame SF: ", self.can_mf_send[signal_name][1][0])
            signal_with_payload.raw = self.can_mf_send[signal_name][1][0]
            print ("source: ", source, " signal_with_PL: ",  signal_with_payload.raw)
            publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
            try:
                stub.PublishSignals(publisher_info)
            except grpc._channel._Rendezvous as err:
                print(err)
            #remove payload after it's been sent
            print ("remove payload after being sent")
            #print ("can_mf_send ", self.can_mf_send)
            try:
                self.can_mf_send.pop(signal_name)
            except KeyError:
                print("Key ", signal_name, " not found.")
            #print ("can_mf_send2 ", self.can_mf_send)
        elif len(self.can_mf_send[signal_name][1]) < 0x7ff:
            print ("send payload as MF")
            # send payload as MF
            
            #send FirstFrame:
            self.send_FF_CAN( stub, signal_name, namespace, frequency=0)
            #send ConsecutiveFrames:
            self.send_CF_CAN( stub, signal_name, rec_name, namespace)
            
            # wait for FC
            # send accordingly
        else:
            print ("payload doesn't fit in one MF")
        
    
# send CAN message (8 bytes load) with raw (hex) payload
    def t_send_signal_hex(self, stub, signal_name, namespace, payload_value):
        #print ("t_send signal_hex")
        source = common_pb2.ClientId(id="app_identifier")
        signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
        signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)
        signal_with_payload.raw = payload_value
        publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]), frequency = 0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)


# similar to t_send_signal_hex, but payload is filled with length of payload, and fillbytes to 8 bytes
    def t_send_signal_raw(self, stub, signal_name, namespace, payload_value):
        #print ("t_send signal_raw")

        source = common_pb2.ClientId(id="app_identifier")
        signal = volvo_grpc_network_api_pb2.SignalId(name = signal_name, namespace = namespace)
        signal_with_payload = volvo_grpc_network_api_pb2.Signal(id = signal)

        signal_with_payload.raw = self.fill_payload(self.add_pl_length(payload_value) + payload_value)
        publisher_info = volvo_grpc_network_api_pb2.PublisherConfig(name = source, signals=volvo_grpc_network_api_pb2.Signals(signal=[signal_with_payload]),  frequency = 0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)


#change parameters of FC and how FC frame is used
    def change_MF_FC(self, sig, BS, ST, FC_delay, FC_flag, FC_auto):
        #global can_subscribes
        #print ("can_subscribes ", self.can_subscribes)
        self.can_subscribes[sig][1] = BS
        self.can_subscribes[sig][2] = ST
        self.can_subscribes[sig][3] = FC_delay
        self.can_subscribes[sig][4] = FC_flag
        #self.can_subscribes[sig][5] = FC_responses
        self.can_subscribes[sig][6] = FC_auto

# build FlowControl frame and send
    def send_FC_frame(self, stub, signal_name, namespace, FC_flag, BS, ST):
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
        self.t_send_signal_hex(stub, signal_name, namespace, payload)
        #can_messages[signal_name].append(list(payload)) #add to list of sent frames

# update list of messages for a given can_rec
    def update_can_messages(self, can_rec):
        # default message_status = 0 - single frame message
        message_status = 0
        mf_CF_count = 0
        mf_mess_size = 0
        #print ("update_can_messages")
        temp_message = [] #empty list as default
    
        #print ("number of frames ", len(self.can_frames[can_rec]))
        for i in self.can_frames[can_rec]:
        #print ("can frame  ", i[2].upper())
        #print ("test against ", can_answer.hex().upper())
            if (message_status == 0):
                #print ("message to handle: ", i[2])
                #print ("message to handle: ", i[2][0:1])
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
                    mf_size_remain = mf_mess_size - 6
                    mf_CF_count = ((mf_CF_count + 1) & 0xF) + 32
                elif (det_mf == 2):
                    print ("consecutive frame not expected without FC")
                elif (det_mf == 3):
                    if not (can_rec in self.can_mf_send):
                        print ("Flow control received - not expected")
                        print ("Can-frame:  ", i)
                        #print ("MF sent: ", self.can_mf_send)
                    else:
                        print ("MF sent: ", self.can_mf_send)
                        print ("FC expected for ", can_rec)
                        #print ("can_frames      ", self.can_frames)
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
                #print ("can_frames      ", self.can_frames)
                #print ("mf_size_remain= ", mf_size_remain)
            else:
                print ("unexpected message status in can_frames")
        # don't add empty messages
        if (len(temp_message) > 0):
            self.can_messages[can_rec].append(list(temp_message))
        #print ("all can messages : ", self.can_messages)
        
     #support function for reading out DTC/DID data:
    #services
    #"DiagnosticSessionControl"=10
    #"reportDTCExtDataRecordByDTCNumber"=19 06
    #"reportDTCSnapdhotRecordByDTCNumber"= 19 04
    #"reportDTCByStatusMask" = 19 02 + "confirmedDTC"=03 / "testFailed" = 00
    #"ReadDataByIentifier" = 22
    # Etc.....
    def can_m_send(self, name, message, mask):
        if name == "DiagnosticSessionControl":
            ret = b'\x10' + message
        elif name == "reportDTCExtDataRecordByDTCNumber":
            ret = b'\x19\x06' + message + b'\xFF'
        elif name == "reportDTCSnapdhotRecordByDTCNumber":
            ret = b'\x19\x04'+ message + b'\xFF'
        elif name == "reportDTCByStatusMask":
            if mask == "confirmedDTC":
                ret = b'\x19\x02\x03'
            elif mask == "testFailed":
                ret = b'\x19\x02\x00'
            else:
                print("You type not supported mask", "\n")
                ret = b''

        elif name == "ReadDataByIentifier":
            ret = b'\x22'+ message
        else:
            print("You type a wrong name", "\n")
            ret = b''

        return ret