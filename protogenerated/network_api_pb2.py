# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: network_api.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import protogenerated.common_pb2 as common__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11network_api.proto\x12\x04\x62\x61se\x1a\x0c\x63ommon.proto\"h\n\x10SubscriberConfig\x12 \n\x08\x63lientId\x18\x01 \x01(\x0b\x32\x0e.base.ClientId\x12 \n\x07signals\x18\x02 \x01(\x0b\x32\x0f.base.SignalIds\x12\x10\n\x08onChange\x18\x03 \x01(\x08\"-\n\tSignalIds\x12 \n\x08signalId\x18\x01 \x03(\x0b\x32\x0e.base.SignalId\"\'\n\x07Signals\x12\x1c\n\x06signal\x18\x01 \x03(\x0b\x32\x0c.base.Signal\"f\n\x0fPublisherConfig\x12\x1e\n\x07signals\x18\x01 \x01(\x0b\x32\r.base.Signals\x12 \n\x08\x63lientId\x18\x02 \x01(\x0b\x32\x0e.base.ClientId\x12\x11\n\tfrequency\x18\x03 \x01(\x05\"\x9c\x01\n\x06Signal\x12\x1a\n\x02id\x18\x01 \x01(\x0b\x32\x0e.base.SignalId\x12\x11\n\x07integer\x18\x02 \x01(\x03H\x00\x12\x10\n\x06\x64ouble\x18\x03 \x01(\x01H\x00\x12\x15\n\x0b\x61rbitration\x18\x04 \x01(\x08H\x00\x12\x0f\n\x05\x65mpty\x18\x06 \x01(\x08H\x00\x12\x0b\n\x03raw\x18\x05 \x01(\x0c\x12\x11\n\ttimestamp\x18\x07 \x01(\x03\x42\t\n\x07payload2\xba\x01\n\x0eNetworkService\x12?\n\x12SubscribeToSignals\x12\x16.base.SubscriberConfig\x1a\r.base.Signals\"\x00\x30\x01\x12\x36\n\x0ePublishSignals\x12\x15.base.PublisherConfig\x1a\x0b.base.Empty\"\x00\x12/\n\x0bReadSignals\x12\x0f.base.SignalIds\x1a\r.base.Signals\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'network_api_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SUBSCRIBERCONFIG._serialized_start=41
  _SUBSCRIBERCONFIG._serialized_end=145
  _SIGNALIDS._serialized_start=147
  _SIGNALIDS._serialized_end=192
  _SIGNALS._serialized_start=194
  _SIGNALS._serialized_end=233
  _PUBLISHERCONFIG._serialized_start=235
  _PUBLISHERCONFIG._serialized_end=337
  _SIGNAL._serialized_start=340
  _SIGNAL._serialized_end=496
  _NETWORKSERVICE._serialized_start=499
  _NETWORKSERVICE._serialized_end=685
# @@protoc_insertion_point(module_scope)
