# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: network_api.proto

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
  name='network_api.proto',
  package='base',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x11network_api.proto\x12\x04\x62\x61se\x1a\x0c\x63ommon.proto\"h\n\x10SubscriberConfig\x12 \n\x08\x63lientId\x18\x01 \x01(\x0b\x32\x0e.base.ClientId\x12 \n\x07signals\x18\x02 \x01(\x0b\x32\x0f.base.SignalIds\x12\x10\n\x08onChange\x18\x03 \x01(\x08\"-\n\tSignalIds\x12 \n\x08signalId\x18\x01 \x03(\x0b\x32\x0e.base.SignalId\"\'\n\x07Signals\x12\x1c\n\x06signal\x18\x01 \x03(\x0b\x32\x0c.base.Signal\"f\n\x0fPublisherConfig\x12\x1e\n\x07signals\x18\x01 \x01(\x0b\x32\r.base.Signals\x12 \n\x08\x63lientId\x18\x02 \x01(\x0b\x32\x0e.base.ClientId\x12\x11\n\tfrequency\x18\x03 \x01(\x05\"\x9c\x01\n\x06Signal\x12\x1a\n\x02id\x18\x01 \x01(\x0b\x32\x0e.base.SignalId\x12\x11\n\x07integer\x18\x02 \x01(\x03H\x00\x12\x10\n\x06\x64ouble\x18\x03 \x01(\x01H\x00\x12\x15\n\x0b\x61rbitration\x18\x04 \x01(\x08H\x00\x12\x0f\n\x05\x65mpty\x18\x06 \x01(\x08H\x00\x12\x0b\n\x03raw\x18\x05 \x01(\x0c\x12\x11\n\ttimestamp\x18\x07 \x01(\x03\x42\t\n\x07payload2\xba\x01\n\x0eNetworkService\x12?\n\x12SubscribeToSignals\x12\x16.base.SubscriberConfig\x1a\r.base.Signals\"\x00\x30\x01\x12\x36\n\x0ePublishSignals\x12\x15.base.PublisherConfig\x1a\x0b.base.Empty\"\x00\x12/\n\x0bReadSignals\x12\x0f.base.SignalIds\x1a\r.base.Signals\"\x00\x62\x06proto3')
  ,
  dependencies=[common__pb2.DESCRIPTOR,])




_SUBSCRIBERCONFIG = _descriptor.Descriptor(
  name='SubscriberConfig',
  full_name='base.SubscriberConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='clientId', full_name='base.SubscriberConfig.clientId', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='signals', full_name='base.SubscriberConfig.signals', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='onChange', full_name='base.SubscriberConfig.onChange', index=2,
      number=3, type=8, cpp_type=7, label=1,
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
  serialized_start=41,
  serialized_end=145,
)


_SIGNALIDS = _descriptor.Descriptor(
  name='SignalIds',
  full_name='base.SignalIds',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='signalId', full_name='base.SignalIds.signalId', index=0,
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
  serialized_start=147,
  serialized_end=192,
)


_SIGNALS = _descriptor.Descriptor(
  name='Signals',
  full_name='base.Signals',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='signal', full_name='base.Signals.signal', index=0,
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
  serialized_start=194,
  serialized_end=233,
)


_PUBLISHERCONFIG = _descriptor.Descriptor(
  name='PublisherConfig',
  full_name='base.PublisherConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='signals', full_name='base.PublisherConfig.signals', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='clientId', full_name='base.PublisherConfig.clientId', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='frequency', full_name='base.PublisherConfig.frequency', index=2,
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
  serialized_start=235,
  serialized_end=337,
)


_SIGNAL = _descriptor.Descriptor(
  name='Signal',
  full_name='base.Signal',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='base.Signal.id', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='integer', full_name='base.Signal.integer', index=1,
      number=2, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='double', full_name='base.Signal.double', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='arbitration', full_name='base.Signal.arbitration', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='empty', full_name='base.Signal.empty', index=4,
      number=6, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='raw', full_name='base.Signal.raw', index=5,
      number=5, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='base.Signal.timestamp', index=6,
      number=7, type=3, cpp_type=2, label=1,
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
    _descriptor.OneofDescriptor(
      name='payload', full_name='base.Signal.payload',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=340,
  serialized_end=496,
)

_SUBSCRIBERCONFIG.fields_by_name['clientId'].message_type = common__pb2._CLIENTID
_SUBSCRIBERCONFIG.fields_by_name['signals'].message_type = _SIGNALIDS
_SIGNALIDS.fields_by_name['signalId'].message_type = common__pb2._SIGNALID
_SIGNALS.fields_by_name['signal'].message_type = _SIGNAL
_PUBLISHERCONFIG.fields_by_name['signals'].message_type = _SIGNALS
_PUBLISHERCONFIG.fields_by_name['clientId'].message_type = common__pb2._CLIENTID
_SIGNAL.fields_by_name['id'].message_type = common__pb2._SIGNALID
_SIGNAL.oneofs_by_name['payload'].fields.append(
  _SIGNAL.fields_by_name['integer'])
_SIGNAL.fields_by_name['integer'].containing_oneof = _SIGNAL.oneofs_by_name['payload']
_SIGNAL.oneofs_by_name['payload'].fields.append(
  _SIGNAL.fields_by_name['double'])
_SIGNAL.fields_by_name['double'].containing_oneof = _SIGNAL.oneofs_by_name['payload']
_SIGNAL.oneofs_by_name['payload'].fields.append(
  _SIGNAL.fields_by_name['arbitration'])
_SIGNAL.fields_by_name['arbitration'].containing_oneof = _SIGNAL.oneofs_by_name['payload']
_SIGNAL.oneofs_by_name['payload'].fields.append(
  _SIGNAL.fields_by_name['empty'])
_SIGNAL.fields_by_name['empty'].containing_oneof = _SIGNAL.oneofs_by_name['payload']
DESCRIPTOR.message_types_by_name['SubscriberConfig'] = _SUBSCRIBERCONFIG
DESCRIPTOR.message_types_by_name['SignalIds'] = _SIGNALIDS
DESCRIPTOR.message_types_by_name['Signals'] = _SIGNALS
DESCRIPTOR.message_types_by_name['PublisherConfig'] = _PUBLISHERCONFIG
DESCRIPTOR.message_types_by_name['Signal'] = _SIGNAL
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SubscriberConfig = _reflection.GeneratedProtocolMessageType('SubscriberConfig', (_message.Message,), {
  'DESCRIPTOR' : _SUBSCRIBERCONFIG,
  '__module__' : 'network_api_pb2'
  # @@protoc_insertion_point(class_scope:base.SubscriberConfig)
  })
_sym_db.RegisterMessage(SubscriberConfig)

SignalIds = _reflection.GeneratedProtocolMessageType('SignalIds', (_message.Message,), {
  'DESCRIPTOR' : _SIGNALIDS,
  '__module__' : 'network_api_pb2'
  # @@protoc_insertion_point(class_scope:base.SignalIds)
  })
_sym_db.RegisterMessage(SignalIds)

Signals = _reflection.GeneratedProtocolMessageType('Signals', (_message.Message,), {
  'DESCRIPTOR' : _SIGNALS,
  '__module__' : 'network_api_pb2'
  # @@protoc_insertion_point(class_scope:base.Signals)
  })
_sym_db.RegisterMessage(Signals)

PublisherConfig = _reflection.GeneratedProtocolMessageType('PublisherConfig', (_message.Message,), {
  'DESCRIPTOR' : _PUBLISHERCONFIG,
  '__module__' : 'network_api_pb2'
  # @@protoc_insertion_point(class_scope:base.PublisherConfig)
  })
_sym_db.RegisterMessage(PublisherConfig)

Signal = _reflection.GeneratedProtocolMessageType('Signal', (_message.Message,), {
  'DESCRIPTOR' : _SIGNAL,
  '__module__' : 'network_api_pb2'
  # @@protoc_insertion_point(class_scope:base.Signal)
  })
_sym_db.RegisterMessage(Signal)



_NETWORKSERVICE = _descriptor.ServiceDescriptor(
  name='NetworkService',
  full_name='base.NetworkService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=499,
  serialized_end=685,
  methods=[
  _descriptor.MethodDescriptor(
    name='SubscribeToSignals',
    full_name='base.NetworkService.SubscribeToSignals',
    index=0,
    containing_service=None,
    input_type=_SUBSCRIBERCONFIG,
    output_type=_SIGNALS,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='PublishSignals',
    full_name='base.NetworkService.PublishSignals',
    index=1,
    containing_service=None,
    input_type=_PUBLISHERCONFIG,
    output_type=common__pb2._EMPTY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ReadSignals',
    full_name='base.NetworkService.ReadSignals',
    index=2,
    containing_service=None,
    input_type=_SIGNALIDS,
    output_type=_SIGNALS,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_NETWORKSERVICE)

DESCRIPTOR.services_by_name['NetworkService'] = _NETWORKSERVICE

# @@protoc_insertion_point(module_scope)
