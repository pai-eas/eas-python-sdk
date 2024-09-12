#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import sys
import logging
import datetime
import hashlib
import hmac
import base64
from urllib3 import PoolManager
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import ProtocolError
from urllib3.exceptions import HTTPError
from .exception import PredictException
from .vipserver_endpoint import VipServerEndpoint
from .cacheserver_endpoint import CacheServerEndpoint
from .gateway_endpoint import GatewayEndpoint

ENDPOINT_TYPE_DIRECT = 'DIRECT'
ENDPOINT_TYPE_VIPSERVER = 'VIPSERVER'
ENDPOINT_TYPE_DEFAULT = 'DEFAULT'


class PredictClient:
    """
    Client for accessing prediction service by creating a fixed size connection pool
    to perform the request through established persistent connections.
    """

    def __init__(self, endpoint='', service_name='', custom_url=''):
        self.retry_count = 5
        self.max_connection_count = 100
        self.token = ''
        self.endpoint = None
        self.timeout = 5000
        self.connection_pool = None
        self.endpoint_type = ''
        self.endpoint_name = endpoint
        self.custom_url = custom_url
        self.service_name = service_name
        self.content_type = ''
        self.headers = {}
        self.stop = False
        self.logger = logging.getLogger(endpoint + '/' + service_name)
        self.logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        self.logger.setLevel(logging.ERROR)

    def __sync_handler(self):
        while True:
            if self.stop:
                break
            try:
                self.endpoint.sync()
            except PredictException as e:
                self.logger.error(str(e))
            time.sleep(3)

    def destroy(self):
        self.stop = True

    def init(self):
        """
        Initialize the client after the functions used to set the client properties are called
        """
        if self.connection_pool is None:
            self.connection_pool = PoolManager(maxsize=self.max_connection_count)

        if self.endpoint_type == '' or self.endpoint_type == ENDPOINT_TYPE_DEFAULT:
            self.endpoint = GatewayEndpoint(self.endpoint_name, self.service_name, self.logger, self.custom_url)
        elif self.endpoint_type == ENDPOINT_TYPE_VIPSERVER:
            self.endpoint = VipServerEndpoint(self.endpoint_name, self.logger)
        elif self.endpoint_type == ENDPOINT_TYPE_DIRECT:
            self.endpoint = CacheServerEndpoint(self.endpoint_name, self.service_name, self.logger)
        else:
            raise PredictException(500, 'Unsupported endpoint type: %s' % self.endpoint_type)

        t = threading.Thread(target=PredictClient.__sync_handler, args=(self,))
        t.daemon = True
        t.start()
        self.logger.debug('Endpoint sync thread started')

    def set_endpoint(self, endpoint):
        """
        Set the endpoint of the service for the client
        :param endpoint_name: name of the endpoint, such as http://pai-eas-vpc.cn-shanghai.aliyuncs.com
        """
        self.endpoint_name = endpoint

    def set_service_name(self, service_name):
        """
        Set the service name for the client
        :param service_name: name of the service to access
        """
        self.service_name = service_name

    def set_endpoint_type(self, endpoint_type):
        """
        Set the endpoint type, support GATEWAY, DIRECT, VIPSERVER, default is GATEWAY
        :param endpoint_type: type of the endpoint
        """
        self.endpoint_type = endpoint_type

    def set_token(self, token):
        """
        Set the authentication token of the service for the client
        :param token: service token, automatically generated when deploying the service
        """
        self.token = token

    def set_content_type(self, content_type):
        """
        Set the content_type for the client
        :param content_type: content_type
        """
        self.content_type = content_type

    def set_log_level(self, log_level):
        """
        Set log level for logging module
        :param log_level: target log level
        """
        self.logger.setLevel(log_level)

    def set_retry_count(self, count):
        """
        Set the max count of retrying when an error occurred during a request
        :param count: max retry count
        """
        self.retry_count = count

    def set_max_connection_count(self, count):
        """
        Set the max connection count which is the upper limit of connections in the connection pool
        :param count: max connection count
        """
        self.max_connection_count = count

    def set_timeout(self, timeout):
        """
        Set the request timeout for the client
        :param timeout: timeout of a single request
        :return:
        """
        self.timeout = timeout

    def add_extra_headers(self, headers: dict):
        """
        Set the request headers for the client
        :param headers: headers of a single request
        :return:
        """
        if not isinstance(headers, dict):
            raise TypeError("headers must be a dict")

        self.headers.update(headers)

    def generate_singaure(self, request_data):
        utcnow = datetime.datetime.now()
        content_type = self.content_type
        if len(content_type) == 0:
            content_type = 'application/octet-stream'

        current_time = utcnow.strftime('%a, %d %b %Y %H:%M:%S GMT')
        if self.custom_url != '':
            return {
                'Date': current_time,
                'Content-Type': content_type,
                'Content-Length': '%d' % len(request_data),
                'Authorization': self.token
            }

        canonicalized_resource = '/api/predict/%s' % self.service_name
        content_md5 = hashlib.md5(request_data).hexdigest()
        verb = 'POST'

        auth = '%s\n%s\n%s\n%s\n%s' % (verb, content_md5, content_type, current_time, canonicalized_resource)

        hmac1 = hmac.new(bytearray(self.token, 'utf-8'), bytearray(auth.strip(), 'utf-8'), hashlib.sha1)
        signature = base64.b64encode(hmac1.digest()).decode()
        authorization = 'EAS %s' % (signature.strip())

        return {
            'Content-MD5': content_md5,
            'Date': current_time,
            'Content-Type': content_type,
            'Content-Length': '%d' % len(request_data),
            'Authorization': authorization
        }

    def predict(self, req):
        """
        Perform the prediction request to the server by sending an http request of which the request body
        may be in different format (string, protobuf or other user defined format), make it an abstract
        class implementing a basic function 'to_string()' to serialized the request to string for sending
        :param req: abstract class of the request
        :return: service response correlated with the input request
        """
        headers = self.headers
        for i in range(0, self.retry_count):
            try:
                domain = self.endpoint.get()
                if self.custom_url != '':
                    url = self.custom_url
                else:
                    url = u'%s/api/predict/%s' % (domain, self.service_name)
                self.logger.debug('Request to url: %s' % url)
                req_str = req.to_string()
                if sys.version_info[0] == 3 and isinstance(req_str, str):
                    req_body = bytearray(req_str, 'utf-8')
                else:
                    req_body = bytearray(req_str)
                if len(self.token) > 0:
                    headers.update(self.generate_singaure(req_body))
                resp = self.connection_pool.request('POST', url,
                                                    headers=headers,
                                                    body=req_body,
                                                    timeout=self.timeout / 1000.0,
                                                    retries=0)
                if resp.status / 100 == 5:
                    if i != self.retry_count - 1:
                        continue
                    raise PredictException(resp.status, resp.data)

                if resp.status != 200:
                    raise PredictException(resp.status, resp.data)

                return req.parse_response(resp.data)
            except (MaxRetryError, ProtocolError, HTTPError) as e:
                self.logger.debug('Request failed, err: %s, retrying', str(e))
                if i != self.retry_count - 1:
                    continue
                raise PredictException(500, 'url: %s, error: %s' % (url, str(e)))
