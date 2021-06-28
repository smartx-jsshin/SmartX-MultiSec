#!/usr/bin/python3
import time
import os
import logging
import datetime
import decimal

import json
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable
from influxdb import InfluxDBClient

class DataTransfer:
    def __init__(self) -> None:
        super().__init__()

        # Initialize Logger
        self._logger = self._init_logger()

        # Load the configuration from the file
        self._cfg = self._load_config("config.post.json")
        self._post_cfg = self._cfg["post"]
        self._vcenter_cfg = self._cfg["v-center"]

        self._cache_cli = self._get_flow_cache_client(self._post_cfg["flow-db"])
        self._interval = self._post_cfg["transfer_interval"]
        self._id = "{}.{}".format(self._post_cfg["where"], self._post_cfg["name"])
        #
        self._logger.info("Initialization was completed")

    def _init_logger(self):
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
        
        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        _logger.addHandler(sh)

        fh = logging.FileHandler(filename="./data_transfer.log")
        fh.setFormatter(fm)
        sh.setLevel(logging.DEBUG)
        _logger.addHandler(fh)
        return _logger

    def _load_config(self, file_path):
        _file_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        with open(_file_abs_path, 'r') as stream:
            file_str = stream.read()
            if file_str:
                return json.loads(file_str)
            else:
                return None

    def _get_flow_cache_client(self, cache_cfg):
        _cache_cli = None
        
        if cache_cfg["type"] == "influxdb":
            _cache_cli = InfluxDBClient(host=cache_cfg["ipaddr"], 
                                        port=cache_cfg["port"], 
                                        username=cache_cfg["id"],
                                        password=cache_cfg["password"])
            # _create_db_if_not_exist(db_cli, cache_cfg["database"]) 
            self._logger.info("InfluxDB Client was initialized")

        else:
            self._logger.error("For flow cache, InfluxDB is only supported")
            exit(1)

        return _cache_cli

    def run(self):
        self._logger.info("Data Transfer module started")
        try:
            while True:
                _start_time = time.time()
                ts = decimal.Decimal((_start_time - self._interval) * (10 ** 9))

                # Retrieve expired flows from Flow cache (i.e., influxdb)
                _active_flows = self._get_flows_from_cache(ts, "active")
                _exp_flows = self._get_flows_from_cache(ts, "expired")

                if len(_active_flows) != 0 or len(_exp_flows) != 0:
                    # self._logger.debug(_exp_flows)
                    msg = self.formatting_msg(_active_flows, _exp_flows)
                    self.transfer_msg(msg)
                    self._logger.info("The transfered message: {}".format(msg))

                _end_time = time.time()
                _next_interval = self._interval - (_end_time - _start_time) 
                if _next_interval > 0:
                    time.sleep(_next_interval)

        except KeyboardInterrupt:
            self._logger.info("Terminated by keyboard interrupt")

    def _get_flows_from_cache(self, ts, flow_type):
        _cache_db_name = self._post_cfg["flow-db"]["database"]

        if flow_type == "active":
            _table_name = self._post_cfg["flow-db"]["table-map"]["active"]
        elif flow_type == "expired":
            _table_name = self._post_cfg["flow-db"]["table-map"]["expired"]

        _query = 'SELECT * FROM "{}" WHERE "time" > {}'.format(_table_name, ts)
        _res = self._cache_cli.query(_query, database=_cache_db_name)

        _flows = list(_res.get_points(measurement=_table_name))
        return _flows


    def formatting_msg(self, active_flows, expired_flows):
        _msg = {}
        # for f in flows:
        #     del f["time"]

        # _msg["flows"] = flows
        # _msg["where"] = "{}.{}".format(self._post_cfg["where"], self._post_cfg["name"])
        # _msg["time"] = int(datetime.datetime.utcnow().timestamp() * 1000000)

        _msg["flow.active"] = active_flows
        _msg["flow.expired"] = expired_flows

        return _msg

    def transfer_msg(self, msg):
        _vcenter_mq_url = "{}:{}".format(self._vcenter_cfg["message-queue"]["ipaddr"], 
                                                self._vcenter_cfg["message-queue"]["port"])
        _vcenter_mq_topic = self._vcenter_cfg["message-queue"]["topic-map"]["flow.measure"]

        try:
            encoded_msg = json.dumps(msg).encode('utf-8')
            producer = KafkaProducer(bootstrap_servers=[_vcenter_mq_url])
            producer.send(_vcenter_mq_topic, encoded_msg)
            producer.close()

        except NoBrokersAvailable as noBrokerExt:
            self._logger.error("Kafka Broker in Security Post is not accessible")
        

if __name__ == "__main__":
    transfer = DataTransfer()
    transfer.run()
