#!/usr/bin/env python
import threading, logging, time
import multiprocessing
from pymongo import MongoClient

from kafka import KafkaConsumer, KafkaProducer


class Consumer(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.stop_event = multiprocessing.Event()
        
    def stop(self):
        self.stop_event.set()
        
    def run(self):
        consumer = KafkaConsumer(bootstrap_servers='localhost:9092',
                                 auto_offset_reset='earliest',
                                 consumer_timeout_ms=1000)
        consumer.subscribe(['my-topic'])

        while not self.stop_event.is_set():
            for message in consumer:
                print(message)
                if self.stop_event.is_set():
                    break

        consumer.close()

    def insert_docs_to_db(_docs):
        mongo_cfg = config["mongo"]

        if mongo_cfg.get("id") is not None and mongo_cfg.get("password") is not None:
            mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"],
                                    username=mongo_cfg["id"],
                                    password=mongo_cfg["password"],
                                    authSource=mongo_cfg["database"],
                                    authMechanism='SCRAM-SHA-256')
        else:
            mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"])

        db = mongo_client[mongo_cfg["database"]]

        db_col = mongo_cfg["collection_map"][collector_name]
        db.drop_collection(db_col)
        coll = db[db_col]
        coll.insert_many(_docs)
        
        
def main():
    tasks = [
        Producer(),
        Consumer()
    ]

    for t in tasks:
        t.start()

    time.sleep(10)
    
    for task in tasks:
        task.stop()

    for task in tasks:
        task.join()
        
        
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
        )
    main()