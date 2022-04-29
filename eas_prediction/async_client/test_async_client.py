#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import unittest

from .async_client import AsyncClient
from .async_client import DataFrameProto

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AsyncClientTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(AsyncClientTestCase, self).__init__(*args, **kwargs)
        # self.client = AsyncClient()

    def test_async_get(self):
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("test", "test-group")
        raw = client.get(6925387844634542080, 1)[0].raw_data.SerializeToString()
        dd = DataFrameProto()
        print(raw)
        dd.ParseFromString(raw)
        print(dd)
        print('dd')

    def test_async_commit(self):
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("test", "test-group")
        print(client.commit([6925492373015232512]))

    def test_async_put(self):
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("test", "test-group")
        print(client.put("test2", {}))

    def test_async_watch(self):
        dd = DataFrameProto()
        # dd.ParseFromString(b'\x00\x00\x00F\x08\x80\x80\x80\xda\xd6\xf1\xfa\x8d`\x121\n\trequestId\x12$8b488f6c-64c9-4a28-a128-59769609bf3b\x1a\x077 hello')
        # print(dd)
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("bar", "test-group2")
        print(client.watch(0, 5))

    def test_async_delete(self):
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("test", "test-group")
        print(client.delete([6925387844634542080]))


if __name__ == '__main__':
    unittest.main()
