# -*- encoding:utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
import argparse
import logging
import sys
import traceback

from eas_prediction.easyrec_request import EasyRecRequest
from eas_prediction.easyrec_predict_pb2 import PBFeature
from eas_prediction.easyrec_predict_pb2 import PBRequest

logging.basicConfig(
    level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(message)s')

try:
  from eas_prediction import PredictClient  # TFRequest
except Exception:
  logging.error('eas_prediction is not installed: pip install eas-prediction')
  sys.exit(1)


def build_request(table_cols, table_data, item_ids=None):
  request_pb = PBRequest()
  assert isinstance(table_data, list)
  try:
    for col_id in range(len(table_cols)):
      cname, dtype = table_cols[col_id]
      value = table_data[col_id]
      feat = PBFeature()
      if value is None:
        continue
      if dtype == 'STRING':
        feat.string_feature = value
      elif dtype in ('FLOAT', 'DOUBLE'):
        feat.float_feature = float(value)
      elif dtype == 'BIGINT':
        feat.long_feature = int(value)
      elif dtype == 'INT':
        feat.int_feature = int(value)

      request_pb.user_features[cname].CopyFrom(feat)
  except Exception:
    traceback.print_exc()
    sys.exit()
  request_pb.item_ids.extend(item_ids)
  return request_pb


def parse_table_schema(create_table_sql):
  create_table_sql = create_table_sql.lower()
  spos = create_table_sql.index('(')
  epos = create_table_sql[spos + 1:].index(')') + spos + 1
  cols = create_table_sql[(spos + 1):epos]
  cols = [x.strip().lower() for x in cols.split(',')]
  col_info_arr = []
  for col in cols:
    col = [k for k in col.split() if k != '']
    assert len(col) == 2
    col[1] = col[1].upper()
    col_info_arr.append(col)
  return col_info_arr


def send_request(req_pb, client, debug_level=0):
  req = EasyRecRequest()
  req.add_feed(req_pb, debug_level)
  tmp = client.predict(req)
  return tmp


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--endpoint',
      type=str,
      default=None,
      help='eas endpoint, such as 12345.cn-beijing.pai-eas.aliyuncs.com')
  parser.add_argument(
      '--service_name', type=str, default=None, help='eas service name')
  parser.add_argument(
      '--token', type=str, default=None, help='eas service token')
  parser.add_argument(
      '--table_schema',
      type=str,
      default=None,
      help='user feature table schema path, example: create table(user_id string, age bigint);')
  parser.add_argument(
      '--table_data',
      type=str,
      default=None,
      help='user feature table data path, content are user_feature values separated by ; , the number and types of feature values should match the definitions in table_schema')
  parser.add_argument('--item_lst', type=str, default=None, help='item list file path, content are item_ids, each in one line')

  args, _ = parser.parse_known_args()

  if args.endpoint is None:
    logging.error('--endpoint is not set')
    sys.exit(1)
  if args.service_name is None:
    logging.error('--service_name is not set')
    sys.exit(1)
  if args.token is None:
    logging.error('--token is not set')
    sys.exit(1)
  if args.table_schema is None:
    logging.error('--table_schema is not set')
    sys.exit(1)
  if args.table_data is None:
    logging.error('--table_data is not set')
    sys.exit(1)
  if args.item_lst is None:
    logging.error('--item_lst is not set')
    sys.exit(1)

  client = PredictClient(args.endpoint, args.service_name)
  client.set_token(args.token)
  client.init()

  with open(args.table_schema, 'r') as fin:
    create_table_sql = fin.read().strip()
  table_cols = parse_table_schema(create_table_sql)

  table_data = []
  with open(args.table_data, 'r') as fin:
    for line_str in fin:
      table_data.append(line_str.strip())

  assert len(table_cols) == len(table_data), 'user features[%s] not match with schema[%s]' % (table_data, table_cols)

  items = []
  with open(args.item_lst, 'r') as fin:
    for line_str in fin:
      items.append(line_str.strip())
 

  req = build_request(table_cols, table_data, item_ids=items)
  resp = send_request(req, client)
  logging.info(resp)
