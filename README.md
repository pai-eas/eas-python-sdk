# 安装方法：

```bash
pip install -U eas-prediction --user
```

# Python SDK调用接口说明
|类|主要接口|描述|
|-----|------|------|
|PredictClient|PredictClient(endpoint, service_name)|PredictClient类构造器，endpoint是服务端的endpoint地址，对于普通服务设置为默认网关endpoint，如eas-shanghai-intranet.alibaba-inc.com；service_name为服务名字；两个参数均可为空，在初始化后单独进行设置。|
||set_endpoint(endpoint)|设置服务的endpoint，endpoint的说明见构造函数|
||set_service_name(service_name)|设置请求的服务名字|
||set_endpoint_type(endpoint_type)|设置服务端的网关类型，支持默认网关PredictClient.ENDPOINT_TYPE_GATEWAY，PredictClient.ENDPOINT_TYPE_DIRECT，默认值为PredictClient.ENDPOINT_TYPE_GATEWAY|
||set_token(token)|设置服务访问的token|
||set_retry_count(max_retry_count)|设置请求失败重试次数，默认为5；该参数非常重要，对于服务端进程异常或机器异常或网关长连接断开等情况带来的个别请求失败，均需由客户端来重试解决，请勿将其设置为0|
||set_max_connection_count(max_connection_count)|设置客户端连接池的最大大小，出于性能考虑，客户端会与服务端建立长连接，并将连接放入连接池中，每次请求从中获取一个空闲连接来访问服务；默认值为100|
||set_timeout(timeout)|设置请求的超时时间，单位为ms，默认为5000|
||init() |对PredictClient对象进行初始化，在上述设置参数的函数执行完成后，同样需要调用init()函数才会生效|
||predict(request)|向在线预测服务提交一个预测请求，request对象是一个抽象类，可以输入不同类型的request，如StringRequest，TFRequest等)，返回为对应的Response|
|StringRequest|StringRequest(request_data)|StringRequest类构造方法，输入为要发送的请求字符串|
||to_string()|返回请求的response body|
|TFRequest|TFRequest(signature_name)|TFRequest类构建方法，输入为要请求模型的signature_name|
||def add_feed(self, input_name, shape, content_type, content)|请求Tensorflow的在线预测服务模型时，设置需要输入的Tensor，input_name表示输入Tensor的别名，data_type表示输入Tensor的DataType， shape表示输入Tensor的TensorShape，content表示输入Tensor的内容（一维数组展开表示）。DataType支持如下几种类型：TFRequest.DT_FLOAT, TFRequest.DT_DOUBLE, TFRequest.DT_INT8, TFRequest.DT_INT16, TFRequest.DT_INT32, TFRequest.DT_INT64, TFRequest.DT_STRING, TFRequest.TF_BOOL|
||def add_fetch(self, output_name)|请求Tensorflow的在线预测服务模型时，设置需要输出的Tensor的别名，对于savedmodel模型该参数可选，若不设置，则输出所有的outputs，对于frozen model该参数必选|
||to_string()|将TFRequest中所构建的用于请求传输的protobuf对象序列化成string|
|TFResponse|get_tensor_shape(output_name)|获得别名为ouputname的输出Tensor的TensorShape|
||get_values(output_name)|获取输出的tensor的数据向量，输出结果以一维数组的形式保存，可配套使用get_tensor_shape()获取对应的tensor的shape，将其还原成所需的多维tensor，输出会根据output的类型不同，返回不同类型的结果数组|
|TorchRequest|TorchRequest()|TFRequest类构建方法|
||def add_feed(self, index, shape, content_type, content)|请求PyTorch的在线预测服务模型时，设置需要输入的Tensor，index表示要输入的tensor的下标，data_type表示输入Tensor的DataType， shape表示输入Tensor的TensorShape，content表示输入Tensor的内容（一维数组展开表示）。DataType支持如下几种类型：TFRequest.DT_FLOAT, TFRequest.DT_DOUBLE, TFRequest.DT_INT8, TFRequest.DT_INT16, TFRequest.DT_INT32, TFRequest.DT_INT64 |
||def add_fetch(self, output_index)|请求PyTorch的在线预测服务模型时，设置需要输出的Tensor的index，可选，若不设置，则输出所有的outputs|
||to_string()|将TorchRequest中所构建的用于请求传输的protobuf对象序列化成string|
|TorchResponse|get_tensor_shape(output_index)|获得下标index的输出Tensor的TensorShape|
||get_values(output_index)|获取输出的tensor的数据向量，输出结果以一维数组的形式保存，可配套使用get_tensor_shape()获取对应的tensor的shape，将其还原成所需的多维tensor，输出会根据output的类型不同，返回不同类型的结果数组|
|OnnxRequest|OnnxRequest()|OnnxRequest类构建方法|
||add_tensor(OnnxData.TensorProto)|请求HIE的在线模型预测服务时，设置需要输入的Tensor，为OnnxData.TensorProto格式；若这个Tensor的name之前已经add过，则之前add的会被新的覆盖|
|OnnxResponse|get_size()|获取输出的tensor的数量|
||get_name(output_index)|获取下标index的输出的Tensor的name|
||get_tensor(output_index)|获取下标index的输出的tensor，为OnnxData.TensorProto格式|
|OnnxDataHelper|to_array(OnnxData.TensorProto)|将OnnxData.TensorProto转成numpy array|
||from_array(numpy.array)|将numpy array转成OnnxData.TensorProto|


# 程序示例
## 字符串输入输出程序示例
对于自定义Processor用户而言，通常采用字符串进行服务的输入输出调用(如pmml模型服务的调用)，具体的demo程序如下：

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction import StringRequest

if __name__ == '__main__':
    client = PredictClient('http://1828488879222746.cn-shanghai.pai-eas.aliyuncs.com', 'scorecard_pmml_example')
    client.set_token('YWFlMDYyZDNmNTc3M2I3MzMwYmY0MmYwM2Y2MTYxMTY4NzBkNzdjOQ==')
    client.init()

    request = StringRequest('[{"fea1": 1, "fea2": 2}]')
    for x in range(0, 1000000):
        resp = client.predict(request)
        print(resp)
```

## Tensorflow输入输出程序示例
TF用户可以使用TFRequest与TFResponse作为数据的输入输出格式，具体demo示例如下：

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction import StringRequest
from eas_prediction import TFRequest

if __name__ == '__main__':
    client = PredictClient('http://1828488879222746.cn-shanghai.pai-eas.aliyuncs.com', 'mnist_saved_model_example')
    client.set_token('YTg2ZjE0ZjM4ZmE3OTc0NzYxZDMyNmYzMTJjZTQ1YmU0N2FjMTAyMA==')
    client.init()

    #request = StringRequest('[{}]')
    req = TFRequest('predict_images')
    req.add_feed('images', [1, 784], TFRequest.DT_FLOAT, [1] * 784)
    for x in range(0, 1000000):
        resp = client.predict(req)
        print(resp)
```

## 通过VPC网络直连的方式调用服务

网络直连方式仅支持部署在EAS公共云控制台中购买专用资源组的服务，且需要在控制台上为该资源组与用户指定的vswitch打通网络后才可使用。调用方法与普通调用方式相比，增加一句 **client.set_endpoint_type(ENDPOINT_TYPE_DIRECT)** 即可，非常适合大流量高并发的服务。

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction import StringRequest
from eas_prediction import TFRequest
from eas_prediction import ENDPOINT_TYPE_DIRECT

if __name__ == '__main__':
    client = PredictClient('http://pai-eas-vpc.cn-hangzhou.aliyuncs.com', 'mnist_saved_model_example')
    client.set_token('M2FhNjJlZDBmMzBmMzE4NjFiNzZhMmUxY2IxZjkyMDczNzAzYjFiMw==')
    client.set_endpoint_type(ENDPOINT_TYPE_DIRECT)
    client.init()

    request = TFRequest('predict_images')
    request.add_feed('images', [1, 784], TFRequest.DT_FLOAT, [1] * 784)
    for x in range(0, 1000000):
        resp = client.predict(request)
        print(resp)
```


## PyTorch输入输出程序示例
PyTorch用户可以使用TorchRequest与TorchResponse作为数据的输入输出格式，具体demo示例如下：

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction import TorchRequest

if __name__ == '__main__':
    client = PredictClient('http://1828488879222746.cn-shanghai.pai-eas.aliyuncs.com', 'pytorch_gpu_wl')
    client.init()

    req = TorchRequest()
    req.add_feed(0, [1, 3, 224, 224], TorchRequest.DT_FLOAT, [1] * 150528)
    # req.add_fetch(0)
    import time
    st = time.time()
    timer = 0
    for x in range(0, 10):
        resp = client.predict(req)
        timer += (time.time() - st)
        st = time.time()
        print(resp.get_tensor_shape(0))
        # print(resp)
    print("average response time: %s s" % (timer / 10) )
```


## BladeProcessor输入输出程序示例
BladeProcessor用户可以使用BladeRequest与BladeResponse作为数据的输入输出格式，具体demo示例如下：

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction import BladeRequest 

if __name__ == '__main__':
    client = PredictClient('http://1828488879222746.cn-shanghai.pai-eas.aliyuncs.com', 'nlp_model_example')
    client.init()

    req = BladeRequest()

    req.add_feed('input_data', 1, [1, 360, 128], BladeRequest.DT_FLOAT, [0.8] * 85680)
    req.add_feed('input_length', 1, [1], BladeRequest.DT_INT32, [187])
    req.add_feed('start_token', 1, [1], BladeRequest.DT_INT32, [104])
    req.add_fetch('output', BladeRequest.DT_FLOAT)
    import time
    st = time.time()
    timer = 0
    for x in range(0, 10):
        resp = client.predict(req)
        timer += (time.time() - st)
        st = time.time()
        # print(resp)
        # print(resp.get_values('output'))
        print(resp.get_tensor_shape('output'))
    print("average response time: %s s" % (timer / 10) )
```


## 兼容EAS默认tensorflow接口的BladeProcessor输入输出程序示例
BladeProcessor用户可以使用"兼容EAS默认tensorflow接口"TFRequest与TFResponse作为数据的输入输出格式, 具体demo示例如下：
NOTE: 需要正确import [eas_prediction/blade_tf_request.py](./eas_prediction/blade_tf_request.py) 文件内定义的TFRequest与TFResponse

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction.blade_tf_request import TFRequest # Need Importing blade TFRequest 

if __name__ == '__main__':
    client = PredictClient('http://1828488879222746.cn-shanghai.pai-eas.aliyuncs.com', 'nlp_model_example')
    client.init()

    req = TFRequest(signature_name='predict_words')

    req.add_feed('input_data', [1, 360, 128], TFRequest.DT_FLOAT, [0.8] * 85680)
    req.add_feed('input_length', [1], TFRequest.DT_INT32, [187])
    req.add_feed('start_token', [1], TFRequest.DT_INT32, [104])
    req.add_fetch('output')
    import time
    st = time.time()
    timer = 0
    for x in range(0, 10):
        resp = client.predict(req)
        timer += (time.time() - st)
        st = time.time()
        # print(resp)
        # print(resp.get_values('output'))
        print(resp.get_tensor_shape('output'))
    print("average response time: %s s" % (timer / 10) )
```


## OnnxProcessor输入输出程序示例
OnnxProcessor用户可以使用OnnxRequest与OnnxResponse作为数据的输入输出格式，具体demo示例如下：

```python
from eas_prediction import PredictClient
from eas_prediction import OnnxRequest, OnnxDataHelper
import numpy as np

if __name__ == '__main__':
    endpoint = 'http://localhost:6016'
    inputs = np.load('0_inputs.npz') # inputs

    client = PredictClient(endpoint, 'hie_eas_processor_bert')
    # client.set_token('YWFlMDYyZDNmNTc3M2I3MzMwYmY0MmYwM2Y2MTYxMTY4NzBkNzdjOQ==')
    client.init()

    req = OnnxRequest()
    for name, arr in inputs.items():
        req.add_tensor(OnnxDataHelper.from_array(arr, name))
    import time
    st = time.time()
    timer = 0
    for x in range(0, 10):
        resp = client.predict(req)
        timer += (time.time() - st)
        st = time.time()
        for i in range(resp.get_size()):
            name = resp.get_name(i)
            arr = OnnxDataHelper.to_array(resp.get_tensor(i))
            print("{}: output: {}, shape: {}".format(x, name, arr.shape))
    print("average response time: %s s" % (timer / 10) )
```

## EasyRecProcessor输入输出程序实例
EasyRec用户可以PBFeature与PBResponse作为数据输入输出格式, 具体demo示例如下:

```python
from eas_prediction import PredictClient
from eas_prediction.easyrec_request import EasyRecRequest
from eas_prediction.easyrec_predict_pb2 import PBFeature
from eas_prediction.easyrec_predict_pb2 import PBRequest

if __name__ == '__main__':
    endpoint = 'http://localhost:6016'

    client = PredictClient(endpoint, 'ali_rec_test')
    # client.set_token('12345xyz')
    client.init()

    req = PBRequest()
    uid = PBFeature()
    uid.string_feature = 'u0001'
    req.user_features['user_id'] = uid
    age = PBFeature()
    age.int_feature = 12
    req.user_features['age'] = age
    weight = PBFeature()
    weight.float_feature = 129.8
    req.user_features['weight'] = weight

    req.item_ids.extend(['item_0001', 'item_0002', 'item_0003'])
    
    easyrec_req = EasyRecRequest()
    easyrec_req.add_feed(req, debug_level=0)
    res = client.predict(easyrec_req)
    print(res)
```

## TorchRecProcessor输入输出程序实例
TorchRec用户可以PBFeature与PBResponse作为数据输入输出格式, 具体demo示例如下:

```python
from eas_prediction import PredictClient
from eas_prediction.torchrec_request import TorchRecRequest


if __name__ == '__main__':
    endpoint = 'http://localhost:6016'

    client = PredictClient(endpoint, 'torch_rec_test')
    # client.set_token('12345xyz')
    client.init()
    torchrec_req = TorchRecRequest()
    
    torchrec_req.add_user_fea('user_id','u001d',"STRING")
    torchrec_req.add_user_fea('age',12,"INT")
    torchrec_req.add_user_fea('weight',129.8,"FLOAT")
    torchrec_req.add_item_id('item_0001')
    torchrec_req.add_item_id('item_0002')
    torchrec_req.add_item_id('item_0003')
    
    res = client.predict(torchrec_req)
    print(res)
```

