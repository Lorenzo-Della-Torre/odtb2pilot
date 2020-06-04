# project:  ODTB2 testenvironment using SignalBroker
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-11
# version:  0.1

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 grPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WArrANTIES Or CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the grPC route guide client."""

from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SUTE = SupportTestODTB2()

#class for supporting Security Access
class SupportSecurityAccess:
    """
    class for supporting Security Access
    """

    #_debug = True
    _debug = False


    @classmethod
    def __convert(cls, bit, x_or):
        """
        __convert
        """
        result = str(int(bit) ^ int(x_or))
        return result


    #Algorithm to decode the Security Access Pin
    def set_security_access_pins(self, sid, fixed_load='FFFFFFFFFF'):
        """
        Algorithm to decode the Security Access Pin
        """
        #step1: load the challenge bytes, bit by bit, into a 64-bit variable space
        #insert fivefixed bytes and 3 seed
        # set LoadChallengeBits: fixed_load + forrandom_seed
        load = fixed_load + sid[4:6] + sid[2:4] + sid[0:2]
        if self._debug:
            print("SecAccess fixed_load ", fixed_load)
            print("SecAccess sid ", sid)
            print("SecAccess load ", load)
        # Test Pins

        load = "{0:064b}".format(int(load, 16))
        if self._debug:
            print("SecAccess sid ", sid)
            print("SecAccess FixedLoad+seed (binary: ", load)
        #Extension for Test Pins

        #step2: Load C541A9 hex into the 24 bit Initial Value variable space
        lista = "{0:024b}".format(int('C541A9', 16))
        if self._debug:
            print("Load init hex: C541A9")
            print("Load init bin: ", lista)

        #step3: Perform the Shift right and Xor operations for 64 times
        for i in reversed(load):

            # fix issue: Xor cannot be treated as !=
            if int(lista[-1]) ^ int(i):
                x_or = '1'
            else:
                x_or = '0'

            # shift right 1 bit, insert XOR-bit as MSB
            lista = x_or + lista[:-1]

            if self._debug:
                print("bit: ", i)
                print("Xor: ", x_or)

            # Now use Xor to do xor on bit 4, 9, 11, 18
            #between last reference list and last Sid arrow

            lista = lista [:3] + self.__convert(lista[3], x_or) +\
                    lista[4:8] + self.__convert(lista[8], x_or) +\
                    lista[9:11] + self.__convert(lista[11], x_or) +\
                    lista[12:18] + self.__convert(lista[18], x_or) +\
                    lista[19:20] + self.__convert(lista[20], x_or) +\
                    lista[21:24]
            if self._debug:
                print("lista: ", lista)

        #step4: Generate r_1, r_2, r_3

        r_1 = "{0:08b}".format(int(lista[12:20], 2))
        if self._debug:
            print("r_1: ", r_1)

        r_2 = "{0:04b}".format(int(lista[8:12], 2)) + "{0:04b}".format(int(lista[0:4], 2))
        if self._debug:
            print("r_2: ", r_2)

        r_3 = "{0:04b}".format(int(lista[20:24], 2)) + "{0:04b}".format(int(lista[4:8], 2))
        if self._debug:
            print("r_3: ", r_3)

        r_0 = r_1 + r_2 + r_3
        if self._debug:
            print("r_0: ", r_0)
            print("Sec_acc_pins: {0:06x}".format(int(r_0, 2)))
        return bytes.fromhex("{0:06x}".format(int(r_0, 2)))


    @classmethod
    def pbl_security_access_request_seed(cls, can_p: CanParam, step_no, purpose):
        """
            Support function: request seed for calculating security access pin
        """
        cpay: CanPayload = {
            "payload" : b'\x27\x01',
            "extra" : ''
        }

        etp: CanTestExtra = {
            "step_no" : step_no,
            "purpose" : purpose,
            "timeout" : 1,
            "min_no_messages" : -1,
            "max_no_messages" : -1
        }

        testresult = SUTE.teststep(can_p, cpay, etp)
        seed = SC.can_messages[can_p["receive"]][0][2][6:12]
        return testresult, seed


    @classmethod
    def pbl_security_access_send_key(cls, can_p: CanParam, payload_value, step_no, purpose):
        """
            Support function: request seed for calculating security access pin
        """
        cpay: CanPayload = {
            "payload" : b'\x27\x02'+ payload_value,
            "extra" : ''
        }

        etp: CanTestExtra = {
            "step_no" : step_no,
            "purpose" : purpose,
            "timeout" : 0.1,
            "min_no_messages" : -1,
            "max_no_messages" : -1
        }

        testresult = SUTE.teststep(can_p, cpay, etp)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_p["receive"]], '6702')
        return testresult


    def activation_security_access(self, can_p: CanParam, step_no, purpose):
        """
        Support function to activate the Security Access
        """
        #Security Access request seed
        testresult, seed = self.pbl_security_access_request_seed(can_p, step_no, purpose)
        fixed_key = 'FFFFFFFFFF'
        r_0 = self.set_security_access_pins(seed, fixed_key)

        #Security Access Send Key
        testresult = testresult and self.pbl_security_access_send_key(can_p, r_0,
                                                                      step_no, purpose)
        return testresult
