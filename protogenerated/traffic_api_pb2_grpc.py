# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import protogenerated.traffic_api_pb2 as traffic__api__pb2


class TrafficServiceStub(object):
    """Missing associated documentation comment in .proto file."""

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
    """Missing associated documentation comment in .proto file."""

    def PlayTraffic(self, request, context):
        """Missing associated documentation comment in .proto file."""
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


 # This class is part of an EXPERIMENTAL API.
class TrafficService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def PlayTraffic(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/base.TrafficService/PlayTraffic',
            traffic__api__pb2.PlaybackInfos.SerializeToString,
            traffic__api__pb2.PlaybackInfos.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
