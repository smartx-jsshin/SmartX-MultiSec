#!/usr/bin/python3
import os
import logging
import copy

import json
from kafka import KafkaConsumer
from pymongo import MongoClient


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

def store_box_tenant(mongo_col, msg):
    matching_rule = dict()
    matching_rule["name"] = msg["name"]
    matching_rule["where"] = msg["where"]
    matching_rule["tier"] = msg["tier"]
    box_tnt = msg.pop("tenant")

    if mongo_col.find_one_and_update(filter=matching_rule, update={"$set": {"tenant": box_tnt}}):
        _logger.info("Updating BoxAlloc table was successful: {}, {}".format(matching_rule, box_tnt))
    else:
        new_msg = matching_rule
        new_msg["tenant"] = box_tnt
        mongo_col.insert(new_msg)
        _logger.info("Insert a new doc to BoxAlloc table: {}".format(new_msg))

def store_to_mongodb(mongo_col, msg):
    # Find the document having same field values "name", "where", "type"
    # Update all specs to the matching document
    matching_rule = dict()
    matching_rule["name"] = msg.pop("name")
    matching_rule["where"] = msg.pop("where")
    matching_rule["tier"] = msg.pop("tier")

    # Get the status of parent box (physical box)
    parent = copy.deepcopy(matching_rule["where"]).split(".")
    parent_name = parent.pop()
    parent_where = ".".join(parent)

    parent_box = mongo_col.find_one({"name": parent_name, "where": parent_where})
    # if the parent box is in INACTIVE status, then the virtual box should have "INACTIVE" status
    if not parent_box or parent_box["status"] == 0:
        msg["status"] = 0

    if mongo_col.find_one_and_update(filter=matching_rule, update={"$set": msg}):
        _logger.info("Updating pvBoxStatus table was successful: {}, {}".format(matching_rule, msg))
    else:
        for k, v in matching_rule.items():
            msg[k] = v
        mongo_col.insert(msg)
        _logger.info("Insert a new doc to pvBoxStatus table: {}".format(msg))
    

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.tower.collection.json")
    _config = load_setting(file_path)

    # Initialize Message Queue Client
    mq_cli = None
    _mq_config = _config["vCenter"]["message-queue"]
    if _mq_config["type"] == "kafka":
        kafka_url = "{}:{}".format(_mq_config["ipaddr"], _mq_config["port"])
        kafka_topic = _mq_config["topicMap"]["slicing.status"]

        mq_cli = KafkaConsumer(kafka_topic,
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
    sstatus_col = mvf_ddb[_ddb_config["collectionMap"]["pvBoxStatus"]]
    box_alloc_col = mvf_ddb[_ddb_config["collectionMap"]["boxAlloc"]]

    try:
        _logger.info("Start consuming messages from message queue: {} / {}".format(kafka_url, kafka_topic))
        for message in mq_cli:
            msg_type = message.key.decode('utf-8')
            msg_val = json.loads(message.value.decode('utf-8'))

            if msg_type == "status":
                _logger.info("status message is received: {}, {}, {}".format(msg_val["name"], msg_val["where"], msg_val["tier"]))
                store_box_tenant(box_alloc_col, msg_val)
                store_to_mongodb(sstatus_col, msg_val)
                
    finally:
        ddb_cli.close()
        mq_cli.close()
        