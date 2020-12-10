#!/usr/bin/python3

import os
import logging

import yaml
import json
from kafka import KafkaProducer
from influxdb import InfluxDBClient

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(fm)
_logger.addHandler(sh)

def load_setting(_file_path):
    with open(_file_path, 'r') as stream:
        try:
            file_str = stream.read()
            print("Parse YAML from the file: \n" + file_str)
            if file_str:
                return yaml.load(file_str, Loader=yaml.FullLoader)
            else:
                return None
        except yaml.YAMLError as exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                print(("YAML Format Error: " + _file_path
                                    + " (Position: line %s, column %s)" %
                                    (mark.line + 1, mark.column + 1)))
                return None

def get_latest_db_records(_client, _db_name, _table_name):
    _client.switch_database(_db_name)
    res = _client.query("SELECT * FROM {}".format(_table_name))

    #rs = cli.query("SELECT * from cpu")
    #points = list(rs.get_points(measurement='cpu', tags={'host_name': 'influxdb.com'}))
    return res

def clear_latest_db_records(_client, _db_name, _table_name):
    _client.switch_database(_db_name)
    _client.drop_measurement(_table_name)

def reformat_msg(_org_records):
    _tags_set = set()
    for _, tags in _org_records.keys():
        _tags_set.add(tags)

    pbox_records = list()
    for _t in _tags_set:
        _org_records.get_points(tags=_t)

    return pbox_records

# def store_history_db_records(_client, _db_name, _records):
#     _client.switch_database(_db_name)
#     _client.write_points(_records)

# def publish_msg(_mq_url, _msg):
#     pass

if __name__ == "__main__":

    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "post.yaml")
    _setting = load_setting(file_path)
    _post_setting = _setting["post"]
    _vcenter_setting = _setting["vCenter"]

    kafka_url = "{}:{}".format(_vcenter_setting["kafka"]["ipaddr"], _vcenter_setting["kafka"]["port"])

    # To consume latest messages and auto-commit offsets
    db_client = InfluxDBClient(host=_post_setting["influxdb"]["ipaddr"], 
                                port=_post_setting["influxdb"]["port"], 
                                username=_post_setting["influxdb"]["id"],
                                password=_post_setting["influxdb"]["password"])

    get_db_records(db_client, _post_setting)

    # Retrieve all records from the latest table in InfluxDB
    # Clear the latest table
    # Reformat messages by summarizing the retrived records
    # Transfer the reformatted records to the message queue of visibility center
    # Store the original records to backup database