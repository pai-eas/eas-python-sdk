#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
from .onnx_request import OnnxData

TENSOR_TYPE_TO_NP_TYPE = {
    int(OnnxData.TensorProto.FLOAT): np.dtype('float32'),
    int(OnnxData.TensorProto.UINT8): np.dtype('uint8'),
    int(OnnxData.TensorProto.INT8): np.dtype('int8'),
    int(OnnxData.TensorProto.UINT16): np.dtype('uint16'),
    int(OnnxData.TensorProto.INT16): np.dtype('int16'),
    int(OnnxData.TensorProto.INT32): np.dtype('int32'),
    int(OnnxData.TensorProto.INT64): np.dtype('int64'),
    int(OnnxData.TensorProto.DOUBLE): np.dtype('float64'),
    int(OnnxData.TensorProto.UINT32): np.dtype('uint32'),
    int(OnnxData.TensorProto.UINT64): np.dtype('uint64')
}

NP_TYPE_TO_TENSOR_TYPE = {v: k for k, v in TENSOR_TYPE_TO_NP_TYPE.items()}

def to_array(tensor):  # type: (OnnxData.TensorProto) -> np.ndarray[Any]
    """Converts a tensor def object to a numpy array.
    Inputs:
        tensor: a OnnxData.TensorProto object.
    Returns:
        arr: the converted array.
    """
    if tensor.data_type == OnnxData.TensorProto.UNDEFINED:
        raise TypeError("The element type in the input tensor is not defined.")

    tensor_dtype = tensor.data_type
    np_dtype = TENSOR_TYPE_TO_NP_TYPE[tensor_dtype]
    dims = tensor.dims

    if sys.byteorder == 'big':
        # Convert endian from little to big
        convert_endian(tensor)
    # Raw_bytes support: using frombuffer.
    return np.frombuffer(
        tensor.raw_data,
        dtype=np_dtype).reshape(dims)


def from_array(arr, name):  # type: (np.ndarray[Any], Text) -> OnnxData.TensorProto
    """Converts a numpy array to a tensor def.
    Inputs:
        arr: a numpy array.
        name: (optional) the name of the tensor.
    Returns:
        tensor_def: the converted tensor def.
    """
    tensor = OnnxData.TensorProto()
    tensor.dims.extend(arr.shape)
    tensor.name = name

    # For numerical types, directly use numpy raw bytes.
    try:
        dtype = NP_TYPE_TO_TENSOR_TYPE[arr.dtype]
    except KeyError:
        raise RuntimeError(
            "Numpy data type not understood yet: {}".format(str(arr.dtype)))
    tensor.data_type = dtype
    tensor.raw_data = arr.tobytes()  # note: tobytes() is only after 1.9.
    if sys.byteorder == 'big':
        # Convert endian from big to little
        convert_endian(tensor)
    return tensor


def convert_endian(tensor):  # type: (OnnxData.TensorProto) -> None
    """
    call to convert endianess of raw data in tensor.
    Inputs:
        tensor: OnnxData.TensorProto object to be converted.
    """
    tensor_dtype = tensor.data_type
    np_dtype = TENSOR_TYPE_TO_NP_TYPE[tensor_dtype]
    tensor.raw_data = np.frombuffer(tensor.raw_data, dtype=np_dtype).byteswap().tobytes()
