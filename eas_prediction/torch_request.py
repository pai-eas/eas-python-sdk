#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .request import Request
from .request import Response
from . import pytorch_predict_pb2 as pt_pb
import snappy

class TorchRequest(Request):
    """
    Request for pytorch services whose input data is in format of protobuf,
    privide methods to generate the required protobuf object, and serialze it to string
    """
    DT_FLOAT = pt_pb.DT_FLOAT
    DT_DOUBLE = pt_pb.DT_DOUBLE
    DT_UINT8 = pt_pb.DT_UINT8
    DT_INT8 = pt_pb.DT_INT8
    DT_INT16 = pt_pb.DT_INT16
    DT_INT32 = pt_pb.DT_INT32
    DT_INT64 = pt_pb.DT_INT64

    def __init__(self,flag=False):
        self.request_data = pt_pb.PredictRequest()
        self.flag=flag
        # self.index = index

    def __str__(self):
        return self.request_data
    
    def set_debug_level(self, dbg_lvl=0):
        self.request_data.debug_level = dbg_lvl

    def add_feed(self, index, shape, content_type, content):
        """
        Add input data for the request, a pytorch model may have many inputs with different
        data types, this methods set data for one of the input with the specified 'index'
        :param index: name of the input to be set
        :param shape: shape of the input tensor in format of array, such as [1, 3, 224, 224]
        :param content_type: type of the input tensor, can be one of the predefined data type, such as TorchRequest.DT_FLOAT
        :param content: data content of the input tensor, which is expanded to one-dimension array, such as [1,2,3,4,5]
        """
        # self.request_data.index = self.index
        while len(self.request_data.inputs) < index + 1:
            self.request_data.inputs.add()
        self.request_data.inputs[index].dtype = content_type
        self.request_data.inputs[index].array_shape.dim.extend(shape)
        if content_type == pt_pb.DT_FLOAT:
            self.request_data.inputs[index].float_val.extend(content)
        elif content_type == pt_pb.DT_DOUBLE:
            self.request_data.inputs[index].double_val.extend(content)
        elif content_type == pt_pb.DT_INT8 or content_type == pt_pb.DT_INT16 or \
                content_type == pt_pb.DT_INT32 or content_type == pt_pb.DT_UINT8:
            self.request_data.inputs[index].int_val.extend(content)
        elif content_type == pt_pb.DT_INT64:
            self.request_data.inputs[index].int64_val.extend(content)
    
    def add_feed_map(self, index, shape, content_type, content):
        """
        Add input data for the request, a pytorch model may have many inputs with different
        data types, this methods set data for one of the input with the specified 'index'
        :param index: name of the input to be set
        :param shape: shape of the input tensor in format of array, such as [1, 3, 224, 224]
        :param content_type: type of the input tensor, can be one of the predefined data type, such as TorchRequest.DT_FLOAT
        :param content: data content of the input tensor, which is expanded to one-dimension array, such as [1,2,3,4,5]
        """
        
        self.request_data.map_inputs[index].dtype = content_type
        self.request_data.map_inputs[index].array_shape.dim.extend(shape)
        if content_type == pt_pb.DT_FLOAT:
            self.request_data.map_inputs[index].float_val.extend(content)
        elif content_type == pt_pb.DT_DOUBLE:
            self.request_data.map_inputs[index].double_val.extend(content)
        elif content_type == pt_pb.DT_INT8 or content_type == pt_pb.DT_INT16 or \
                content_type == pt_pb.DT_INT32 or content_type == pt_pb.DT_UINT8:
            self.request_data.map_inputs[index].int_val.extend(content)
        elif content_type == pt_pb.DT_INT64:
            self.request_data.map_inputs[index].int64_val.extend(content)

    def add_fetch(self, output_index):
        """
        Add output index for the request to get, if not specified, then all the known outputs are fetched
        :param index: index of the output node to fetch
        """
        self.request_data.output_filter.append(output_index)

    def to_string(self):
        """
        Serialize the request to string for transmission
        :return: the request data in format of string
        """
        data = self.request_data.SerializeToString()
        if self.flag:
            data = snappy.compress(data)
        return data

    def parse_response(self, response_data):
        """
        Parse the given response data in string format to the related TorchResponse object
        :param response_data: the service response data in string format
        :return: the TorchResponse object related the request
        """
        return TorchResponse(response_data)


class TorchResponse(Response):
    """
    Deserialize the response data to a structured object for users to read
    """

    def __init__(self, response_data=None):
        self.response = pt_pb.PredictResponse()
        self.response.ParseFromString(response_data)

    def __str__(self):
        return str(self.response)
    def to_string(self):
        return str(self.response)
    def get_tensor_shape(self, output_index):
        """
        Get the shape of a specified output tensor
        :param output_index: name of the output tensor
        :return: the shape in format of list
        """
        return list(self.response.outputs[output_index].array_shape.dim)

    def get_values(self, output_index):
        """
        Get the value of a specified output tensor
        :param output_index: name of the output tensor
        :return: the content of the output tensor
        """
        output = self.response.outputs[output_index]
        if output.dtype == TorchRequest.DT_FLOAT:
            return output.float_val
        elif output.dtype == TorchRequest.DT_INT8 or output.dtype == TorchRequest.DT_INT16 or \
                output.dtype == TorchRequest.DT_INT32 or output.dtype == TorchRequest.DT_UINT8:
            return output.int_val
        elif output.dtype == TorchRequest.DT_INT64:
            return output.int64_val
        elif output.dtype == TorchRequest.DT_DOUBLE:
            return output.double_val

    def get_tensor_shape_map(self, output_index):
        """
        Get the shape of a specified output tensor
        :param output_index: name of the output tensor
        :return: the shape in format of list
        """
        return list(self.response.map_outputs[output_index].array_shape.dim)

    def get_values_map(self, output_index):
        """
        Get the value of a specified output tensor
        :param output_index: name of the output tensor
        :return: the content of the output tensor
        """
        output = self.response.map_outputs[output_index]
        if output.dtype == TorchRequest.DT_FLOAT:
            return output.float_val
        elif output.dtype == TorchRequest.DT_INT8 or output.dtype == TorchRequest.DT_INT16 or \
                output.dtype == TorchRequest.DT_INT32 or output.dtype == TorchRequest.DT_UINT8:
            return output.int_val
        elif output.dtype == TorchRequest.DT_INT64:
            return output.int64_val
        elif output.dtype == TorchRequest.DT_DOUBLE:
            return output.double_val