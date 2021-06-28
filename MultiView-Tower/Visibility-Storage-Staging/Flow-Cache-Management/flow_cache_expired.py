#!/usr/bin/python3

import os
import json
import logging
import time
import decimal

from influxdb import InfluxDBClient

class ExpiredFlowCache:
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
        
        fh = logging.FileHandler(filename="./flow_cache_expired.log")
        fh.setFormatter(fm)
        fh.setLevel(logging.DEBUG)
        self._logger.addHandler(fh)

        # Load the configuration from a file
        _cfg = self._load_setting("../config.post.json")
        self._post_cfg = _cfg["post"]

        self._cache_cfg = self._post_cfg["flow-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._active_table_name = self._cache_cfg["table-map"]["active"]
        self._expired_table_name = self._cache_cfg["table-map"]["expired"]
        self._interval = self._cache_cfg["cache_policy"]["expired_polling_interval"]
        self._idle_timeout = self._cache_cfg["cache_policy"]["idle_timeout"]
        self._query_time_offset = 0.5

        # Initialize InfluxDB Client to access flow cache
        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        # Define InfluxDB Message Format
        self._tag_map = ["point", "dip", "sip", "dport", "sport", "proto"]

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
        self._logger.info("Flow Cache Manager - Expired Flows started")
        try:
            while True:
                _start_time = time.time()
                
                # Get IDLE Flows
                # Remove IDLE Flows

                # Get ALL Remaining Flows
                # Find flows having FIN CNT > 0
                # Find Pair Flows

                ts = decimal.Decimal((_start_time - self._idle_timeout) * (10 ** 9))

                _idle_flows = self._read_idle_flows(ts)
                if len(_idle_flows) > 0:
                    _msg = self._format_influx_msgs(_idle_flows, self._expired_table_name)
                    self._cache_cli.write_points(_msg, database=self._cache_db_name, time_precision='u')
                    self._delete_idle_flows(ts)

                _fin_flows = self._read_flows_with_fin()
                if len(_fin_flows):
                    self._delete_fin_flows(_fin_flows)
                    _msg = self._format_influx_msgs(_fin_flows, self._expired_table_name)
                    self._cache_cli.write_points(_msg, database=self._cache_db_name, time_precision='u')


                # _active_flows = self._read_all_flows(self._active_table_name)
                # if len(_active_flows) != 0:
                #     self._logger.debug("active flows: {}". format(_active_flows))
                #     tmp = time.time()
                #     self._logger.info("Elapsed Time for reading active flows: {}".format(tmp - _start_time))


                #     expired_flows = self.filter_expired_flows(_active_flows)
                #     self._logger.debug("expired_flows: {}".format(expired_flows))
                #     tmp = time.time()
                #     self._logger.info("Elapsed Time for filtering active flows: {}".format(tmp - _start_time))

                #     if len(expired_flows) > 0:
                #         _msg = self._format_influx_msgs(expired_flows, self._expired_table_name)
                #         self._logger.debug("formatted influx messages: {}".format(_msg))
                #         tmp = time.time()
                #         self._logger.info("Elapsed Time for formatting messages: {}".format(tmp - _start_time))

                #         self._delete_flows_matching_tuples(_msg, self._active_table_name)
                #         tmp = time.time()
                #         self._logger.info("Elapsed Time for deleting active flows: {}".format(tmp - _start_time))

                #         self._cache_cli.write_points(_msg, database=self._cache_db_name, time_precision='u')
                #         tmp = time.time()
                #         self._logger.info("Elapsed Time for storing expired flows: {}".format(tmp - _start_time))

                #         self._logger.info("Expire inactive flows successfully. # of Expired flows: {}".format(len(expired_flows)))

                _end_time = time.time()
                _next_interval = self._interval - (_end_time - _start_time)
                if _next_interval > 0:
                    time.sleep(_next_interval)
                
        except KeyboardInterrupt:
            self._logger.info("Terminated by keyboard interrupt")

    def _read_idle_flows(self, ts):
        _query = 'SELECT * FROM "{}" WHERE time < {}'.format(self._active_table_name, ts)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)
        _flows = list(_res.get_points(measurement=self._active_table_name))
        return _flows

    def _delete_idle_flows(self, ts):
        _query = 'DELETE FROM "{}" WHERE time < {}'.format(self._active_table_name, ts)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)
        return _res

    def _read_flows_with_fin(self):
        _query = 'SELECT * FROM "{}" WHERE tcp_fin_cnt > 0'.format(self._active_table_name)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)
        _flows = list(_res.get_points(measurement=self._active_table_name))
        return _flows

    def _delete_fin_flows(self, fin_flows):
        for fin_flow in fin_flows:
            flow_tags = {}
            for t in self._tag_map:
                flow_tags[t] = fin_flow[t]
            _query = 'DELETE FROM "{}" WHERE point=$point AND dip=$dip AND sip=$sip AND dport=$dport AND sport=$sport AND proto=$proto'.format(self._active_table_name)
            _res = self._cache_cli.query(_query, bind_params=flow_tags, database=self._cache_db_name)

    def _format_influx_msgs(self, flows, table_name):
        _msgs = []

        for f in flows:
            _msg = {}
            _msg["measurement"] = table_name
            
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

    # def _read_all_flows(self, table_name):
    #     _query = 'SELECT * FROM "{}"'.format(table_name)
    #     _res = self._cache_cli.query(_query, database=self._cache_db_name)

    #     _raw_flows = list(_res.get_points(measurement=table_name))
    #     return _raw_flows

    # def filter_expired_flows(self, active_flows):
    #     _expired_flows = []
    #     _expired_flows += self._get_idle_flows(active_flows)
    #     _expired_flows += self._get_fin_flows(active_flows)
    #     _expired_flows += self._find_pairs(_expired_flows, active_flows)
    #     return _expired_flows

    # def _get_idle_flows(self, candidates):
    #     _now_in_usec = int(datetime.datetime.utcnow().timestamp() * 1000000)
    #     _idle_timeout_in_usec = self._idle_timeout * 1000000

    #     _expired_flows = []
    #     for f in candidates:
    #         flow_last_arrival_time = int(datetime.datetime.strptime(f["time"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000000)
    #         idle_time = _now_in_usec - flow_last_arrival_time
    #         self._logger.debug("Idle time since the last packet: {}".format(idle_time // 1000000))

    #         if idle_time > _idle_timeout_in_usec:
    #             candidates.remove(f)
    #             _expired_flows.append(f)

    #     return _expired_flows
    
    # def _get_fin_flows(self, candidates):
    #     _expired_flows = []
    #     for f in candidates:
    #         if f["tcp_fin_cnt"] > 0:
    #             candidates.remove(f)
    #             _expired_flows.append(f)
    #     return _expired_flows

    # def _find_pairs(self, targets, candidates):
    #     _pair_flows = []
    #     for tf in targets:
    #         pf = self._find_pair(tf, candidates)
    #         if pf:
    #             _pair_flows.append(pf)
    #     return _pair_flows

    # def _find_pair(self, target, candidates):
    #     _pair_flows = []
    #     for f in candidates:
    #         if target["dip"] == f["sip"] and target["sip"] == f["dip"] and \
    #             target["dport"] == f["sport"] and target["sport"] == f["dport"] and \
    #             target["proto"] == f["proto"]:
    #             candidates.remove(f)
    #             _pair_flows.append(f)

    #     if len(_pair_flows) == 0:
    #         return None
    #     elif len(_pair_flows) == 1:
    #         return _pair_flows[0]
    #     else:
    #         self._logger.warn("Multiple pair flows. Something goes wrong. TARGET: {} / PAIRFLOWS: {}".format(target, _pair_flows))
    #         return _pair_flows[0]
    
    # def _delete_flows_matching_tuples(self, flows, table_name):
    #     for f in flows:
    #         self._cache_cli.delete_series(database=self._cache_db_name, 
    #                                     measurement=table_name, 
    #                                     tags=f["tags"])

if __name__ == "__main__":
    exp_flow_mgr = ExpiredFlowCache()
    exp_flow_mgr.run()
