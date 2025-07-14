#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.parse
import uuid
import json
import logging
import threading
import websocket
import time

from urllib3.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import ProtocolError

from .queue_types.queueservice_pb2 import DataFrameListProto
from .queue_types.queueservice_pb2 import DataFrameProto
from .exception import PredictException
from .predict_client import PredictClient

HeaderRedisUid = "X-EAS-QueueService-Redis-Uid"
HeaderRedisGid = "X-EAS-QueueService-Redis-Gid"
HeaderRequestId = "X-Eas-Queueservice-Request-Id"
HeaderAuthorization = "Authorization"


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


class Watcher:
    def __init__(self, queue, url, headers, logger):
        self.queue = queue
        self.event = threading.Event()
        self.url = url
        self.headers = headers
        self.logger = logger
        self.closed = False

    def _ping(self):
        while not self.event.wait(2):
            with self.queue.watch_lock:
                if not self.closed:
                    try:
                        self.queue.watch_sock.ping("ping")
                    except Exception as ex:
                        self.logger and self.logger.warning(
                            "send_ping error ({})".format(ex))
                else:
                    self.logger and self.logger.debug(
                        "send_ping routine exited")
                    break

    def run(self):
        with self.queue.watch_lock:
            if self.queue.watch_sock is not None:
                raise PredictException(
                    400, 'Another watcher is already running')
            self.queue.watch_sock = websocket.create_connection(
                self.url, header=self.headers)

        thread = threading.Thread(target=self._ping)
        thread.daemon = True
        thread.start()

        while True:
            try:
                df = self.queue.watch_sock.recv()
                yield DataFrameCodec.decode(df)
            except Exception as ex:
                self.logger and self.logger.warning(
                    "connection closed (%s), try to reconnect" % str(ex))
                while True:
                    try:
                        self.queue.watch_sock = websocket.create_connection(
                            self.url, header=self.headers)
                        break
                    except Exception as e:
                        time.sleep(1)
                        self.logger and self.logger.warning(
                            "reconnect failed (%s), retrying..." % str(e))

    def close(self):
        with self.queue.watch_lock:
            self.event.set()
            self.queue.watch_sock.abort()
            self.queue.watch_sock = None
            self.closed = True


class QueueClient(PredictClient):
    """
    Client for accessing prediction service by creating a fixed size connection pool
    to perform the request through established persistent connections.
    """

    def init(self, uid=None, gid='eas', custom_url='', path_suffix=''):
        """
        init async client with uid and group id
        """
        super(QueueClient, self).init()

        if uid is None:
            self.uid = str(uuid.uuid4())
        else:
            self.uid = uid
        self.gid = gid
        self.watch_sock = None
        self.watch_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.custom_url = custom_url
        self.path_suffix = path_suffix

    def set_logger(self, logger=None):
        self.logger = logger

    def _with_identity(self):
        """
        add identity info into headers
        """
        headers = dict(self.headers)
        if len(self.content_type) > 0:
            headers.update({'Content-Type': self.content_type})

        headers[HeaderAuthorization] = self.token
        headers[HeaderRedisUid] = self.uid
        headers[HeaderRedisGid] = self.gid
        return headers

    def _check_index(self, index):
        if isinstance(index, (int, float)) and index > 0:
            return True
        elif isinstance(index, str) and index.isnumeric() and int(index) > 0:
            return True
        else:
            return False

    def _build_url(self, query, websocket=False):
        """
        build the url of target queue service
        """
        domain = self.endpoint.get()
        if self.custom_url == '':
            if self.path_suffix == '':
                url = '%s/api/predict/%s' % (domain, self.service_name)
            else:
                url = '%s/api/predict/%s/%s' % (domain, self.service_name, self.path_suffix)
        else:
            url = self.custom_url

        if websocket:
            url = url.replace('http://', 'ws://').replace('https://', 'wss://')
            if (not url.startswith('ws://')) and (not url.startswith('wss://')):
                url = 'ws://' + url

        query_str = urllib.parse.urlencode(query)
        if len(query_str) != 0:
            url += '?' + query_str
        return url

    def _process_indexes(self, indexes, method):
        """
        common code for indexes related request
        """
        query = {'_indexes_': ','.join([str(ind) for ind in indexes])}
        url = self._build_url(query)
        headers = self._with_identity()
        return self._do_request(url, method, headers).data

    def _do_request(self, url, method, headers, body=None):
        """
        common code for a http request
        """
        try:
            for i in range(self.retry_count + 1):
                resp = self.connection_pool.request(method, url,
                                                    headers=headers,
                                                    body=body,
                                                    timeout=self.timeout / 1000.0,
                                                    retries=self.retry_count)

                # retry for non-200
                if int(resp.status / 100) != 2:
                    continue

                return resp

            raise PredictException(resp.status, resp.data)

        except (MaxRetryError, ProtocolError, HTTPError) as e:
            self.logger and self.logger.debug(
                'Request failed, err: %s', str(e))
            raise PredictException(502, 'url: %s, error: %s' % (url, str(e)))

    def truncate(self, index):
        """
        delete data whose indexes are smaller than the specified index from a queue service
        """
        query = {
            '_index_': index,
            '_trunc_': 'true'
        }
        url = self._build_url(query)

        headers = self._with_identity()
        return self._do_request(url, 'DELETE', headers).data

    def put(self, data, tags: dict = {}):
        """
        put data into a queue service
        """
        url = self._build_url(tags)

        headers = self._with_identity()
        resp = self._do_request(url, 'POST', headers, data)
        request_id = resp.headers[HeaderRequestId]
        return resp.data.decode('utf-8'), request_id

    def attributes(self):
        """
        get the attributes of a queue service
        """
        url = self._build_url({'_attrs_': 'true'})

        headers = self._with_identity()
        resp = self._do_request(url, 'GET', headers)
        return json.loads(resp.data.strip().decode('utf-8'))

    def search(self,  index):
        """
        search the info of data
        """
        if not self._check_index(index):
            self.logger and self.logger.warning(
                "invalid search index: {}".format(index))
            return json.loads("{}")
        query = {
            '_search_': 'true',
            '_index_': str(index)
        }
        url = self._build_url(query)

        headers = self._with_identity()
        try:
            resp = self._do_request(url, 'GET', headers)
        except PredictException as e:
            self.logger and self.logger.warning("search error: {}".format(e))
            return json.loads("{}")
        return json.loads(resp.data.strip().decode('utf-8'))

    def get(self, request_id=None, index=0, length=1, timeout='5s', auto_delete=True, tags={}):
        """
        get the data in queue service
        """
        query = {
            '_index_': str(index),
            '_length_': str(length),
            '_timeout_': str(timeout),
            '_raw_': 'false',
            '_auto_delete_': str(auto_delete).lower(),
        }
        if request_id is not None:
            query['requestId'] = request_id

        query.update(tags)

        url = self._build_url(query)

        headers = self._with_identity()
        headers['Accept'] = 'application/vnd.google.protobuf'  # default

        resp = self._do_request(url, 'GET', headers)
        dfl = DataFrameListCodec.decode(resp.data)
        return dfl.get_list()

    def delete(self, index):
        """
        delete indexes
        """
        if not isinstance(index, list):
            index = [index]
        return self._process_indexes(index, 'DELETE').decode('utf-8')

    def watch(self, index: int, window: int, index_only=False, auto_commit=False, tags=None):
        """
        create a watcher to read data items from a queue
        """
        if tags is None:
            tags = {}

        query = {
            '_watch_': 'true',
            '_index_': index,
            '_window_': window,
            '_index_only_': str(index_only).lower(),
            '_auto_commit_': str(auto_commit).lower(),
        }
        query.update(tags)
        url = self._build_url(query, websocket=True)

        headers = self._with_identity()
        headers['Accept'] = 'application/vnd.google.protobuf'  # default

        try:
            return Watcher(self, url, headers, self.logger)
        except websocket._exceptions.WebSocketException as e:
            self.watch_sock = None
            raise PredictException(400, 'url: %s, error: %s' % (url, str(e)))

    def commit(self, index):
        """
        commit indexes
        """
        if not isinstance(index, list):
            index = [index]
        return self._process_indexes(index, 'PUT')
