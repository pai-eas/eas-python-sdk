#!/usr/bin/env python
# -*- coding: utf-8 -*-

from eas_prediction.request import Request
from eas_prediction.torchrec_predict_pb2 import PBRequest, PBResponse,PBFeature

class TorchRecRequest(Request):
    """
    Request for tensorflow services whose input data is in format of protobuf,
    privide methods to generate the required protobuf object, and serialze it to string
    """

    def __init__(self):
        self.request_data = PBRequest()


    def __str__(self):
        return self.request_data


    def add_feed(self, data, dbg_lvl=0):
        self.request_data.ParseFromString(data)
        self.request_data.debug_level = dbg_lvl


    def set_debug_level(self, dbg_lvl=0):
        self.request_data.debug_level = dbg_lvl
        
    def add_feat(self, value, dtype):
        dtype=dtype.upper()
        feat = PBFeature()
        if value is None or ((isinstance(value, dict) or isinstance(value,list)) and len(value)==0):
            feat.string_feature = ""
        elif dtype == "STRING":
            feat.string_feature = value
        elif dtype == "FLOAT":
            feat.float_feature = value
        elif dtype == "DOUBLE":
            feat.double_feature = value
        elif dtype in ("BIGINT","INT64"):
            feat.long_feature = value
        elif dtype == "INT":
            feat.int_feature = value
        elif dtype in ("LIST<FLOAT>","LIST<STRING>","LIST<DOUBLE>","LIST<INT>","LIST<INT64>","LIST<BIGINT>",
                       "ARRAY<FLOAT>","ARRAY<STRING>","ARRAY<DOUBLE>","ARRAY<INT>","ARRAY<INT64>","ARRAY<BIGINT>"):
            if not isinstance(value, list):
                raise ValueError("Expected value to be a list for LIST<FLOAT> dtype")
            if dtype in ("LIST<STRING>","ARRAY<STRING>"):
                list_v = feat.string_list
            elif dtype in ("LIST<FLOAT>","ARRAY<FLOAT>"):
                list_v = feat.float_list
            elif dtype in ("LIST<DOUBLE>","ARRAY<DOUBLE>"):
                list_v = feat.double_list
            elif dtype in ("LIST<BIGINT>","LIST<INT64>","ARRAY<BIGINT>","ARRAY<INT64>"):
                list_v = feat.long_list
            elif dtype in ("LIST<INT>","ARRAY<INT>"):
                list_v = feat.int_list
            for v in value:
                list_v.features.append(v)
        elif dtype in ("MAP<INT,INT>","MAP<INT,INT64>","MAP<INT,BIGINT>","MAP<INT,STRING>","MAP<INT,FLOAT>","MAP<INT,DOUBLE>" ,
                       "MAP<INT64,INT>","MAP<INT64,INT64>","MAP<INT64,BIGINT>","MAP<INT64,STRING>","MAP<INT64,FLOAT>","MAP<INT64,DOUBLE>" ,
                       "MAP<BIGINT,INT>","MAP<BIGINT,INT64>","MAP<BIGINT,BIGINT>","MAP<BIGINT,STRING>","MAP<BIGINT,FLOAT>","MAP<BIGINT,DOUBLE>"
        ):
            if not isinstance(value, dict):
                raise ValueError("Expected value to be a dict for MAP<INT,INT> dtype")
            if dtype == "MAP<INT,INT>":
                map_v = feat.int_int_map.map_field
            elif dtype in ("MAP<INT,INT64>","MAP<INT,BIGINT>"):
                map_v = feat.int_long_map.map_field
            elif dtype == "MAP<INT,STRING>":
                map_v = feat.int_string_map.map_field
            elif dtype == "MAP<INT,FLOAT>":
                map_v = feat.int_float_map.map_field
            elif dtype == "MAP<INT,DOUBLE>":
                map_v = feat.int_double_map.map_field
            
            elif dtype in ("MAP<INT64,INT>","MAP<BIGINT,INT>"):
                map_v = feat.long_int_map.map_field
            elif dtype in ("MAP<INT64,INT64>","MAP<BIGINT,BIGINT>","MAP<INT64,BIGINT>","MAP<BIGINT,INT64>"):
                map_v = feat.long_long_map.map_field
            elif dtype in ("MAP<INT64,STRING>","MAP<BIGINT,STRING>"):
                map_v = feat.long_string_map.map_field
            elif dtype in ("MAP<INT64,FLOAT>","MAP<BIGINT,FLOAT>"):
                map_v = feat.long_float_map.map_field
            elif dtype in ("MAP<INT64,DOUBLE>","MAP<BIGINT,DOUBLE>"):
                map_v = feat.long_double_map.map_field
            
            for k, v in value.items():
                # dict in json,all key is str,must convert to int
                map_v[int(k)]=v
        elif dtype in ("MAP<STRING,INT>","MAP<STRING,INT64>","MAP<STRING,BIGINT>","MAP<STRING,STRING>","MAP<STRING,FLOAT>","MAP<STRING,DOUBLE>" 
        ):
            if not isinstance(value, dict):
                raise ValueError("Expected value to be a dict for MAP<INT,INT> dtype")
            if dtype == "MAP<STRING,INT>":
                map_v = feat.string_int_map.map_field
            elif dtype in ("MAP<STRING,INT64>","MAP<STRING,BIGINT>"):
                map_v = feat.string_long_map.map_field
            elif dtype == "MAP<STRING,STRING>":
                map_v = feat.string_string_map.map_field
            elif dtype == "MAP<STRING,FLOAT>":
                map_v = feat.string_float_map.map_field
            elif dtype == "MAP<STRING,DOUBLE>":
                map_v = feat.string_double_map.map_field
            for k, v in value.items():
                map_v[k]=v
        elif dtype in ("ARRAY<ARRAY<FLOAT>>","LIST<LIST<FLOAT>>"):
            if not isinstance(value, list) or not all(isinstance(sublist, list) for sublist in value):
                raise ValueError("Expected value to be a list of lists for ARRAY<ARRAY<FLOAT>> dtype")
            float_lists = feat.float_lists 
            for sublist in value:
                float_list = float_lists.lists.add()  
                float_list.features.extend(sublist)  
        else:
            raise ValueError("unsupport dtype:",dtype)
        return feat
    
    def add_user_fea(self, k, value, dtype):
        feat=self.add_feat(value,dtype)
        self.request_data.user_features[k].CopyFrom(feat)

    def add_context_fea(self,k,value,dtype):
        feat=self.add_feat(value,dtype)
        self.request_data.context_features[k].features.add().CopyFrom(feat)
    
    def add_item_fea(self,k,value,dtype):
        feat=self.add_feat(value,dtype)
        self.request_data.item_features[k].features.add().CopyFrom(feat)
               
    def add_item_id(self, k):
        self.request_data.item_ids.append(str(k))
    
    def set_faiss_neigh_num(self, k):
        self.request_data.faiss_neigh_num = k

    def to_string(self):
        """
        Serialize the request to string for transmission
        :return: the request data in format of string
        """
        return self.request_data.SerializeToString()

    def parse_response(self, response_data):
        """
        Parse the given response data in string format to the related TFResponse object
        :param response_data: the service response data in string format
        :return: the TFResponse object related the request
        """
        self.response = PBResponse()
        self.response.ParseFromString(response_data)
        return self.response

