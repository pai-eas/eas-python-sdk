#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import unittest
import time
import json
import threading

from .queue_client import QueueClient
from .queue_client import PredictException

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


QueueEndpoint = '1828488879222746.cn-shanghai.pai-eas.aliyuncs.com'
QueueName = 'test_group.qservice'
SinkQueueName = 'test_group.qservice/sink'
QueueToken = 'YmE3NDkyMzdiMzNmMGM3ZmE4ZmNjZDk0M2NiMDA3OTZmNzc1MTUxNg=='

input_queue = None
sink_queue = None


class QueueClientTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(QueueClientTestCase, self).__init__(*args, **kwargs)
        global input_queue
        global sink_queue
        if input_queue is None:
            input_queue = QueueClient(QueueEndpoint, QueueName)
            input_queue.set_token(QueueToken)
            input_queue.init()
        if sink_queue is None:
            sink_queue = QueueClient(QueueEndpoint, SinkQueueName)
            sink_queue.set_token(QueueToken)
            sink_queue.init()

        self.input_queue = input_queue
        self.sink_queue = sink_queue

    def truncate(self):
        info = self.input_queue.info()
        if 'stream.lastEntry' in info:
            self.input_queue.truncate(int(info['stream.lastEntry']) + 1)

        info = self.sink_queue.info()
        if 'stream.lastEntry' in info:
            self.sink_queue.truncate(int(info['stream.lastEntry']) + 1)

    def test_queue_get_by_request_id(self):
        self.truncate()

        index, request_id = self.sink_queue.put('abc')

        res_list = self.sink_queue.get(request_id=request_id)
        self.assertEqual(len(res_list), 1)
        self.assertEqual(res_list[0].data.decode('utf-8'), 'abc')

    def test_queue_get_by_index(self):
        index, request_id = self.sink_queue.put('abc')

        res_list = self.sink_queue.get(index=index)
        self.assertEqual(len(res_list), 1)
        self.assertEqual(res_list[0].data.decode('utf-8'), 'abc')

    def test_queue_truncate(self):
        latest_index = 0
        for x in range(10):
            index, request_id = self.sink_queue.put('abc')
            latest_index = index

        info = self.sink_queue.info()
        self.assertTrue(int(info['stream.length']) > 1)

        self.sink_queue.truncate(int(latest_index) + 1)

        info = self.sink_queue.info()

        self.assertEqual(int(info['stream.length']), 0)

    def test_watch_with_auto_commit(self):

        for x in range(10):
            index, request_id = self.sink_queue.put(str(x))

        i = 0
        watcher = self.sink_queue.watch(0, 5, auto_commit=True)
        for x in watcher.run():
            self.assertEqual(i, int(x.data.decode('utf-8')))
            i += 1
            if i == 10:
                break

        watcher.close()
        info = self.sink_queue.info()

        time.sleep(1)

        info = self.sink_queue.info()

        self.assertEqual(int(info['stream.length']), 0)

    def test_watch_with_manual_commit(self):

        for x in range(10):
            index, request_id = self.sink_queue.put(str(x))

        info = self.sink_queue.info()

        i = 0
        watcher = self.sink_queue.watch(0, 5, auto_commit=False)
        for x in watcher.run():
            self.assertEqual(i, int(x.data.decode('utf-8')))
            i += 1
            self.sink_queue.commit(x.index)
            if i == 10:
                break

        watcher.close()

        info = self.sink_queue.info()

        self.assertEqual(int(info['stream.length']), 0)

    def test_watch_with_inference_service_sync(self):
        self.truncate()

        for x in range(100):
            index, request_id = self.input_queue.put('[{}]')

        info = self.input_queue.info()

        i = 0
        watcher = self.sink_queue.watch(0, 5, auto_commit=False)
        for x in watcher.run():
            js = json.loads(x.data.decode('utf-8'))
            self.assertEqual(len(js[0].items()), 2)
            self.sink_queue.commit(x.index)
            i += 1
            if i == 100:
                break

        watcher.close()

        info = self.sink_queue.info()

        self.assertEqual(int(info['stream.length']), 0)

    def test_watch_with_inference_service_async(self):
        self.truncate()

        count = 1000

        send_items = set()
        recv_items = set()

        def send_thread():
            for x in range(count):
                index, request_id = self.input_queue.put('[{}]')
                send_items.add(request_id)

        def watch_thread():
            watcher = self.sink_queue.watch(0, 5, auto_commit=True)
            i = 0
            for x in watcher.run():
                recv_items.add(x.tags['requestId'])
                i += 1
                if i == count:
                    break
            watcher.close()

        thread1 = threading.Thread(target=watch_thread)
        thread2 = threading.Thread(target=send_thread)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        self.assertEqual(send_items, recv_items)

    def test_watch_with_two_watcher(self):
        for x in range(1):
            index, request_id = self.sink_queue.put('[{}]')

        watcher = self.sink_queue.watch(0, 5, auto_commit=True)
        for x in watcher.run():
            break
        with self.assertRaises(PredictException):
            for x in watcher.run():
                break
        watcher.close()


if __name__ == '__main__':
    unittest.main()
