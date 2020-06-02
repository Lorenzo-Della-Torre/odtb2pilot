""" project:  ODTB2 testenvironment using SignalBroker
    author:   fjansso8 (Fredrik Jansson)
    date:     2020-05-12
    version:  1.3

    Inspired by https://grpc.io/docs/tutorials/basic/python.html

    Copyright 2015 gRPC authors.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    The Python implementation of the gRPC route guide client.
"""

import time
import logging
import os
import threading
from threading import Thread
import sys
#from typing import TypedDict, NewType
from typing import Dict
import re
import yaml
import grpc
#from support_can_hw import SupportCanHW
#SC_HW = SupportCanHW()
sys.path.append('generated')

import network_api_pb2 # pylint: disable=wrong-import-position
import network_api_pb2_grpc # pylint: disable=wrong-import-position
#import functional_api_pb2
import functional_api_pb2_grpc # pylint: disable=wrong-import-position
#import system_api_pb2
#import system_api_pb2_grpc
import common_pb2 # pylint: disable=wrong-import-position


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


class CanParam(Dict):
    """
        CanParam
        All CAN send/receive parameters
    """
    netstub: str
    send: str
    receive: str
    namespace: str


class CanTestExtra(Dict):
    """
        CanTestExtra
    """
    step_no: int
    purpose: str
    timeout: int
    min_no_messages: int
    max_no_messages: int


class CanPayload(Dict):
    """
        CanPayload
        payload to send,
        extra   to add to command
    """
    payload: bytes
    extra: bytes

class Support_CAN:
    # Disable the too-many-public-methods violation. Not sure how to split it
    # pylint: disable=too-many-public-methods
    """
        class for supporting sending/receiving CAN frames
    """
    # Buffer for receives CAN frames and messages
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

    def clear_old_cf_frames(self):
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


    @classmethod
    def signal2message(cls, sig_time, my_signal):
        """
        signal2message
        """
        # Format signal to be better readable
        return ([sig_time, my_signal.signal[0].id.name,\
            "{0:016X}".format(my_signal.signal[0].integer)])


    #def subscribe_to_sig(self, can_param, sig, timeout=5):
    def subscribe_to_sig(self, can_p: CanParam, timeout=5):
        """
        Subscribe to signal sig in namespace nsp

        can_p["netstub"] = stub
        can_p["send"] = send
        can_p["namespace"] = nsp
        """
        #time_start=time.time()
        source = common_pb2.ClientId(id="app_identifier")
        #signal = common_pb2.SignalId(name=sig, namespace=can_param["can_nspace"])
        signal = common_pb2.SignalId(name=can_p["rec"], namespace=can_p["namespace"])
        sub_info = network_api_pb2.SubscriberConfig(clientId=source,\
        signals=network_api_pb2.SignalIds(signalId=[signal]), onChange=False)

        # add signal to dictionary, empty list of messages
        self.can_frames[can_p["rec"]] = list()
        self.can_messages[can_p["rec"]] = list()
        self.can_cf_received[can_p["rec"]] = list()


        # Frame control handling
        fc_param = dict()
        #default for each signal to register
        fc_param["block_size"] = 0      # send remaining frames without flow control
        fc_param["separation_time"] = 0 # no separation time needed between frames
        fc_param["delay"] = 0           # delay to send FC response in ms
        fc_param["flag"] = 48           # 48=0x30 continue to send
        fc_param["responses"] = 0       # number of FC responses sent already
                                        #(needed for max delay frames)
        fc_param["auto"] = True         # send FC frame automatically

        try:
            if timeout == 0:

                # subscribe_object = can_param["stub"].SubscribeToSignals(sub_info)
            # else:
                # subscribe_object = can_param["stub"].SubscribeToSignals(sub_info, timeout)
            # print("Subscribe to signal ", sig)
            # self.can_subscribes[sig] =\
                # [subscribe_object, fc_param["block_size"], fc_param["separation_time"],
                 # fc_param["delay"], fc_param["flag"], fc_param["responses"], fc_param["auto"]]
            # for response in subscribe_object:
                # #if multiframe detected prepare answer and send it
                # det_mf = response.signal[0].integer>>60
                # if (det_mf == 1) and (self.can_subscribes[sig][6]):
                    # # send wanted reply with delay
                    # time.sleep(self.can_subscribes[sig][3]/1000)
                    # SC_HW.send_fc_frame(can_param, self.can_subscribes[sig][4],
                                        # self.can_subscribes[sig][1], self.can_subscribes[sig][2])
                    # # increment FC responses sent
                    # self.can_subscribes[sig][5] += 1
                # #there is a MF to send, and FC received for it:
                # if (det_mf == 3) and (can_p["send"] in self.can_mf_send and\
                    # self.can_mf_send[can_p["send"]] == []):
                    # print("No CF was expected for ", can_p["send"])
                # self.can_frames[sig].append(self.signal2message(time.time(), response))
        # except grpc._channel._Rendezvous as err: # pylint: disable=protected-access

                subscribe_object = can_p["netstub"].SubscribeToSignals(sub_info)
            else:
                subscribe_object = can_p["netstub"].SubscribeToSignals(sub_info, timeout)
            print("Subscribe to signal ", can_p["rec"])
            self.can_subscribes[can_p["rec"]] =\
                [subscribe_object, block_size, separation_time, frame_control_delay,
                 frame_control_flag, frame_control_responses, frame_control_auto]
            #print("list response in sub_info ",\
            #      [can_p["netstub"].SubscribeToSignals(sub_info, timeout)])
            for response in subscribe_object:
                #if multiframe detected prepare answer and send it
                det_mf = response.signal[0].integer>>60
                #print("Test if AUTO_FC[",can_p["rec"],"]: ",self.can_subscribes[can_p["rec"]][6])
                if (det_mf == 1) and (self.can_subscribes[can_p["rec"]][6]):
                    # send wanted reply with delay
                    #print("send ", can_p["send"], "NSP: ", can_p["nspace"], "frame_control_flag ",
                    #       frame_control_flag,
                    #" block_size ", block_size, " separation_time ", separation_time)
                    time.sleep(self.can_subscribes[can_p["rec"]][3]/1000)
                    #self.send_FC_frame(can_p["netstub"], can_p["send"], can_p["nspace"],
                    #                   frame_control_flag, block_size,
                    #                   separation_time)
                    ###print("FC_values: frame_control_delay",self.can_subscribes[can_p["rec"]][4],\
                    ###         " block_size:", self.can_subscribes[can_p["rec"]][1],\
                    ###         " TS: ", self.can_subscribes[can_p["rec"]][2])
                    self.send_FC_frame(can_p["netstub"], can_p["send"], can_p["namespace"],\
                        self.can_subscribes[can_p["rec"]][4],\
                        self.can_subscribes[can_p["rec"]][1],\
                        self.can_subscribes[can_p["rec"]][2])
                    #print("frame_control_responses ", self.can_subscribes[can_p["rec"]][5])
                    # increment FC responses sent
                    self.can_subscribes[can_p["rec"]][5] += 1
                    #print("frame_control_responses ", self.can_subscribes[can_p["rec"]][5])
                #there is a MF to send, and FC received for it:
                if (det_mf == 3) and\
                   (can_p["send"] in self.can_mf_send and self.can_mf_send[can_p["send"]] == []):
                    print("No CF was expected for ", can_p["send"])
                self.can_frames[can_p["rec"]].append(self.signal2message(time.time(), response))
                #print("received: ", self.can_frames[can_p["rec"]])
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            # suppress 'Deadline Exceeded', show other errors
            if not err._state.details == "Deadline Exceeded": # pylint: disable=protected-access
                print(err)

    #def subscribe_signal(self, stub, can_send, can_rec, can_nspace, timeout):
    #def subscribe_signal(self, can_param, timeout):
    def subscribe_signal(self, can_p: CanParam, timeout):
        """
        subscribe_signal

        can_p["netstub"] = stub
        can_p["send"] = can_send
        can_p["rec"] = can_rec
        can_p["namespace"] = can_nspace
        """
        # start every subscribe as extra thread as subscribe is blocking
        # thread_1 = Thread(target=self.subscribe_to_sig,
                  # args=(can_param["stub"], can_p["send"], can_p["rec"],
                        # can_param["can_nspace"], timeout))
        thread_1 = Thread(target=self.subscribe_to_sig,\
                          args=(can_p, timeout))
        thread_1.deamon = True
        thread_1.start()

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

    @classmethod
    def thread_stop(cls):
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


    #def start_periodic(self, stub, per_name, per_send, per_id, per_nspace, per_frame,
    #                   per_intervall):
    def start_periodic(self, stub, per_param):
        """
        start_periodic

        Start a periodic signal: parameters network_stub, send TRUE/FALSE,\
                           name, DBC_name, DBC_namespace, CAN_frame, intervall

        per_param["name"] = per_name
        per_param["send"] = per_send
        per_param["id"] = per_id
        per_param["nspace"] = per_nspace
        per_param["frame"] = per_frame
        per_param["intervall"] = per_intervall
        """
        print("start_sending_periodic: ", per_param["name"])
        self.can_periodic[per_param["name"]] = [per_param["send"], per_param["id"],\
            per_param["nspace"], per_param["frame"], per_param["intervall"]]

        # start periodic, repeat every per_intervall (ms)
        thread_1 = Thread(target=self.send_periodic, args=(stub, per_param["name"]))
        thread_1.daemon = True
        thread_1.start()
        print("wait 1sec for periodic signal to start:", per_param["name"])
        time.sleep(1)


    def set_periodic(self, per_param):
        """
        Update parameter to periodic signal: name, parameters send TRUE/FALSE,
        DBC_name, DBC_namespace, CAN_frame, intervall

        Replaced:
        per_param["name"] = per_name
        per_param["send"] = per_send
        per_param["id"] = per_id
        per_param["nspace"] = per_nspace
        per_param["frame"] = per_frame
        per_param["intervall"] = per_intervall
        """
        if per_param["name"] in self.can_periodic:
            self.can_periodic[per_param["name"]][0] = per_param["send"]
            self.can_periodic[per_param["name"]][1] = per_param["id"]
            self.can_periodic[per_param["name"]][2] = per_param["nspace"]
            self.can_periodic[per_param["name"]][3] = per_param["frame"]
            self.can_periodic[per_param["name"]][4] = per_param["intervall"]
        else:
            print("set_periodic: Name " + per_param["name"] + "not in periodic signals")


    def send_periodic(self, stub, per_name):
        """
        Try to send periodic signal: parameters network_stub, name
        """
        #source = common_pb2.ClientId(id="app_identifier")
        while self.can_periodic[per_name][0]:
            #print("Can_periodic ", self.can_periodic[per_name])
            try:
                #print("send periodic signal_name: ", self.can_periodic[per_name])
                SC_HW.t_send_signal_hex(stub, self.can_periodic[per_name][1],\
                    common_pb2.NameSpace(name=self.can_periodic[per_name][2]),\
                                            self.can_periodic[per_name][3])
                time.sleep(self.can_periodic[per_name][4])
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                print(err)


    def stop_periodic(self, per_name):
        """
        stop_periodic
        """
        if per_name in self.can_periodic:
            print("stop_periodic ", per_name)
            per_param = dict()
            per_param["name"] = per_name
            per_param["send"] = False
            per_param["id"] = self.can_periodic[per_name][1]
            per_param["nspace"] = self.can_periodic[per_name][2]
            per_param["frame"] = self.can_periodic[per_name][3]
            per_param["intervall"] = self.can_periodic[per_name][4]

            self.set_periodic(per_param)
        else:
            print("set_periodic: Name " + per_name + "not in periodic signals")


    def stop_periodic_all(self):
        """
        stop_periodic_all
        """
        for per in self.can_periodic:
            self.stop_periodic(per)


    @classmethod
    def send_burst(cls, stub, burst_param):
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

        burst_param["id"] = burst_id
        burst_param["nspace"] = burst_nspace
        burst_param["frame"] = burst_frame
        burst_param["intervall"] = burst_intervall
        burst_param["quantity"] = burst_quantity
        """
        for _ in range(burst_param["quantity"]):
            SC_HW.t_send_signal_hex(stub, burst_param["id"], burst_param["nspace"],
                                    burst_param["frame"])
            time.sleep(burst_param["intervall"])


    def start_heartbeat(self, stub, hb_param):
        """
        start_heartbeat

        hb_param["id"] = hb_id
        hb_param["nspace"] = hb_nspace
        hb_param["frame"] = hb_frame
        hb_param["intervall"] = hb_intervall

        per_param["per_name"]
        per_param["per_send"]
        per_param["per_id"]
        per_param["per_nspace"]
        per_param["per_frame"]
        per_param["per_intervall"]
        """
        print("start_heartbeat")

        per_param = dict()
        per_param["name"] = 'heartbeat'
        per_param["send"] = True
        per_param["id"] = hb_param["id"]
        per_param["nspace"] = hb_param["nspace"]
        per_param["frame"] = hb_param["frame"]
        per_param["intervall"] = hb_param["intervall"]

        self.start_periodic(stub, per_param)
        # Wait for heartbeat to start")
        time.sleep(4)
        print("start_heartbeat end")


    def stop_heartbeat(self):
        """
        stop_heartbeat
        """
        self.stop_periodic('heartbeat')


    @classmethod
    def connect_to_signalbroker(cls, sb_address, sb_port):
        """
        connect_to_signalbroker
        """
        channel = grpc.insecure_channel(sb_address + ':' + sb_port)
        functional_api_pb2_grpc.FunctionalServiceStub(channel)
        network_stub = network_api_pb2_grpc.NetworkServiceStub(channel)
        return network_stub


    @classmethod
    def nspace_lookup(cls, namespace):
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
    @classmethod
    def subscribe_to_heartbeat(cls, stub):
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
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                print(err)


    @classmethod
    def t_send_signal(cls, stub, signal_name, namespace, payload_value):
        """
        t_send_signal

        Send signal on CAN: parameters name_DBC, namespace_DBC, payload
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
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            print(err)


    @classmethod
    def can_receive(cls, can_send, can_extra):
        """
        can_receive

        Add offset \x40 to first byte
        Add can_extra to message
        """
        #print("can_receive can_send ", can_send)
        #print("can_receive can_extra ", can_extra)
        #print("len can_send ", len(can_send))
        can_ret = ''

        #print("Conditions:  len(can_send):", len(can_send), "len(can_extra):",\
        #                   len(can_extra), "can_send0 ", can_send[0])
        # check if receive frame/message can be build
        if can_send and (len(can_send)+len(can_extra) < 7) and (can_send[0] < 192):
            can_ret = bytes([can_send[0]+ 0x40])
            for count in range(len(can_send)-1):
                can_ret = can_ret + bytes([can_send[count+1]])
            for count in range(len(can_extra)):
                can_ret = can_ret + bytes([can_extra[count]])
        #print("payload to receive: ", str(can_ret))
        return can_ret

    @classmethod
    def __msg_status_2(cls, temp_message, mf_size_remain, i):
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


    def send_FF_CAN(self, can_p: CanParam, freq=0):
        """
        send_FF_CAN
        
        Replaced:
        can_p["netstub"] = stub
        can_p["send"] = signal_name
        can_p["namespace"] = name_space
        """
        #print("Send first frame of MF")
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_p["send"], namespace=can_p["namespace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = self.can_mf_send[can_p["send"]][1][0]

        #print("Signal_with_payload : ", self.can_mf_send[can_p["send"]][1][0].hex().upper())
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=freq)
        try:
            can_p["netstub"].PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            print(err)
        self.can_mf_send[can_p["send"]][0] += 1 # notify frame sent
        print("Frames sent(FF/SF): ", self.can_mf_send[can_p["send"]][0],\
              "of ", len(self.can_mf_send[can_p["send"]][1]))




    def send_CF_CAN(self, can_p: CanParam, frequency=0, timeout_ms=1000):
    #def send_cf_can(self, can_param, frequency=0, timeout_ms=1000):
        """
        send_CF_CAN

        Replaced
        can_p["send"] = can_param["can_send"] = signal_name
        can_p["rec"] = can_param["can_rec"] = r_var
        """
        time_start = time.time()
        last_frame = '00'

        # wait for FC frame to arrive (max 1 sec)
        # take last frame received
        if self.can_frames[can_p["rec"]]:
            last_frame = self.can_frames[can_p["rec"]][-1][2]
        print("try to get FC frame")
        while ((time.time() - time_start)*1000 < timeout_ms) and (int(last_frame[0:1]) != 3):
            if self.can_frames[can_p["rec"]] != []:
                last_frame = self.can_frames[can_p["rec"]][-1][2]
        #ToDo: if FC timed out: delete message to send # pylint: disable=fixme
        if self.can_frames[can_p["rec"]] == []:
            print("send_CF_CAN: FC timed out, discard rest of message to send")
            self.can_mf_send[can_p["send"]] = []
            return "Error: FC timed out, message discarded"

        # continue as stated in FC
        if int(last_frame[0:1]) == 3:
            # fetch next CAN frames to send
            frame_control_flag = int(last_frame[1:2], 16)
            block_size = int(last_frame[2:4], 16)
            separation_time = int(last_frame[4:6], 16)

            # safe CF received for later analysis
            self.can_cf_received[can_p["rec"]].\
                append(self.can_frames[can_p["rec"]][0])

            if frame_control_flag == 1:
                # Wait flag - wait for next FC frame
                self.send_cf_can(can_p, frequency, timeout_ms)
            elif frame_control_flag == 2:
                # overflow / abort
                print("Error: FC 32 received, empty buffer to send.")
                self.can_mf_send[can_p["send"]] = []
                return "Error: FC 32 received"
            elif frame_control_flag == 0:
                # continue sending as stated in FC frame
                self.__send_cf_can_ok(can_p, separation_time, block_size)
            else:
                return "FAIL: invalid value in FC"
        if self.can_mf_send[can_p["send"]][0] ==\
            len(self.can_mf_send[can_p["send"]][1]):
            print("MF sent, remove MF")
            print("CAN_CF_RECEIVED: ", self.can_cf_received)
            self.can_mf_send[can_p["send"]] = []
            print("remove CF from received frames:")
            self.can_frames[can_p["rec"]].pop(0)
            return "OK: MF message sent"
        return "FAIL: MF message failed to send"


    def add_canframe_tosend(self, signal_name, frame):
        """
        add_canframe_tosend
        appends a canframe for MF messages for later sending
        """
        self.can_mf_send[signal_name][1].append(frame) # SF_Data_Length + payload


    def t_send_signal_CAN_MF(self, can_p: CanParam, cpay: CanPayload, padding=True,
                             padding_byte=0x00):
        """
        t_send_signal_CAN_MF

        # Replaced:
        # can_p["netstub"] = stub
        # can_p["send"] = signal_name
        # can_p["namespace"] = namespace
        # can_p["receive"] = rec_name
        """
        #print("signals to send: ", self.can_mf_send)
        if can_p["send"] in self.can_mf_send:
            while self.can_mf_send[can_p["send"]]:
                print("CAN_MF_send: still payload to send. Wait 1sec")
                time.sleep(1)
        else:
            self.can_mf_send[can_p["send"]] = []
        #number of frames to send, array of frames to send
        self.can_mf_send[can_p["send"]] = [0, []]
        #print("signals to send: ", self.can_mf_send)
        #print("t_send signal_CAN_MF_hex")
        #print("send CAN_MF payload ", cpay["payload"])
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_p["send"], namespace=can_p["namespace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # ToDo: test if payload can be sent over CAN(payload less then 4096 bytes) # pylint: disable=fixme

        # build array of frames to send:
        mess_length = len(cpay["payload"])
        # if single_frame:
        if mess_length < 8:
            self.__send_sf(can_p, padding, padding_byte)
        # if multi_frame:
        elif mess_length < 4096:
            self.__send_mf(can_p, padding, padding_byte)
        if self.can_mf_send[can_p["send"]][1] == []:
            print("payload empty: nothing to send")
            # if single_frame:
        elif len(self.can_mf_send[can_p["send"]][1]) == 1:
            #print("Send first frame SF: ", self.can_mf_send[signal_name][1][0])
            signal_with_payload.raw = self.can_mf_send[can_p["send"]][1][0]
            #print("source: ", source, " signal_with_PL: ",  signal_with_payload.raw)
            publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
            try:
                can_p["netstub"].PublishSignals(publisher_info)
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                print(err)
            #remove payload after it's been sent
            print("remove payload after being sent")
            #print("can_mf_send ", self.can_mf_send)
            try:
                self.can_mf_send.pop(can_p["send"])
            except KeyError:
                print("Key ", can_p["send"], " not found.")
            #print("can_mf_send2 ", self.can_mf_send)
        elif len(self.can_mf_send[can_p["send"]][1]) < 0x7ff:
            print("send payload as MF")
            # send payload as MF

            #send FirstFrame:
            self.send_ff_can(can_p, freq=0)
            #send ConsecutiveFrames:
            self.send_cf_can(can_p)

            # wait for FC
            # send accordingly
        else:
            print("Payload doesn't fit in one MF")


@classmethod
    def t_send_signal_hex(cls, stub, signal_name, namespace, payload_value):
        """
        t_send_signal_hex

        Send CAN message (8 bytes load) with raw (hex) payload
        """
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = payload_value
        #print("\nstub ", stub,
        #      "\nsignal_name ", signal_name,
        #      "\nnamespace ", namespace,
        #      "\nPayload_value ", payload_value)
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                            signals=network_api_pb2.Signals(signal=[signal_with_payload]),\
                                                                    frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            print("Exception", err)



    def __check_msg(self, can_rec, temp_message, mf_size_remain):
        """
        __check_msg
        """
        can_mess_updated = False
        if temp_message:
            if mf_size_remain == 0:
                can_mess_updated = True
                self.can_messages[can_rec].append(list(temp_message))
        return can_mess_updated


    #change parameters of FC and how FC frame is used
    def change_MF_FC(self, sig, can_mf_param: CanMFParam):
        """
        change_MF_FC
        """
        print("change_MF_FC")
        print("change_MF_FC param:", can_mf_param)
        #global can_subscribes
        print("can_subscribes ", self.can_subscribes)
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
        if self.can_frames[can_rec]:
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
                        print("MF sent: ", self.can_mf_send)
                        print("FC expected for ", can_rec)
                        #print("can_frames      ", self.can_frames)
                    else:
                        print("Reserved CAN-header")
                elif message_status == 1:
                    print("message not expected")
                elif message_status == 2:
                    self.__msg_status_2(temp_message, mf_size_remain, i)
                else:
                    print("unexpected message status in can_frames")
            # don't add empty messages
            can_mess_updated = self.__check_msg(can_rec, temp_message, mf_size_remain)
        return can_mess_updated
