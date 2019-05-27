#!/usr/bin/env python
# -*- coding: utf-8 -*-

from endpoint import Endpoint
import urllib2
import json


class CacheServerEndpoint(Endpoint):
    def __init__(self, domain, service_name):
        super(CacheServerEndpoint, self).__init__()
        self.domain = domain
        self.service_name = service_name

    def sync(self):
        namespace = self.service_name.replace('_', '-')
        url = 'http://%s/exported/apis/eas.alibaba-inc.k8s.io/v1/namespaces/%s/easendpoints' % \
              (self.domain, namespace)
        endpoints = []
        try:
            resp = urllib2.urlopen(url).read()
            result = json.loads(resp)
            hosts = result['items']
            for host in hosts:
                endpoints.append(({
                                      'ip': host['ip'],
                                      'port': host['port'],
                                  }, host['weight']))
            self.set_endpoints(endpoints)
        except (urllib2.HTTPError, urllib2.URLError) as e:
            print('sync vipserver endpoints http error, [%s]: %s' % (url, str(e)))
        except Exception as e:
            print('sync vipserver endpoints unknown error, [%s]: %s' % (url, str(e)))
