#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .endpoint import Endpoint


class GatewayEndpoint(Endpoint):
    """
    Endpoint for the gateway access which provide a static http address for
    service accessing, there's no need for client to implement round robin,
    every time a request is invoked, just return the static http address.
    """
    def __init__(self, domain):
        if not domain.startswith('http://'):
            domain = 'http://' + domain
        if domain.endswith('/'):
            domain = domain[:len(domain)-1]
        self.domain = domain

    def set_endpoints(self, endpoints):
        print('sync nothing for gateway endpoint')

    def get(self):
        return self.domain

