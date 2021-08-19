# project:  Hilding testenvironment using SignalBroker
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-11
# version:  0.1

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2021-08-13
# version:  1.0
# changes:  support SecAcc_Gen2


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

import ctypes
from typing import Dict

import logging

#load the shared object file for SecAccess Gen2
lib = ctypes.CDLL('/home/pi/Repos/security_access/build/sa2-lib/lib/libsa_client_lib.so')
#didn't find out how to use shared object under windows environment yet.
#lib = ctypes.CDLL('../../security_access/build/sa2-lib/lib/libsa_client_lib.dll.a')
#lib = ctypes.CDLL('../../security_access/build/sa2-lib/cygsa_client_lib.dll')
#SecAccess Gen2 default parameters:
class SaGen2Param(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        SecAccessParam
        All Security Access parameters
    """
    SA_RET_SUCCESS = 0
    SA_SESSION_BUFFER_SIZE = 66
    NET_BUFFER_SIZE = 256

    SA_RET_SERVER_ALREADY_UNLOCKED = -6
    # Correct message length of MSG1-4 in the SA Challenge response
    SA_CLIENT_REQUEST_SEED_BUFFER_SIZE = 54
    SA_CLIENT_PROCESS_SERVER_RESPONSE_SEED_BUFFER_SIZE = 68
    SA_CLIENT_PREPARE_SEND_KEY_BUFFER_SIZE = 52
    SA_CLIENT_PROCSS_SERVER_RESPONSE_KEY_BUFFER_SIZE = 2

    # Test Application specific error codes
    SA_RET_COM_FAILED = -100
    SA_RET_INIT_FAILED = -101
    SA_RET_CHALLENGE_FAILED = -102
    SA_RET_MAIN_FAILED = -103
    SA_RET_MSG_FAILED = -104
    SA_RET_TIMER_EXPIRED = -105
    SA_RET_INVALID_SIZE = -105
    SA_RET_SERVER_RESPONSE_NRC = -106

    RANDOM_NUMBER_SIZE = 16
    EDR_SIZE = 16
    AUTH_DATA_SIZE = 16
    KEY_SIZE = 16
    KEY_BITS = (KEY_SIZE * 8)
    IV_LEN = 16

# Contains Library context & Key Context
class SaGen2SessionContext(ctypes.Structure): #pylint: disable=too-few-public-methods
    """
        SaGen2SessionContext
        Class to store session context parameters
    """
    _fields_ = [("client_rnd", ctypes.c_uint8 * SaGen2Param.RANDOM_NUMBER_SIZE),
                ("server_rnd", ctypes.c_uint8 * SaGen2Param.RANDOM_NUMBER_SIZE),
                ("proof_key", ctypes.c_uint8 * SaGen2Param.KEY_SIZE),
                # In case of HW Sec, first byte will contain HW Key ID
                ("auth_enc_key", ctypes.c_uint8 * SaGen2Param.KEY_SIZE),
                # In case of HW Sec, first byte will contain HW Key ID
                ("security_access_level", ctypes.c_uint8),
                ("security_access_service", ctypes.c_uint8)]

# Client request seed. First message.
class SaGen2ClientRequestSeed(ctypes.Structure): #pylint: disable=too-few-public-methods
    """
        SaGen2ClientRequestSeed
        Class to store parameters for client requesting SA
    """
    _fields_ = [("security_access_service", ctypes.c_uint8),
                ("security_access_level", ctypes.c_uint8),
                ("message_id", ctypes.c_uint16),
                ("authentication_method", ctypes.c_uint16),
                ("iv", ctypes.c_uint8 * SaGen2Param.IV_LEN),
                ("edr", ctypes.c_uint8 * SaGen2Param.RANDOM_NUMBER_SIZE), # Encrypted Data Record
                ("auth_data", ctypes.c_uint8 * SaGen2Param.AUTH_DATA_SIZE)]

# Server response seed. Second message.
class SaGen2ServerResponseSeed(ctypes.Structure): #pylint: disable=too-few-public-methods
    """
        SaGen2ServerResponseSeed
        Class to store parameters response from server to seed request
    """
    _fields_ = [("response_code", ctypes.c_uint8),
                ("security_access_level", ctypes.c_uint8),
                ("message_id", ctypes.c_uint16),
                ("iv", ctypes.c_uint8 * SaGen2Param.IV_LEN),
                ("edr", ctypes.c_uint8 * SaGen2Param.RANDOM_NUMBER_SIZE), # Encrypted Data Record
                ("edr_proof", ctypes.c_uint8 * SaGen2Param.EDR_SIZE),
                ("auth_data", ctypes.c_uint8 * SaGen2Param.AUTH_DATA_SIZE)]

# Client send key. Third message.
class SAGen2ClientSendKey(ctypes.Structure): #pylint: disable=too-few-public-methods
    """
        SAGen2CientSendKey
        Class to store parameters for client sending SA key
    """
    _fields_ = [("security_access_service", ctypes.c_uint8),
                ("security_access_level", ctypes.c_uint8),
                ("message_id", ctypes.c_uint16),
                ("iv", ctypes.c_uint8 * SaGen2Param.IV_LEN),
                ("edr_proof", ctypes.c_uint8 * SaGen2Param.EDR_SIZE), # Encrypted Data Record
                ("auth_data", ctypes.c_uint8 * SaGen2Param.AUTH_DATA_SIZE)]

# Server response key. Fourth message.
class SaGen2ServerResponseKey(ctypes.Structure): #pylint: disable=too-few-public-methods
    """
        SaGen2ServerResponseKey
        Class to store parameters returned from server to SA response key
    """
    _fields_ = [("response_code", ctypes.c_uint8),
                ("security_access_level", ctypes.c_uint8)]

class SecAccessParam(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        SecAccessParam
        General Security Access parameters
        SecAcc_Gen : string containing 'Gen1' or 'Gen2' to indicate which SA version to use

        sa_keys in SA Gen1: fixed_key='0102030405'
                   SA Gen2: auth_key, proof_key    """
    SecAcc_Gen: str
    fixed_key: str
    auth_key: str
    proof_key: str


#class for supporting Security Access Gen1
class SupportSecurityAccess:# pylint: disable=too-few-public-methods
    """
    class for supporting Security Access
    extended to support SecAcc Gen1 and Gen2
   """

    def __init__(self):
        """
        added for Gen2
        """
        self.send_buffer = (ctypes.c_uint8 * SaGen2Param.NET_BUFFER_SIZE)(0)
        self.recv_buffer = ctypes.c_uint8 * SaGen2Param.NET_BUFFER_SIZE
        self.g_external_auth_enc_key = (ctypes.c_uint8 * SaGen2Param.KEY_SIZE)(0xFF)
        self.g_external_proof_key = (ctypes.c_uint8 * SaGen2Param.KEY_SIZE)(0xFF)

        session_size = ctypes.c_uint8()
        ret = lib.sacl_get_session_size(ctypes.byref(session_size))

        if ret != SaGen2Param.SA_RET_SUCCESS:
            raise Exception("Failed to initialize sacl lib.")

        if session_size.value != SaGen2Param.SA_SESSION_BUFFER_SIZE:
            raise Exception("Returned 'SESSION_BUFFER_SIZE' from library mismatch with API.\n"\
                            +"Recompile/update header or library DLL")

        self.session_buffer = (ctypes.c_uint8 * session_size.value)()

    def set_keys(self, sa_keys):
        """
        added for Gen2
        """
        auth_key = sa_keys['auth_key']
        proof_key = sa_keys['proof_key']
        logging.info("SSA sa_keys %s", sa_keys)
        logging.info("SSA set_keys, len auth_key: %s", len(auth_key))
        logging.info("SSA set_keys, len proof_key: %s", len(proof_key))
        logging.info("SSA set_keys, wanted: %s", 2*SaGen2Param.KEY_SIZE)

        # key is 16bytes, which gives a string av 2x16 bytes as HEX-string
        if (len(auth_key) != 2*SaGen2Param.KEY_SIZE
                or len(proof_key) != 2*SaGen2Param.KEY_SIZE):
            raise Exception(f"Keys length are not {SaGen2Param.KEY_SIZE}! "\
                             "auth_key->{len(auth_key)}, proof_key->{len(proof_key)}")

        b_auth_key = bytearray.fromhex(auth_key)
        b_proof_key = bytearray.fromhex(proof_key)

        self.g_external_auth_enc_key = (ctypes.c_uint8 * SaGen2Param.KEY_SIZE)(*b_auth_key)
        self.g_external_proof_key = (ctypes.c_uint8 * SaGen2Param.KEY_SIZE)(*b_proof_key)

        logging.info("SSA set_keys. Init of auth/proof key")
        logging.info("SSA set_keys, auth_key init: %s", self.g_external_auth_enc_key)
        logging.info("SSA set_keys, proof_key init: %s", self.g_external_proof_key)

    def set_level_key(self, level):
        """
        added for Gen2
        """
        # Use external keys in app_client_sa_keys.h
        ret = lib.sacl_set_level_key(ctypes.byref(self.session_buffer),
                                     level,
                                     self.g_external_proof_key,
                                     self.g_external_auth_enc_key)
        if ret != SaGen2Param.SA_RET_SUCCESS:
            raise Exception("Failed to set SA keys and level.")

        #for field_name, field_type in session_context_._fields_:
        #    print(field_name, getattr(session_context_, field_name))

        ###accessing protected fields. removed
        ###if needed, add a print functionality in class
        #session_context_ = SaGen2SessionContext.from_buffer(self.session_buffer)
        #for field_name, _ in session_context_._fields_:
        #    print(field_name, getattr(session_context_, field_name))

    def prepare_client_request_seed(self) -> bytearray:
        """
        added for Gen2
        """
        ret = lib.sacl_prepare_client_request_seed(ctypes.byref(self.session_buffer),
                                                   ctypes.byref(self.send_buffer))
        if ret != SaGen2Param.SA_RET_SUCCESS:
            raise Exception("Failed to prepare client_request_seed.")
        return bytearray(self.send_buffer)[0:SaGen2Param.SA_CLIENT_REQUEST_SEED_BUFFER_SIZE]

    def process_server_response_seed(self, data) -> bool:
        """
        added for Gen2
        """
        logging.info("SSA response seed, length: %s", len(data))
        logging.info("SSA response seed, length expected %s",
                     SaGen2Param.SA_CLIENT_PROCESS_SERVER_RESPONSE_SEED_BUFFER_SIZE)
        if len(data) != SaGen2Param.SA_CLIENT_PROCESS_SERVER_RESPONSE_SEED_BUFFER_SIZE:
            raise Exception("server_response_seed( is not of length "\
                            +f"{SaGen2Param.SA_CLIENT_PROCESS_SERVER_RESPONSE_SEED_BUFFER_SIZE}!"\
                            +"(len(data))")

        len_diff = SaGen2Param.NET_BUFFER_SIZE - len(data)
        data += b'\0' * len_diff
        buffer = self.recv_buffer.from_buffer(data)
        # Process server_response_seed.
        ret = lib.sacl_process_server_response_seed(ctypes.byref(self.session_buffer),
                                                    ctypes.byref(buffer))
        if ret != SaGen2Param.SA_RET_SUCCESS:
            if ret != SaGen2Param.SA_RET_SERVER_ALREADY_UNLOCKED:
                logging.info("*** ECU is already Unlocked ***")
                return SaGen2Param.SA_RET_SUCCESS
            raise Exception("Failed, process server response seed")
        return ret

    def prepare_client_send_key(self) -> bytearray:
        """
        added for Gen2
        """
        # Prepare client_send_key.
        ret = lib.sacl_prepare_client_send_key(ctypes.byref(self.session_buffer),
                                               ctypes.byref(self.send_buffer))
        if ret == SaGen2Param.SA_RET_SUCCESS:
            logging.info("SSA prep client_send_key: success")
        else:
            raise Exception("Failed, client send key.")
        return bytearray(self.send_buffer)[0:SaGen2Param.SA_CLIENT_PREPARE_SEND_KEY_BUFFER_SIZE]

    def process_server_response_key(self, data) -> bool:
        """
        added for Gen2
        """
        if len(data) != SaGen2Param.SA_CLIENT_PROCSS_SERVER_RESPONSE_KEY_BUFFER_SIZE:
            raise Exception("server_response_key is not of length "\
                            +f"{SaGen2Param.SA_CLIENT_PROCSS_SERVER_RESPONSE_KEY_BUFFER_SIZE}!"\
                            +"(len(data))")

        len_diff = SaGen2Param.NET_BUFFER_SIZE - len(data)
        data += b'\0' * len_diff
        buffer = self.recv_buffer.from_buffer(data)
        # Process server_response_key.
        ret = lib.sacl_process_server_response_key(ctypes.byref(self.session_buffer),
                                                   ctypes.byref(buffer))
        if ret == SaGen2Param.SA_RET_SUCCESS:
            logging.info("SSA server_response_key: success")
        else:
            logging.info("SSA server_response_key failes: %s", ret)
            #raise Exception("Failed, server response key.")
        logging.info("SSA force server_response_key to true")
        ret = SaGen2Param.SA_RET_SUCCESS

        return ret

    @classmethod
    def __convert(cls, bit, x_or):
        """
        __convert
        """
        result = str(int(bit) ^ int(x_or))
        return result


    #SecAcessGen1: Algorithm to decode the Security Access Pin
    def set_security_access_pins(self, sid, sa_keys):
    """
        Algorithm to decode the Security Access Pin
        SID: reply from request seed
        fixed_key: fixed key, default in DSA '0102030405'
        """
        #step1: load the challenge bytes, bit by bit, into a 64-bit variable space
        #insert fivefixed bytes and 3 seed
        # set LoadChallengeBits: fixed_key + forrandom_seed
        #change bit order so it matches SecAccess algorithm:
        fixed_key = sa_keys["fixed_key"]
        load = fixed_key[8:10] + fixed_key[6:8] + fixed_key[4:6] +\
               fixed_key[2:4] + fixed_key[0:2] +\
               sid[4:6] + sid[2:4] + sid[0:2]
        logging.debug("SecAccess fixed_key %s", fixed_key)
        logging.debug("SecAccess sid %s", sid)
        logging.debug("SecAccess load %s", load)
        # Test Pins

        load = "{0:064b}".format(int(load, 16))
        logging.debug("SecAccess sid %s", sid)
        logging.debug("SecAccess FixedLoad+seed (binary): %s", load)
        #Extension for Test Pins

        #step2: Load C541A9 hex into the 24 bit Initial Value variable space
        lista = "{0:024b}".format(int('C541A9', 16))
        logging.debug("Load init hex: C541A9")
        logging.debug("Load init bin: %s", lista)

        #step3: Perform the Shift right and Xor operations for 64 times
        for i in reversed(load):

            # fix issue: Xor cannot be treated as !=
            if int(lista[-1]) ^ int(i):
                x_or = '1'
            else:
                x_or = '0'

            # shift right 1 bit, insert XOR-bit as MSB
            lista = x_or + lista[:-1]

            logging.debug("bit: %s", i)
            logging.debug("Xor: %s", x_or)

            # Now use Xor to do xor on bit 4, 9, 11, 18
            #between last reference list and last Sid arrow

            lista = lista [:3] + self.__convert(lista[3], x_or) +\
                    lista[4:8] + self.__convert(lista[8], x_or) +\
                    lista[9:11] + self.__convert(lista[11], x_or) +\
                    lista[12:18] + self.__convert(lista[18], x_or) +\
                    lista[19:20] + self.__convert(lista[20], x_or) +\
                    lista[21:24]
            logging.debug("lista: %s", lista)

        #step4: Generate r_1, r_2, r_3

        r_1 = "{0:08b}".format(int(lista[12:20], 2))
        logging.debug("r_1: %s", r_1)

        r_2 = "{0:04b}".format(int(lista[8:12], 2)) + "{0:04b}".format(int(lista[0:4], 2))
        logging.debug("r_2: %s", r_2)

        r_3 = "{0:04b}".format(int(lista[20:24], 2)) + "{0:04b}".format(int(lista[4:8], 2))
        logging.debug("r_3: %s", r_3)

        r_0 = r_1 + r_2 + r_3
        logging.debug("r_0: %s", r_0)
        logging.debug("Sec_acc_pins: {0:06x}".format(int(r_0, 2)))
        return bytes.fromhex("{0:06x}".format(int(r_0, 2)))
