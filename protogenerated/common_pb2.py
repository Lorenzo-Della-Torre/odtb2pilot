# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: common.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='common.proto',
  package='base',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=b'\n\x0c\x63ommon.proto\x12\x04\x62\x61se\"\x07\n\x05\x45mpty\"\x16\n\x08\x43lientId\x12\n\n\x02id\x18\x01 \x01(\t\"<\n\x08SignalId\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\"\n\tnamespace\x18\x02 \x01(\x0b\x32\x0f.base.NameSpace\"J\n\nSignalInfo\x12\x1a\n\x02id\x18\x01 \x01(\x0b\x32\x0e.base.SignalId\x12 \n\x08metaData\x18\x02 \x01(\x0b\x32\x0e.base.MetaData\"d\n\x08MetaData\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\x0b\n\x03max\x18\x05 \x01(\x05\x12\x0b\n\x03min\x18\x06 \x01(\x05\x12\x0c\n\x04unit\x18\x07 \x01(\t\x12\x0c\n\x04size\x18\x08 \x01(\x05\x12\r\n\x05isRaw\x18\t \x01(\x08\"\x19\n\tNameSpace\x12\x0c\n\x04name\x18\x01 \x01(\t\"7\n\rConfiguration\x12&\n\x0bnetworkInfo\x18\x01 \x03(\x0b\x32\x11.base.NetworkInfo\"T\n\x0bNetworkInfo\x12\"\n\tnamespace\x18\x01 \x01(\x0b\x32\x0f.base.NameSpace\x12\x0c\n\x04type\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\"V\n\tFrameInfo\x12$\n\nsignalInfo\x18\x01 \x01(\x0b\x32\x10.base.SignalInfo\x12#\n\tchildInfo\x18\x02 \x03(\x0b\x32\x10.base.SignalInfo\"(\n\x06\x46rames\x12\x1e\n\x05\x66rame\x18\x01 \x03(\x0b\x32\x0f.base.FrameInfob\x06proto3'
)




_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='base.Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=29,
)


_CLIENTID = _descriptor.Descriptor(
  name='ClientId',
  full_name='base.ClientId',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='base.ClientId.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=31,
  serialized_end=53,
)


_SIGNALID = _descriptor.Descriptor(
  name='SignalId',
  full_name='base.SignalId',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='base.SignalId.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='namespace', full_name='base.SignalId.namespace', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=55,
  serialized_end=115,
)


_SIGNALINFO = _descriptor.Descriptor(
  name='SignalInfo',
  full_name='base.SignalInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='base.SignalInfo.id', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='metaData', full_name='base.SignalInfo.metaData', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=117,
  serialized_end=191,
)


_METADATA = _descriptor.Descriptor(
  name='MetaData',
  full_name='base.MetaData',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='description', full_name='base.MetaData.description', index=0,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='max', full_name='base.MetaData.max', index=1,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='min', full_name='base.MetaData.min', index=2,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='unit', full_name='base.MetaData.unit', index=3,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='size', full_name='base.MetaData.size', index=4,
      number=8, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='isRaw', full_name='base.MetaData.isRaw', index=5,
      number=9, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=193,
  serialized_end=293,
)


_NAMESPACE = _descriptor.Descriptor(
  name='NameSpace',
  full_name='base.NameSpace',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='base.NameSpace.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=295,
  serialized_end=320,
)


_CONFIGURATION = _descriptor.Descriptor(
  name='Configuration',
  full_name='base.Configuration',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='networkInfo', full_name='base.Configuration.networkInfo', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=322,
  serialized_end=377,
)


_NETWORKINFO = _descriptor.Descriptor(
  name='NetworkInfo',
  full_name='base.NetworkInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='namespace', full_name='base.NetworkInfo.namespace', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='type', full_name='base.NetworkInfo.type', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='description', full_name='base.NetworkInfo.description', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=379,
  serialized_end=463,
)


_FRAMEINFO = _descriptor.Descriptor(
  name='FrameInfo',
  full_name='base.FrameInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='signalInfo', full_name='base.FrameInfo.signalInfo', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='childInfo', full_name='base.FrameInfo.childInfo', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=465,
  serialized_end=551,
)


_FRAMES = _descriptor.Descriptor(
  name='Frames',
  full_name='base.Frames',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='frame', full_name='base.Frames.frame', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=553,
  serialized_end=593,
)

_SIGNALID.fields_by_name['namespace'].message_type = _NAMESPACE
_SIGNALINFO.fields_by_name['id'].message_type = _SIGNALID
_SIGNALINFO.fields_by_name['metaData'].message_type = _METADATA
_CONFIGURATION.fields_by_name['networkInfo'].message_type = _NETWORKINFO
_NETWORKINFO.fields_by_name['namespace'].message_type = _NAMESPACE
_FRAMEINFO.fields_by_name['signalInfo'].message_type = _SIGNALINFO
_FRAMEINFO.fields_by_name['childInfo'].message_type = _SIGNALINFO
_FRAMES.fields_by_name['frame'].message_type = _FRAMEINFO
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
DESCRIPTOR.message_types_by_name['ClientId'] = _CLIENTID
DESCRIPTOR.message_types_by_name['SignalId'] = _SIGNALID
DESCRIPTOR.message_types_by_name['SignalInfo'] = _SIGNALINFO
DESCRIPTOR.message_types_by_name['MetaData'] = _METADATA
DESCRIPTOR.message_types_by_name['NameSpace'] = _NAMESPACE
DESCRIPTOR.message_types_by_name['Configuration'] = _CONFIGURATION
DESCRIPTOR.message_types_by_name['NetworkInfo'] = _NETWORKINFO
DESCRIPTOR.message_types_by_name['FrameInfo'] = _FRAMEINFO
DESCRIPTOR.message_types_by_name['Frames'] = _FRAMES
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.Empty)
  })
_sym_db.RegisterMessage(Empty)

ClientId = _reflection.GeneratedProtocolMessageType('ClientId', (_message.Message,), {
  'DESCRIPTOR' : _CLIENTID,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.ClientId)
  })
_sym_db.RegisterMessage(ClientId)

SignalId = _reflection.GeneratedProtocolMessageType('SignalId', (_message.Message,), {
  'DESCRIPTOR' : _SIGNALID,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.SignalId)
  })
_sym_db.RegisterMessage(SignalId)

SignalInfo = _reflection.GeneratedProtocolMessageType('SignalInfo', (_message.Message,), {
  'DESCRIPTOR' : _SIGNALINFO,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.SignalInfo)
  })
_sym_db.RegisterMessage(SignalInfo)

MetaData = _reflection.GeneratedProtocolMessageType('MetaData', (_message.Message,), {
  'DESCRIPTOR' : _METADATA,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.MetaData)
  })
_sym_db.RegisterMessage(MetaData)

NameSpace = _reflection.GeneratedProtocolMessageType('NameSpace', (_message.Message,), {
  'DESCRIPTOR' : _NAMESPACE,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.NameSpace)
  })
_sym_db.RegisterMessage(NameSpace)

Configuration = _reflection.GeneratedProtocolMessageType('Configuration', (_message.Message,), {
  'DESCRIPTOR' : _CONFIGURATION,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.Configuration)
  })
_sym_db.RegisterMessage(Configuration)

NetworkInfo = _reflection.GeneratedProtocolMessageType('NetworkInfo', (_message.Message,), {
  'DESCRIPTOR' : _NETWORKINFO,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.NetworkInfo)
  })
_sym_db.RegisterMessage(NetworkInfo)

FrameInfo = _reflection.GeneratedProtocolMessageType('FrameInfo', (_message.Message,), {
  'DESCRIPTOR' : _FRAMEINFO,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.FrameInfo)
  })
_sym_db.RegisterMessage(FrameInfo)

Frames = _reflection.GeneratedProtocolMessageType('Frames', (_message.Message,), {
  'DESCRIPTOR' : _FRAMES,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:base.Frames)
  })
_sym_db.RegisterMessage(Frames)


# @@protoc_insertion_point(module_scope)