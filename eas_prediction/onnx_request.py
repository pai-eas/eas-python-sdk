#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .request import Request
from .request import Response
from . import onnx_processor_data_pb2 as OnnxData


class OnnxRequest(Request):
    """
    Request for hie onnx processor services whose input data is in format of protobuf,
    privide methods to generate the required protobuf object, and serialze it to string
    """

    def __init__(self):
        self.request_data = OnnxData.DataProto()
        self.name_index_map = {}

    def __str__(self):
        return str(self.request_data)

    def add_tensor(self, tensor): # type: (OnnxData.TensorProto) -> int
        """
        Add input tensor for the request
        :param tensor: a OnnxData.TensorProto object
        :return: this tensor's index in request
        """
        name = tensor.name
        if name in self.name_index_map:
            index = self.name_index_map[name]
        else:
            index = len(self.request_data.tensors)
            self.name_index_map[name] = index
            self.request_data.tensors.add()
        self.request_data.tensors[index].CopyFrom(tensor)
        return index

    def to_string(self):
        """
        Serialize the request to string for transmission
        :return: the request data in format of string
        """
        return self.request_data.SerializeToString()

    def parse_response(self, response_data):
        """
        Parse the given response data in string format to the related OnnxResponse object
        :param response_data: the service response data in string format
        :return: the OnnxResponse object related the request
        """
        return OnnxResponse(response_data)


class OnnxResponse(Response):
    """
    Deserialize the response data to a structured object for users to read
    """

    def __init__(self, response_data=None):
        self.response = OnnxData.DataProto()
        self.response.ParseFromString(response_data)

    def __str__(self):
        return str(self.response)

    def get_size(self):
        """
        Get the number of tensors of a response
        :return: the tensors size in format of int
        """
        return len(self.response.tensors)

    def get_name(self, output_index): # type: (int) -> OnnxData.TensorProto
        """
        Get the name of a specified output tensor
        :param output_index: name of the output tensor
        :return: the name in format of string
        """
        return self.response.tensors[output_index].name

    def get_tensor(self, output_index): # type: (int) -> OnnxData.TensorProto
        """
        Get the shape of a specified output tensor
        :param output_index: name of the output tensor
        :return: the shape in format of list
        """
        return self.response.tensors[output_index]
