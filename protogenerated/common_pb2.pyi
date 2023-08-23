from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClientId(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class FrameInfo(_message.Message):
    __slots__ = ["childInfo", "signalInfo"]
    CHILDINFO_FIELD_NUMBER: _ClassVar[int]
    SIGNALINFO_FIELD_NUMBER: _ClassVar[int]
    childInfo: _containers.RepeatedCompositeFieldContainer[SignalInfo]
    signalInfo: SignalInfo
    def __init__(self, signalInfo: _Optional[_Union[SignalInfo, _Mapping]] = ..., childInfo: _Optional[_Iterable[_Union[SignalInfo, _Mapping]]] = ...) -> None: ...

class Frames(_message.Message):
    __slots__ = ["frame"]
    FRAME_FIELD_NUMBER: _ClassVar[int]
    frame: _containers.RepeatedCompositeFieldContainer[FrameInfo]
    def __init__(self, frame: _Optional[_Iterable[_Union[FrameInfo, _Mapping]]] = ...) -> None: ...

class MetaData(_message.Message):
    __slots__ = ["cycleTime", "description", "factor", "isRaw", "max", "min", "offset", "receiver", "sender", "size", "startValue", "unit"]
    CYCLETIME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FACTOR_FIELD_NUMBER: _ClassVar[int]
    ISRAW_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    STARTVALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    cycleTime: float
    description: str
    factor: float
    isRaw: bool
    max: float
    min: float
    offset: float
    receiver: _containers.RepeatedScalarFieldContainer[str]
    sender: _containers.RepeatedScalarFieldContainer[str]
    size: int
    startValue: float
    unit: str
    def __init__(self, description: _Optional[str] = ..., max: _Optional[float] = ..., min: _Optional[float] = ..., unit: _Optional[str] = ..., size: _Optional[int] = ..., isRaw: bool = ..., factor: _Optional[float] = ..., offset: _Optional[float] = ..., sender: _Optional[_Iterable[str]] = ..., receiver: _Optional[_Iterable[str]] = ..., cycleTime: _Optional[float] = ..., startValue: _Optional[float] = ...) -> None: ...

class NameSpace(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class NetworkInfo(_message.Message):
    __slots__ = ["description", "namespace", "type"]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    description: str
    namespace: NameSpace
    type: str
    def __init__(self, namespace: _Optional[_Union[NameSpace, _Mapping]] = ..., type: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class SignalId(_message.Message):
    __slots__ = ["name", "namespace"]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    namespace: NameSpace
    def __init__(self, name: _Optional[str] = ..., namespace: _Optional[_Union[NameSpace, _Mapping]] = ...) -> None: ...

class SignalInfo(_message.Message):
    __slots__ = ["id", "metaData"]
    ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: SignalId
    metaData: MetaData
    def __init__(self, id: _Optional[_Union[SignalId, _Mapping]] = ..., metaData: _Optional[_Union[MetaData, _Mapping]] = ...) -> None: ...
