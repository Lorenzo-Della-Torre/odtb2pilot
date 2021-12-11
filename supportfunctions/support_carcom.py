/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


""" project:  Hilding testenvironment using SignalBroker
    author:   fjansso8 (Fredrik Jansson)
    date:     2020-05-12
    version:  1.0

    author:   j-assar1 (Joel Assarsson)
    date:     2020-10-23
    version:  1.1

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

class SupportCARCOM:
    # Disable the too-few-public-methods violation. I'm sure we will have more methods later.
    # pylint: disable=too-few-public-methods
    """
        SupportCARCOM
    """

    @classmethod
    def __read_dtc_by_status_mask(cls, mask):
        """
        __read_dtc_by_status_mask
        """
        #logging.debug("SCarCom: status_mask: %s", mask)
        switcher = {
            "confirmedDTC": b'\x03',
            "testFailed": b'\x00',
            "testFailedThisMonitoringCycle": b'\x01',
            "pendingDTC": b'\x02',
            "testNotCompletedSinceLastClear": b'\x04',
            "testFailedSinceLastClear": b'\x05',
            "testNotCompletedThisMonitoringCycle": b'\x06',
            "warningIndicatorRequested": b'\x07',
            b'confirmedDTC': b'\x03',
            b'testFailed': b'\x00',
            b'testFailedThisMonitoringCycle': b'\x01',
            b'pendingDTC': b'\x02',
            b'testNotCompletedSinceLastClear': b'\x04',
            b'testFailedSinceLastClear': b'\x05',
            b'testNotCompletedThisMonitoringCycle': b'\x06',
            b'warningIndicatorRequested': b'\x07',
        }
        #logging.debug("SCarCom: status_mask switcher: %s", switcher.get(mask, b''))
        return switcher.get(mask, b'')


    def can_m_send(self, name, message, mask):
        """
            Support function for reading out DTC/DID data:
            services
            "DiagnosticSessionControl"=10
            "reportDTCExtDataRecordByDTCNumber"=19 06
            "reportDTCSnapdhotRecordByDTCNumber"= 19 04
            "reportDTCByStatusMask"=19 02 + "confirmedDTC"=03 / "testFailed"=00
            "ReadDataByIentifier"=22
            Etc.....
        """
        #logging.debug("SCarCom: can_m_send name: %s, message: %s mask: %s", name, message, mask)
        switcher = {
            "DiagnosticSessionControl": b'\x10' + message,
            "ECUResetHardReset": b'\x11\x01' + message,
            "ECUResetHardReset_noreply": b'\x11\x81' + message,
            "ClearDiagnosticInformation": b'\x14' + message,
            "ReadDTCInfoExtDataRecordByDTCNumber": b'\x19\x06' + message + mask,
            "ReadDTCInfoExtDataRecordByDTCNumber(86)": b'\x19\x86' + message + mask,
            "ReadDTCInfoSnapshotRecordByDTCNumber": b'\x19\x04'+ message + mask,
            "ReadDTCInfoSnapshotRecordByDTCNumber(84)": b'\x19\x84'+ message + mask,
            "ReadDTCInfoSnapshotIdentification": b'\x19\x03',
            "ReadDTCInfoSnapshotIdentification(83)": b'\x19\x83',
            "ReadDTCInfoReportSupportedDTC": b'\x19\x0A',
            "ReadDTCInfoReportDTCWithPermanentStatus": b'\x19\x15',
            "ReadDataByIdentifier": b'\x22'+ message + mask,
            "ReadMemoryByAddress": b'\x23'+ mask + message,
            "SecurityAccessRequestSeed": b'\x27\x01'+ mask + message,
            "SecurityAccessRequestSeed_mode1_3": b'\x27\x05'+ mask + message,
            "SecurityAccessSendKey": b'\x27\x02'+ mask + message,
            "SecurityAccessSendKey_mode1_3": b'\x27\x06'+ mask + message,
            "ReadDataByPeriodicIdentifier": b'\x2A'+ mask + message,
            "DynamicallyDefineDataIdentifier": b'\x2C'+ mask + message,
            "WriteDataByIdentifier": b'\x2E'+ message,
            "RoutineControlRequestSID": b'\x31'+ mask + message,
            "RequestDownload": b'\x34'+ message,
            "RequestUpload": b'\x35'+ message,
            "TransferData": b'\x36'+ message,
            "ReadGenericInformationReportGenericSnapshotByDTCNumber": b'\xAF\x04' + message + mask,
            "ReadGenericInformationReportGenericSnapshotByDTCNumber(84)": b'\xAF\x84' \
                + message + mask,
            "ReadGenericInformationReportGenericExtendedDataByDTCNumber": b'\xAF\x06' \
                + message + mask,
            "ReadGenericInformationReportGenericExtendedDataByDTCNumber(86)": b'\xAF\x86' \
                + message + mask,
            "ReadDTCByStatusMask": b'\x19\x02' + self.__read_dtc_by_status_mask(mask),
            "ReadDTCByStatusMask(82)": b'\x19\x82' + self.__read_dtc_by_status_mask(mask)
        }
        switched = switcher.get(name, b'')
        #logging.debug("Name:    [%s]", name)
        #logging.debug("Message: [%s]", message)
        #logging.debug("Mask:    [%s]", mask)
        #logging.debug("Switched:  [%s]", switched)
        if switched == b'':
            logging.warning("You typed a wrong name: %s", name)
        return switched
