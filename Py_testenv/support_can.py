# project:  ODTB2 testenvironment using SignalBroker
# author:   hweiler (Hans-Klaus Weiler)
# date:     2020-02-12
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

#from datetime import datetime
import time
#import logging
import os
import threading
from threading import Thread
import sys
#from typing import TypedDict, NewType
from typing import Dict, NewType
import yaml
import re
#import random
import grpc
#import string
sys.path.append('generated')
import network_api_pb2
import network_api_pb2_grpc
import functional_api_pb2
import functional_api_pb2_grpc
import system_api_pb2
import system_api_pb2_grpc
import common_pb2

#class Can_MF_Param(TypedDict):
#CANMFPARAMS = NewType('CANMFPARAMS', Dict)
#class CanMFParam(TypedDict):
class CanMFParam(Dict):
    """
        CanMFParam
        Added to allow fixed keys when setting MF parameters for CAN
    """
    block_size: int
    separation_time: int
    frame_control_delay: int
    frame_control_flag: bool
    frame_control_auto: bool

class Support_CAN:
    """
        class for supporting sending/receiving CAN frames
    """
    # Buffer for receives CAN frames and messages
    #can_cf_received = [1554802159.4773512, 'BecmToVcu1Front1DiagResFrame', '30000A000000FCCF']
    can_cf_received = dict()
    can_frames = dict()
    can_messages = dict()
    can_subscribes = dict()
    can_periodic = dict()


    _heartbeat = False
    _debug = False

    #init array for payload to send
    can_mf_send = dict()
    pl_array = []


    def add_pl_length(self, payload_value):
        """
        add_pl_length
        """
        payload_value = bytes([len(payload_value)]) + payload_value
        #print("new payload: ", payload_value)
        return payload_value

    def fill_payload(self, payload_value, fill_value=0):
        """
        fill_payload
        """
        print("payload to complete: ", str(payload_value))
        while len(payload_value) < 8:
            payload_value = payload_value + bytes([fill_value])
        print("new payload: ", payload_value)
        return payload_value

    def clear_old_CF_frames(self):
        """
        clear_old_CF_frames
        """
        for s_frame in self.can_cf_received:
            self.can_cf_received[s_frame] = list()

    def clear_can_message(self, can_mess):
        """
        clear_can_message
        """
        self.can_messages[can_mess] = list()
        return True

    def clear_all_can_messages(self):
        """
        clear_all_can_messages
        """
        for can_mess in self.can_messages:
            self.can_messages[can_mess] = list()
        return True

    def clear_can_frame(self, can_frame):
        """
        clear_can_frame
        """
        self.can_frames[can_frame] = list()
        return True

    def clear_all_can_frames(self):
        """
        clear_all_can_frames
        """
        for can_frame in self.can_frames:
            self.can_frames[can_frame] = list()
        return True

    def signal2message(self, sig_time, my_signal):
        """
        signal2message
        """
        # format signal to be better readable
        return ([sig_time, my_signal.signal[0].id.name,\
            "{0:016X}".format(my_signal.signal[0].integer)])


# subscribe to signal sig in namespace nsp
    def subscribe_to_sig(self, stub, send, sig, nsp, timeout=5):
        """
        subscribe_to_sig
        """
        #time_start=time.time()
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=sig, namespace=nsp)
        sub_info = network_api_pb2.SubscriberConfig(clientId=source,\
            signals=network_api_pb2.SignalIds(signalId=[signal]), onChange=False)

        # add signal to dictionary, empty list of messages
        self.can_frames[sig] = list()
        self.can_messages[sig] = list()
        self.can_cf_received[sig] = list()


# Frame control handling
        #default for each signal to register
        block_size = 0          # send remaining frames without flow control
        separation_time = 0          # no separation time needed between frames
        frame_control_delay = 0    # delay to send FC response in ms
        frame_control_flag = 48    # 48=0x30 continue to send
        frame_control_responses = 0    # number of FC responses sent already
                                       #(needed for max delay frames)
        frame_control_auto = True  # send FC frame automatically

        #print("subscribe: new can_frames list", self.can_frames)
        try:
            if timeout == 0:
                subscribe_object = stub.SubscribeToSignals(sub_info)
            else:
                subscribe_object = stub.SubscribeToSignals(sub_info, timeout)
            print("Subscribe to signal ", sig)
            self.can_subscribes[sig] =\
                [subscribe_object, block_size, separation_time, frame_control_delay,
                 frame_control_flag, frame_control_responses, frame_control_auto]
            #print("list response in sub_info ", [stub.SubscribeToSignals(sub_info, timeout)])
            for response in subscribe_object:
                #if multiframe detected prepare answer and send it
                det_mf = response.signal[0].integer>>60
                #print("Test if AUTO_FC[",sig,"]: ",self.can_subscribes[sig][6])
                if (det_mf == 1) and (self.can_subscribes[sig][6]):
                    # send wanted reply with delay
                    #print("send ", send, "NSP: ", nsp, "frame_control_flag ", frame_control_flag,\
                    #" block_size ", block_size, " separation_time ", separation_time)
                    time.sleep(self.can_subscribes[sig][3]/1000)
                    #self.send_FC_frame(stub, send, nsp, frame_control_flag, block_size,
                    #                   separation_time)
                    ###print("FC_values: frame_control_delay",self.can_subscribes[sig][4],\
                    ###         " block_size:", self.can_subscribes[sig][1],\
                    ###         " TS: ", self.can_subscribes[sig][2])
                    self.send_FC_frame(stub, send, nsp, self.can_subscribes[sig][4],\
                        self.can_subscribes[sig][1], self.can_subscribes[sig][2])
                    #print("frame_control_responses ", self.can_subscribes[sig][5])
                    # increment FC responses sent
                    self.can_subscribes[sig][5] += 1
                    #print("frame_control_responses ", self.can_subscribes[sig][5])
                #there is a MF to send, and FC received for it:
                if (det_mf == 3) and (send in self.can_mf_send and self.can_mf_send[send] == []):
                    print("No CF was expected for ", send)
                self.can_frames[sig].append(self.signal2message(time.time(), response))
                #print("received: ", self.can_frames[sig])
        except grpc._channel._Rendezvous as err:
            # suppress 'Deadline Exceeded', show other errors
            if not err._state.details == "Deadline Exceeded":
                print(err)
                #print("err_status: ", err._state.code)
                #print("err_details:", err._state.details)

    def subscribe_signal(self, stub, can_send, can_rec, can_nspace, timeout):
        """
        subscribe_signal
        """
        # start every subscribe as extra thread as subscribe is blocking
        t1 = Thread(target=self.subscribe_to_sig,\
                args=(stub, can_send, can_rec, can_nspace, timeout))
        t1.deamon = True
        t1.start()

    def unsubscribe_signal(self, signame):
        """
        unsubscribe_signal
        """
        # start every subscribe as extra thread as subscribe is blocking
        print("unsubscribe signal:", signame)
        #print("unsubcribe ", self.can_subscribes[signame][0])
        #print("received signals available: ", self.can_subscribes)
        self.can_subscribes[signame][0].cancel()


    def unsubscribe_signals(self):
        """
        unsubscribe_signals
        """

        #print("Signals to unsubscribe")
        #print("Number of signals subscribed ", len(self.can_subscribes))
        #print("Can signals subscribed to: ", self.can_subscribes)
        for unsubsc in self.can_subscribes:
            self.unsubscribe_signal(unsubsc)
        time.sleep(5)

    def thread_stop(self):
        """
        thread_stop
        """
        print("active threads remaining: ", threading.active_count())
        #cleanup
        #postcondition(network_stub)
        while threading.active_count() > 1:
            item = (threading.enumerate())[-1]
            print("thread to join ", item)
            item.join(5)
            time.sleep(5)
            print("active thread after join ", threading.active_count())
            print("thread enumerate ", threading.enumerate())


# start a periodic signal: parameters network_stub, send TRUE/FALSE,\
#                           name, DBC_name, DBC_namespace, CAN_frame, intervall
    def start_periodic(self, stub, per_name, per_send, per_id, per_nspace,\
                        per_frame, per_intervall):
        """
        start_periodic
        """
        print("start_sending_periodic: ", per_name)
        #self.can_periodic[per_name]=list()
        self.can_periodic[per_name] = [per_send, per_id, per_nspace, per_frame, per_intervall]
        #print("send_periodic1: ", self.can_periodic)
        #print("send_periodic2: ", self.can_periodic[per_name])

        # start periodic, repeat every per_intervall (ms)
        t = Thread(target=self.send_periodic, args=(stub, per_name))
        t.daemon = True
        t.start()
        print("wait 1sec for periodic signal to start:", per_name)
        time.sleep(1)
        #print("start_periodic end")

# update parameter to periodic signal: name, parameters send TRUE/FALSE,\
#                                       DBC_name, DBC_namespace, CAN_frame, intervall
    def set_periodic(self, per_name, per_send, per_id, per_nspace, per_frame, per_intervall):
        """
        set_periodic
        """
        if per_name in self.can_periodic:
            #print("can_periodic ", self.can_periodic)
            self.can_periodic[per_name][0] = per_send
            self.can_periodic[per_name][1] = per_id
            self.can_periodic[per_name][2] = per_nspace
            self.can_periodic[per_name][3] = per_frame
            self.can_periodic[per_name][4] = per_intervall
        else:
            print("set_periodic: Name " + per_name + "not in periodic signals")

# try to send periodic signal: parameters network_stub, name
    def send_periodic(self, stub, per_name):
        """
        send_periodic
        """
        #source = common_pb2.ClientId(id="app_identifier")
        while self.can_periodic[per_name][0]:
            #print("Can_periodic ", self.can_periodic[per_name])
            try:
                #print("send periodic signal_name: ", self.can_periodic[per_name])
                self.t_send_signal_hex(stub, self.can_periodic[per_name][1],\
                    common_pb2.NameSpace(name=self.can_periodic[per_name][2]),\
                                            self.can_periodic[per_name][3])
                time.sleep(self.can_periodic[per_name][4])
            except grpc._channel._Rendezvous as err:
                print(err)

    def stop_periodic(self, per_name):
        """
        stop_periodic
        """
        if per_name in self.can_periodic:
            print("stop_periodic ", per_name)
            self.set_periodic(per_name, False,\
                self.can_periodic[per_name][1],\
                self.can_periodic[per_name][2],\
                self.can_periodic[per_name][3],\
                self.can_periodic[per_name][4])
        else:
            print("set_periodic: Name " + per_name + "not in periodic signals")

    def stop_periodic_all(self):
        """
        stop_periodic_all
        """
        for per in self.can_periodic:
            self.stop_periodic(per)

# send frames as burst
    def send_burst(self, stub, burst_id, burst_nspace,\
                    burst_frame, burst_intervall, burst_quantity):
        """
        send_burst

        Sends a number of CAN-frames in a row with given intervall.
        That's sometimes needed for waking up MCU or getting frames sent
        withing a certain time intervall.

        Parameters
        burst_id        Name from CAN-DB for getting CAN ID for burst to be sent
        burst_namespace Namespace to look for burst-id
        burst_frame     String containing frame as hex
        burst_intervall time between frames to send
        burst_quantity  number of frames to be send as burst
        """
        for i in range(burst_quantity):
            self.t_send_signal_hex(stub, burst_id, burst_nspace, burst_frame)
            time.sleep(burst_intervall)


    def start_heartbeat(self, stub, hb_id, hb_nspace, hb_frame, hb_intervall):
        """
        start_heartbeat
        """
        print("start_heartbeat")
        self.start_periodic(stub, 'heartbeat', True, hb_id, hb_nspace, hb_frame, hb_intervall)
        #print("wait 5sec for heartbeat to start")
        time.sleep(4)
        print("start_heartbeat end")

    def stop_heartbeat(self):
        """
        stop_heartbeat
        """
        self.stop_periodic('heartbeat')


    def connect_to_signalbroker(self, sb_address, sb_port):
        """
        connect_to_signalbroker
        """
        channel = grpc.insecure_channel(sb_address + ':' + sb_port)
        functional_stub = functional_api_pb2_grpc.FunctionalServiceStub(channel)
        network_stub = network_api_pb2_grpc.NetworkServiceStub(channel)
        return network_stub

    def nspace_lookup(self, namespace):
        """
        nspace_lookup
        """
        return common_pb2.NameSpace(name=namespace)



# make sure you have Front1CANCfg0 namespace in interfaces.json
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
    def subscribe_to_heartbeat(self, stub):
        """
        subscribe_to_heartbeat
        """
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name="BecmFront1NMFr", namespace="Front1CANCfg0")
        sub_info = network_api_pb2.SubscriberConfig(clientId=source,\
                    signals=network_api_pb2.SignalIds(signalId=[signal]), onChange=False)
        while True:
            try:
                for response in stub.SubscribeToSignals(sub_info):
                    print("Response start: \n", response)
                    print("Response stop")
            except grpc._channel._Rendezvous as err:
                print(err)


# send signal on CAN: parameters name_DBC, namespace_DBC, payload
    def t_send_signal(self, stub, signal_name, namespace, payload_value):
        """
        t_send_signal
        """
        #print("t_send signal")
        source = common_pb2.ClientId(id="app_identifier")

        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.integer = payload_value
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                            signals=network_api_pb2.Signals(signal=[signal_with_payload]),\
                                                                    frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)


# add offset \x40 to first byte
# add can_extra to message
    def can_receive(self, can_send, can_extra):
        """
        can_receive
        """
        #print("can_receive can_send ", can_send)
        #print("can_receive can_extra ", can_extra)
        #print("len can_send ", len(can_send))
        can_ret = ''

        #print("Conditions:  len(can_send):", len(can_send), "len(can_extra):",\
        #                   len(can_extra), "can_send0 ", can_send[0])
        # check if receive frame/message can be build
        if (len(can_send) > 0) and (len(can_send)+len(can_extra) < 7) and (can_send[0] < 192):
            can_ret = bytes([can_send[0]+ 0x40])
            for c in range(len(can_send)-1):
                can_ret = can_ret + bytes([can_send[c+1]])
            for c in range(len(can_extra)):
                can_ret = can_ret + bytes([can_extra[c]])
        #print("payload to receive: ", str(can_ret))
        return can_ret


# send GPIO message  with raw (hex) payload
    def t_send_GPIO_signal_hex(self, stub, signal_name, namespace, payload_value):
        """
        t_send_GPIO_signal_hex
        """
        #print("t_send GPIO signal_hex")
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = payload_value
        #print("source: ", source, " signal_with_PL: ",  payload_value)
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)

    def send_FF_CAN(self, stub, s, ns, freq=0):
        """
        send_FF_CAN
        """
        print("send_FF_CAN")

        #print("Send first frame of MF")
        #print("payload available: ", self.can_mf_send)
        #print("payload signal:    ", self.can_mf_send[s])
        #print("first frame signal ", self.can_mf_send[s][1])
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=s, namespace=ns)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = self.can_mf_send[s][1][0]

        #print("Signal_with_payload : ", self.can_mf_send[s][1][0].hex().upper())
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=freq)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)
        self.can_mf_send[s][0] += 1 # notify frame sent
        print("Frames sent(FF/SF): ", self.can_mf_send[s][0], "of ", len(self.can_mf_send[s][1]))

    def send_CF_CAN(self, stub, s, r, ns, frequency=0, timeout_ms=1000):
        """
        send_CF_CAN
        """
        print("send_CF_CAN")
        time_start = time.time()
        last_frame = '00'

        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=s, namespace=ns)
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # wait for FC frame to arrive (max 1 sec)
        # take last frame received
        if self.can_frames[r]:
            last_frame = self.can_frames[r][-1][2]
        print("try to get FC frame")
        while ((time.time() - time_start)*1000 < timeout_ms) and (int(last_frame[0:1]) != 3):
            if self.can_frames[r] != []:
                last_frame = self.can_frames[r][-1][2]
        #print("Time till FC: ", (time.time() - time_start)*1000,\
        #"last_frame received: ", last_frame)
        #ToDo: if FC timed out: delete message to send
        if self.can_frames[r] == []:
            print("send_CF_CAN: FC timed out, discard rest of message to send")
            self.can_mf_send[s] = []
            return "Error: FC timed out, message discarded"

        # continue as stated in FC

        #print("last frame ", last_frame)
        #print("last frame ", last_frame[0:1])
        #print("last frame to test : ", int(last_frame[0:1]))
        if int(last_frame[0:1]) == 3:
            # fetch next CAN frames to send
            frame_control_flag = int(last_frame[1:2], 16)
            block_size = int(last_frame[2:4], 16)
            separation_time = int(last_frame[4:6], 16)

            # safe CF received for later analysis
            self.can_cf_received[r].append(self.can_frames[r][0])

            if frame_control_flag == 1:
                # Wait flag - wait for next FC frame
                self.send_CF_CAN(stub, s, r, ns, frequency, timeout_ms)
            elif frame_control_flag == 2:
                # overflow / abort
                print("Error: FC 32 received, empty buffer to send.")
                self.can_mf_send[s] = []
                return "Error: FC 32 received"
            elif frame_control_flag == 0:
                # continue sending as stated in FC frame
                print("continue sending MF message")
                # delay frame sent after FC received as stated if frame_control_delay
                if self.can_subscribes[s][3] != 0:
                    print("delay frame after FC as stated in frame_control_delay [ms]:",\
                        self.can_subscribes[s][3])
                    time.sleep(self.can_subscribes[s][3]/1000)
                #print("already sent: ", self.can_mf_send[s][0])
                #print("length mess:  ", len(self.can_mf_send[s][1]))
                while self.can_mf_send[s][0] < len(self.can_mf_send[s][1]):
                    signal_with_payload.raw = self.can_mf_send[s][1][self.can_mf_send[s][0]]
                    if self._debug:
                        print("Signal_with_payload : ", signal_with_payload.raw.hex().upper())
                    publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                        signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
                    try:
                        stub.PublishSignals(publisher_info)
                        self.can_mf_send[s][0] += 1
                        # wait ms, only 0-127 ms allowed, microseconds 0xF1-0xF9 ignored:
                        time.sleep((separation_time and 0x7F) / 1000)
                        if self._debug:
                            print("Frames sent(CF): ", self.can_mf_send[s][0],\
                                    "of ", len(self.can_mf_send[s][1]))
                        block_size -= 1
                        if block_size == 0: break
                    except grpc._channel._Rendezvous as err:
                        print(err)
            else:
                return "FAIL: invalid value in FC"
        if self.can_mf_send[s][0] == len(self.can_mf_send[s][1]):
            print("MF sent, remove MF")
            print("CAN_CF_RECEIVED: ", self.can_cf_received)
            #print("CAN_CF_RECEIVED: ", self.can_cf_received[r])
            #print("before: can_mf_send[s] ", self.can_mf_send[s])
            self.can_mf_send[s] = []
            #self.can_mf_send[s].pop(0)
            #print("after:  can_mf_send[s] ", self.can_mf_send[s])
            print("remove CF from received frames:")
            #print("before ", self.can_frames[r])
            #self.can_cf_received[r].append(self.can_frames[r][0])
            self.can_frames[r].pop(0)
            #print("after  ", self.can_frames[r])
            #print("Safed CF ", self.can_cf_received)
            return "OK: MF message sent"
        else:
            return "FAIL: MF message failed to send"

    def add_canframe_tosend(self, signal_name, frame):
        self.can_mf_send[signal_name][1].append(frame) # SF_Data_Length + payload


# send CAN MF message (0-4094 bytes payload hex)
    def t_send_signal_CAN_MF(self, stub, signal_name, rec_name, namespace,\
                             payload_value, padding=True, padding_byte=0x00):
        """
        t_send_signal_CAN_MF
        """
        pl_fcount = 0x21

        #self.can_mf_send[signal_name]
        #print("signals to send: ", self.can_mf_send)
        if signal_name in self.can_mf_send:
            while self.can_mf_send[signal_name]:
                print("CAN_MF_send: still payload to send. Wait 1sec")
                time.sleep(1)
        else:
            self.can_mf_send[signal_name] = []
        self.can_mf_send[signal_name] = [0, []] #number of frames to send, array of frames to send
        #print("signals to send: ", self.can_mf_send)
        #print("t_send signal_CAN_MF_hex")
        #print("send CAN_MF payload ", payload_value)
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # ToDo: test if payload can be sent over CAN(payload less then 4096 bytes)

        # build array of frames to send:
        mess_length = len(payload_value)
        pl_work = payload_value
        # if single_frame:
        if mess_length < 8:
            if padding:
                self.add_canframe_tosend(signal_name,\
                    self.fill_payload(bytes([mess_length])\
                    + payload_value, padding_byte)) # SF_Data_Length + payload
            else:
                self.add_canframe_tosend(signal_name, bytes([mess_length])\
                    + payload_value, padding_byte) # SF_Data_Length + payload
        # if multi_frame:
        elif mess_length < 4096:
            # add first frame
            #print("MF pl_append  ",\
            #    ( int(0x1000 | mess_length).to_bytes(2, 'big') + pl_work[0:6]).hex().upper() )
            self.add_canframe_tosend(signal_name,\
                (int(0x1000 | mess_length).to_bytes(2, 'big') + pl_work[0:6]))
            pl_work = pl_work[6:]
            #print("payload ", payload_value.hex().upper())
            print("Payload stored: ", self.can_mf_send)
            # add  remaining frames:
            while pl_work:
            # still bytes to take
                #print("payload rest ", pl_work)
                if len(pl_work) > 7:
                    #print("MF pl_append  ", ( bytes([pl_fcount]) + pl_work[0:6]).hex().upper() )
                    self.add_canframe_tosend(signal_name, (bytes([pl_fcount]) + pl_work[0:7]))
                    pl_work = pl_work[7:]
                    pl_fcount = (pl_fcount + 1) & 0x2F
                else:
                    if padding:
                        #print("MF pl_append  ", (self.fill_payload((bytes([pl_fcount]) +\
                        #       pl_work[0:]), padding_byte)).hex().upper() )
                        self.add_canframe_tosend(signal_name,\
                            self.fill_payload((bytes([pl_fcount]) + pl_work[0:]), padding_byte))
                    else:
                        #print("MF pl_append  ", (bytes([pl_fcount]) + pl_work[0:]).hex().upper() )
                        self.add_canframe_tosend(signal_name, bytes([pl_fcount]) + pl_work[0:])
                    pl_work = []
        if self._debug:
            print("PayLoad array as hex: : ")
            for pl_frames in self.can_mf_send[signal_name][1]:
                print(pl_frames.hex().upper())

        if self.can_mf_send[signal_name][1] == []:
            print("payload empty: nothing to send")
            # if single_frame:
        elif len(self.can_mf_send[signal_name][1]) == 1:
            #print("Send first frame SF: ", self.can_mf_send[signal_name][1][0])
            signal_with_payload.raw = self.can_mf_send[signal_name][1][0]
            #print("source: ", source, " signal_with_PL: ",  signal_with_payload.raw)
            publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
            try:
                stub.PublishSignals(publisher_info)
            except grpc._channel._Rendezvous as err:
                print(err)
            #remove payload after it's been sent
            print("remove payload after being sent")
            #print("can_mf_send ", self.can_mf_send)
            try:
                self.can_mf_send.pop(signal_name)
            except KeyError:
                print("Key ", signal_name, " not found.")
            #print("can_mf_send2 ", self.can_mf_send)
        elif len(self.can_mf_send[signal_name][1]) < 0x7ff:
            print("send payload as MF")
            # send payload as MF

            #send FirstFrame:
            self.send_FF_CAN(stub, signal_name, namespace, freq=0)
            #send ConsecutiveFrames:
            self.send_CF_CAN(stub, signal_name, rec_name, namespace)

            # wait for FC
            # send accordingly
        else:
            print("payload doesn't fit in one MF")


# send CAN message (8 bytes load) with raw (hex) payload
    def t_send_signal_hex(self, stub, signal_name, namespace, payload_value):
        """
        t_send_signal_hex
        """
        #print("t_send signal_hex")
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = payload_value
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                            signals=network_api_pb2.Signals(signal=[signal_with_payload]),\
                                                                    frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)


    def t_send_signal_raw(self, stub, signal_name, namespace, payload_value):
        """
        t_send_signal_raw
            similar to t_send_signal_hex, but payload is filled with length of payload \
            and fillbytes to 8 bytes
        """
        #print("t_send signal_raw")

        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)

        signal_with_payload.raw = self.fill_payload(self.add_pl_length(payload_value)\
                                                    + payload_value)
        publisher_info = network_api_pb2.PublisherConfig(
            clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]),\
                                                      frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err:
            print(err)


#change parameters of FC and how FC frame is used
    #def change_MF_FC(self, sig,\
    #                 block_size, separation_time,\
    #                 frame_control_delay, frame_control_flag,\
    #                 frame_control_auto):
    def change_MF_FC(self, sig, can_mf_param: CanMFParam):
        """
        change_MF_FC
        """
        print("change_MF_FC")
        print("change_MF_FC param:", can_mf_param)
        #global can_subscribes
        #print("can_subscribes ", self.can_subscribes)
        self.can_subscribes[sig][1] = can_mf_param['block_size']
        self.can_subscribes[sig][2] = can_mf_param['separation_time']
        self.can_subscribes[sig][3] = can_mf_param['frame_control_delay']
        self.can_subscribes[sig][4] = can_mf_param['frame_control_flag']
        #self.can_subscribes[sig][5]=can_mf_param.frame_control_responses
        self.can_subscribes[sig][6] = can_mf_param['frame_control_auto']

# build FlowControl frame and send
    def send_FC_frame(self, stub,\
                      signal_name, namespace,\
                      frame_control_flag, block_size,\
                      separation_time):
        """
        send_FC_frame
        """
        #print("send_FC_frame")

        #print("send_FC_frame parameters: SigName ", signal_name," NSP ",namespace, \
        #           " frame_control_flag ", frame_control_flag," block_size ",\
        #           block_size, " separation_time ",separation_time)
        #payload=(frame_control_flag << 8) + block_size
        #payload=(payload << 8) + separation_time
        if (frame_control_flag < 48) | (frame_control_flag > 50):
            print("CAN Flowcontrol: Error frame_control_flag: Out_of_range ", frame_control_flag)
        if block_size > 255:
            print("CAN Flowcontrol: Blocksize ouf_of_range ", block_size)
        #if(separation_time < b'\xf1') | (separation_time > b'\xf9'):
        if(separation_time > 127) & ((separation_time < 241) | (separation_time > 249)):
            print("CAN Flowcontrol: separationtime out_of_range", separation_time)
        #payload= b'\x30\x00\x00\x00\x00\x00\x00\x00'
        #print("payload FC ", frame_control_flag +1,\
        #      "to_bytes ", frame_control_flag.to_bytes(1,'big'))
        #print("payload block_size ", block_size,\
        #      " to_bytes ", block_size.to_bytes(1,'big'))
        #print("payload separation_time ", separation_time,\
        #      " to_bytes ", separation_time.to_bytes(1,'big'))

        payload = frame_control_flag.to_bytes(1, 'big') \
                    +block_size.to_bytes(1, 'big') \
                    +separation_time.to_bytes(1, 'big') \
                    +b'\x00\x00\x00\x00\x00'
        #print("Payload FC frame", payload)
        self.t_send_signal_hex(stub, signal_name, namespace, payload)
        #can_messages[signal_name].append(list(payload)) #add to list of sent frames

    def update_can_messages(self, can_rec):
        """
        update list of messages for a given can_rec

        parameter:
        can_rec :   dict() containing frames

        return:
        can_mess_updated :  True if messages could be build from CAN-frames in can_rec
                        False if frames contained in can_rec not being used for building a messages
        """
        # default message_status=0 - single frame message
        can_mess_updated = False
        message_status = 0
        mf_cf_count = 0
        mf_mess_size = 0
        #print("update_can_messages")
        temp_message = [] #empty list as default

        #print("records received ", can_rec)
        #print("number of frames ", len(self.can_frames[can_rec]))
        if len(self.can_frames[can_rec]) != 0:
            for i in self.can_frames[can_rec]:
                #print("whole can_frame : ",i)
                #print("can frame  ", i[2].upper())
                #print("test against ", can_answer.hex().upper())
                if message_status == 0:
                    #print("message to handle: ", i[2])
                    #print("message to handle: ", i[2][0:1])
                    det_mf = int(i[2][0:1], 16)
                    if det_mf == 0:
                        #Single frame message, add frame as message
                        #can_messages[can_rec].append(i)
                        temp_message = i
                        mf_size_remain = 0
                        #print("Single frame message received")
                    elif det_mf == 1:
                        # First frame of MF-message, change to status=2 consective frames to follow
                        message_status = 2
                        mf_cf_count = 32
                        # get size of message to receive:
                        #mf_mess_size = (i.integer >> 48) & 0x0FFF
                        mf_mess_size = int(i[2][1:4], 16)
                        #print("update_can_message: message_size ", mf_mess_size)
                        # add first payload
                        #print("update_can_message: whole frame ", i[2])
                        #print("update_can_message firstpayload ", i[2][10:])
                        #temp_message=i[2][10:]
                        temp_message = i[:]
                        mf_size_remain = mf_mess_size - 6
                        mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
                    elif det_mf == 2:
                        print("consecutive frame not expected without FC")
                    elif det_mf == 3:
                        if not can_rec in self.can_mf_send:
                            print("Flow control received - not expected")
                            print("Can-frame:  ", i)
                            #print("MF sent: ", self.can_mf_send)
                            return can_mess_updated
                        else:
                            print("MF sent: ", self.can_mf_send)
                            print("FC expected for ", can_rec)
                            #print("can_frames      ", self.can_frames)
                    else:
                        print("Reserved CAN-header")
                elif message_status == 1:
                    print("message not expected")
                elif message_status == 2:
                    #print("update_can_message: handling of CS frame")
                    #CF_count = int(i[2][0:2], 16)
                    #print("update_can_message: secure no frames dropped via CF count:",\
                    #           CF_count, "/", mf_cf_count)
                    if mf_size_remain > 7:
                        temp_message[2] = temp_message[2] + i[2][2:16]
                        mf_size_remain -= 7
                        mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
                    else:
                        temp_message[2] = temp_message[2] + i[2][2:(2+mf_size_remain*2)]
                        mf_size_remain = 0
                    #print("temp_message    ", temp_message)
                    #print("can_frames      ", self.can_frames)
                    #print("mf_size_remain= ", mf_size_remain)
                else:
                    print("unexpected message status in can_frames")
            # don't add empty messages
            if len(temp_message) > 0:
                if mf_size_remain == 0:
                    can_mess_updated = True
                    self.can_messages[can_rec].append(list(temp_message))
                    #print("can_mess_updated ", can_mess_updated)
            #print("all can messages : ", self.can_messages)
        return can_mess_updated

    def Extract_Parameter_yml(self, *argv, **kwargs):
        """
        Extract requested data from a Parameter dictionary from yaml.
        """
        # Import Parameters if REQPROD name are compatible
        pattern_req = re.match(r"\w+_(?P<reqprod>\d{3,})_\w+", sys.argv[0])
        listOfFiles = os.listdir('./parameters_yml')
        # intitialize a tuple
        value = dict()
        try:
            for entry in listOfFiles:
                entry_req = re.match(r"\w+_(?P<reqprod>\d{3,})\.\w+", entry)
                if entry_req.group('reqprod') == pattern_req.group('reqprod'):
                    entry_good = entry
            # extract yaml data from directory
            with open('./parameters_yml/' + entry_good) as f:
                data = yaml.safe_load(f)
        except IOError:
            logging.info("The pattern {} is not present in the directory\n"\
                  .format(pattern_req.group('reqprod')))
            sys.exit(1)
        for key, arg in kwargs.items():
            # if yaml key return value from yaml file
            if data[str(argv[0])].get(key) is not None:
                value[key] = data[str(argv[0])].get(key)
                #convert some values to bytes
                if key in('mode', 'mask', 'did'):
                    value[key] = bytes(value[key], 'utf-8')
            else:
                value[key] = arg
        return value

    def can_m_send(self, name, message, mask):
        """
            can_m_send

            support function for reading out DTC/DID data:
            services
            "DiagnosticSessionControl"=10
            "reportDTCExtDataRecordByDTCNumber"=19 06
            "reportDTCSnapdhotRecordByDTCNumber"= 19 04
            "reportDTCByStatusMask"=19 02 + "confirmedDTC"=03 / "testFailed"=00
            "ReadDataByIentifier"=22
            Etc.....
        """
        if name == "DiagnosticSessionControl":
            ret = b'\x10' + message
        elif name == "ECUResetHardReset":
            ret = b'\x11\x01' + message
        elif name == "ClearDiagnosticInformation":
            ret = b'\x14' + message
        elif name == "ReadDTCInfoExtDataRecordByDTCNumber":
            #ret = b'\x19\x06' + message + b'\xFF'
            ret = b'\x19\x06' + message + mask
        elif name == "ReadDTCInfoExtDataRecordByDTCNumber(86)":
            #ret = b'\x19\x86' + message + b'\xFF'
            ret = b'\x19\x86' + message + mask
        elif name == "ReadDTCInfoSnapshotRecordByDTCNumber":
            #ret = b'\x19\x04'+ message + b'\xFF'
            ret = b'\x19\x04'+ message + mask
        elif name == "ReadDTCInfoSnapshotRecordByDTCNumber(84)":
            #ret = b'\x19\x84'+ message + b'\xFF'
            ret = b'\x19\x84'+ message + mask
        elif name == "ReadDTCInfoSnapshotIdentification":
            #ret = b'\x19\x03'
            ret = b'\x19\x03'
        elif name == "ReadDTCInfoSnapshotIdentification(83)":
            #ret = b'\x19\x83'
            ret = b'\x19\x83'
        elif name == "ReadDTCInfoReportSupportedDTC":
            #ret = b'\x19\x0A'
            ret = b'\x19\x0A'
        elif name == "ReadDTCInfoReportDTCWithPermanentStatus":
            #ret = b'\x19\x15'
            ret = b'\x19\x15'

    #ReadDTCByStatusMask (02) support
        elif name == "ReadDTCByStatusMask":
            ret = b'\x19\x02'
            if mask == "confirmedDTC":
                ret = ret + b'\x03'
            elif mask == "testFailed":
                ret = ret + b'\x00'
            elif mask == "testFailedThisMonitoringCycle":
                ret = ret + b'\x01'
            elif mask == "pendingDTC":
                ret = ret + b'\x02'
            elif mask == "testNotCompletedSinceLastClear":
                ret = ret + b'\x04'
            elif mask == "testFailedSinceLastClear":
                ret = ret + b'\x05'
            elif mask == "testNotCompletedThisMonitoringCycle":
                ret = ret + b'\x06'
            elif mask == "warningIndicatorRequested":
                ret = ret + b'\x07'
            else:
                print("ReadDTC: Supported mask missing.\n")
                ret = b''
    #ReadDTCByStatusMask (82) support
        elif name == "ReadDTCByStatusMask(82)":
            ret = b'\x19\x82'
            if mask == "confirmedDTC":
                ret = ret + b'\x03'
            elif mask == "testFailed":
                ret = ret + b'\x00'
            elif mask == "testFailedThisMonitoringCycle":
                ret = ret + b'\x01'
            elif mask == "pendingDTC":
                ret = ret + b'\x02'
            elif mask == "testNotCompletedSinceLastClear":
                ret = ret + b'\x04'
            elif mask == "testFailedSinceLastClear":
                ret = ret + b'\x05'
            elif mask == "testNotCompletedThisMonitoringCycle":
                ret = ret + b'\x06'
            elif mask == "warningIndicatorRequested":
                ret = ret + b'\x07'
            else:
                print("ReadDTC: Supported mask missing.\n")
                ret = b''
        elif name == "ReadDataByIdentifier":
            ret = b'\x22'+ message
        elif name == "ReadMemoryByAddress":
            ret = b'\x23'+ mask + message
        elif name == "SecurityAccess":
            ret = b'\x27'+ mask + message
        elif name == "DynamicallyDefineDataIdentifier":
            ret = b'\x2A'+ mask + message
        elif name == "ReadDataBePeriodicIdentifier":
            ret = b'\x2C'+ mask + message
        elif name == "WriteDataByIdentifier":
            ret = b'\x2E'+ message
        elif name == "RoutineControlRequestSID":
            ret = b'\x31'+ mask + message
        elif name == "RequestUpload":
            ret = b'\x35'+ message
        elif name == "TransferData":
            ret = b'\x36'+ message
        elif name == "RequestDownload":
            ret = b'\x74'+ message
        elif name == "ReadGenericInformationReportGenericSnapshotByDTCNumber":
            #ret = b'\xAF\x04' + message + b'\xFF'
            ret = b'\xAF\x04' + message + mask
        elif name == "ReadGenericInformationReportGenericSnapshotByDTCNumber(84)":
            #ret = b'\xAF\x04' + message + b'\xFF'
            ret = b'\xAF\x84' + message + mask
        elif name == "ReadGenericInformationReportGenericExtendedDataByDTCNumber":
            #ret = b'\xAF\x06'+ message + b'\xFF'
            ret = b'\xAF\x06' + message + mask
        elif name == "ReadGenericInformationReportGenericExtendedDataByDTCNumber(86)":
            #ret = b'\xAF\x06'+ message + b'\xFF'
            ret = b'\xAF\x86' + message + mask
        else:
            print("You type a wrong name: ", name, "\n")
            ret = b''
        return ret
