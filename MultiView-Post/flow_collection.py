import os
import logging

import json
from kafka import KafkaConsumer
from influxdb import InfluxDBClient


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(fm)
_logger.addHandler(sh)

def load_setting(_file_path):
    with open(_file_path, 'r') as stream:
        file_str = stream.read()
        if file_str:
            return json.loads(file_str)
        else:
            return None

def format_influx_msg(_msg, table_name):
    _msgs = list()

    # key = _msg.key.decode('utf-8')
    value = json.loads(_msg.value.decode('utf-8'))

    for f in value["flows"]:
        _formatted_msg = dict()
        _formatted_msg["measurement"] = table_name

        _tags = {}
        _tags["pbox"] = value["pbox"]
        _tags["net_point"] = value["net_point"]
        _tags["func"] = value["func"]
        _formatted_msg["tags"] = _tags

        _formatted_msg["time"] = value["timestamp"] 

        flows = f.split(",")
        _fields = dict()
        _fields["dest_ip"] = flows[0]
        _fields["src_ip"] = flows[1]
        _fields["dest_port"] = flows[2]
        _fields["src_port"] = flows[3]
        _fields["l4_proto"] = flows[4]
        _fields["flow_cnt"] = flows[5]
        _fields["flow_bytes"] = flows[6]
        _formatted_msg["fields"] = _fields

        _msgs.append(_formatted_msg)

    return _msgs


def store_collected_messages(_db_client, _db_name, _msg):
    _db_list = _db_client.get_list_database()

    if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
        _logger.info("Create database: {}".format(_db_name))
        _db_client.create_database(_db_name)

    _db_client.write_points(_msg, database=_db_name)
    

if __name__ == "__main__":

    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "post.yaml")
    _setting = load_setting(file_path)
    _post_setting = _setting["post"]
    _vcenter_setting = _setting["vCenter"]

    mq_cli = None
    db_cli = None

    if _post_setting["message-queue"]["type"] == "kafka":
        kafka_url = "{}:{}".format(_post_setting["message-queue"]["ipaddr"], _post_setting["message-queue"]["port"])

        # To consume latest messages and auto-commit offsets
        mq_cli = KafkaConsumer(_post_setting["message-queue"]["topicMap"]["flow.measure"],
                                group_id="multi-sec",
                                bootstrap_servers=[kafka_url])

    if _post_setting["timeseries-db"]["type"] == "influxdb":
        db_cli = InfluxDBClient(host=_post_setting["timeseries-db"]["ipaddr"], 
                                    port=_post_setting["timeseries-db"]["port"], 
                                    username=_post_setting["timeseries-db"]["id"],
                                    password=_post_setting["timeseries-db"]["password"])

    for message in mq_cli:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        # print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                     message.offset, message.key,
        #                                     message.value))
    
        formatted_msg = format_influx_msg(message, _post_setting["timeseries-db"]["tableMap"]["latest"])
        _logger.info(formatted_msg)
        store_collected_messages(db_cli, _post_setting["timeseries-db"]["database"], formatted_msg)
    