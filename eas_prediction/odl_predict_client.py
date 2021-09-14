#!/usr/bin/env python
# -*- coding: utf-8 -*-

import farmhash
import numpy as np
from .predict_client import PredictClient

class OdlPredictClient:
    """
    Client for accessing prediction service by creating a fixed size connection pool
    to perform the request through established persistent connections.
    User can specify shard_key to split service into several sub-services, then
    client will send request to one sub-service according hash(shard_key) % var_shard_count. 
    """
    def __init__(self, endpoint='', service_name='',
                 var_shard_count = 1, shard_key_type='string'):
        if shard_key_type == 'string':
          self.do_hash = True
        elif shard_key_type == 'int64':
          self.do_hash = False
        else:
          raise PredictException(500, 'Unsupported shard_key type: %s' % shard_key_type)
        self.var_shard_count = var_shard_count
        self.hash_block = 1000
        self.int64_max = np.int64(0x7FFFFFFFFFFFFFFF)
        self.clients = []
        self.clients.append(PredictClient(endpoint, service_name))
        for i in range (1, var_shard_count):
            self.clients.append(PredictClient(endpoint, service_name+'_'+str(i)))

    def destroy(self):
        for client in self.clients:
            client.destroy()

    def init(self):
        """
        Initialize the client after the functions used to set the client properties are called
        """
        for client in self.clients:
            client.init()

    def set_endpoint(self, endpoint):
        """
        Set the endpoint of the service for the client
        :param endpoint_name: name of the endpoint, such as http://pai-eas-vpc.cn-shanghai.aliyuncs.com
        """
        for client in self.clients:
            client.set_endpoint(endpoint)

    def set_service_name(self, service_name):
        """
        Set the service name for the client
        :param service_name: name of the service to access
        """
        self.clients[0].set_service_name(service_name)
        for i in range (1, var_shard_count):
            self.clients[i].set_service_name(service_name+'_'+str(i))

    def set_endpoint_type(self, endpoint_type):
        """
        Set the endpoint type, support GATEWAY, DIRECT, VIPSERVER, default is GATEWAY
        :param endpoint_type: type of the endpoint
        """
        for client in self.clients:
            client.set_endpoint_type(endpoint_type)

    def set_token(self, token):
        """
        Set the authentication token of the service for the client
        :param token: service token, automatically generated when deploying the service
        """
        for client in self.clients:
            client.set_token(token)

    def set_log_level(self, log_level):
        """
        Set log level for logging module
        :param log_level: target log level
        """
        for client in self.clients:
            client.set_log_level(log_level)

    def set_retry_count(self, count):
        """
        Set the max count of retrying when an error occurred during a request
        :param count: max retry count
        """
        for client in self.clients:
            client.set_retry_count(count)

    def set_max_connection_count(self, count):
        """
        Set the max connection count which is the upper limit of connections in the connection pool
        :param count: max connection count
        """
        for client in self.clients:
            client.set_max_connection_count(count)

    def set_timeout(self, timeout):
        """
        Set the request timeout for the client
        :param timeout: timeout of a single request
        :return:
        """
        for client in self.clients:
            client.set_timeout(timeout)

    def gen_id(self, key):
        if self.do_hash:
            key = farmhash.hash64(key) & self.int64_max
        return key % self.hash_block % self.var_shard_count

    def predict(self, req, shard_key=None):
        """
        Perform the prediction request to the server by sending an http request of which the request body
        may be in different format (string, protobuf or other user defined format), make it an abstract
        class implementing a basic function 'to_string()' to serialized the request to string for sending
        User can specify shard_key which maybe 'userid', predict will send current req to one sub-service
        according hash(shard_key) % var_shard_count. 
        :param req: abstract class of the request
        :return: service response correlated with the input request
        """
        service_id = 0
        if shard_key is not None:
            service_id = self.gen_id(shard_key)

        return self.clients[service_id].predict(req)

