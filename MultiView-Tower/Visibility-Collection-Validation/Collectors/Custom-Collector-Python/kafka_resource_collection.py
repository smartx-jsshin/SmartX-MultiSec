#!/usr/bin/python3
import os
import logging

import json
from kafka import KafkaConsumer
from pymongo import MongoClient
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

def store_to_mongodb(mongo_col, msg):
    # Find the document having same field values "name", "where", "type"
    # Update all specs to the matching document
    matching_rule = dict()
    matching_rule["name"] = msg.pop("name")
    matching_rule["where"] = msg.pop("where")
    
    if mongo_col.find_one_and_update(filter=matching_rule, update={"$set": msg}):
        _logger.info("Updating MongoDB was successful: {}, {}".format(matching_rule, msg))
    else:
        _logger.info("Updating MongoDB was failed: {}, {}".format(matching_rule, msg))
    
        
def format_influxdb_msg(_msg, table_name):
    _formatted_msg = dict()
    _tags = dict()
    _fields = dict()
    
    tag_keys = ["name", "where", "tier"]

    for k, v in _msg.items():
        if k in tag_keys:
            _tags[k] = v
        elif k == "timestamp":
            _formatted_msg["time"] = v
        else:
            _fields[k] = v

    _formatted_msg["measurement"] = table_name
    _formatted_msg["tags"] = _tags
    _formatted_msg["fields"] = _fields

    return [_formatted_msg]

def store_to_influxdb(_db_client, _db_name, _msg):
    _db_list = _db_client.get_list_database()

    if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
        _logger.info("Create database: {}".format(_db_name))
        _db_client.create_database(_db_name)

    if _db_client.write_points(_msg, database=_db_name):
        _logger.info("Writing InfluxDB was successful: {}".format(_msg))
    else:
        _logger.info("Writing InfluxDB was failed: {}".format(_msg))
    

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.tower.collection.json")
    _config = load_setting(file_path)

    # Initialize Message Queue Client
    mq_cli = None
    _mq_config = _config["vCenter"]["message-queue"]
    if _mq_config["type"] == "kafka":
        kafka_url = "{}:{}".format(_mq_config["ipaddr"], _mq_config["port"])

        mq_cli = KafkaConsumer(_mq_config["topicMap"]["resource"],
                                group_id="multi-view.resource",
                                bootstrap_servers=[kafka_url])

    # Initialize Document DB Client
    ddb_cli = None
    _ddb_config = _config["vCenter"]["document-db"]
    if _ddb_config["type"] == "mongodb":
        ddb_cli = MongoClient(host=_ddb_config["ipaddr"], 
                                port=int(_ddb_config["port"]), 
                                username=_ddb_config["userId"], 
                                password=_ddb_config["userPassword"], 
                                authSource=_ddb_config["authDb"])
    else:
        _logger.error("A Document DB \"{}\" is not supported.".format(_ddb_config["type"]))
        exit()

    mvf_ddb = ddb_cli[_ddb_config["userDb"]]
    rstatus_col = mvf_ddb[_ddb_config["collectionMap"]["pvBoxStatus"]]

    # Initialize Timeseries DB Client
    tdb_cli = None
    _tdb_config = _config["vCenter"]["timeseries-db"]
    if _tdb_config["type"] == "influxdb":
        tdb_cli = InfluxDBClient(host=_tdb_config["ipaddr"], 
                                    port=_tdb_config["port"], 
                                    username=_tdb_config["id"],
                                    password=_tdb_config["password"])
    else:
        _logger.error("A Time-Series DB \"{}\" is not supported.".format(_tdb_config["type"]))
        exit()

    _tdb_db_name = _tdb_config["database"]
    _tdb_table_name = _tdb_config["measurementMap"]["resource.performance"]

    try:
        for message in mq_cli:
            msg_type = message.key.decode('utf-8')
            msg_val = json.loads(message.value.decode('utf-8'))

            if msg_type == "status":
                _logger.debug("status message is received: {}, {}, {}".format(msg_val["name"], msg_val["where"], msg_val["tier"]))
                store_to_mongodb(rstatus_col, msg_val)
                
            elif msg_type == "performance":
                _logger.debug("performance message is received: {}, {}, {}".format(msg_val["name"], msg_val["where"], msg_val["tier"]))
                _msg = format_influxdb_msg(msg_val, _tdb_table_name)
                store_to_influxdb(tdb_cli, _tdb_db_name, _msg)

    finally:
        ddb_cli.close()
        mq_cli.close()
        