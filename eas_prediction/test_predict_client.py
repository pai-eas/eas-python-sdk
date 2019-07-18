#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from .predict_client import PredictClient
from .string_request import StringRequest
from .tf_request import TFRequest
from .exception import PredictException


class PredictClientTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(PredictClientTestCase, self).__init__(*args, **kwargs)
        self.client = PredictClient()

    def setUp(self):
        self.client.set_endpoint('http://pai-eas-vpc.cn-shanghai.aliyuncs.com')
        self.client.set_service_name('scorecard_pmml_example')
        self.client.set_token('YWFlMDYyZDNmNTc3M2I3MzMwYmY0MmYwM2Y2MTYxMTY4NzBkNzdjOQ==')
        self.client.init()

    def tearDown(self):
        self.client.destroy()

    def test_predict_pmml_empty(self):
        req = StringRequest()
        ex = None
        try:
            self.client.predict(req)
        except PredictException as ex:
            pass

        self.assertEqual(ex, None)

    def test_prediction_pmml_bad_json(self):
        req = StringRequest('[{]]')
        ex = None
        try:
            self.client.predict(req)
        except Exception as ex:
            pass

        self.assertEqual(True, isinstance(ex, PredictException))

    def test_prediction_bad_endpoint(self):
        req = StringRequest('[{}]')
        response = self.client.predict(req)

    def test_prediction_tensorflow(self):
        self.client.set_service_name('mnist_saved_model_example')
        self.client.set_token('YTg2ZjE0ZjM4ZmE3OTc0NzYxZDMyNmYzMTJjZTQ1YmU0N2FjMTAyMA==')
        self.client.init()

        req = TFRequest('predict_images')
        req.add_feed('images', [1, 784], TFRequest.DT_FLOAT, [8] * 784)
        response = self.client.predict(req)
        print(response)
        print(response.get_values('scores'))
        print(response.get_tensor_shape('scores'))

    def test_prediction_tf_benying(self):
        self.client.set_service_name('mnist_saved_model_example_test')
        self.client.set_token('N2ExMmM0NjhjNzEyZTU1NDJlNTJkNDQxMzdjNWVmNTEwMzFhZGVjZg==')
        self.client.init()

        req = TFRequest('serving_default')
        req.add_feed('sentence1', [200, 15], TFRequest.DT_INT32, [1] * 200 * 15)
        req.add_feed('sentence2', [200, 15], TFRequest.DT_INT32, [1] * 200 * 15)
        req.add_feed('y', [200, 2], TFRequest.DT_INT32, [2] * 200 * 2)
        req.add_feed('keep_rate', [], TFRequest.DT_FLOAT, [0.2])
        f = open('tf.pb', 'w+')
        f.write(req.to_string())
        f.close()

        response = self.client.predict(req)
        print(response)

    def test_vipserver_endpoint(self):
        from vipserver_endpoint import VipServerEndpoint
        print(VipServerEndpoint.get_server())

    def test_vipserver_sync(self):
        from vipserver_endpoint import VipServerEndpoint
        endpoint = VipServerEndpoint('conn-test.shanghai.eas.vipserver')
        print(endpoint.sync())
        print(endpoint.get())


if __name__ == '__main__':
    unittest.main()
