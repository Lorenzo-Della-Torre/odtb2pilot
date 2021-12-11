"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

""" project:  Hilding testenvironment using SignalBroker
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

import logging
import sys
import grpc
sys.path.append('generated')
import protogenerated.network_api_pb2 as network_api_pb2 # pylint: disable=wrong-import-position
import protogenerated.common_pb2 as common_pb2 # pylint: disable=wrong-import-position

class SupportRpiGpio:
    # Disable the too-few-public-methods violation. I'm sure we will have more methods later.
    # pylint: disable=too-few-public-methods
    """
        SupportCAN
    """

    @classmethod
    def t_send_gpio_signal_hex(cls, stub, signal_name, namespace, payload_value):
        """
        t_send_GPIO_signal_hex

        Send GPIO message  with raw (hex) payload
        """
        source = common_pb2.ClientId(id="app_identifier")
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
