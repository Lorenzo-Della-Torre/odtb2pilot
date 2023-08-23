import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SenderInfo(_message.Message):
    __slots__ = ["clientId", "frequency", "value"]
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    clientId: _common_pb2.ClientId
    frequency: int
    value: Value
    def __init__(self, clientId: _Optional[_Union[_common_pb2.ClientId, _Mapping]] = ..., value: _Optional[_Union[Value, _Mapping]] = ..., frequency: _Optional[int] = ...) -> None: ...

class SubscriberRequest(_message.Message):
    __slots__ = ["clientId", "onChange"]
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    ONCHANGE_FIELD_NUMBER: _ClassVar[int]
    clientId: _common_pb2.ClientId
    onChange: bool
    def __init__(self, clientId: _Optional[_Union[_common_pb2.ClientId, _Mapping]] = ..., onChange: bool = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ["payload"]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: int
    def __init__(self, payload: _Optional[int] = ...) -> None: ...
