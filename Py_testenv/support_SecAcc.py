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

#import time
from support_service27 import SupportService27

from support_can import Support_CAN, CanParam
from support_test_odtb2 import Support_test_ODTB2

SC = Support_CAN()
SUTE = Support_test_ODTB2()

SE27 = SupportService27()

#class for supporting Security Access
class Support_Security_Access:
    """
    class for supporting Security Access
    """

    #_debug = True
    _debug = False

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
        #load = '43BB42AA41'
        #load = load + '8A' + '96' + '4E'

        #load = (bin(int(load, 16)))
        #load = load[2:]
        load = "{0:064b}".format(int(load, 16))
        if self._debug:
            print("SecAccess sid ", sid)
            print("SecAccess FixedLoad+seed (binary: ", load)
        #Extension for Test Pins
        #load = '0' + load
        #print(hex(int(load[:8])))

        #invert load - not needed loop reverse instead
        #load = load[::-1]

        #step2: Load C541A9 hex into the 24 bit Initial Value variable space
        #lista = bin(int('C541A9', 16))
        #lista = lista[2:]
        lista = "{0:024b}".format(int('C541A9', 16))
        if self._debug:
            print("Load init hex: C541A9")
            print("Load init bin: ", lista)

        #step3: Perform the Shift right and Xor operations for 64 times
        for i in reversed(load):

            # fix issue: Xor cannot be treated as !=
            #lista1 = bin(lista[-1] != i)
            #lista1 = lista1[2:]
            if int(lista[-1]) ^ int(i):
                x_or = '1'
            else:
                x_or = '0'
            # shift right 1 bit, insert XOR-bit as MSB
            lista = x_or + lista[:-1]
            # Now use Xor to do xor on bit 4, 9, 11, 18
            #between last reference list and last Sid arrow
            lista3 = str(int(lista[3]) ^ int(x_or))
            lista8 = str(int(lista[8]) ^ int(x_or))
            lista11 = str(int(lista[11]) ^ int(x_or))
            lista18 = str(int(lista[18]) ^ int(x_or))
            lista20 = str(int(lista[20]) ^ int(x_or))

            if self._debug:
                print("bit: ", i)
                print("Xor: ", x_or)
            lista = lista [:3] + lista3 + lista[4:8] + lista8 + lista[9:11] +\
                 lista11 + lista[12:18] + lista18 + lista[19:20] + lista20 + lista[21:24]
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

    #Support function to activate the Security Access
    def activation_security_access(self, can_p: CanParam, step_no, purpose):
        """
        Support function to activate the Security Access
        """
        #Security Access request seed
        testresult, seed = SE27.pbl_security_access_request_seed(can_p, step_no, purpose)

        fixed_key = 'FFFFFFFFFF'
        r_0 = self.set_security_access_pins(seed, fixed_key)

        #Security Access Send Key
        testresult = testresult and SE27.pbl_security_access_send_key(can_p, r_0, step_no, purpose)
        return testresult
