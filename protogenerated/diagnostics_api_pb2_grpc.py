/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import diagnostics_api_pb2 as diagnostics__api__pb2


class DiagnosticsServiceStub(object):
    """# 0x22 read data by identinifier (Service id)
    # 0x1f90 did for vin number (Data identifier)

    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SendDiagnosticsQuery = channel.unary_unary(
                '/base.DiagnosticsService/SendDiagnosticsQuery',
                request_serializer=diagnostics__api__pb2.DiagnosticsRequest.SerializeToString,
                response_deserializer=diagnostics__api__pb2.DiagnosticsResponse.FromString,
                )


class DiagnosticsServiceServicer(object):
    """# 0x22 read data by identinifier (Service id)
    # 0x1f90 did for vin number (Data identifier)

    """

    def SendDiagnosticsQuery(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DiagnosticsServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SendDiagnosticsQuery': grpc.unary_unary_rpc_method_handler(
                    servicer.SendDiagnosticsQuery,
                    request_deserializer=diagnostics__api__pb2.DiagnosticsRequest.FromString,
                    response_serializer=diagnostics__api__pb2.DiagnosticsResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'base.DiagnosticsService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class DiagnosticsService(object):
    """# 0x22 read data by identinifier (Service id)
    # 0x1f90 did for vin number (Data identifier)

    """

    @staticmethod
    def SendDiagnosticsQuery(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/base.DiagnosticsService/SendDiagnosticsQuery',
            diagnostics__api__pb2.DiagnosticsRequest.SerializeToString,
            diagnostics__api__pb2.DiagnosticsResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)
