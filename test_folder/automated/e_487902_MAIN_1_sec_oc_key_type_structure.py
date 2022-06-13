"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487902
version: 1
title: SecOC - Key type structure
purpose: >
    Define the format and structure of the SecOC key(s), when programmed to the ECU server.
    The distribution of keys to e.g. diagnostic clients shall comply with other methods.

description: >
    The SecOC key(s) shall be represented in hexadecimal format when programmed using
    writeDataByIdentifier service 0x2E to the ECU server with data identifier 0xD0CA.

    To ensure the integrity of the key, a checksum is appended to the key data record when
    programmed. The ECU must successfully verify the checksum prior to the key is stored in
    non-volatile memory.

    The format of the key(s) when programmed shall be the concatenation of one Byte long SecOC key
    attributes, two Bytes long SecOC Cluster Key Identifier number, 16 Byte long SecOC key
    encryption Initialization Vector (IV) used for encrypting old plain text key and new plain text
    key together, SecOC key data records of corresponding SecOC Cluster Key Identifier (old and
    new key of 16 Byte long each in plain text format or one 32 Byte encrypted keys data record
    format of old and new keys), followed by a two Byte long CRC16-CCIT computed over whole message
    (SecOC Key Attributes || SecOC Cluster Key Identifier number || SecOC Key Encryption
    Initialization Vector || ((old plain text key || new plain text key) or Encrypted key data
    record)).

    The CRC16-CCIT shall have the initial value 0xFFFF and using normal representation, i.e. the
    polynomial is 0x1021.

    ECU shall verify SecOC Cluster Key Identifier value and old plain text key before storing new
    key for respective SecOC Cluster Key Identifier during programming of SecOC key.

    Key Attributes:
    One Byte value which describes the attributes of keys in DID write request.

    Key format:
    LSB 2 bits of Byte key attributes value. Describes format of keys present in DID write request
    when programming SecOC key.
    0b00- Plain text key format
    0b01- Encrypted key format - AES128 CTR mode
    0b10- Reserved
    0b11- Reserved
    Remaining 6 bits in key attributes byte are reserved for future purpose and shall have default
    values as zero.

    SecOC Key - Encryption IV:
    A 128-bit Cryptographic nonce, typically a random value, used as Initialization Vector when
    encrypting/decrypting both SecOC plain text old and new keys together in DID request. The SecOC
    key encryption IV value shall be discarded after usage, i.e. after DID operation, and shall
    never be persistently stored in ECU.

    Note: The SecOC key encryption IV shall always be present in key structure of DID request and
    not used in ECU when key format in key attributes is in plain text format (Key format = 0b00)
    but is used only for CRC 16 checksum verification in this case.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 488712 because new SecOC key is programmed using
    WriteDataByIdentifier service 0x2E upon receiving DID 0xD0CA.
"""
import logging
import sys
from e_488712_MAIN_0_sec_oc_key_update_handling_in_ecu import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
