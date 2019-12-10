# project:  ODTB2 testenvironment using SignalBroker
# author:   hweiler (Hans-Klaus Weiler)
# date:     2019-12-10
# version:  1.0


#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC route guide client."""


#from __future__ import print_function
from datetime import datetime
import time

import logging
import os
import sys

import threading
from threading import Thread

import random

import grpc
import string


#import network_api_pb2
#import network_api_pb2_grpc
#import functional_api_pb2
#import functional_api_pb2_grpc
#import system_api_pb2
#import system_api_pb2_grpc
#import common_pb2


#class for supporting activating and using security access
class Support_SecAcc:

# Global variables for use in SecAss

    _heartbeat = False

    
    def Sec_Acc_request_sid(self, payload_value):
        payload_value = bytes([len(payload_value)]) + payload_value
        #print ("new payload: ", payload_value)
        return(payload_value)


