import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

BADDATE: LicenseStatus
BADSIGNATURE: LicenseStatus
DESCRIPTOR: _descriptor.FileDescriptor
EXPIRED: LicenseStatus
INCOMPLETEJSON: LicenseStatus
INVALIDJSON: LicenseStatus
MALFORMED: LicenseStatus
NOTERMSAGREEMENT: LicenseStatus
SERVERERROR: LicenseStatus
UNSET: LicenseStatus
VALID: LicenseStatus
WRONGMACHINE: LicenseStatus

class Configuration(_message.Message):
    __slots__ = ["interfacesJson", "networkInfo", "publicAddress", "serverVersion"]
    INTERFACESJSON_FIELD_NUMBER: _ClassVar[int]
    NETWORKINFO_FIELD_NUMBER: _ClassVar[int]
    PUBLICADDRESS_FIELD_NUMBER: _ClassVar[int]
    SERVERVERSION_FIELD_NUMBER: _ClassVar[int]
    interfacesJson: bytes
    networkInfo: _containers.RepeatedCompositeFieldContainer[_common_pb2.NetworkInfo]
    publicAddress: str
    serverVersion: str
    def __init__(self, networkInfo: _Optional[_Iterable[_Union[_common_pb2.NetworkInfo, _Mapping]]] = ..., interfacesJson: _Optional[bytes] = ..., publicAddress: _Optional[str] = ..., serverVersion: _Optional[str] = ...) -> None: ...

class FileDescription(_message.Message):
    __slots__ = ["path", "sha256"]
    PATH_FIELD_NUMBER: _ClassVar[int]
    SHA256_FIELD_NUMBER: _ClassVar[int]
    path: str
    sha256: str
    def __init__(self, sha256: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class FileDownloadResponse(_message.Message):
    __slots__ = ["chunk", "errorMessage"]
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    chunk: bytes
    errorMessage: str
    def __init__(self, chunk: _Optional[bytes] = ..., errorMessage: _Optional[str] = ...) -> None: ...

class FileUploadChunkRequest(_message.Message):
    __slots__ = ["cancelUpload", "chunk", "chunkId", "chunks", "fileDescription", "uploadTimeout"]
    CANCELUPLOAD_FIELD_NUMBER: _ClassVar[int]
    CHUNKID_FIELD_NUMBER: _ClassVar[int]
    CHUNKS_FIELD_NUMBER: _ClassVar[int]
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    FILEDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    UPLOADTIMEOUT_FIELD_NUMBER: _ClassVar[int]
    cancelUpload: bool
    chunk: bytes
    chunkId: int
    chunks: int
    fileDescription: FileDescription
    uploadTimeout: int
    def __init__(self, fileDescription: _Optional[_Union[FileDescription, _Mapping]] = ..., chunks: _Optional[int] = ..., chunkId: _Optional[int] = ..., chunk: _Optional[bytes] = ..., cancelUpload: bool = ..., uploadTimeout: _Optional[int] = ...) -> None: ...

class FileUploadRequest(_message.Message):
    __slots__ = ["chunk", "fileDescription"]
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    FILEDESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    chunk: bytes
    fileDescription: FileDescription
    def __init__(self, fileDescription: _Optional[_Union[FileDescription, _Mapping]] = ..., chunk: _Optional[bytes] = ...) -> None: ...

class FileUploadResponse(_message.Message):
    __slots__ = ["cancelled", "errorMessage", "finished"]
    CANCELLED_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    FINISHED_FIELD_NUMBER: _ClassVar[int]
    cancelled: bool
    errorMessage: str
    finished: bool
    def __init__(self, finished: bool = ..., cancelled: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...

class License(_message.Message):
    __slots__ = ["data", "termsAgreement"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    TERMSAGREEMENT_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    termsAgreement: bool
    def __init__(self, data: _Optional[bytes] = ..., termsAgreement: bool = ...) -> None: ...

class LicenseInfo(_message.Message):
    __slots__ = ["expires", "json", "requestId", "requestMachineId", "status"]
    EXPIRES_FIELD_NUMBER: _ClassVar[int]
    JSON_FIELD_NUMBER: _ClassVar[int]
    REQUESTID_FIELD_NUMBER: _ClassVar[int]
    REQUESTMACHINEID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    expires: str
    json: bytes
    requestId: str
    requestMachineId: bytes
    status: LicenseStatus
    def __init__(self, status: _Optional[_Union[LicenseStatus, str]] = ..., json: _Optional[bytes] = ..., expires: _Optional[str] = ..., requestId: _Optional[str] = ..., requestMachineId: _Optional[bytes] = ...) -> None: ...

class ReloadMessage(_message.Message):
    __slots__ = ["configuration", "errorMessage"]
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    configuration: Configuration
    errorMessage: str
    def __init__(self, configuration: _Optional[_Union[Configuration, _Mapping]] = ..., errorMessage: _Optional[str] = ...) -> None: ...

class LicenseStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
