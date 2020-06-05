""" project:  ODTB2 testenvironment using SignalBroker
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
        switcher = {
            "confirmedDTC": b'\x03',
            "testFailed": b'\x00',
            "testFailedThisMonitoringCycle": b'\x01',
            "pendingDTC": b'\x02',
            "testNotCompletedSinceLastClear": b'\x04',
            "testFailedSinceLastClear": b'\x05',
            "testNotCompletedThisMonitoringCycle": b'\x06',
            "warningIndicatorRequested": b'\x07',
        }
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
        switcher = {
            "DiagnosticSessionControl": b'\x10' + message,
            "ECUResetHardReset": b'\x11\x01' + message,
            "ClearDiagnosticInformation": b'\x14' + message,
            "ReadDTCInfoExtDataRecordByDTCNumber": b'\x19\x06' + message + mask,
            "ReadDTCInfoExtDataRecordByDTCNumber(86)": b'\x19\x86' + message + mask,
            "ReadDTCInfoSnapshotRecordByDTCNumber": b'\x19\x04'+ message + mask,
            "ReadDTCInfoSnapshotRecordByDTCNumber(84)": b'\x19\x84'+ message + mask,
            "ReadDTCInfoSnapshotIdentification": b'\x19\x03',
            "ReadDTCInfoSnapshotIdentification(83)": b'\x19\x83',
            "ReadDTCInfoReportSupportedDTC": b'\x19\x0A',
            "ReadDTCInfoReportDTCWithPermanentStatus": b'\x19\x15',
            "ReadDataByIdentifier": b'\x22'+ message,
            "ReadMemoryByAddress": b'\x23'+ mask + message,
            "SecurityAccessRequestSeed": b'\x27\x01'+ mask + message,
            "SecurityAccessSendKey": b'\x27\x02'+ mask + message,
            "DynamicallyDefineDataIdentifier": b'\x2A'+ mask + message,
            "ReadDataBePeriodicIdentifier": b'\x2C'+ mask + message,
            "WriteDataByIdentifier": b'\x2E'+ message,
            "RoutineControlRequestSID": b'\x31'+ mask + message,
            "RequestUpload": b'\x35'+ message,
            "TransferData": b'\x36'+ message,
            "RequestDownload": b'\x74'+ message,
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
        result = switcher.get(name, b'')
        logging.debug("Name:    [%s]", name)
        logging.debug("Message: [%s]", message)
        logging.debug("Mask:    [%s]", mask)
        logging.debug("Result:  [%s]", result)
        if result == b'':
            logging.warning("You typed a wrong name: %s", name)
        return result
