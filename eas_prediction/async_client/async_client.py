#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.parse

from urllib3.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import ProtocolError

from .async_types.queueservice_pb2 import DataFrameListProto
from .async_types.queueservice_pb2 import DataFrameProto
from ..exception import PredictException
from ..predict_client import PredictClient

redisHeaderUid = "X-EAS-QueueService-Redis-Uid"
redisHeaderGid = "X-EAS-QueueService-Redis-Gid"


class DataFrame:
    def __init__(self, df):
        self.raw_data = df
        self.data = df.data
        self.index = df.index
        self.tags = df.tags
        self.message = df.message

    def set_data(self, data):
        self.data = data

    def set_index(self, index):
        self.index = index

    def set_message(self, message):
        self.message = message

    def set_tags(self, tags: dict):
        self.tags = tags

    def __str__(self):
        return self.raw_data.__str__()


class DataFrameList:
    def __init__(self, dataframe_list):
        self.raw_data = dataframe_list
        self.dataframe_list = []

        for i in range(len(dataframe_list.index)):
            df = dataframe_list.index[i]
            self.dataframe_list.append(DataFrame(df))

    def get_list(self):
        return self.dataframe_list

    def __getitem__(self, item):
        return self.dataframe_list[item]

    def __str__(self):
        return self.raw_data.__str__()


class DataFrameCodec:
    # TODO(lingcai.wl): support flatbuffer (maybe not necessary)
    def __init__(self, type="protobuffer"):
        self.type = type
        self.request_data = DataFrameProto()

    @classmethod
    def encode(cls, dataframe: DataFrame):
        request_data = DataFrameProto()
        request_data.data = dataframe.data
        request_data.index = dataframe.index
        request_data.tags = dataframe.tags
        request_data.message = dataframe.message
        return request_data.SerializeToString()

    @classmethod
    def decode(cls, raw_data):
        request_data = DataFrameProto()
        request_data.ParseFromString(raw_data)
        return DataFrame(request_data)

    def to_string(self):
        return self.request_data.SerializeToString()


class DataFrameListCodec:
    # TODO(lingcai.wl): support flatbuffer (maybe not necessary)
    def __init__(self, type="protobuffer"):
        self.type = type
        self.request_data = DataFrameListProto()

    @classmethod
    def encode(cls, dataframe_list: DataFrameList):
        request_data = DataFrameListProto()
        for i, df in enumerate(dataframe_list):
            request_data[i] = DataFrameCodec.encode(df)
        return request_data.SerializeToString()

    @classmethod
    def decode(cls, raw_data):
        request_data = DataFrameListProto()
        request_data.ParseFromString(raw_data)
        return DataFrameList(request_data)

    def to_string(self):
        return self.request_data.SerializeToString()


class AsyncClient(PredictClient):
    """
    Client for accessing prediction service by creating a fixed size connection pool
    to perform the request through established persistent connections.
    """

    def init(self, uid, gid):
        """
        init async client with uid and group id
        :param uid:
        :type uid:
        :param gid:
        :type gid:
        :return:
        :rtype:
        """
        self.logger.debug('Endpoint sync thread started')
        super(AsyncClient, self).init()

        self.uid = uid
        self.gid = gid

    def with_identity(self, headers):
        """
        add identity info into headers
        :param headers:
        :type headers:
        :return:
        :rtype:
        """
        headers[redisHeaderUid] = self.uid
        headers[redisHeaderGid] = self.gid
        return headers

    def build_url(self):
        """
        build the url of target queue service
        :return:
        :rtype:
        """
        domain = self.endpoint.get()
        return u'%s/api/predict/%s' % (domain, self.service_name)

    def do_request(self, url, method, headers, body=None):
        """
        common code for a http request
        :param url:
        :type url:
        :param method:
        :type method:
        :param headers:
        :type headers:
        :param body:
        :type body:
        :return:
        :rtype:
        """
        try:
            resp = self.connection_pool.request(method, url,
                                                headers=headers,
                                                body=body,
                                                timeout=self.timeout / 1000.0,
                                                retries=self.retry_count)

            if resp.status != 200:
                raise PredictException(resp.status, resp.data)
            return resp

        except (MaxRetryError, ProtocolError, HTTPError) as e:
            self.logger.debug('Request failed, err: %s', str(e))
            raise PredictException(resp.status, 'url: %s, error: %s' % (url, str(e)))

    def end(self, force: bool):
        """
        end the queue
        :param force:
        :type force:
        :return:
        :rtype:
        """
        url = self.build_url()
        query = {"_eos_": "true"}
        if force:
            query["_force_"] = "true"

        query_str = urllib.parse.urlencode(query)
        if query_str != '':
            url = url + '?' + query_str

        headers = {'Authorization': self.token}
        headers = self.with_identity(headers)
        self.do_request(url, "POST", headers)

    def truncate(self, index):
        url = self.build_url()
        query = {"_index_": str(index), "_trunc_": "true"}
        query_str = urllib.parse.urlencode(query)
        if query_str != '':
            url = url + '?' + query_str

        headers = {'Authorization': self.token}
        headers = self.with_identity(headers)
        return self.do_request(url, "DELETE", headers).data

    def put(self, data, tags: dict):
        """
        put data into a queue service
        :param data:
        :type data:
        :param tags:
        :type tags:
        :return:
        :rtype:
        """
        url = self.build_url()
        query_str = urllib.parse.urlencode(tags)
        if query_str != '':
            url = url + '?' + query_str

        headers = {'Authorization': self.token}
        headers = self.with_identity(headers)
        return self.do_request(url, "POST", headers, data).data

    def get(self, index=0, length=1, timeout=0, tags={}):
        """
        get the data in queue service
        :param index:
        :type index:
        :param length:
        :type length:
        :param timeout:
        :type timeout:
        :param tags:
        :type tags:
        :return:
        :rtype:
        """
        url = self.build_url()
        query = {'_index_': str(index), '_length_': str(length),
                 '_timeout_': str(timeout),
                 # '_raw_': 'false',
                 # '_auto_delete_': 'false'
                 }
        query.update(tags)
        query_str = urllib.parse.urlencode(query)
        if query_str != '':
            url = url + '?' + query_str

        headers = {'Authorization': self.token}
        headers = self.with_identity(headers)
        headers['Accept'] = 'application/vnd.google.protobuf'  # default

        raw_resp = self.do_request(url, "GET", headers)
        dfl = DataFrameListCodec.decode(raw_resp.data)
        return dfl

    def watch_reader(self, resp):
        """
        read data from a watch request connection and decode into dataframe

        :param resp:
        :type resp:
        :return:
        :rtype:
        """
        read_length = 4
        read_raw = False
        # TODO(lingcai.wl): Is there any better solution than this?
        while not resp.isclosed() and not self.stop:
            # TODO(lingcai.wl): how to close the conn
            chunk = resp.read(read_length)
            if not read_raw:
                read_length = int.from_bytes(chunk, 'big')
                read_raw = True
            else:
                df = DataFrameCodec.decode(chunk)
                yield df
                read_raw = False
                read_length = 4

        resp.release_conn()

    def watch(self, index: int, window: int, index_only=False, auto_commit=False):
        """
        watch function, not implemented completely

        :param index:
        :type index:
        :param window:
        :type window:
        :param index_only:
        :type index_only:
        :param auto_commit:
        :type auto_commit:
        :return:
        :rtype:
        """

        query = {"_watch_": "true", "_index_": index, "_window_": str(window)}
        if index_only:
            query['_index_only_'] = 'true'
        if auto_commit:
            query['_auto_commit_'] = 'true'

        url = self.build_url()
        query_str = urllib.parse.urlencode(query)
        if query_str != '':
            url = url + '?' + query_str

        headers = {'Authorization': self.token}
        headers = self.with_identity(headers)
        headers['Accept'] = 'application/vnd.google.protobuf'  # default

        try:
            resp = self.connection_pool.request("GET", url,
                                                headers=headers,
                                                retries=0,
                                                preload_content=False)

            if resp.status != 200:
                raise PredictException(resp.status, resp.data)
            return self.watch_reader(resp)

        except (MaxRetryError, ProtocolError, HTTPError) as e:
            self.logger.debug('Request failed, err: %s', str(e))
            raise PredictException(resp.status, 'url: %s, error: %s' % (url, str(e)))

    def deal_with_indexes(self, indexes, method):
        """
        common code for indexes related request
        :param indexes:
        :type indexes:
        :param method:
        :type method:
        :return:
        :rtype:
        """
        url = self.build_url()
        query = {"_indexes_": ",".join([str(ind) for ind in indexes])}
        query_str = urllib.parse.urlencode(query)
        if query_str != '':
            url = url + '?' + query_str
        headers = {'Authorization': self.token}
        headers = self.with_identity(headers)
        return self.do_request(url, method, headers).data

    def commit(self, indexes):
        """
        commit indexes
        :param indexes:
        :type indexes:
        :return:
        :rtype:
        """
        return self.deal_with_indexes(indexes, "PUT")

    def delete(self, indexes):
        """
        delete indexes
        :param indexes:
        :type indexes:
        :return:
        :rtype:
        """
        return self.deal_with_indexes(indexes, "DELETE").data
