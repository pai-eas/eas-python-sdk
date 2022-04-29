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
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("bar", "test-group2")
        for df in client.watch(0, 5):
            print(df)
            # client.commit([df.index])

    def test_async_delete(self):
        client = AsyncClient('11.160.138.124:3031', '')
        client.init("test", "test-group")
        print(client.delete([6925387844634542080]))


if __name__ == '__main__':
    unittest.main()
