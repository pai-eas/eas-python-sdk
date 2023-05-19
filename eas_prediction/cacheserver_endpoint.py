#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .endpoint import Endpoint
import urllib3
import json
import os


class CacheServerEndpoint(Endpoint):
    def __init__(self, domain, service_name, logger):
        super(CacheServerEndpoint, self).__init__(logger)
        self.domain = domain
        self.service_name = service_name.split('/')[0]
        self.http = urllib3.PoolManager()
        self.logger = logger
        self.logger.info('Service discovery endpoint is: %s' % self.domain)

    def sync(self):
        self.domain = self.domain.replace('http://', '')
        self.domain = self.domain.replace('https://', '')
        namespace = os.getenv('NAMESPACE')
        pod_name = os.getenv('POD_NAME')
        internal = False
        if namespace is not None and pod_name is not None:
            internal = True
        url = 'http://%s/exported/apis/eas.alibaba-inc.k8s.io/v1/upstreams/%s%s' % \
              (self.domain, self.service_name, '?internal=true' if internal else '')
        endpoints = []
        try:
            resp = self.http.request('GET', url)
            if resp.status != 200:
                self.logger.error('sync service endpoints error: %s, %s' % (resp.status, resp.data))
                return

            resp_data = resp.data.decode('utf-8')
            result = json.loads(resp_data)
            hosts = result['endpoints']['items']
            for host in hosts:
                endpoints.append(({
                                      'ip': host['ip'],
                                      'port': host['port'],
                                  }, host['weight']))
            self.logger.debug(endpoints)
            self.set_endpoints(endpoints)
        except urllib3.exceptions.HTTPError as e:
            self.logger.error('sync service endpoints http error, [%s]: %s' % (url, str(e)))
        except Exception as e:
            self.logger.error('sync service endpoints error, [%s]: %s' % (url, str(e)))
