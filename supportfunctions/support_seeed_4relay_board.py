""" project:  ODTB2 testenvironment using SignalBroker
    author:   hweiler (Hans-Klaus Weiler)
    date:     2020-09-25
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
#import sys
from typing import Dict

import smbus

# The number of relay ports on the relay board.
# This value should never change!
#NUM_RELAY_PORTS = 4

# Change the following value if your Relay board uses a different I2C address.
#DEVICE_ADDRESS = 0x20  # 7 bit address (will be left shifted to add the read write bit)

# Don't change the values, there's no need for that.
#DEVICE_REG_MODE1 = 0x06
#DEVICE_REG_DATA = 0xff

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

class Seeed(Dict): # pylint: disable=inherit-non-class, too-few-public-methods
    """
        Parameters used in VBF header
        For keywords see Volvo Document 31808832 Rev 015
        SWRS Versatile Binary Format Specification
    """
    NUM_RELAY_PORTS: int
    DEVICE_ADDRESS: int
    DEVICE_REG_MODE1: int
    DEVICE_REG_DATA: int

class Support_Seeed_4Relay:
    """
        The Seeed 4-relay-card is mounted on the GPIO of the Raspberry
        and communicates via I2C.
        Doing this only 2 pins of GPIO are used:
            GPIO2 (SDA) - PIN3
            GPIO3 (SCL) - PIN5
        More info about that card:
            https://www.seeedstudio.com/Raspberry-Pi-Relay-Board-v1-0.html
    """


    @staticmethod
    def relay_on(relay_num, seeed):
        """
            Turns relay on
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """
        if isinstance(relay_num, int):
            # do we have a valid relay number?
            if 0 < relay_num <= seeed["NUM_RELAY_PORTS"]:
                logging.debug('Turning relay %s ON', relay_num)
                seeed["DEVICE_REG_DATA"] &= ~(0x1 << (relay_num - 1))
                bus.write_byte_data(seeed["DEVICE_ADDRESS"],\
                                    seeed["DEVICE_REG_MODE1"],\
                                    seeed["DEVICE_REG_DATA"])
            else:
                logging.debug('Invalid relay #%s:', relay_num)
        else:
            logging.debug('Relay number must be an Integer value')


    @staticmethod
    def relay_off(relay_num, seeed):
        """
            Turns relay off
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """

        if isinstance(relay_num, int):
            # do we have a valid relay number?
            if 0 < relay_num <= seeed["NUM_RELAY_PORTS"]:
                logging.debug('Turning relay %s OFF', relay_num)
                seeed["DEVICE_REG_DATA"] |= (0x1 << (relay_num - 1))
                bus.write_byte_data(seeed["DEVICE_ADDRESS"],\
                                    seeed["DEVICE_REG_MODE1"],\
                                    seeed["DEVICE_REG_DATA"])
            else:
                logging.debug('Invalid relay #%s:', relay_num)
        else:
            logging.debug('Relay number must be an Integer value')

    def relay_toggle(self, relay_num, seeed):
        """
            Toggles relay
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """
        logging.debug('Toggling relay: %s', relay_num)
        if self.relay_get_status(relay_num, seeed):
            # it's on, so turn it off
            self.relay_off(relay_num, seeed)
        else:
            # it's off, so turn it on
            self.relay_on(relay_num, seeed)

    def relay_get_status(self, relay_num, seeed):
        """
            return relay status
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """
        # determines whether the specified port is ON/OFF
        logging.debug('Checking status of relay %s', relay_num)
        res = self.relay_get_port_data(relay_num, seeed)
        if res > 0:
            mask = 1 << (relay_num - 1)
            # return the specified bit status
            return (seeed["DEVICE_REG_DATA"] & mask) == 0
        # otherwise (invalid port), always return False
        logging.debug("Specified relay port is invalid")
        return False


    @staticmethod
    def relay_get_port_data(relay_num, seeed):
        """
            return relay_get_port_data
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
            gets the current byte value stored in the relay board
        """
        logging.debug('Reading relay status value for relay %s', relay_num)
        # do we have a valid port?
        if 0 < relay_num <= seeed["NUM_RELAY_PORTS"]:
            # read the memory location
            seeed["DEVICE_REG_DATA"] = bus.read_byte_data(seeed["DEVICE_ADDRESS"],\
                                                          seeed["DEVICE_REG_MODE1"])
            # return the specified bit status
            return seeed["DEVICE_REG_DATA"]
        # otherwise (invalid port), always return 0
        logging.debug("Specified relay port is invalid")
        return 0


    @staticmethod
    def relay_all_on(seeed):
        """
            Turns all relay on
            Parameter: seeed    I2C parameters for relay card
        """
        logging.debug('Turning all relays ON')
        seeed["DEVICE_REG_DATA"] &= ~(0xf << 0)
        bus.write_byte_data(seeed["DEVICE_ADDRESS"],\
                            seeed["DEVICE_REG_MODE1"],\
                            seeed["DEVICE_REG_DATA"])


    @staticmethod
    def relay_all_off(seeed):
        """
            Turns all relay off
            Parameter: seeed    I2C parameters for relay card
        """

        logging.debug('Turning all relays OFF')
        seeed["DEVICE_REG_DATA"] |= (0xf << 0)
        #bus.write_byte_data(DEVICE_ADDRESS, DEVICE_REG_MODE1, DEVICE_REG_DATA)
        bus.write_byte_data(seeed["DEVICE_ADDRESS"],\
                            seeed["DEVICE_REG_MODE1"],\
                            seeed["DEVICE_REG_DATA"])


#    @classmethod
#    def t_send_gpio_signal_hex(cls, stub, signal_name, namespace, payload_value):
#        """
#        t_send_GPIO_signal_hex
#
#        Send GPIO message  with raw (hex) payload
#        """
#        source = common_pb2.ClientId(id="app_identifier")
#        signal = common_pb2.SignalId(name=signal_name, namespace=namespace)
#        signal_with_payload = network_api_pb2.Signal(id=signal)
#        signal_with_payload.raw = payload_value
#        logging.debug("source: %s signal_with_PL: %s", source, payload_value)
#        publisher_info = network_api_pb2.PublisherConfig(clientId=source,\
#            signals=network_api_pb2.Signals(signal=[signal_with_payload]), frequency=0)
#        try:
#            stub.PublishSignals(publisher_info)
#        except grpc._channel._Rendezvous as err: # pylint: disable=protected-access
#            logging.error(err)
