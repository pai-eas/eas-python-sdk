#!/usr/bin/env python
# -*- coding: utf-8 -*-

from endpoint import Endpoint
from exception import PredictException
import urllib2
import random
import json


class VipServerEndpoint(Endpoint):
    def __init__(self, domain):
        super(VipServerEndpoint, self).__init__()
        self.domain = domain

    @staticmethod
    def get_server():
        vipserver_endpoint = 'http://jmenv.tbsite.net:8080/vipserver/serverlist'
        try:
            servers = urllib2.urlopen(vipserver_endpoint).read()
            server_list = servers.strip().split('\n')
        except urllib2.HTTPError as e:
            raise PredictException(e.code, e.read())
        except urllib2.URLError as e:
            raise PredictException(500, str(e))
        return server_list[random.randint(0, len(server_list) - 1)]

    def sync(self):
        server = VipServerEndpoint.get_server()
        url = 'http://%s/vipserver/api/srvIPXT?dom=%s&clusters=DEFAULT' % (server, self.domain)
        endpoints = []
        try:
            resp = urllib2.urlopen(url).read()
            result = json.loads(resp)
            hosts = result['hosts']
            for host in hosts:
                if host['valid']:
                    endpoints.append(({
                        'ip': host['ip'],
                        'port': host['port'],
                    }, host['weight']))
            self.set_endpoints(endpoints)
        except (urllib2.HTTPError, urllib2.URLError) as e:
            print('sync vipserver endpoints http error, [%s]: %s' % (url, str(e)))
        except Exception as e:
            print('sync vipserver endpoints unknown error, [%s]: %s' % (url, str(e)))
