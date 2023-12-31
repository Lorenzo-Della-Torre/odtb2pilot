# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: functional_api.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import protogenerated.common_pb2 as common__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='functional_api.proto',
  package='base',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x14\x66unctional_api.proto\x12\x04\x62\x61se\x1a\x0c\x63ommon.proto\"]\n\nSenderInfo\x12 \n\x08\x63lientId\x18\x01 \x01(\x0b\x32\x0e.base.ClientId\x12\x1a\n\x05value\x18\x02 \x01(\x0b\x32\x0b.base.Value\x12\x11\n\tfrequency\x18\x03 \x01(\x05\"G\n\x11SubscriberRequest\x12 \n\x08\x63lientId\x18\x01 \x01(\x0b\x32\x0e.base.ClientId\x12\x10\n\x08onChange\x18\x02 \x01(\x08\"\x18\n\x05Value\x12\x0f\n\x07payload\x18\x01 \x01(\x05\x32\xe7\x01\n\x11\x46unctionalService\x12/\n\x0eOpenPassWindow\x12\x0e.base.ClientId\x1a\x0b.base.Empty\"\x00\x12\x30\n\x0f\x43losePassWindow\x12\x0e.base.ClientId\x1a\x0b.base.Empty\"\x00\x12.\n\x0bSetFanSpeed\x12\x10.base.SenderInfo\x1a\x0b.base.Empty\"\x00\x12?\n\x13SubscribeToFanSpeed\x12\x17.base.SubscriberRequest\x1a\x0b.base.Value\"\x00\x30\x01\x62\x06proto3')
  ,
  dependencies=[common__pb2.DESCRIPTOR,])




_SENDERINFO = _descriptor.Descriptor(
  name='SenderInfo',
  full_name='base.SenderInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='clientId', full_name='base.SenderInfo.clientId', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='base.SenderInfo.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='frequency', full_name='base.SenderInfo.frequency', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
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
  serialized_start=44,
  serialized_end=137,
)


_SUBSCRIBERREQUEST = _descriptor.Descriptor(
  name='SubscriberRequest',
  full_name='base.SubscriberRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='clientId', full_name='base.SubscriberRequest.clientId', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='onChange', full_name='base.SubscriberRequest.onChange', index=1,
      number=2, type=8, cpp_type=7, label=1,
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
  serialized_start=139,
  serialized_end=210,
)


_VALUE = _descriptor.Descriptor(
  name='Value',
  full_name='base.Value',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='payload', full_name='base.Value.payload', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
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
  serialized_start=212,
  serialized_end=236,
)

_SENDERINFO.fields_by_name['clientId'].message_type = common__pb2._CLIENTID
_SENDERINFO.fields_by_name['value'].message_type = _VALUE
_SUBSCRIBERREQUEST.fields_by_name['clientId'].message_type = common__pb2._CLIENTID
DESCRIPTOR.message_types_by_name['SenderInfo'] = _SENDERINFO
DESCRIPTOR.message_types_by_name['SubscriberRequest'] = _SUBSCRIBERREQUEST
DESCRIPTOR.message_types_by_name['Value'] = _VALUE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SenderInfo = _reflection.GeneratedProtocolMessageType('SenderInfo', (_message.Message,), {
  'DESCRIPTOR' : _SENDERINFO,
  '__module__' : 'functional_api_pb2'
  # @@protoc_insertion_point(class_scope:base.SenderInfo)
  })
_sym_db.RegisterMessage(SenderInfo)

SubscriberRequest = _reflection.GeneratedProtocolMessageType('SubscriberRequest', (_message.Message,), {
  'DESCRIPTOR' : _SUBSCRIBERREQUEST,
  '__module__' : 'functional_api_pb2'
  # @@protoc_insertion_point(class_scope:base.SubscriberRequest)
  })
_sym_db.RegisterMessage(SubscriberRequest)

Value = _reflection.GeneratedProtocolMessageType('Value', (_message.Message,), {
  'DESCRIPTOR' : _VALUE,
  '__module__' : 'functional_api_pb2'
  # @@protoc_insertion_point(class_scope:base.Value)
  })
_sym_db.RegisterMessage(Value)



_FUNCTIONALSERVICE = _descriptor.ServiceDescriptor(
  name='FunctionalService',
  full_name='base.FunctionalService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=239,
  serialized_end=470,
  methods=[
  _descriptor.MethodDescriptor(
    name='OpenPassWindow',
    full_name='base.FunctionalService.OpenPassWindow',
    index=0,
    containing_service=None,
    input_type=common__pb2._CLIENTID,
    output_type=common__pb2._EMPTY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ClosePassWindow',
    full_name='base.FunctionalService.ClosePassWindow',
    index=1,
    containing_service=None,
    input_type=common__pb2._CLIENTID,
    output_type=common__pb2._EMPTY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='SetFanSpeed',
    full_name='base.FunctionalService.SetFanSpeed',
    index=2,
    containing_service=None,
    input_type=_SENDERINFO,
    output_type=common__pb2._EMPTY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='SubscribeToFanSpeed',
    full_name='base.FunctionalService.SubscribeToFanSpeed',
    index=3,
    containing_service=None,
    input_type=_SUBSCRIBERREQUEST,
    output_type=_VALUE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_FUNCTIONALSERVICE)

DESCRIPTOR.services_by_name['FunctionalService'] = _FUNCTIONALSERVICE

# @@protoc_insertion_point(module_scope)
