#!/usr/bin/env python
import sys
import logging
import time
import signal

import json
from pymongo import MongoClient
from kafka import KafkaConsumer, KafkaProducer


class KafkaMongoDBConsumer():
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        self.stop_flag = False
        self.config = self.load_config()

        kafka_url = self.config["kafka"]["broker_ip"] + ":" + self.config["kafka"]["broker_port"]
        self.consumer = KafkaConsumer(bootstrap_servers= kafka_url, 
            auto_offset_reset='earliest',
            group_id='mongodb-group',
            consumer_timeout_ms=1000
            )
        self.consumer.subscribe(self.config["kafka"]["topic_list"])

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def load_config(self):
        with open(config_file) as f:
            read_data = f.read()
            read_json = json.loads(read_data)
        return read_json

    def consume(self):
        # while not self.stop_flag:
        while not self.stop_flag:
            for message in self.consumer:
                print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                    message.offset, message.key,
                    message.value)
                    )
        self.consumer.close()

    def insert_docs_to_db(self, _docs):
        mongo_cfg = self.config["mongo"]

        if mongo_cfg.get("id") is not None and mongo_cfg.get("password") is not None:
            mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"],
                                    username=mongo_cfg["id"],
                                    password=mongo_cfg["password"],
                                    authSource=mongo_cfg["database"],
                                    authMechanism='SCRAM-SHA-256')
        else:
            mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"])

        db = mongo_client[mongo_cfg["database"]]

        db_col = mongo_cfg["collection_map"]["collector_name"]
        db.drop_collection(db_col)
        coll = db[db_col]
        coll.insert_many(_docs)
    
    def signal_handler(self, signal, frame):
        self.logger.info("Visibility Point {} was finished successfully".format(self.__class__.__name__))
        self.stop_flag = True
        self.consumer.close()
        sys.exit(0)

        
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
        )

    if len(sys.argv) == 1:
        config_file = "config.json"
    elif len(sys.argv) == 2:
        # Load configuration from a file passed by second argument in the command
        config_file = sys.argv[1]
    else:
        exit(1)

    mongoDbConsumer = KafkaMongoDBConsumer()
    mongoDbConsumer.consume()
