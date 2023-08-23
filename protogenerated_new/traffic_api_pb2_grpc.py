# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import protogenerated.traffic_api_pb2 as traffic__api__pb2


class TrafficServiceStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.PlayTraffic = channel.unary_unary(
        '/base.TrafficService/PlayTraffic',
        request_serializer=traffic__api__pb2.PlaybackInfos.SerializeToString,
        response_deserializer=traffic__api__pb2.PlaybackInfos.FromString,
        )


class TrafficServiceServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def PlayTraffic(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_TrafficServiceServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'PlayTraffic': grpc.unary_unary_rpc_method_handler(
          servicer.PlayTraffic,
          request_deserializer=traffic__api__pb2.PlaybackInfos.FromString,
          response_serializer=traffic__api__pb2.PlaybackInfos.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'base.TrafficService', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
