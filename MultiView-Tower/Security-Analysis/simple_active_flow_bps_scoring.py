#!/usr/bin/env python3

import os
import logging
import json
import time
import decimal
import re

from influxdb import InfluxDBClient
from pymongo import MongoClient


class SimpleActiveFlowBPFScoring:
    def __init__(self, cfg_file_path) -> None:
        # initialize logger
        self._logger = self._init_logger()

        # read the configuration file
        self._cfg = self._load_config(cfg_file_path)
        self._cache_cfg = self._cfg["vCenter"]["flow-db"]
        self._data_store_cfg = self._cfg["vCenter"]["document-db"]

        # source_db_interface -> influxdb
        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        # destination_db_interface -> mongodb
        self._data_store_cli = self._get_data_store_client(self._data_store_cfg)

        self._interval_sec = 1
        self._query_time_offset = 0.5

    def _init_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')

        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        return logger

    def _load_config(self, file_path) -> dict:
        _file_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        with open(_file_abs_path, 'r') as stream:
            file_str = stream.read()
            if file_str:
                return json.loads(file_str)
            else:
                return None

    def _get_flow_cache_client(self, cache_cfg) -> InfluxDBClient:
        if cache_cfg["type"] == "influxdb":
            _cache_cli = InfluxDBClient(host=cache_cfg["ipaddr"], 
                                        port=cache_cfg["port"], 
                                        username=cache_cfg["id"],
                                        password=cache_cfg["password"])
            self._create_db_if_not_exist(_cache_cli, cache_cfg["database"]) 
            self._logger.info("InfluxDB Client was initialized")
            return _cache_cli

        else:
            self._logger.error("For flow cache, InfluxDB is only supported")
            exit(1)
        
    def _create_db_if_not_exist(self, _db_client, _db_name):
        _db_list = _db_client.get_list_database()

        if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
            self._logger.info("Create database: {}".format(_db_name))
            _db_client.create_database(_db_name)

    def _get_data_store_client(self, ds_cfg) -> MongoClient:
        if ds_cfg["type"] == "mongodb":
            _store_cli = MongoClient(host=ds_cfg["ipaddr"], 
                            port=int(ds_cfg["port"]), 
                            username=ds_cfg["userId"], 
                            password=ds_cfg["userPassword"], 
                            authSource=ds_cfg["authDb"])

            return _store_cli[ds_cfg["multiviewDb"]][ds_cfg["collectionMap"]["multiSecBoxes"]]

        else:
            self._logger.error("For MVF data store, MongoDB is only supported")
            exit(1)

    def run(self):
        # repeat in specific seconds
        try:
            while True:
                _key_features_per_boxes = {}

                _start_time = time.time()
                ts = decimal.Decimal((_start_time - self._query_time_offset) * (10 ** 9))

                # Retreive all entries from flow cache
                flow_entities = self._get_bps_features(self._cache_cfg["table-map"]["flow.measure.staged"], ts)

                if len(flow_entities) > 0:
                    self._clear_flow_table(self._cache_cfg["table-map"]["flow.measure.staged"], ts)

                    # For every entry
                    #   add bps -> box
                    for f in flow_entities:
                        where = f["where"]
                        bps = int(f["pkt_bytes_per_sec"]) * 8

                        if where in _key_features_per_boxes:
                            _key_features_per_boxes[where] = _key_features_per_boxes[where] + bps
                        else:
                            _key_features_per_boxes[where] = bps

                    # For every box
                    #   bps to score
                    #   store the score to MVF store
                    for k, v in _key_features_per_boxes.items():
                        sec_level = self._scoring(v)
                        self._store_sec_level(k, sec_level)

                _end_time = time.time()
                _next_interval = self._interval_sec - (_end_time - _start_time)
                if _next_interval > 0:
                    time.sleep(_next_interval)

        except KeyboardInterrupt:
            self._logger.info("Keyboard Interrupted")
            exit(1)

    def _get_all_entities(self, table_name, ts):
        _query = 'SELECT * FROM "{}" WHERE "time" < {}'.format(table_name, ts)
        _queried = self._cache_cli.query(_query, database=self._cache_cfg["database"])
        _res = list(_queried.get_points(measurement=table_name))
        return _res

    def _get_bps_features(self, table_name, ts):
        _query = 'SELECT "where", "pkt_bytes_per_sec" FROM "{}" WHERE "time" < {}'.format(table_name, ts)
        _queried = self._cache_cli.query(_query, database=self._cache_cfg["database"])
        _res = list(_queried.get_points(measurement=table_name))
        return _res

    def _clear_flow_table(self, table_name, ts):
        _query = 'DELETE FROM "{}" WHERE time < {}'.format(table_name, ts)
        _res = self._cache_cli.query(_query, database=self._cache_cfg["database"])
        return _res

    def _scoring(self, features):
        res = int(features / (10 ** 8))
        if res > 100:
            res = 100
        return res

    def _store_sec_level(self, location, sec_level):
        _, _, box = location.rpartition(".")
        matching_rule = dict()
        matching_rule["name"] = re.compile(box, re.IGNORECASE)
        matching_rule["where"] = re.compile(location, re.IGNORECASE)

        res = self._data_store_cli.update_one(filter=matching_rule, update={'$set': {'securityLevel': str(sec_level)}})

        if res.acknowledged:
            self._logger.info("Updated Successfully. Name: {} / Where: {} / SecurityLevel: {}".format(box, location, sec_level))

if __name__ == "__main__":
    # cfg_file_path = "./config.json"
    cfg_file_path = "../MultiView-Configurations/k-one/config.json"
    scorer = SimpleActiveFlowBPFScoring(cfg_file_path)
    scorer.run()