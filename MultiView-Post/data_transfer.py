#!/usr/bin/python3
import time
import os
import logging
import datetime

import json
from kafka import KafkaProducer
from kafka.error import NoBrokersAvailable
from influxdb import InfluxDBClient

class DataTransfer:
    def __init__(self) -> None:
        super().__init__()

        # Initialize Logger
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
        
        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        sh.setLevel(logging.DEBUG)
        self._logger.addHandler(sh)

        fh = logging.FileHandler(filename="./data_transfer.log")
        fh.setFormatter(fm)
        sh.setLevel(logging.DEBUG)
        self._logger.addHandler(fh)

        # Load the configuration from the file
        self._cfg = self._load_setting("config.post.json")

        self._post_cfg = self._cfg["post"]
        self._cache_cfg = self._post_cfg["flow-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._expired_table_name = self._cache_cfg["table-map"]["expired"]
        self._interval = self._post_cfg["transfer_interval"]

        self._vcenter_cfg = self._cfg["v-center"]
        self._vcenter_mq_url = "{}:{}".format(self._vcenter_cfg["message-queue"]["ipaddr"], 
                                                self._vcenter_cfg["message-queue"]["port"])
        self._vcenter_mq_topic = self._vcenter_cfg["topic-map"]["flow.measure"]

        #
        self._last_cycle_time = 0
        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        self._logger.info("Initialization was completed")

    def _load_setting(self, file_path):
        _file_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        with open(_file_abs_path, 'r') as stream:
            file_str = stream.read()
            if file_str:
                return json.loads(file_str)
            else:
                return None

    def _get_flow_cache_client(self, cache_cfg):
        _db_cli = None
        
        if cache_cfg["type"] == "influxdb":
            _db_cli = InfluxDBClient(host=cache_cfg["ipaddr"], 
                                        port=cache_cfg["port"], 
                                        username=cache_cfg["id"],
                                        password=cache_cfg["password"])
            # _create_db_if_not_exist(db_cli, cache_cfg["database"]) 
            self._logger.info("InfluxDB Client was initialized")

        else:
            self._logger.error("For flow cache, InfluxDB is only supported")
            exit(1)

        return _db_cli

    def run(self):
        self._logger.info("Data Transfer module started")
        try:
            while True:
                _start_time = time.time()

                # Retrieve expired flows from Flow cache (i.e., influxdb)
                _exp_flows = self._get_expired_flows()

                if len(_exp_flows) != 0:
                    self._logger.debug(_exp_flows)
                    msg = self.formatting_msg(_exp_flows)
                    self.transfer_msg(msg)

                _end_time = time.time()
                _next_interval = self._interval - (_end_time - _start_time) 
                if _next_interval > 0:
                    time.sleep(_next_interval)

        except KeyboardInterrupt:
            self._logger.info("Terminated by keyboard interrupt")

        pass

    def _get_expired_flows(self):
        _query = 'SELECT * FROM "{}" WHERE "time" > now() - {}s'.format(self._expired_table_name, self._interval)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)

        _exp_flows = list(_res.get_points(measurement=self._expired_table_name))
        return _exp_flows

    def formatting_msg(self, flows):
        _msg = {}

        for f in flows:
            del f["time"]

        _msg["flows"] = flows
        _msg["point"] = "{}.{}".format(self._post_cfg["where"], self._post_cfg["name"])
        _msg["time"] = int(datetime.utcnow().timestamp() * 1000000)

        return _msg

    def transfer_msg(self, msg):
        try:
            encoded_msg = json.dumps(msg).encode('utf-8')
            producer = KafkaProducer(bootstrap_servers=[self._vcenter_mq_url])
            producer.send(self._vcenter_mq_topic, encoded_msg)
            producer.close()

        except NoBrokersAvailable as noBrokerExt:
            self._logger.error("Kafka Broker in Security Post is not accessible")
        

if __name__ == "__main__":
    transfer = DataTransfer()
    transfer.run()
