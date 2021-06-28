#!/usr/bin/env python3

import os
import logging
import json
from kafka import KafkaConsumer
from influxdb import InfluxDBClient

class TowerFlowCollection:
    def __init__(self) -> None:
        super().__init__()
        pass

        # Initialize Logger
        self._logger = self._init_logger()

        # Load the configuration from the file
        self._cfg = self._load_config("config.tower.collection.json")

        self._tower_cfg = self._cfg["tower"]
        self._mq_cfg = self._tower_cfg["message-queue"]

        self._cache_cfg = self._tower_cfg["timeseries-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._active_flow_table = self._cache_cfg["table-map"]["flow.measure.active"]
        self._expired_flow_table = self._cache_cfg["table-map"]["flow.measure.expired"]

        #
        self._mq_cli = self._get_message_queue_client(self._mq_cfg)
        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        #
        self._tag_map = ["where", "dip", "sip", "dport", "sport", "proto"]

        self._field_map = ["start_ts", "last_ts", "pkt_cnt", 
                    "pkt_bytes_total", "pkt_bytes_sqr_total", "pkt_bytes_min", "pkt_bytes_max",
                    "ipat_total", "ipat_sqr_total", "ipat_min", "ipat_max",
                    "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

        self._logger.info("Initialization was completed")

    def _init_logger(self) -> logging.Logger:
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
        
        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        _logger.addHandler(sh)

        # fh = logging.FileHandler(filename="./flow_data_collection.log")
        # fh.setFormatter(fm)
        # sh.setLevel(logging.DEBUG)
        # _logger.addHandler(fh)
        return _logger

    def _load_config(self, file_path):
        _file_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        with open(_file_abs_path, 'r') as stream:
            file_str = stream.read()
            if file_str:
                return json.loads(file_str)
            else:
                return None

    def _get_message_queue_client(self, mq_cfg):
        _mq_url = "{}:{}".format(mq_cfg["ipaddr"], 
                                mq_cfg["port"])

        _mq_cli = KafkaConsumer(mq_cfg["topic-map"]["flow.measure"],
                                group_id="multi-sec",
                                bootstrap_servers=[_mq_url])

        return _mq_cli

    def _get_flow_cache_client(self, cache_cfg):
        _db_cli = None
        
        if cache_cfg["type"] == "influxdb":
            _db_cli = InfluxDBClient(host=cache_cfg["ipaddr"], 
                                        port=cache_cfg["port"], 
                                        username=cache_cfg["id"],
                                        password=cache_cfg["password"])
            self._create_db_if_not_exist(_db_cli, cache_cfg["database"]) 
            self._logger.info("InfluxDB Client was initialized")

        else:
            self._logger.error("For flow cache, InfluxDB is only supported")
            exit(1)

        return _db_cli

    def _create_db_if_not_exist(self, _db_client, _db_name):
        _db_list = _db_client.get_list_database()

        if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
            self._logger.info("Create database: {}".format(_db_name))
            _db_client.create_database(_db_name)

    def run(self):
        self._logger.info("Data Collection module in Tower started")
        try:
            for message in self._mq_cli:
                formatted_msg = self.format_influx_msg(message)
                self._store_messages(formatted_msg)
                self._logger.info("Stored data: {}".format(formatted_msg))
                
        except KeyboardInterrupt:
            self._logger.info("Terminated by Keyboard Interrupt")
            
    def format_influx_msg(self, message):
        _influx_msgs = []

        _decoded_msg = json.loads(message.value.decode('utf-8'))
        self._logger.debug(_decoded_msg)
        
        for f in _decoded_msg["flow.active"]:
            _formatted_flow = self._from_json(f)
            _formatted_flow["measurement"] = self._active_flow_table
            _influx_msgs.append(_formatted_flow)

        for f in _decoded_msg["flow.expired"]:
            _formatted_flow = self._from_json(f)
            _formatted_flow["measurement"] = self._expired_flow_table
            _influx_msgs.append(_formatted_flow)
        
        return _influx_msgs
    
    def _from_json(self, flow_json):
        _formatted_msg = dict()

        _tags = {}
        for _t in self._tag_map:
            _tags[_t] = str(flow_json[_t])
        _formatted_msg["tags"] = _tags
        
        _fields = {}
        for _f in self._field_map:
            _fields[_f] = flow_json[_f]
        _formatted_msg["fields"] = _fields

        return _formatted_msg 

    def _store_messages(self, msgs):
        self._cache_cli.write_points(msgs, database=self._cache_db_name, time_precision='u')

if __name__ == "__main__":
    flow_collector = TowerFlowCollection()
    flow_collector.run()
    pass