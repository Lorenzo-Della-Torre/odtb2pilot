import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DiagnosticsRequest(_message.Message):
    __slots__ = ["dataIdentifier", "downLink", "serviceId", "upLink"]
    DATAIDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    DOWNLINK_FIELD_NUMBER: _ClassVar[int]
    SERVICEID_FIELD_NUMBER: _ClassVar[int]
    UPLINK_FIELD_NUMBER: _ClassVar[int]
    dataIdentifier: bytes
    downLink: _common_pb2.SignalId
    serviceId: bytes
    upLink: _common_pb2.SignalId
    def __init__(self, upLink: _Optional[_Union[_common_pb2.SignalId, _Mapping]] = ..., downLink: _Optional[_Union[_common_pb2.SignalId, _Mapping]] = ..., serviceId: _Optional[bytes] = ..., dataIdentifier: _Optional[bytes] = ...) -> None: ...

class DiagnosticsResponse(_message.Message):
    __slots__ = ["raw"]
    RAW_FIELD_NUMBER: _ClassVar[int]
    raw: bytes
    def __init__(self, raw: _Optional[bytes] = ...) -> None: ...
