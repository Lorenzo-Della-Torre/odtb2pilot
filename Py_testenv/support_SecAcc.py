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

import time

from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2

SC = Support_CAN()
SUTE = Support_test_ODTB2()

#class for supporting Security Access
class Support_Security_Access:
    """
    class for supporting Security Access
    """

    #Algorithm to decode the Security Access Pin
    def set_security_access_pins(self, sid):
        """
        Algorithm to decode the Security Access Pin
        """
        #iteration variable
        i = int

        #step1: load the challenge bytes, bit by bit, into a 64-bit variable space
        #insert fivefixed bytes and 3 seed
        load = 'FFFFFFFFFF'
        load = load + sid[4:6] + sid[2:4] + sid[0:2]
        # Test Pins
        #load = '43BB42AA41'
        #load = load + '8A' + '96' + '4E'
        load = (bin(int(load, 16)))
        load = load[2:]
        #Extension for Test Pins
        #load = '0' + load
        #print(hex(int(load[:8])))
        load = load[::-1]

        #step2: Load C541A9 hex into the 24 bit Initial Value variable space
        lista = bin(int('C541A9', 16))
        lista = lista[2:]

        #step3: Perform the Shift right and Xor operations for 64 times
        for i in load:

            lista1 = bin(lista[-1] != i)
            lista1 = lista1[2:]
            # invert position of first bit with the last
            lista = lista1 + lista[:-1]
            # Xor between last reference list and last Sid arrow
            lista3 = bin(lista[3] != lista1)
            lista3 = lista3[2:]
            #successive Xor between Blast and ....
            lista8 = bin(lista[8] != lista1)
            lista8 = lista8[2:]

            lista11 = bin(lista[11] != lista1)
            lista11 = lista11[2:]

            lista18 = bin(lista[18] != lista1)
            lista18 = lista18[2:]

            lista20 = bin(lista[20] != lista1)
            lista20 = lista20[2:]

            lista = lista [:3] + lista3 + lista[4:8] + lista8 + lista[9:11] +\
                 lista11 + lista[12:18] + lista18 + lista[19:20] + lista20 + lista[21:24]

        #step4: Generate r_1, r_2, r_3
        r_1 = hex(int(lista[12:20], 2))
        r_1 = hex(int(r_1, 16) + int("0x200", 16))
        r_1 = r_1[3:]
        #print(r_1)
        r_2 = hex(int((lista[8:12] + lista[0:4]), 2))
        r_2 = hex(int(r_2, 16) + int("0x200", 16))
        r_2 = r_2[3:]
        #print(r_2)
        r_3 = hex(int((lista[20:24] + lista[4:8]), 2))
        r_3 = hex(int(r_3, 16) + int("0x200", 16))
        r_3 = r_3[3:]
        #print(r_3)
        r_0 = hex(int(('0x' + r_1 + r_2 + r_3), 16) + int("0x2000000", 16))
        r_0 = r_0[3:]
        print(r_0)
        return bytes.fromhex(r_0)

    #Support function to activate the Security Access
    def activation_security_access(self, stub, can_send, can_rec, can_nspace, step_no, purpose):
        """
        Support function to activate the Security Access
        """
        #Security Access request sid
        testresult = True
        timeout = 0.05
        min_no_messages = 1
        max_no_messages = 1

        can_m_send = b'\x27\x01'
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)

        r_0 = self.set_security_access_pins(SC.can_messages[can_rec][0][2][6:12])

        #Security Access Send Key
        timeout = 0.05
        min_no_messages = -1
        max_no_messages = -1

        can_m_send = b'\x27\x02'+ r_0
        can_mr_extra = ''

        testresult = testresult and SUTE.teststep(stub, can_m_send, can_mr_extra, can_send,
                                                  can_rec, can_nspace, step_no, purpose,
                                                  timeout, min_no_messages, max_no_messages)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_rec], '6702')
        time.sleep(1)
        return testresult