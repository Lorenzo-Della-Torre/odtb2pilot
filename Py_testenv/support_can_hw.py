""" project:  ODTB2 testenvironment using SignalBroker
    author:   fjansso8 (Fredrik Jansson)
    date:     2020-05-12
    version:  1.0

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
import sys
import grpc
sys.path.append('generated')
import network_api_pb2 # pylint: disable=wrong-import-position
import common_pb2 # pylint: disable=wrong-import-position

class SupportCanHW:
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

    @classmethod
    def add_pl_length(cls, payload_value):
        """
        add_pl_length
        """
        payload_value = bytes([len(payload_value)]) + payload_value
        #print("new payload: ", payload_value)
        return payload_value


    @classmethod
    def fill_payload(cls, payload_value, fill_value=0):
        """
        fill_payload
        """
        print("payload to complete: ", str(payload_value))
        while len(payload_value) < 8:
            payload_value = payload_value + bytes([fill_value])
        print("new payload: ", payload_value)
        return payload_value


    def send_ff_can(self, stub, signal_name, name_space, freq=0):
        """
        send_FF_CAN
        """
        print("send_FF_CAN")

        #print("Send first frame of MF")
        #print("payload available: ", self.can_mf_send)
        #print("payload signal:    ", self.can_mf_send[signal_name])
        #print("first frame signal ", self.can_mf_send[signal_name][1])
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=signal_name, namespace=name_space)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = self.can_mf_send[signal_name][1][0]

        #print("Signal_with_payload : ", self.can_mf_send[signal_name][1][0].hex().upper())
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=freq)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            print(err)
        self.can_mf_send[signal_name][0] += 1 # notify frame sent
        print("Frames sent(FF/SF): ", self.can_mf_send[signal_name][0], "of ",
              len(self.can_mf_send[signal_name][1]))


    def __send_cf_can_ok(self, can_param, separation_time, block_size):
        """
            __send_cf_can_ok

            Subfunction of send_cf_can
        """
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_param["signal_name"],
                                     namespace=can_param["nspace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # continue sending as stated in FC frame
        print("continue sending MF message")
        # delay frame sent after FC received as stated if frame_control_delay
        if self.can_subscribes[can_param["signal_name"]][3] != 0:
            print("delay frame after FC as stated in frame_control_delay [ms]:",\
                self.can_subscribes[can_param["signal_name"]][3])
            time.sleep(self.can_subscribes[can_param["signal_name"]][3]/1000)
        while self.can_mf_send[can_param["signal_name"]][0] <\
            len(self.can_mf_send[can_param["signal_name"]][1]):
            signal_with_payload.raw = \
                self.can_mf_send[can_param["signal_name"]][1]\
                    [self.can_mf_send[can_param["signal_name"]][0]]
            if self._debug:                            # Not sure how to fix this pylint warning
                print("Signal_with_payload : ", signal_with_payload.raw.hex().upper()) # pylint: disable=no-member
            publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
            try:
                can_param["stub"].PublishSignals(publisher_info)
                self.can_mf_send[can_param["signal_name"]][0] += 1
                # wait ms, only 0-127 ms allowed, microseconds 0xF1-0xF9 ignored:
                time.sleep((separation_time and 0x7F) / 1000)
                if self._debug:
                    print("Frames sent(CF): ",
                          self.can_mf_send[can_param["signal_name"]][0], "of ",\
                              len(self.can_mf_send[can_param["signal_name"]][1]))
                block_size -= 1
                if block_size == 0:
                    break
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                print(err)


    def send_cf_can(self, can_param, frequency=0, timeout_ms=1000):
        """
        send_CF_CAN

        Replaced
        can_param["can_send"] = signal_name
        can_param["can_rec"] = r_var
        """
        print("send_CF_CAN")
        time_start = time.time()
        last_frame = '00'

        # wait for FC frame to arrive (max 1 sec)
        # take last frame received
        if self.can_frames[can_param["can_rec"]]:
            last_frame = self.can_frames[can_param["can_rec"]][-1][2]
        print("try to get FC frame")
        while ((time.time() - time_start)*1000 < timeout_ms) and (int(last_frame[0:1]) != 3):
            if self.can_frames[can_param["can_rec"]] != []:
                last_frame = self.can_frames[can_param["can_rec"]][-1][2]
        #ToDo: if FC timed out: delete message to send # pylint: disable=fixme
        if self.can_frames[can_param["can_rec"]] == []:
            print("send_CF_CAN: FC timed out, discard rest of message to send")
            self.can_mf_send[can_param["can_send"]] = []
            return "Error: FC timed out, message discarded"

        # continue as stated in FC
        if int(last_frame[0:1]) == 3:
            # fetch next CAN frames to send
            frame_control_flag = int(last_frame[1:2], 16)
            block_size = int(last_frame[2:4], 16)
            separation_time = int(last_frame[4:6], 16)

            # safe CF received for later analysis
            self.can_cf_received[can_param["can_rec"]].\
                append(self.can_frames[can_param["can_rec"]][0])

            if frame_control_flag == 1:
                # Wait flag - wait for next FC frame
                self.send_cf_can(can_param, frequency, timeout_ms)
            elif frame_control_flag == 2:
                # overflow / abort
                print("Error: FC 32 received, empty buffer to send.")
                self.can_mf_send[can_param["can_send"]] = []
                return "Error: FC 32 received"
            elif frame_control_flag == 0:
                # continue sending as stated in FC frame
                self.__send_cf_can_ok(can_param, separation_time, block_size)
            else:
                return "FAIL: invalid value in FC"
        if self.can_mf_send[can_param["can_send"]][0] ==\
            len(self.can_mf_send[can_param["can_send"]][1]):
            print("MF sent, remove MF")
            print("CAN_CF_RECEIVED: ", self.can_cf_received)
            self.can_mf_send[can_param["can_send"]] = []
            print("remove CF from received frames:")
            self.can_frames[can_param["can_rec"]].pop(0)
            return "OK: MF message sent"
        return "FAIL: MF message failed to send"


    def add_canframe_tosend(self, signal_name, frame):
        """
        add_canframe_tosend
        """
        self.can_mf_send[signal_name][1].append(frame) # SF_Data_Length + payload


    def __send_mf(self, can_param, padding, padding_byte):
        """
        __send_mf
        """
        pl_fcount = 0x21
        mess_length = len(can_param["m_send"])
        pl_work = can_param["m_send"]

        # add first frame
        self.add_canframe_tosend(can_param["signal_name"],\
            (int(0x1000 | mess_length).to_bytes(2, 'big') + pl_work[0:6]))
        pl_work = pl_work[6:]
        print("Payload stored: ", self.can_mf_send)
        # add  remaining frames:
        while pl_work:
        # still bytes to take
            if len(pl_work) > 7:
                self.add_canframe_tosend(can_param["signal_name"],
                                         (bytes([pl_fcount]) + pl_work[0:7]))
                pl_work = pl_work[7:]
                pl_fcount = (pl_fcount + 1) & 0x2F
            else:
                if padding:
                    self.add_canframe_tosend(can_param["signal_name"],\
                        self.fill_payload((bytes([pl_fcount]) + pl_work[0:]), padding_byte))
                else:
                    self.add_canframe_tosend(can_param["signal_name"],
                                             bytes([pl_fcount]) + pl_work[0:])
                pl_work = []


    def __send_sf(self, can_param, padding, padding_byte):
        """
        __send_sf
        """
        mess_length = len(can_param["m_send"])
        if padding:
            self.add_canframe_tosend(can_param["signal_name"],\
                self.fill_payload(bytes([mess_length])\
                + can_param["m_send"], padding_byte))
        else:
            self.add_canframe_tosend(can_param["signal_name"], bytes([mess_length])\
                + can_param["m_send"])


    def __print_payload(self, can_param):
        if self._debug:
            print("PayLoad array as hex: : ")
            for pl_frames in self.can_mf_send[can_param["signal_name"]][1]:
                print(pl_frames.hex().upper())


    def t_send_signal_can_mf(self, can_param, padding=True, padding_byte=0x00):
        """
        t_send_signal_can_mf

        Send CAN MF message (0-4094 bytes payload hex)

        Replaced:
        can_param["stub"] = stub
        can_param["signal_name"] = signal_name
        can_param["nspace"] = namespace
        can_param["rec_name"] = rec_name
        can_param["m_send"] = payload_value
        """

        if can_param["signal_name"] in self.can_mf_send:
            while self.can_mf_send[can_param["signal_name"]]:
                print("CAN_MF_send: still payload to send. Wait 1sec")
                time.sleep(1)
        else:
            self.can_mf_send[can_param["signal_name"]] = []
        #number of frames to send, array of frames to send
        self.can_mf_send[can_param["signal_name"]] = [0, []]
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_param["signal_name"], namespace=can_param["nspace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # ToDo: test if payload can be sent over CAN(payload less then 4096 bytes) # pylint: disable=fixme

        # build array of frames to send:
        mess_length = len(can_param["m_send"])

        # if single_frame:
        if mess_length < 8:
            self.__send_sf(can_param, padding, padding_byte)
        # if multi_frame:
        elif mess_length < 4096:
            self.__send_mf(can_param, padding, padding_byte)
        self.__print_payload(can_param)
        if self.can_mf_send[can_param["signal_name"]][1] == []:
            print("payload empty: nothing to send")
            # if single_frame:
        elif len(self.can_mf_send[can_param["signal_name"]][1]) == 1:
            signal_with_payload.raw = self.can_mf_send[can_param["signal_name"]][1][0]
            publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
            try:
                can_param["stub"].PublishSignals(publisher_info)
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                print(err)
            #remove payload after it's been sent
            print("remove payload after being sent")
            try:
                self.can_mf_send.pop(can_param["signal_name"])
            except KeyError:
                print("Key ", can_param["signal_name"], " not found.")
        elif len(self.can_mf_send[can_param["signal_name"]][1]) < 0x7ff:
            print("send payload as MF")
            # send payload as MF

            #send FirstFrame:
            self.send_ff_can(can_param["stub"], can_param["signal_name"], can_param["nspace"],
                             freq=0)
            #send ConsecutiveFrames:
            self.send_cf_can(can_param)

            # wait for FC
            # send accordingly
        else:
            print("payload doesn't fit in one MF")


    @classmethod
    def t_send_signal_hex(cls, stub, signal_name, namespace, payload_value):
        """
        t_send_signal_hex

        Send CAN message (8 bytes load) with raw (hex) payload
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
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            print(err)


    def t_send_signal_raw(self, stub, signal_name, namespace, payload_value):
        """
        Similar to t_send_signal_hex, but payload is filled with length of payload \
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
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            print(err)


#    def change_mf_fc(self, sig, block_size, separation_time, frame_control_delay,
#                     frame_control_flag, frame_control_auto):
    def change_mf_fc(self, sig, block_size, separation_time, fc_param):
        """
        Change parameters of FC and how FC frame is used

        fc_param["delay"] = frame_control_delay
        fc_param["flag"] = frame_control_flag
        fc_param["auto"] = frame_control_auto
        """
        self.can_subscribes[sig][1] = block_size
        self.can_subscribes[sig][2] = separation_time
        self.can_subscribes[sig][3] = fc_param["delay"]
        self.can_subscribes[sig][4] = fc_param["flag"]
        #self.can_subscribes[sig][5]=frame_control_responses
        self.can_subscribes[sig][6] = fc_param["auto"]


#    def send_fc_frame(self, stub, signal_name, namespace, frame_control_flag, block_size,
#                      separation_time):
    def send_fc_frame(self, can_param, frame_control_flag, block_size, separation_time):
        """
        Build FlowControl frame and send

        can_param["stub"] = stub
        can_param["signal_name"] = signal_name
        can_param["nspace"] = namespace
        """
        if (frame_control_flag < 48) | (frame_control_flag > 50):
            print("CAN Flowcontrol: Error frame_control_flag: Out_of_range ", frame_control_flag)
        if block_size > 255:
            print("CAN Flowcontrol: Blocksize ouf_of_range ", block_size)
        if(separation_time > 127) & ((separation_time < 241) | (separation_time > 249)):
            print("CAN Flowcontrol: separationtime out_of_range", separation_time)

        payload = frame_control_flag.to_bytes(1, 'big') \
                    +block_size.to_bytes(1, 'big') \
                    +separation_time.to_bytes(1, 'big') \
                    +b'\x00\x00\x00\x00\x00'
        self.t_send_signal_hex(can_param["stub"], can_param["signal_name"], can_param["nspace"],
                               payload)
