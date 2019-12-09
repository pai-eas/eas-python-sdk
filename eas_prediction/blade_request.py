#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .request import Request
from .request import Response
from . import blade_pb2
from functools import reduce 
import operator


class BladeRequest(Request):
    """
    Request for tensorflow services whose input data is in format of protobuf,
    privide methods to generate the required protobuf object, and serialze it to string
    """
    DT_FLOAT = blade_pb2.DT_FLOAT
    DT_INT32 = blade_pb2.DT_INT32
    DT_INT64 = blade_pb2.DT_INT64
    DT_STRING = blade_pb2.DT_STRING

    def __init__(self, signature_name=None):
        self.request_data = blade_pb2.Request()
        self.set_signature_name(signature_name)

    def __str__(self):
        return self.request_data

    def set_signature_name(self, signature_name):
        """
        Set the signature name of the model
        :param signature_name: signature name of the tensorflow model
        """
        self.tf_signature_name = signature_name
        self.request_data.tf_signature_name = self.tf_signature_name

    def volume(self, shape):
        return reduce(operator.mul, shape)

    def add_feed(self, input_name, batchsize, shape, content_type, content):
        """
        Add input data for the request, a tensorflow model may have many inputs with different
        data types, this methods set data for one of the input with the specified name 'input_name'
        :param input_name: name of the input to be set
        :param batchsize: batch size of the input tensor
        :param shape: shape of the input tensor in format of array, such as [1,784]
        :param content_type: type of the input tensor (predefined data type, such as BladeRequest.DT_FLOAT)
        :param content: data content of the input tensor, the content could be a single value (e.g. 3.14), or a expanded one-dimension array (e.g. [1,2,3,4,5])
        """
        if (not input_name):
            raise AssertionError('"input name" can not be emtpy')
        if (not isinstance(batchsize, int) or batchsize <= 0):
            raise AssertionError('Invalid batchsize value: {}'.format(batchsize))
        if (not isinstance(shape, list)):
            raise AssertionError('Invalid type for "shape": {}'.format(type(shape)))
        arr = self.request_data.inputs.add()
        arr.shape.dim.extend(shape)
        arr.name_in_dl_model = input_name
        arr.blade_blob_name = input_name # HERE: 'blade blob name' is identical to 'name in DL model'.
        arr.batchsize = batchsize
        if (content_type == blade_pb2.DT_FLOAT):
            if (isinstance(content, float)):
                if (int(self.volume(shape)) == 1):
                    arr.float_val.append(content)
            elif (isinstance(content, list)):
                if (int(self.volume(shape)) == int(len(content))):
                    arr.float_val.extend(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), len(content)))
            else:
                raise AssertionError('Expect float or list of float type')
        elif (content_type == blade_pb2.DT_INT32):
            if (isinstance(content, int)):
                if (int(self.volume(shape)) == 1):
                    arr.int_val.append(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), 1))
            elif (isinstance(content, list)):
                if (int(self.volume(shape)) == int(len(content))):
                    arr.int_val.extend(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), len(content)))
            else:
                raise AssertionError('Expect int32 or list of int32 type')
        elif (content_type == blade_pb2.DT_INT64):
            if (isinstance(content, int)):
                if (int(self.volume(shape)) == 1):
                    arr.in64_val.append(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), 1))
            elif (isinstance(content, list)):
                if (int(self.volume(shape)) == int(len(content))):
                    arr.int64_val.extend(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), len(content)))
            else:
                raise AssertionError('Expect int64 or list of int64 type')
        elif (content_type == blade_pb2.DT_STRING):
            if (isinstance(content, str)):
                if (int(self.volume(shape)) == 1):
                    arr.string_val.append(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), 1))
            elif (isinstance(content, list)):
                if (int(self.volume(shape)) == int(len(content))):
                    arr.string_val.extend(content)
                else:
                    raise AssertionError('Shape volume {} mis-match content size {}'.format( \
                            self.volume(shape), len(content)))
            else:
                raise AssertionError('Expect str or list of str type')
        else:
            raise AssertionError('Unknown data_type: "{}"'.format(data_type))
        return

    def add_fetch(self, output_name, output_type):
        """
        Add output node name for the request to get, if not specified, then all the known outputs are fetched,
        but for frozen models, the output name must be specified, or else the service would throw exception like:
        'Must specify at least one target to fetch or execute.'
        :param output_name: name of the output node to fetch
        :param output_type: type of the output tensor (predefined data type, e.g BladeRequest.DT_FLOAT)
        """
        if (not output_name):
            raise AssertionError('"input name" can not be emtpy')
        if (output_type not in blade_pb2.DataType.values()):
            raise AssertionError('Unknown data_type: "{}"'.format(data_type))
        out_info = self.request_data.output_info.add()
        out_info.blade_blob_name = output_name
        out_info.name_in_dl_model = output_name
        out_info.data_type = output_type
        return

    def to_string(self):
        """
        Serialize the request to string for transmission
        :return: the request data in format of string
        """
        return self.request_data.SerializeToString()

    def parse_response(self, response_data):
        """
        Parse the given response data in string format to the related BladeResponse object
        :param response_data: the service response data in string format
        :return: the BladeResponse object related the request
        """
        return BladeResponse(response_data)


class BladeResponse(Response):
    """
    Deserialize the response data to a structured object for users to read
    """

    def __init__(self, response_data=None):
        self.response = blade_pb2.Response()
        self.response.ParseFromString(response_data)

    def __str__(self):
        return str(self.response)

    def get_tensor_shape(self, output_name):
        """
        Get the shape of a specified output tensor
        :param output_name: name of the output tensor
        :return: the shape in format of list
        """
        for out in self.response.outputs:
            if (str(out.name_in_dl_model).strip() == str(output_name).strip()):
                return list(out.shape.dim)
        raise AssertionError('Unknown output name: "{}"'.format(output_name))

    def get_values(self, output_name, output_type):
        """
        Get the value of a specified output tensor
        :param output_name: name of the output tensor
        :param output_type: type of the output tensor (predefined data type, e.g BladeRequest.DT_FLOAT)
        :return: the content of the output tensor
        """
        if (output_type not in blade_pb2.DataType.values()):
            raise AssertionError('Unknown data_type: "{}"'.format(data_type))
        for out in self.response.outputs:
            if (str(out.name_in_dl_model).strip() == str(output_name).strip()):
                if (output_type == BladeRequest.DT_FLOAT):
                    return out.float_val
                elif (output_type == BladeRequest.DT_INT32):
                    return out.int_val
                elif (output_type == BladeRequest.DT_INT64):
                    return out.int64_val
                elif (output_type == BladeRequest.DT_STRING):
                    return out.string_val
        raise AssertionError('Unknown output name: "{}"'.format(output_name))
