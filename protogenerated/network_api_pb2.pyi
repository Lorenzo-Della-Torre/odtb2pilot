import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PublisherConfig(_message.Message):
    __slots__ = ["clientId", "frequency", "signals"]
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    SIGNALS_FIELD_NUMBER: _ClassVar[int]
    clientId: _common_pb2.ClientId
    frequency: int
    signals: Signals
    def __init__(self, signals: _Optional[_Union[Signals, _Mapping]] = ..., clientId: _Optional[_Union[_common_pb2.ClientId, _Mapping]] = ..., frequency: _Optional[int] = ...) -> None: ...

class Signal(_message.Message):
    __slots__ = ["arbitration", "double", "empty", "id", "integer", "raw", "timestamp"]
    ARBITRATION_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INTEGER_FIELD_NUMBER: _ClassVar[int]
    RAW_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    arbitration: bool
    double: float
    empty: bool
    id: _common_pb2.SignalId
    integer: int
    raw: bytes
    timestamp: int
    def __init__(self, id: _Optional[_Union[_common_pb2.SignalId, _Mapping]] = ..., integer: _Optional[int] = ..., double: _Optional[float] = ..., arbitration: bool = ..., empty: bool = ..., raw: _Optional[bytes] = ..., timestamp: _Optional[int] = ...) -> None: ...

class SignalIds(_message.Message):
    __slots__ = ["signalId"]
    SIGNALID_FIELD_NUMBER: _ClassVar[int]
    signalId: _containers.RepeatedCompositeFieldContainer[_common_pb2.SignalId]
    def __init__(self, signalId: _Optional[_Iterable[_Union[_common_pb2.SignalId, _Mapping]]] = ...) -> None: ...

class Signals(_message.Message):
    __slots__ = ["signal"]
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    signal: _containers.RepeatedCompositeFieldContainer[Signal]
    def __init__(self, signal: _Optional[_Iterable[_Union[Signal, _Mapping]]] = ...) -> None: ...

class SubscriberConfig(_message.Message):
    __slots__ = ["clientId", "onChange", "signals"]
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    ONCHANGE_FIELD_NUMBER: _ClassVar[int]
    SIGNALS_FIELD_NUMBER: _ClassVar[int]
    clientId: _common_pb2.ClientId
    onChange: bool
    signals: SignalIds
    def __init__(self, clientId: _Optional[_Union[_common_pb2.ClientId, _Mapping]] = ..., signals: _Optional[_Union[SignalIds, _Mapping]] = ..., onChange: bool = ...) -> None: ...
