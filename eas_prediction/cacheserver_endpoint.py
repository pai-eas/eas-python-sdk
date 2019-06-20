#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .endpoint import Endpoint
import urllib3
import json


class CacheServerEndpoint(Endpoint):
    def __init__(self, domain, service_name):
        super(CacheServerEndpoint, self).__init__()
        self.domain = domain
        self.service_name = service_name
        self.http = urllib3.PoolManager()

    def sync(self):
        self.domain = self.domain.replace('http://', '')
        self.domain = self.domain.replace('https://', '')
        url = 'http://%s/exported/apis/eas.alibaba-inc.k8s.io/v1/upstreams/%s' % \
              (self.domain, self.service_name)
        endpoints = []
        try:
            resp = self.http.request('GET', url)
            if resp.status != 200:
                print('sync service endpoints error: %s, %s' % (resp.status, resp.data))
                return

            result = json.loads(resp.data)
            hosts = result['endpoints']['items']
            for host in hosts:
                endpoints.append(({
                                      'ip': host['ip'],
                                      'port': host['port'],
                                  }, host['weight']))
            self.set_endpoints(endpoints)
        except urllib3.exceptions.HTTPError as e:
            print('sync service endpoints http error, [%s]: %s' % (url, str(e)))
        except Exception as e:
            print('sync service endpoints unknown error, [%s]: %s' % (url, str(e)))
