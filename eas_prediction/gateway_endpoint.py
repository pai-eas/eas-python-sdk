#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .endpoint import Endpoint
from .exception import PredictException
import os


class GatewayEndpoint(Endpoint):
    """
    Endpoint for the gateway access which provide a static http address for
    service accessing, there's no need for client to implement round robin,
    every time a request is invoked, just return the static http address.
    """

    def __init__(self, domain, service_name, logger, custom_url=''):
        super(GatewayEndpoint, self).__init__(logger)
        if domain is not None and len(custom_url) > 0:
            domain = custom_url
        elif domain is None or len(domain) == 0:
            namespace = os.getenv('NAMESPACE')
            if namespace is None or len(namespace) == 0:
                raise PredictException(500, '\'endpoint\' must be set when running outside eas service')
            service_name = service_name.replace('_', '-')
            domain = '%s.%s:8080' % (service_name, namespace)

        if not domain.startswith('http://'):
            domain = 'http://' + domain
        if domain.endswith('/'):
            domain = domain[:len(domain)-1]
        self.domain = domain
        self.logger = logger

    def set_endpoints(self, endpoints):
        self.logger.debug('sync nothing for gateway endpoint')

    def get_size(self):
        return 1

    def get(self):
        return self.domain
