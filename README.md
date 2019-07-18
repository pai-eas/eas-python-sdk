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
||to_string()|将TFRequest中所构建的用于请求传输的protobuf对象序列化成string|
|TFResponse|get_tensor_shape(output_name)|获得别名为ouputname的输出Tensor的TensorShape|
||get_values(output_name)|获取输出的tensor的数据向量，输出结果以一维数组的形式保存，可配套使用get_tensor_shape()获取对应的tensor的shape，将其还原成所需的多维tensor，输出会根据output的类型不同，返回不同类型的结果数组|


# 程序示例
## 字符串输入输出程序示例
对于自定义Processor用户而言，通常采用字符串进行服务的输入输出调用(如pmml模型服务的调用)，具体的demo程序如下：

```python
#!/usr/bin/env python

from eas_prediction import PredictClient
from eas_prediction import StringRequest

if __name__ == '__main__':
    client = PredictClient('http://pai-eas-vpc.cn-shanghai.aliyuncs.com', 'scorecard_pmml_example')
    client.set_token('NjEyY2EwZTY0OWUyOWY3ZDAzNDU2ZWMwOGFlZjA3YjUwMjA0MzViNw==')
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
    client = PredictClient('http://pai-eas-vpc.cn-shanghai.aliyuncs.com', 'mnist_saved_model_example')
    #client.set_token('M2FhNjJlZDBmMzBmMzE4NjFiNzZhMmUxY2IxZjkyMDczNzAzYjFiMw==')
    client.init()

    #request = StringRequest('[{}]')
    req = TFRequest('predict_images')
    req.add_feed('images', [1, 784], TFRequest.DT_FLOAT, [1] * 784)
    for x in range(0, 1000000):
        resp = client.predict(req)
        print(resp)
```
