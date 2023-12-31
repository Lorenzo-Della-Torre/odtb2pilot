"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

    project:  Hilding testenvironment using BeamyBroker
    author:   hweiler (Hans-Klaus Weiler)
    date:     2022-01-27
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

import logging
import sys
import grpc
sys.path.append('generated')
import protogenerated.network_api_pb2 as network_api_pb2 # pylint: disable=wrong-import-position
import protogenerated.common_pb2 as common_pb2 # pylint: disable=wrong-import-position

class Support_emu_udp:
    # Disable the too-few-public-methods violation. I'm sure we will have more methods later.
    # pylint: disable=too-few-public-methods
    """
        SupportCAN
    """

    @classmethod
    def t_send_udp_request_hex(cls, stub, signal_name, namespace, payload_value):
        """
        Send a request via UDP interface (BeamyBroker) setting the payload to signal
        manually as a hex-value

        Using this request is usefull when sending a whole frame
        May be used when testing setting unused bits in a frame, values out of range etc.
        """
        source = common_pb2.ClientId(id="support_udp_hex")
        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
        signal_with_payload = network_api_pb2.Signal(id=signal)
        signal_with_payload.raw = payload_value
        logging.debug("source: %s signal_with_PL: %s", source, payload_value)
        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            logging.error(err)

    @classmethod
    def t_send_udp_request_list(cls, stub, sig_payl_list, namespace):
        """
        Send a request via UDP interface (BeamyBroker) setting a list signals and their
        payload values.
        May be used advantageously for setting a bunch of signals simultaneously without
        caring witch messages/frames are involved. BeamyBroker picks the correct messages
        from DBC and take care of formatting.

        For each element in sig_payl_list the name is checked against DBC.
        If signal exists then signal/payload is added to request to send.
        """
        source = common_pb2.ClientId(id="support_upd_list")
        for sig, payl in sig_payl_list:
            signal = common_pb2.SignalId(name=sig, namespace=namespace)
            signal_with_payload = network_api_pb2.Signal(id=signal)
            signal_with_payload.raw = payl
            logging.debug("source: %s signal_with_PL: %s", source, payl)
            publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
        try:
            stub.PublishSignals(publisher_info)
        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
            logging.error(err)
