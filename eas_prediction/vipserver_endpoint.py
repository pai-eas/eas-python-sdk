#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .endpoint import Endpoint
from .exception import PredictException
import urllib3
import random
import json
import re


class VipServerEndpoint(Endpoint):
    def __init__(self, domain, logger):
        super(VipServerEndpoint, self).__init__(logger)
        self.domain = domain
        self.http = urllib3.PoolManager()
        self.logger = logger

    def get_server(self):
        vipserver_endpoint = 'http://jmenv.tbsite.net:8080/vipserver/serverlist'
        try:
            resp = self.http.request('GET', vipserver_endpoint)
            if resp.status != 200:
                raise PredictException(resp.status, resp.data)
            servers = str(resp.data)
            server_list = re.split('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', servers)
            server_list = [x for x in server_list if re.match('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', x) is not None ]
        except Exception as e:
            raise PredictException(500, str(e))
        return server_list[random.randint(0, len(server_list) - 1)]

    def sync(self):
        server = self.get_server()
        url = 'http://%s/vipserver/api/srvIPXT?dom=%s&clusters=DEFAULT' % (server, self.domain)
        endpoints = []
        try:
            resp = self.http.request('GET', url)
            if resp.status != 200:
                self.logger.error('sync service endpoints error: %s, %s' % (resp.status, resp.data))
                return

            if isinstance(resp.data, bytes):
                result = json.loads(resp.data.decode('utf-8'))
            else:
                result = json.loads(resp.data)
            hosts = result['hosts']
            for host in hosts:
                if host['valid']:
                    endpoints.append(({
                        'ip': host['ip'],
                        'port': host['port'],
                    }, host['weight']))
            self.logger.debug(endpoints)
            self.set_endpoints(endpoints)
        except urllib3.exceptions.HTTPError as e:
            self.logger.error('sync service endpoints http error, [%s]: %s' % (url, str(e)))
        except Exception as e:
            self.logger.error('sync service endpoints unknown error, [%s]: %s' % (url, str(e)))
