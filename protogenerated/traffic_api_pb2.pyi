import common_pb2 as _common_pb2
import system_api_pb2 as _system_api_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
PAUSE: Mode
PLAY: Mode
RECORD: Mode
STOP: Mode

class PlaybackConfig(_message.Message):
    __slots__ = ["fileDescription", "namespace"]
    FILEDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    fileDescription: _system_api_pb2.FileDescription
    namespace: _common_pb2.NameSpace
    def __init__(self, fileDescription: _Optional[_Union[_system_api_pb2.FileDescription, _Mapping]] = ..., namespace: _Optional[_Union[_common_pb2.NameSpace, _Mapping]] = ...) -> None: ...

class PlaybackInfo(_message.Message):
    __slots__ = ["playbackConfig", "playbackMode"]
    PLAYBACKCONFIG_FIELD_NUMBER: _ClassVar[int]
    PLAYBACKMODE_FIELD_NUMBER: _ClassVar[int]
    playbackConfig: PlaybackConfig
    playbackMode: PlaybackMode
    def __init__(self, playbackConfig: _Optional[_Union[PlaybackConfig, _Mapping]] = ..., playbackMode: _Optional[_Union[PlaybackMode, _Mapping]] = ...) -> None: ...

class PlaybackInfos(_message.Message):
    __slots__ = ["playbackInfo"]
    PLAYBACKINFO_FIELD_NUMBER: _ClassVar[int]
    playbackInfo: _containers.RepeatedCompositeFieldContainer[PlaybackInfo]
    def __init__(self, playbackInfo: _Optional[_Iterable[_Union[PlaybackInfo, _Mapping]]] = ...) -> None: ...

class PlaybackMode(_message.Message):
    __slots__ = ["EOF", "errorMessage", "mode"]
    EOF: str
    EOF_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    errorMessage: str
    mode: Mode
    def __init__(self, errorMessage: _Optional[str] = ..., EOF: _Optional[str] = ..., mode: _Optional[_Union[Mode, str]] = ...) -> None: ...

class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
