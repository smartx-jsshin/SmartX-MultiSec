#!/usr/bin/python3

import os
import json
import logging
import time
import decimal

from influxdb import InfluxDBClient

class ActiveFlowCache:
    def __init__(self) -> None:
        super().__init__()

        # Initialize Logger
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
        
        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        self._logger.addHandler(sh)

        fh = logging.FileHandler(filename = "./flow_cache_active.log")
        fh.setFormatter(fm)
        fh.setLevel(logging.DEBUG)
        self._logger.addHandler(fh)

        # Load the configuration from a file
        _cfg = self._load_setting("../config.post.json")
        self._post_cfg = _cfg["post"]

        self._cache_cfg = self._post_cfg["flow-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._raw_table_name = self._cache_cfg["table-map"]["raw"]
        self._active_table_name = self._cache_cfg["table-map"]["active"]
        self._interval = self._cache_cfg["cache_policy"]["active_polling_interval"]
        self._query_time_offset = 0.5

        # Initialize InfluxDB Client to access flow cache
        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        # Define InfluxDB Message Format
        self._tag_map = ["where", "dip", "sip", "dport", "sport", "proto"]

        self._field_map = ["start_ts", "last_ts", "pkt_cnt", 
                    "pkt_bytes_total", "pkt_bytes_sqr_total", "pkt_bytes_min", "pkt_bytes_max",
                    "ipat_total", "ipat_sqr_total", "ipat_min", "ipat_max",
                    "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]
                
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

        return _db_cli

    def run(self):
        self._logger.info("Flow Cache Manager - Active Flows started")
        _last_ts = 0
        try:
            while True:
                _start_time = time.time()
                _cur_ts = decimal.Decimal((_start_time - self._query_time_offset) * (10 ** 9))
                
                _raw_flows = self._read_all_flows(self._raw_table_name, _cur_ts)

                if len(_raw_flows) != 0:
                    self._logger.debug("raw flows: {}". format(_raw_flows))
                    self._delete_all_flows(self._raw_table_name, _cur_ts)
                    _raw_flows = self._aggregate_raw_flows(_raw_flows)
                    self._logger.debug("combined raw flows: {}".format(_raw_flows))

                    _active_flows = self._read_all_flows(self._active_table_name, _cur_ts)
                    self._logger.debug("existing active flows: {}". format(_active_flows))

                    _new_active_flows = self._combine_fields_active_to_raw(_active_flows, _raw_flows)
                    self._logger.debug("aggreagted active flows: {}". format(_new_active_flows))

                    _msg = self._format_influx_msgs(_new_active_flows, self._active_table_name)
                    self._delete_flows_matching_tuples(_msg, self._active_table_name)

                    self._cache_cli.write_points(_msg, database=self._cache_db_name, time_precision='u')
                    self._logger.info("Stored to active flow cache: {}".format(_msg))
                
                # _last_ts = _cur_ts
                _end_time = time.time()
                _next_interval = self._interval - (_end_time - _start_time)
                if _next_interval > 0:
                    time.sleep(_next_interval)
                
        except KeyboardInterrupt:
            self._logger.info("Terminated by keyboard interrupt")

    def _read_all_flows(self, table_name, cur_ts):
        _query = 'SELECT * FROM "{}" WHERE time <= {}'.format(table_name, cur_ts)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)

        _flows = list(_res.get_points(measurement=table_name))
        return _flows

    def _delete_all_flows(self, table_name, cur_ts):
        _query = 'DELETE FROM "{}" WHERE time <= {}'.format(table_name, cur_ts)
        self._cache_cli.query(_query, database=self._cache_db_name)
        # self._cache_cli.delete_series(database=self._cache_db_name, measurement=table_name)

    def _aggregate_raw_flows(self, raw_flows):
        _aggregated_dict = {}
        self._logger.info("# raw flows {}".format(len(raw_flows)))
        for rf in raw_flows:
            # raw_flows.remove(rf)

            _tags = {}
            for _tkey in self._tag_map:
                _tags[_tkey] = rf[_tkey]
            _flow_id = json.dumps(_tags)

            _matched = _aggregated_dict.get(_flow_id, None)
            if _matched:
                self._logger.debug("HIT: {}".format(_flow_id))
                self._combine_fields_of_two_flows(_matched, rf)
            else:
                _fields = {}
                for _fkey in self._field_map:
                    _fields[_fkey] = rf[_fkey]
                # _fields["time"] = rf["time"]
                _aggregated_dict[_flow_id] = _fields
        # self._logger.info("# aggregated dict {}".format(len(_aggregated_dict)))

        _aggregated_list = []

        for k, v in _aggregated_dict.items():
            _tags = json.loads(k)

            _tags.update(v)
            _aggregated_list.append(_tags)

        # self._logger.info("# aggregated list {}".format(len(_aggregated_dict)))


        return _aggregated_list


    def _combine_fields_active_to_raw(self, active_flow, raw_flows):
        for rf in raw_flows:

            for af in active_flow:

                if rf["where"] == af["where"] and \
                    rf["dip"] == af["dip"] and rf["sip"] == af["sip"] and \
                    rf["dport"] == af["dport"] and rf["sport"] == af["sport"] and \
                    rf["proto"] == af["proto"]:

                    if rf["last_ts"] - af["start_ts"] > 18000000000:
                        continue
                    active_flow.remove(af)
                    self._combine_fields_of_two_flows(rf, af)

        return raw_flows
    
    def _combine_fields_of_two_flows(self, target, base):
        ipat = None
        if target["start_ts"] > base["last_ts"]:
            ipat = target["start_ts"] - base["last_ts"]
            self._logger.info("target[start_ts] {} / base[last_ts] {} / ipat {}".format(target["start_ts"], base["last_ts"], ipat))

        elif target["last_ts"] < base["start_ts"]:
            ipat = base["start_ts"] - target["last_ts"]
            self._logger.info("target[last_ts] {} / base[start_ts] {} / ipat {}".format(target["last_ts"], base["start_ts"], ipat))

        else:
            ipat = target["start_ts"] - base["last_ts"]
            self._logger.warn("ipat is lower than zero: target[start_ts] {} / base[last_ts] {} / ipat {}".format(target["start_ts"], base["last_ts"], ipat))

        if ipat <= 0:
            self._logger.warn("ipat is lower than zero: {}".format(ipat))
            ipat = ipat * -1

        for k in self._field_map:
            k_tok = k.split("_")
            k_suffix = k_tok[-1]

            if ipat > 0 and "ipat" in k_tok:
                if "sqr" in k_tok:
                    target[k] += (ipat ** 2)
                elif target[k] == 0:
                    target[k] = ipat
                elif k_suffix in ["total"]:
                    target[k] = target[k] + ipat
                elif k_suffix in ["min"]:
                    if target[k] > ipat: target[k] = ipat
                elif k_suffix in ["max"]:
                    if target[k] < base[k]: target[k] = ipat

            if k_suffix in ["cnt", "total"]:
                target[k] = target[k] + base[k]
            elif k_suffix in ["min"]:
                if base[k] > 0 and target[k] > base[k]: target[k] = base[k]
            elif k_suffix in ["max"]:
                if base[k] > 0 and target[k] < base[k]: target[k] = base[k]
            elif k == "start_ts":
                if target[k] > base[k]: target[k] = base[k]
            elif k == "last_ts":
                if target[k] < base[k]: target[k] = base[k]
            else:
                self._logger.debug("Unknwon Key in field_map: {}".format(k))
        
        # if target["time"] < base["time"]:
        #     target["time"] = base["time"]


    def _format_influx_msgs(self, flows, table_name):
        _msgs = []

        for f in flows:
            _msg = {}
            _msg["measurement"] = table_name
            # _msg["time"] = f["time"]
            
            _tags = {}
            for _tkey in self._tag_map:
                _tags[_tkey] = f[_tkey]
            _msg["tags"] = _tags

            _fields = {}
            for _fkey in self._field_map:
                _fields[_fkey] = f[_fkey]
            _msg["fields"] = _fields

            _msgs.append(_msg)

        return _msgs

    def _delete_flows_matching_tuples(self, flows, table_name):
        for f in flows:
            self._cache_cli.delete_series(database=self._cache_db_name, 
                                        measurement=table_name, 
                                        tags=f["tags"])


if __name__ == "__main__":
    active_cache_mgr = ActiveFlowCache()
    active_cache_mgr.run()
