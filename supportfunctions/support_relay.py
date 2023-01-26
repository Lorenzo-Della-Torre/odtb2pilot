"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

    project:  Hilding testenvironment using Beamy Broker
    author:   hweiler (Hans-Klaus Weiler) and jpiousmo (Jenefer Liban P)
    date:     2020-09-25
    version:  1.0
    date:     2022-12-20
    version:  2.0

    Description: This file provides support to use different relay types to control the
    current flow to the ECU or do some other tests like bus off.

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
import os
from typing import Dict
from pathlib import Path
import time
import yaml

import smbus

from hilding import get_conf

try:
    bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
except FileNotFoundError:
    logging.error("Relay hardware is not connected. Please check the connection")

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


    def relay_on(self, relay_num, seeed):
        """
            Turns relay on
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """

        seeed["DEVICE_REG_DATA"] = self.relay_get_port_data(relay_num, seeed)
        seeed["DEVICE_REG_DATA"] &= ~(0x1 << (relay_num - 1))

        logging.debug('Turning relay %s ON', relay_num)
        self.write_relay(relay_num, seeed)


    def relay_off(self, relay_num, seeed):
        """
            Turns relay off
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """

        seeed["DEVICE_REG_DATA"] = self.relay_get_port_data(relay_num, seeed)
        seeed["DEVICE_REG_DATA"] |= (0x1 << (relay_num - 1))

        logging.debug('Turning relay %s ON', relay_num)
        self.write_relay(relay_num, seeed)

    def relay_toggle(self, relay_num, seeed):
        """
            Toggles relay
            Parameter: relay_num (1..4, depending on relays on card)
                       seeed    I2C parameters for relay card
        """
        logging.debug('Toggling relay: %s', relay_num)
        relay_state = self.relay_get_status(self, relay_num, seeed)#pylint:disable=too-many-function-args
        if relay_state:
            # it's on, so turn it off
            self.relay_off(self, relay_num, seeed)#pylint:disable=too-many-function-args
        else:
            # it's off, so turn it on
            self.relay_on(self, relay_num, seeed)#pylint:disable=too-many-function-args

        # return True if the state changed
        return relay_state != self.relay_get_status(self, relay_num, seeed)#pylint:disable=too-many-function-args

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

    @staticmethod
    def write_relay(relay_num, seeed):
        """ writes the data received to the relay """
        if isinstance(relay_num, int):
            # do we have a valid relay number?
            if 0 < relay_num <= seeed["NUM_RELAY_PORTS"]:
                bus.write_byte_data(seeed["DEVICE_ADDRESS"],\
                                    seeed["DEVICE_REG_MODE1"],\
                                    seeed["DEVICE_REG_DATA"])
            else:
                logging.debug('Invalid relay #%s:', relay_num)
        else:
            logging.debug('Relay number must be an Integer value')


class Sequent_Relay:
    """
        The Sequent relay card is mounted on the GPIO of the Raspberry
        and communicates via I2C.
    """

    @staticmethod
    def relay_on(relay_num, num_of_relays):
        """
            Turns relay on
            Parameter: relay_num (1..8, depending on relays on card)
                       seeed    I2C parameters for relay card
        """
        # Here 0 is the level of the relay connected. Assumed 0 as
        # there will only be one relay connected and at level 0
        if num_of_relays == 4:
            os.system("4relind 0 write "+ str(relay_num) + " on")
        else:
            os.system("8relind 0 write "+ str(relay_num) + " on")

    @staticmethod
    def relay_off(relay_num, num_of_relays):
        """
            Turns relay off
            Parameter: relay_num (1..8, depending on relays on card)
                       seeed    I2C parameters for relay card
        """
        # Here 0 is the level of the relay connected. Assumed 0 as
        # there will only be one relay connected at level 0
        if num_of_relays == 4:
            os.system("4relind 0 write "+ str(relay_num) + " off")
        else:
            os.system("8relind 0 write "+ str(relay_num) + " off")

    @staticmethod
    def relay_all_on(num_of_relays):
        """
            Turns all relays on
        """
        # Here 0 is the level of the relay connected. Assumed 0 as
        # there will only be one relay connected at level 0
        if num_of_relays == 4:
            os.system("4relind 0 write 1 on")
            os.system("4relind 0 write 2 on")
            os.system("4relind 0 write 3 on")
            os.system("4relind 0 write 4 on")
        else:
            os.system("8relind 0 write 1 on")
            os.system("8relind 0 write 2 on")
            os.system("8relind 0 write 3 on")
            os.system("8relind 0 write 4 on")
            os.system("8relind 0 write 5 on")
            os.system("8relind 0 write 6 on")
            os.system("8relind 0 write 7 on")
            os.system("8relind 0 write 8 on")

    @staticmethod
    def relay_all_off(num_of_relays):
        """
            Turns all relays off
        """
        # Here 0 is the level of the relay connected. Assumed 0 as
        # there will only be one relay connected at level 0
        if num_of_relays == 4:
            os.system("4relind 0 write 1 off")
            os.system("4relind 0 write 2 off")
            os.system("4relind 0 write 3 off")
            os.system("4relind 0 write 4 off")
        else:
            os.system("8relind 0 write 1 off")
            os.system("8relind 0 write 2 off")
            os.system("8relind 0 write 3 off")
            os.system("8relind 0 write 4 off")
            os.system("8relind 0 write 5 off")
            os.system("8relind 0 write 6 off")
            os.system("8relind 0 write 7 off")
            os.system("8relind 0 write 8 off")

    def relay_toggle(self, num_of_relays, relay_num):
        """
            Toggle relay based on the current state.
        """
        # Here 0 is the level of the relay connected. Assumed 0 as
        # there will only be one relay connected at level 0
        if num_of_relays == 4:
            relay_state = self.relay_get_status(num_of_relays, relay_num)
            if relay_state == 1:
                os.system("4relind 0 write "+ str(relay_num) + " off")
            elif relay_state == 0:
                os.system("4relind 0 write "+ str(relay_num) + " on")
        else:
            relay_state = self.relay_get_status(num_of_relays, relay_num)
            if relay_state == 1:
                os.system("8relind 0 write "+ str(relay_num) + " off")
            elif relay_state == 0:
                os.system("8relind 0 write "+ str(relay_num) + " on")

        # return True if the state changed
        return relay_state != self.relay_get_status(num_of_relays, relay_num)


    @staticmethod
    def relay_get_status(num_of_relays, relay_num):
        """  Returns the current state of relay """
        if num_of_relays == 4:
            relay_state = os.popen("4relind 0 read " + str(relay_num)).read().strip()
        else:
            relay_state = os.popen("8relind 0 read " + str(relay_num)).read().strip()
        return int(relay_state)

class Relay: #pylint: disable= too-many-instance-attributes
    """
        The master class to call different types of relays.
    """

    def __init__(self):
        self.relay_name = get_conf().rig.relay_name
        self.conf_relay = self.get_relay_attributes().get("relay_types")
        if self.relay_name in self.conf_relay:
            self.relay_addr = self.conf_relay.get(self.relay_name).get("address")
            self.register = self.conf_relay.get(self.relay_name).get("register")
            self.number_of_relays = self.conf_relay.get(self.relay_name).get("number_of_relays")
            self.power_relay_num = self.conf_relay.get(
                                                self.relay_name).get("power_relay_num")
            self.PSR_relay_num = self.conf_relay.get(self.relay_name).get("PSR_relay_num")
            self.is_relay_connected = True
        else: # Creating variables with dummy values to avoid pylint
            self.relay_addr = 0x20
            self.register = 0x06
            self.number_of_relays = 4
            self.power_relay_num = 1
            self.PSR_relay_num = 2
            self.is_relay_connected = False

    @staticmethod
    def get_relay_attributes():
        """ returns a dictionary with the relay configuration """
        conf_relay_yml = Path(__file__).parent.parent.joinpath("conf_relay.yml")
        with open(conf_relay_yml) as conf_relay_file:
            conf_relay = yaml.safe_load(conf_relay_file)
        return conf_relay

    def relay_on(self, relay_num):
        """
            Turns relay on
            Parameter: relay_num (1..8, depending on relays on card)
                       seeed    I2C parameters for relay card
        """

        if self.relay_name == "sequent_relay_4set":
            Sequent_Relay.relay_on(relay_num,self.number_of_relays)
        elif self.relay_name == "sequent_relay_8set":
            Sequent_Relay.relay_on(relay_num,self.number_of_relays)
        elif self.relay_name == "52pi_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_on(Support_Seeed_4Relay,relay_num, seeed)
        elif self.relay_name == "heli_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_on(Support_Seeed_4Relay, relay_num, seeed)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        time.sleep(0.5)

    def relay_off(self, relay_num):
        """
            Turns relay off
            Parameter: relay_num (1..8, depending on relays on card)
                       seeed    I2C parameters for relay card
        """

        if self.relay_name == "sequent_relay_4set":
            Sequent_Relay.relay_off(relay_num,self.number_of_relays)
        elif self.relay_name == "sequent_relay_8set":
            Sequent_Relay.relay_off(relay_num,self.number_of_relays)
        elif self.relay_name == "52pi_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_off(Support_Seeed_4Relay, relay_num, seeed)
        elif self.relay_name == "heli_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_off(Support_Seeed_4Relay, relay_num, seeed)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        time.sleep(0.5)

    def relay_all_on(self):
        """
            Turns all relay on
        """
        if self.relay_name == "sequent_relay_4set":
            Sequent_Relay.relay_all_on(self.number_of_relays)
        elif self.relay_name == "sequent_relay_8set":
            Sequent_Relay.relay_all_on(self.number_of_relays)
        elif self.relay_name == "52pi_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_all_on(seeed)
        elif self.relay_name == "heli_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_all_on(seeed)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        time.sleep(0.5)

    def relay_all_off(self):
        """
            Turns all relay on
        """
        if self.relay_name == "sequent_relay_4set":
            Sequent_Relay.relay_all_off(self.number_of_relays)
        elif self.relay_name == "sequent_relay_8set":
            Sequent_Relay.relay_all_off(self.number_of_relays)
        elif self.relay_name == "52pi_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_all_off(seeed)
        elif self.relay_name == "heli_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            Support_Seeed_4Relay.relay_all_off(seeed)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        time.sleep(0.5)

    def relay_toggle(self, relay_num):
        """
            Toggles the relay by reading the current state.
        """
        relay_state = -1
        if self.relay_name == "sequent_relay_4set":
            relay_state = Sequent_Relay.relay_toggle(
                                Sequent_Relay, self.number_of_relays, relay_num)
        elif self.relay_name == "sequent_relay_8set":
            relay_state = Sequent_Relay.relay_toggle(
                                Sequent_Relay, self.number_of_relays, relay_num)
        elif self.relay_name == "52pi_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            relay_state = Support_Seeed_4Relay.relay_toggle(Support_Seeed_4Relay, relay_num, seeed) # pylint: disable= no-value-for-parameter
        elif self.relay_name == "heli_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            relay_state = Support_Seeed_4Relay.relay_toggle(Support_Seeed_4Relay, relay_num, seeed)# pylint: disable= no-value-for-parameter
        else:
            logging.info("Error, the relay is unknown / Not connected")

        return relay_state

    def relay_status(self, relay_num):
        """
            Returns the current selected relay state.
        """
        relay_state = -1
        if self.relay_name == "sequent_relay_4set":
            relay_state = Sequent_Relay.relay_get_status(self.number_of_relays, relay_num)
        elif self.relay_name == "sequent_relay_8set":
            relay_state = Sequent_Relay.relay_get_status(self.number_of_relays, relay_num)
        elif self.relay_name == "52pi_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            relay_state = Support_Seeed_4Relay.relay_get_status(
                                            Support_Seeed_4Relay, relay_num, seeed) # pylint: disable= no-value-for-parameter
        elif self.relay_name == "heli_relay_4set":
            seeed: Seeed = {
            "NUM_RELAY_PORTS": self.number_of_relays,
            "DEVICE_ADDRESS": self.relay_addr,
            "DEVICE_REG_MODE1": self.register,
            "DEVICE_REG_DATA" : 0xff
                }
            relay_state = Support_Seeed_4Relay.relay_get_status(
                                            Support_Seeed_4Relay, relay_num, seeed)# pylint: disable= no-value-for-parameter
        else:
            logging.info("Error, the relay is unknown / Not connected")
            relay_state = -1

        return relay_state

    def power_off(self):
        """
            Turns power on
        """
        if self.is_relay_connected == 1:
            self.relay_on(self.power_relay_num)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        return self.verify_relay_state(self.power_relay_num, 1)

    def power_on(self):
        """
            Turns power off
        """
        if self.is_relay_connected == 1:
            self.relay_off(self.power_relay_num)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        return self.verify_relay_state(self.power_relay_num, 0)

    def psr_off(self):
        """
            Turns PSR on
        """
        if self.is_relay_connected == 1:
            self.relay_on(self.PSR_relay_num)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        return self.verify_relay_state(self.PSR_relay_num, 1)

    def psr_on(self):
        """
            Turns PSR off
        """
        if self.is_relay_connected == 1:
            self.relay_off(self.PSR_relay_num)
        else:
            logging.info("Error, the relay is unknown / Not connected")

        return self.verify_relay_state(self.PSR_relay_num, 0)

    def ecu_on(self):
        """
            Turns PSR and power on
        """
        state_power = self.power_on()
        state_psr = self.psr_on()

        return state_power and state_psr

    def ecu_off(self):
        """
            Turns PSR and power off
        """
        state_power = self.power_off()
        state_psr = self.psr_off()

        return state_power and state_psr

    def toggle_power(self):
        """
            Toggle ECU power and PSR
        """
        success = -1
        if self.is_relay_connected == 1:
            state_psr = self.relay_toggle(self.PSR_relay_num)
            state_power = self.relay_toggle(self.power_relay_num)
            success = state_power and state_psr
        else:
            logging.info("Error, the relay is unknown / Not connected")

        return success

    def verify_relay_state(self, relay_num, expected_state):
        """
            Returns whether the given relay number is set as per the data or not
        """
        relay_state = self.relay_status(relay_num)
        return bool(relay_state == expected_state)
