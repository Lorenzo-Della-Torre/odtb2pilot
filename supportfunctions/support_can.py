""" project:  Hilding testenvironment using SignalBroker
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

import logging
import time
import threading
from threading import Thread
import sys
from typing import Dict
import grpc
sys.path.append('generated')
import protogenerated.network_api_pb2 as network_api_pb2 # pylint: disable=wrong-import-position
import protogenerated.network_api_pb2_grpc as network_api_pb2_grpc # pylint: disable=wrong-import-position
import protogenerated.functional_api_pb2_grpc as functional_api_pb2_grpc # pylint: disable=wrong-import-position
import protogenerated.system_api_pb2_grpc as system_api_pb2_grpc # pylint: disable=wrong-import-position
import protogenerated.common_pb2 as common_pb2 # pylint: disable=wrong-import-position


class CanMFParam(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        CanMFParam
        Added to allow fixed keys when setting MF parameters for CAN
    """
    block_size: int
    separation_time: int
    frame_control_delay: int
    frame_control_flag: int
    frame_control_auto: bool


class CanParam(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        CanParam
        All CAN send/receive parameters
    """
    def __init__(self):
        super(CanParam, self).__init__(
        {'netstub': '',
         'sytem_stub': '',
         'send': '',
         'receive': '',
         'namespace': '',
         'padding': True,
         'framelength_max': 8,
         'protocol': 'can'})


class CanTestExtra(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        CanTestExtra
    """
    step_no: int
    purpose: str
    timeout: int
    min_no_messages: int
    max_no_messages: int


class CanPayload(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        CanPayload
        payload to send,
        extra   to add to command
    """
    payload: bytes
    extra: bytes


class PerParam(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        Periodic Parameters
    """
    name: str
    send: bool
    id: str
    nspace: str
    frame: bytes
    intervall: float


class SupportCAN:
    # Disable the too-many-public-methods violation. Not sure how to split it
    # pylint: disable=too-many-public-methods,too-many-lines
    """
        Class for supporting sending/receiving CAN frames
    """
    # Buffer for receives CAN frames and messages
    can_cf_received = dict()
    can_frames = dict()
    can_messages = dict()
    can_subscribes = dict()
    can_periodic = dict()

    _heartbeat = False

    #init array for payload to send
    can_mf_send = dict()
    pl_array = []

    @classmethod
    def add_pl_length(cls, payload_value):
        """
        add_pl_length
        """
        payload_value = bytes([len(payload_value)]) + payload_value
        return payload_value


    @classmethod
    def fill_payload(cls, payload_value, fill_value=0):
        """
        fill_payload
        """
        logging.debug("Payload to complete: %s", str(payload_value))
        while len(payload_value) < 8:
            payload_value = payload_value + bytes([fill_value])
        logging.debug("New payload: %s", payload_value)
        return payload_value



    def remove_first_can_frame(self, can_frame):
        """
        remove first frame in list
        """
        self.can_frames[can_frame].pop()

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

    @classmethod
    def display_signals_available(cls, can_p: CanParam):
        """
        display_signals_available
        display all signals beamybroker can access in namespaces
        """
        logging.info("can_p setup: %s", can_p)
        configuration = can_p["system_stub"].GetConfiguration(common_pb2.Empty())
        for network_info in configuration.networkInfo:
            logging.info(
                "signals in namespace %s %s",
                network_info.namespace.name,
                can_p["system_stub"].ListSignals(network_info.namespace),
                )

    def subscribe_to_sig(self, can_p: CanParam, timeout=5):
        """
        Subscribe to signal sig in namespace nsp
        """
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_p["receive"], namespace=can_p["namespace"])
        sub_info = network_api_pb2.SubscriberConfig(clientId=source,\
        signals=network_api_pb2.SignalIds(signalId=[signal]), onChange=False)

        # add signal to dictionary, empty list of messages
        self.can_frames[can_p["receive"]] = list()
        self.can_messages[can_p["receive"]] = list()
        self.can_cf_received[can_p["receive"]] = list()

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
                subscribe_object = can_p["netstub"].SubscribeToSignals(sub_info)
            else:
                subscribe_object = can_p["netstub"].SubscribeToSignals(sub_info, timeout)
            logging.debug("Subscribe to signal %s", can_p["receive"])
            self.can_subscribes[can_p["receive"]] =\
                [subscribe_object, fc_param["block_size"], fc_param["separation_time"],\
                fc_param["delay"], fc_param["flag"], fc_param["responses"], fc_param["auto"]]
            logging.debug("Added object %s to subcribe %s", can_p["receive"], self.can_subscribes)
            for response in subscribe_object:
                #if multiframe detected prepare answer and send it
                det_mf = response.signal[0].integer>>60
                if (det_mf == 1) and (self.can_subscribes[can_p["receive"]][6]):
                    # send wanted reply with delay
                    time.sleep(self.can_subscribes[can_p["receive"]][3]/1000)
                    self.send_fc_frame(can_p,\
                        self.can_subscribes[can_p["receive"]][4],\
                        self.can_subscribes[can_p["receive"]][1],\
                        self.can_subscribes[can_p["receive"]][2])
                    #print("frame_control_responses ", self.can_subscribes[can_p["receive"]][5])
                    # increment FC responses sent
                    self.can_subscribes[can_p["receive"]][5] += 1
                    #print("frame_control_responses ", self.can_subscribes[can_p["receive"]][5])
                #there is a MF to send, and FC received for it:
                if (det_mf == 3) and\
                   (can_p["send"] in self.can_mf_send and self.can_mf_send[can_p["send"]] == []):
                    logging.warning("No CF was expected for %s", can_p["send"])
                self.can_frames[can_p["receive"]].append(self.signal2message(time.time(), response))
                #print("received: ", self.can_frames[can_p["receive"]])
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            # suppress 'Deadline Exceeded', show other errors
            if not err._state.details == "Deadline Exceeded": # pylint: disable=protected-access
                logging.error(err)


    def subscribe_signal(self, can_p: CanParam, timeout):
        """
        subscribe_signal
        """
        # start every subscribe as extra thread as subscribe is blocking
        thread_1 = Thread(target=self.subscribe_to_sig, args=(can_p, timeout))

        # perhaps this should have a number attached like SubscribeThread-1
        # since more than one signal is typically subscribed
        thread_1.name = "SubscribeThread"
        thread_1.deamon = True
        thread_1.start()


    def unsubscribe_signal(self, signame):
        """
        unsubscribe_signal
        """
        # start every subscribe as extra thread as subscribe is blocking
        logging.debug("unsubscribe signal: %s", signame)
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
        stop any remaining active threads that we have created in support_can
        with a join
        """
        logging.debug("Active threads: %s", threading.enumerate())
        threads = [t.name for t in threading.enumerate()
                   if t.name in ["SignalThread", "PeriodicThread"]]

        logging.debug("Signal or periodic threads remaining: %s", len(threads))

        for thread in threads:
            logging.debug("Joining thread: %s", thread)
            thread.join()

        logging.debug("Active threads: %s", threading.enumerate())


    def start_periodic(self, stub, per_param):
        """
        start_periodic

        Start a periodic signal: parameters network_stub, send TRUE/FALSE,\
                           name, DBC_name, DBC_namespace, CAN_frame, intervall
        """
        logging.debug("Start_sending_periodic: %s", per_param["name"])
        self.can_periodic[per_param["name"]] = [per_param["send"], per_param["id"],\
            per_param["nspace"], per_param["frame"], per_param["intervall"]]

        logging.debug("self.can_periodic: %s", self.can_periodic)

        # start periodic, repeat every per_intervall (ms)
        thread_1 = Thread(target=self.send_periodic, args=(stub, per_param["name"]))

        # perhaps this should have a number attached like PeriodicThread-1
        thread_1.name = "PeriodicThread"
        thread_1.daemon = True
        thread_1.start()
        logging.debug("Wait 1sec for periodic signal to start: %s", per_param["name"])
        time.sleep(1)


    def set_periodic(self, per_param):
        """
        Update parameter to periodic signal: name, parameters send TRUE/FALSE,
        DBC_name, DBC_namespace, CAN_frame, intervall
        """
        if per_param["name"] in self.can_periodic:
            self.can_periodic[per_param["name"]][0] = per_param["send"]
            self.can_periodic[per_param["name"]][1] = per_param["id"]
            self.can_periodic[per_param["name"]][2] = per_param["nspace"]
            self.can_periodic[per_param["name"]][3] = per_param["frame"]
            self.can_periodic[per_param["name"]][4] = per_param["intervall"]
        else:
            logging.error("Set_periodic: Name %s not in periodic signals", per_param["name"])


    def send_periodic(self, stub, per_name):
        """
        Try to send periodic signal: parameters network_stub, name
        """
        while self.can_periodic[per_name][0]:
            #print("Can_periodic ", self.can_periodic[per_name])
            try:
                #print("Send periodic signal_name: ", self.can_periodic[per_name])
                self.t_send_signal_hex(stub, self.can_periodic[per_name][1],\
                    common_pb2.NameSpace(name=self.can_periodic[per_name][2]),\
                                            self.can_periodic[per_name][3])
                time.sleep(self.can_periodic[per_name][4])
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                logging.error("Exception: %s", err)


    def stop_periodic(self, per_name):
        """
        stop_periodic
        """
        if per_name in self.can_periodic:
            logging.debug("stop_periodic %s", per_name)
            per_param = dict()
            per_param["name"] = per_name
            per_param["send"] = False
            per_param["id"] = self.can_periodic[per_name][1]
            per_param["nspace"] = self.can_periodic[per_name][2]
            per_param["frame"] = self.can_periodic[per_name][3]
            per_param["intervall"] = self.can_periodic[per_name][4]

            self.set_periodic(per_param)
        else:
            logging.error("Set_periodic: Name %s not in periodic signals", per_name)


    def stop_periodic_all(self):
        """
        stop_periodic_all
        """
        for per in self.can_periodic:
            self.stop_periodic(per)


    def send_burst(self, stub, burst_param: PerParam, quantity: int):
        """
        send_burst

        Sends a number of CAN-frames in a row with given intervall.
        That's sometimes needed for waking up MCU or getting frames sent
        withing a certain time intervall.
        """
        logging.debug("SC.send_burst nspace: %s", burst_param["nspace"])
        for _ in range(quantity):
            self.t_send_signal_hex(stub, burst_param["id"], burst_param["nspace"],
                                   burst_param["frame"])
            time.sleep(burst_param["intervall"])


    def start_heartbeat(self, stub, hb_param):
        """
        start_heartbeat
        """
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
        network_stub, _ = cls.connect_to_signalbroker_new(sb_address, sb_port)
        return network_stub

    @classmethod
    def connect_to_signalbroker_new(cls, sb_address, sb_port):
        """
        connect_to_signalbroker
        """
        channel = grpc.insecure_channel(sb_address + ':' + sb_port)
        functional_api_pb2_grpc.FunctionalServiceStub(channel)
        network_stub = network_api_pb2_grpc.NetworkServiceStub(channel)
        system_stub = system_api_pb2_grpc.SystemServiceStub(channel)
        return network_stub, system_stub


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
                    logging.debug("Response start: %s", response)
                    logging.debug("Response stop")
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                logging.error(err)


    @classmethod
    def t_send_signal(cls, stub, signal_name, namespace, payload_value):
        """
        Send signal on CAN: parameters name_DBC, namespace_DBC, payload
        """
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
            logging.error(err)


    @classmethod
    def can_receive(cls, can_send, can_extra):
        """
        Services have 2byte, except service 14, 22, 2E
        Service 22 and 2E have a DID added (extra 2 bytes)

        Positive reply will have \x40 added to first byte of service.
        """
        if can_extra == '':
            can_extra = b''
        can_ret = b''

        # check if receive frame/message can be build
        #Determine if SF or MF request:
        #if can_send and (len(can_send)+len(can_extra) < 7) and (can_send[0] < 192):
        logging.debug("can_send: bytes in request      : %s", can_send)
        logging.debug("can_send: bytes in request (hex): %s", can_send.hex())

        #add 0x40 to CAN_ID for positive reply
        can_ret = bytes([can_send[0]+ 0x40])
        if can_send[0] == 0x14:
            logging.info("can_receive: Service14 not implemented yet")
        #UDS requests have 2 byte commands (like EDA0) which appear in reply
        elif can_send[0] == 0x22 or can_send[0] == 0x2E:
            can_ret = can_ret + can_send[1:3]
        #other request only have 1 byte command (as 1001, 1002, 1003, 1101
        else:
            can_ret = can_ret + can_send[1:2]
        can_ret = can_ret + can_extra

        logging.debug("expected in payload received      : %s", can_ret)
        logging.debug("expected in payload received (hex): %s", can_ret.hex())
        return can_ret


    @classmethod
    def __msg_status_2(cls, temp_message, mf_size_remain, i):
        if mf_size_remain > 7:
            temp_message[2] = temp_message[2] + i[2][2:16]
            mf_size_remain -= 7
            mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32


    def send_mf(self, can_p: CanParam, cpay, padding, padding_byte):# pylint: disable=too-many-branches
        """
        send_mf
        """
        if can_p["protocol"] == "can":
            logging.info("support_can, send_mf: build framelist for can_fd")
            pl_fcount = 0x21
            #get parameters for message to send: length of payload, DLC
            mess_length = len(cpay["payload"])
            #copy of payload
            pl_work = cpay["payload"]
            fl_max = can_p["framelength_max"]

            # add first frame
            self.add_canframe_tosend(can_p["send"],\
                (int(0x1000 | mess_length).to_bytes(2, 'big') + pl_work[0:fl_max-2]))
            pl_work = pl_work[fl_max-2:]
            logging.debug("Payload stored first frame: %s", self.can_mf_send)
            # add  remaining frames:
            while pl_work:
            # still bytes to take
                if len(pl_work) > fl_max-1:
                    self.add_canframe_tosend(can_p["send"],
                                             (bytes([pl_fcount]) + pl_work[0:fl_max-1]))
                    pl_work = pl_work[fl_max-1:]
                    pl_fcount = (pl_fcount + 1) & 0x2F
                else:
                    if padding:
                        self.add_canframe_tosend(can_p["send"],\
                            self.fill_payload((bytes([pl_fcount]) + pl_work[0:]), padding_byte))
                    else:
                        self.add_canframe_tosend(can_p["send"],
                                                 bytes([pl_fcount]) + pl_work[0:])
                    pl_work = []
        elif can_p["protocol"] == "can_fd":
            logging.info("support_can, send_mf: build framelist for can_fd")
            pl_fcount = 0x21
            mess_length = len(cpay["payload"])
            pl_work = cpay["payload"]
            fl_max = can_p["framelength_max"]

            # add first frame
            self.add_canframe_tosend(can_p["send"],\
                (int(0x100000000000000000000000000000000000 | mess_length).to_bytes(2, 'big')
                 + pl_work[0:fl_max-2]))
            pl_work = pl_work[fl_max-2:]
            logging.debug("Payload stored first frame: %s", self.can_mf_send)
            # add  remaining frames:
            while pl_work:
            # still bytes to take
                if len(pl_work) > fl_max-1:
                    self.add_canframe_tosend(can_p["send"],
                                             (bytes([pl_fcount]) + pl_work[0:fl_max-1]))
                    pl_work = pl_work[fl_max-1:]
                    pl_fcount = (pl_fcount + 1) & 0x2F
                else:
                    if padding:
                        self.add_canframe_tosend(can_p["send"],\
                            self.fill_payload((bytes([pl_fcount]) + pl_work[0:]), padding_byte))
                    else:
                        self.add_canframe_tosend(can_p["send"],
                                                 bytes([pl_fcount]) + pl_work[0:])
                    pl_work = []
        else:
            logging.info("support_can, send_mf: unknown format to build "\
                         "frames from messages in send_mf")


    def __send_sf(self, can_p: CanParam, cpay, padding, padding_byte):
        """
        __send_sf
        """
        mess_length = len(cpay["payload"])
        if padding:
            self.add_canframe_tosend(can_p["send"],\
                self.fill_payload(bytes([mess_length])\
                + cpay["payload"], padding_byte))
        else:
            self.add_canframe_tosend(can_p["send"], bytes([mess_length])\
                + cpay["payload"])


    def __print_payload(self, can_p: CanParam):
        logging.debug("PayLoad array as hex: ")
        for pl_frames in self.can_mf_send[can_p["send"]][1]:
            logging.debug("%s", pl_frames.hex().upper())


    def send_ff_can(self, can_p: CanParam, freq=0):
        """
        send_FF_CAN
        """
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_p["send"], namespace=can_p["namespace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = self.can_mf_send[can_p["send"]][1][0]

        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=freq)
        try:
            can_p["netstub"].PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            logging.error(err)
        self.can_mf_send[can_p["send"]][0] += 1 # notify frame sent
        logging.debug("Frames sent(FF/SF): %s of %s", self.can_mf_send[can_p["send"]][0],
                      len(self.can_mf_send[can_p["send"]][1]))


    def send_cf_can(self, can_p: CanParam, frequency=0, timeout_ms=1000):
        """
        send_CF_CAN

        Replaced
        can_p["send"] = can_p["send"] = signal_name
        can_p["receive"] = can_p["receive"] = r_var
        """
        time_start = time.time()
        last_frame = '00'

        # wait for FC frame to arrive (max 1 sec)
        # take last frame received
        if self.can_frames[can_p["receive"]]:
            last_frame = self.can_frames[can_p["receive"]][-1][2]
        logging.debug("Try to get FC frame")
        while ((time.time() - time_start)*1000 < timeout_ms) and (int(last_frame[0:1]) != 3):
            if self.can_frames[can_p["receive"]] != []:
                last_frame = self.can_frames[can_p["receive"]][-1][2]
        #ToDo: if FC timed out: delete message to send # pylint: disable=fixme
        if self.can_frames[can_p["receive"]] == []:
            logging.error("Send_CF_CAN: FC timed out, discard rest of message to send")
            self.can_mf_send[can_p["send"]] = []
            return "Error: FC timed out, message discarded"

        # continue as stated in FC
        if int(last_frame[0:1]) == 3:
            # fetch next CAN frames to send
            frame_control_flag = int(last_frame[1:2], 16)
            block_size = int(last_frame[2:4], 16)
            separation_time = int(last_frame[4:6], 16)

            # safe CF received for later analysis
            self.can_cf_received[can_p["receive"]].\
                append(self.can_frames[can_p["receive"]][0])

            if frame_control_flag == 1:
                # Wait flag - wait for next FC frame
                self.send_cf_can(can_p, frequency, timeout_ms)
            elif frame_control_flag == 2:
                # overflow / abort
                logging.error("Error: FC 32 received, empty buffer to send.")
                self.can_mf_send[can_p["send"]] = []
                return "Error: FC 32 received"
            elif frame_control_flag == 0:
                # continue sending as stated in FC frame
                self.__send_cf_can_ok(can_p, separation_time, block_size)
                # not whole block sent? Wait for next FC frame and send rest
                if self.can_mf_send[can_p["send"]][0] <\
                    len(self.can_mf_send[can_p["send"]][1]):
                    self.send_cf_can(can_p, frequency, timeout_ms)
            else:
                return "FAIL: invalid value in FC"
        if self.can_mf_send[can_p["send"]][0] ==\
            len(self.can_mf_send[can_p["send"]][1]):
            logging.debug("MF sent, remove MF")
            logging.debug("CAN_CF_RECEIVED: %s", self.can_cf_received)
            self.can_mf_send[can_p["send"]] = []
            logging.debug("remove CF from received frames:")
            self.can_frames[can_p["receive"]].pop(0)
            return "OK: MF message sent"
        return "FAIL: MF message failed to send"


    def add_canframe_tosend(self, signal_name, frame):
        """
        Appends a canframe for MF messages for later sending
        """
        self.can_mf_send[signal_name][1].append(frame) # SF_Data_Length + payload


    def t_send_signal_can_mf(self, can_p: CanParam, cpay: CanPayload,# pylint: disable=too-many-branches, too-many-statements
                             padding=True, padding_byte=0x00):
        """
        t_send_signal_CAN_MF
        """
        #print("signals to send: ", self.can_mf_send)
        if can_p["send"] in self.can_mf_send:
            while self.can_mf_send[can_p["send"]]:
                logging.debug("CAN_MF_send: still payload to send. Wait 1sec")
                time.sleep(1)
        else:
            self.can_mf_send[can_p["send"]] = []
        #number of frames to send, array of frames to send
        self.can_mf_send[can_p["send"]] = [0, []]
        #print("signals to send: ", self.can_mf_send)
        #print("t_send signal_CAN_MF_hex")
        #print("send CAN_MF payload ", payload_value)
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_p["send"], namespace=can_p["namespace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # ToDo: test if payload can be sent over CAN(payload less then 4096 bytes) # pylint: disable=fixme

        # build array of frames to send:
        mess_length = len(cpay["payload"])

        if can_p["protocol"] == 'can':
            logging.info("Send payload as CAN frames")
            # if single_frame:
            if mess_length < can_p["framelength_max"]:
                self.__send_sf(can_p, cpay, padding, padding_byte)
            # if multi_frame:
            elif mess_length < 0x1000:
                #build list of frames to send
                self.send_mf(can_p, cpay, padding, padding_byte)

            ### send all frames built
            if self.can_mf_send[can_p["send"]][1] == []:
                logging.debug("payload empty: nothing to send")
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
                    logging.error(err)
                #remove payload after it's been sent
                logging.debug("Remove payload after being sent")
                #print("can_mf_send ", self.can_mf_send)
                try:
                    self.can_mf_send.pop(can_p["send"])
                except KeyError:
                    logging.error("Key %s not found", can_p["send"])
                #print("can_mf_send2 ", self.can_mf_send)
            # check if payload fits into block to send
            elif len(self.can_mf_send[can_p["send"]][1]) < 0x1000:
                logging.debug("Send payload as MF")
                # send payload as MF

                #send FirstFrame:
                self.send_ff_can(can_p, freq=0)
                #send ConsecutiveFrames:
                self.send_cf_can(can_p)

                # wait for FC
                # send accordingly
            else:
                logging.debug("Payload doesn't fit in one MF message")
        elif can_p["protocol"] == 'can_fd':
            logging.info("Send payload as CAN_FD frames")
            # if single_frame:
            if mess_length < can_p["framelength_max"]-1:
                self.__send_sf(can_p, cpay, padding, padding_byte)
            # if multi_frame (max 4GB)
            elif mess_length < 0x1000000000000000000000000:
                self.send_mf(can_p, cpay, padding, padding_byte)
            if self.can_mf_send[can_p["send"]][1] == []:
                logging.debug("payload empty: nothing to send")
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
                    logging.error(err)
                #remove payload after it's been sent
                logging.debug("Remove payload after being sent")
                #print("can_mf_send ", self.can_mf_send)
                try:
                    self.can_mf_send.pop(can_p["send"])
                except KeyError:
                    logging.error("Key %s not found", can_p["send"])
                #print("can_mf_send2 ", self.can_mf_send)
            elif len(self.can_mf_send[can_p["send"]][1]) < 0x1000000000000000000000000:
                logging.debug("Send payload as MF message")
                # send payload as MF

                #send FirstFrame:
                self.send_ff_can(can_p, freq=0)
                #send ConsecutiveFrames:
                self.send_cf_can(can_p)

                # wait for FC
                # send accordingly
            else:
                logging.debug("Payload doesn't fit in one MF")
        else:
            logging.info("Unknown format for sending payload")


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
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                            signals=network_api_pb2.Signals(signal=[signal_with_payload]),\
                                                                    frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            logging.error("Exception %s", err)


    def __send_cf_can_ok(self, can_p: CanParam, separation_time, block_size):
        """
            __send_cf_can_ok

            Subfunction of send_cf_can
        """
        source = common_pb2.ClientId(id="app_identifier")
        signal = common_pb2.SignalId(name=can_p["send"],
                                     namespace=can_p["namespace"])
        signal_with_payload = network_api_pb2.Signal(id=signal)

        # continue sending as stated in FC frame
        logging.debug("Continue sending MF message")
        # delay frame sent after FC received as stated if frame_control_delay
        if self.can_subscribes[can_p["send"]][3] != 0:
            logging.debug("Delay frame after FC as stated in frame_control_delay [ms]: %s",
                          self.can_subscribes[can_p["send"]][3])
            time.sleep(self.can_subscribes[can_p["send"]][3]/1000)
        while self.can_mf_send[can_p["send"]][0] <\
            len(self.can_mf_send[can_p["send"]][1]):
            signal_with_payload.raw = \
                self.can_mf_send[can_p["send"]][1]\
                    [self.can_mf_send[can_p["send"]][0]]
            logging.debug("Signal_with_payload : %s", signal_with_payload.raw.hex().upper()) # Not sure how to fix this pylint warning. pylint: disable=no-member
            publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
                signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
            try:
                can_p["netstub"].PublishSignals(publisher_info)
                self.can_mf_send[can_p["send"]][0] += 1
                # wait ms, only 0-127 ms allowed, microseconds 0xF1-0xF9 ignored:
                time.sleep((separation_time and 0x7F) / 1000)
                logging.debug("Frames sent(CF): %s of %s",
                              self.can_mf_send[can_p["send"]][0],
                              len(self.can_mf_send[can_p["send"]][1]))
                block_size -= 1
                if block_size == 0:
                    break
            except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
                logging.error(err)


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
            logging.error(err)


    def change_mf_fc(self, sig, can_mf_param: CanMFParam):
        """
        change parameters of FC and how FC frame is used
        """
        self.can_subscribes[sig][1] = can_mf_param['block_size']
        self.can_subscribes[sig][2] = can_mf_param['separation_time']
        self.can_subscribes[sig][3] = can_mf_param['frame_control_delay']
        self.can_subscribes[sig][4] = can_mf_param['frame_control_flag']
        #self.can_subscribes[sig][5]=can_mf_param.frame_control_responses
        self.can_subscribes[sig][6] = can_mf_param['frame_control_auto']


    def send_fc_frame(self, can_p: CanParam, frame_control_flag, block_size, separation_time):
        """
        Build FlowControl frame and send

        can_p["netstub"] = stub
        can_p["send"] = signal_name
        can_p["namespace"] = namespace
        """
        if (frame_control_flag < 48) | (frame_control_flag > 50):
            logging.error("CAN Flowcontrol: Error frame_control_flag: Out_of_range %s",
                          frame_control_flag)
        if block_size > 255:
            logging.error("CAN Flowcontrol: Blocksize ouf_of_range %s", block_size)
        if(separation_time > 127) & ((separation_time < 241) | (separation_time > 249)):
            logging.error("CAN Flowcontrol: separationtime out_of_range %s", separation_time)

        payload = frame_control_flag.to_bytes(1, 'big') \
                    +block_size.to_bytes(1, 'big') \
                    +separation_time.to_bytes(1, 'big') \
                    +b'\x00\x00\x00\x00\x00'
        self.t_send_signal_hex(can_p["netstub"], can_p["send"], can_p["namespace"],
                               payload)


    def __update_msg(self, can_rec, temp_message, mf_size_remain):
        """
        __update_msg
        """
        can_mess_updated = False
        # don't add empty messages
        if temp_message:
            #print("mf_size_remain: ", mf_size_remain)
            if mf_size_remain == 0:
                can_mess_updated = True
                logging.debug("Add messages to can_messages: %s", self.can_messages[can_rec])
                logging.debug("Messages: %s", list(temp_message))
                self.can_messages[can_rec].append(list(temp_message))
        return can_mess_updated


    def update_can_messages(self, can_p): # pylint: disable=too-many-branches, too-many-statements
        """
        update list of messages for a given can_p["receive"]

        parameter:
        can_p :   dict() containing can parameters and received frames

        return:
        can_mess_updated :  True if messages could be build from CAN-frames in can_rec
                        False if frames contained in can_rec not being used for building a messages
        """
        # default message_status=0 - single frame message
        can_mess_updated = False
        message_status = 0
        mf_cf_count = 0
        mf_mess_size = 0
        temp_message = [] #empty list as default

        can_rec = can_p["receive"]
        #logging.debug("records received %s", can_rec)
        #logging.debug("number of frames %s", len(self.can_frames[can_rec]))
        #logging.debug("frames received %s", self.can_frames[can_rec])
        if self.can_frames[can_rec]:
            for i in self.can_frames[can_rec]:
                #logging.debug("Whole can_frame : %s", i)
                if message_status == 0:
                    det_mf = int(i[2][0:1], 16)
                    if det_mf == 0:
                        #Single frame message, add frame as message
                        temp_message = i
                        mf_size_remain = 0
                        #logging.debug("Single frame message received")
                    elif det_mf == 1:
                        # added for CAN / CAN_FD:
                        # 1. detect if FirstFrame is CAN/CAN_FD
                        #    (https://en.wikipedia.org/wiki/CAN_FD)
                        # 2. get payload length of message
                        #logging.debug("detect if CAN/CAN_FD multiframe")
                        if int(i[2][1:4], 16) == 0:
                            #logging.debug("decode CAN_FD multiframe")
                            protocol = 'can_fd'
                            mf_mess_size = int(i[2][4:12], 16)
                            mess_bytes_received = (len(i[2]) / 2)-12 #payload starts byte6
                        else:
                            #logging.debug("decode CAN multiframe")
                            protocol = 'can'
                            mf_mess_size = int(i[2][1:4], 16)
                            mess_bytes_received = (len(i[2]) / 2)-4 #payload starts byte2
                        # 3.
                        # First frame of MF-message, change to status=2 consective frames to follow
                        message_status = 2
                        mf_cf_count = 32 # CF franes start with 0x20..0x2F for CAN and CAN_FD

                        # get size of message to receive:
                        if protocol == 'can_fd':
                            # CAN_FD message
                            #logging.debug("add first payload CAN_FD")
                            mess_bytes_received = (len(i[2]) // 2)-12 #payload starts byte6
                        # add first payload
                            temp_message = i[:]
                            #logging.debug("first payload CAN_FD %s", temp_message)
                            #logging.debug("CAN_FD message size %s", mf_mess_size)
                            mf_size_remain = mf_mess_size - mess_bytes_received
                            mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
                            #logging.debug("mf_size_remain: %s", mf_size_remain)
                        else:
                            logging.debug("add first payload CAN")
                            # CAN message
                            mf_mess_size = int(i[2][1:4], 16)
                            #mess_bytes_received = 6
                            mess_bytes_received = (len(i[2]) // 2)-2 #payload starts byte2
                        # add first payload
                            temp_message = i[:]
                            #logging.debug("first payload CAN %s", temp_message)
                            #logging.debug("CAN message size %s", mf_mess_size)
                            mf_size_remain = mf_mess_size - mess_bytes_received
                            #logging.debug("mf_mess_size: %s, received %s, new size %s.",
                            #                                 mf_mess_size,
                            #                                 mess_bytes_received,
                            #                                 mf_size_remain)
                            mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
                            #logging.debug("mf_size_remain: %s", mf_size_remain)

                        #logging.debug("update_can_message: message_size %s", mf_mess_size)
                        # add first payload
                        #logging.debug("update_can_message: whole frame %s", i[2])
                        #logging.debug("update_can_message firstpayload %s", i[2][10:])
#                        temp_message = i[:]
                        # calculate bytes to be removed from mf_mess_size
                        #mf_size_remain = mf_mess_size - 6
#                        mf_size_remain = mf_mess_size - mess_bytes_received
#                        mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
                    elif det_mf == 2:
                        logging.error("Consecutive frame not expected without FC")
                    elif det_mf == 3:
                        if not can_rec in self.can_mf_send:
                            logging.error("Flow control received - not expected")
                            logging.error("Can-frame:  %s", i)
                            #print("MF sent: ", self.can_mf_send)
                            return can_mess_updated
                        logging.debug("MF sent: %s", self.can_mf_send)
                        logging.debug("FC expected for %s", can_rec)
                        logging.debug("Can_frames      %s", self.can_frames)
                    else:
                        logging.debug("Reserved CAN-header")
                elif message_status == 1:
                    logging.error("message not expected")
                elif message_status == 2:
                    if mf_size_remain > can_p["framelength_max"]-1:
                        #temp_message[2] = temp_message[2] + i[2][2:16]
                        temp_message[2] = temp_message[2] + i[2][2:]
                        #logging.debug("Update temp_message: %s", temp_message[2])
                        mf_size_remain -= can_p["framelength_max"]-1
                        mf_cf_count = ((mf_cf_count + 1) & 0xF) + 32
                        #logging.debug("mf_size_remain: %s", mf_size_remain)
                    else:
                        logging.debug("Last frame to add")
                        #logging.debug("slice indices: i[2] %s", type(i[2]))
                        #logging.debug("slice indices: mf_size_remain %s", type(mf_size_remain))
                        #logging.debug("slice indices: 2+mf_size_remain*2 %s",
                        #              type(2+mf_size_remain*2))
                        #logging.debug("slice indices: mess_bytes_received %s",
                        #              type(mess_bytes_received))
                        #logging.debug("slice indices: mf_mess_size %s", type(mf_mess_size))
                        temp_message[2] = temp_message[2] + i[2][2:(2+mf_size_remain*2)]
                        mf_size_remain = 0
                else:
                    logging.error("Unexpected message status in can_frames")
            can_mess_updated = self.__update_msg(can_rec, temp_message, mf_size_remain)
        return can_mess_updated
