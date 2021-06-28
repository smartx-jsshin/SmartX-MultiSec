import logging
import os
import time
import decimal

import json
from influxdb import InfluxDBClient

class FlowClustering:
    def __init__(self) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')

        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.DEBUG)
        self._logger.addHandler(sh)

        self._cfg = self._load_config("config.tower.collection.json")
        self._tower_cfg = self._cfg["tower"]
        self._cache_cfg = self._tower_cfg["timeseries-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._from_table = self._cache_cfg["table-map"]["flow.measure.staged"]
        self._to_table = self._cache_cfg["table-map"]["flow.measure.clustered"]

        self._interval = 1  # in seconds
        self._query_time_offset = 0.5

        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        self._tuples = ["point", "dip", "sip", "dport", "sport", "proto"]
        self._features = ["flow_duration", "pkt_cnt", "pkt_per_sec",
            "pkt_bytes_per_sec", "pkt_bytes_std", "pkt_bytes_mean", "pkt_bytes_min", "pkt_bytes_max",
            "ipat_mean", "ipat_std", "ipat_min", "ipat_max",
            "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

        self._total_features = ["pkt_cnt", "pkt_per_sec",
            "pkt_bytes_per_sec", "pkt_bytes_std", "pkt_bytes_mean", "pkt_bytes_min", "pkt_bytes_max",
        ]
        self._direc_features = ["pkt_cnt", "pkt_per_sec",
            "pkt_bytes_per_sec", "pkt_bytes_std", "pkt_bytes_mean", "pkt_bytes_min", "pkt_bytes_max",
            "ipat_mean", "ipat_std", "ipat_min", "ipat_max"
            ]

    def _load_config(self, file_path: str):
        _file_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        with open(_file_abs_path, 'r') as stream:
            content = stream.read()
            if content:
                return json.loads(content)
            else:
                return None
    
    def _get_flow_cache_client(self, cache_cfg):
        _db_cli = None
        
        if cache_cfg["type"] == "influxdb":
            _db_cli = InfluxDBClient(host=cache_cfg["ipaddr"], 
                                        port=cache_cfg["port"], 
                                        username=cache_cfg["id"],
                                        password=cache_cfg["password"],
                                        database=cache_cfg["database"])
            self._create_db_if_not_exist(_db_cli, cache_cfg["database"]) 
            self._logger.info("InfluxDB Client was initialized")

        else:
            self._logger.error("Multi-Sec supports only InfluxDB for Flow cache, at this time")
            exit(1)

        return _db_cli    

    def run(self):
        # Retrieve Staged data from flow cache
        try:
            while True:
                _start_time = time.time()
                ts = decimal.Decimal((_start_time - self._interval) * (10 ** 9))

                _staged_flows = self._get_flows_stored_after(self._from_table, ts)
                # Clustering Rules
                # 1. Bidirectional Flows
                # 2. Flows having same source/dest IP addresses
                #    which were generated within a specific time windows
                # 3. Flows having same destination IP addresses within a time window
                # 4. Flows having same port numbers within a time window

                _end_time = time.time()
                _next_interval = self._interval - (_end_time - _start_time)
                if _next_interval > 0:
                    time.sleep(_next_interval)

        except KeyboardInterrupt:
            exit(1)

    def _get_flows_stored_after(self, table, time_from):
        _query = 'SELECT * FROM "{}" WHERE time > {}'.format(table, time_from)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)

        _flows = list(_res.get_points(measurement=table))
        return _flows

    def _get_bidirec_flow_pairs(self, uni_flows):
        _paired_flows = []
        
        while True:
            found = False

            f1 = uni_flows.pop()
            f1 = self._fill_fwd_flow_features(f1)

            for f2 in uni_flows:
                if f1["dip"] == f2["sip"] and f1["sip"] == f2["dip"] and \
                    f1["dport"] == f2["sport"] and f1["sport"] == f2["dport"] and \
                    f1["proto"] == f2["proto"] and f1["point"] == f2["point"]:

                    found = True
                    uni_flows.remove(f2)
                    f1 = self._combine_fields_of_flow_pair(f1, f2)

                elif f1["dip"] == f2["dip"] and f1["sip"] == f2["sip"] and \
                    f1["dport"] == f2["dport"] and f1["sport"] == f2["sport"] and \
                    f1["proto"] == f2["proto"] and f1["point"] == f2["point"]:
                    pass

            if f1 and not found:
                f1 = self._dummy_bwd_flow_fields(f1)

            _paired_flows.append(f1)

            if len(uni_flows) == 0:
                break

        return _paired_flows
        # self._features = ["flow_duration", "pkt_cnt", "pkt_per_sec",
        #     "pkt_bytes_per_sec", "pkt_bytes_std", "pkt_bytes_mean", "pkt_bytes_min", "pkt_bytes_max",
        #     "ipat_mean", "ipat_std", "ipat_min", "ipat_max",
        #     "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

    def _fill_fwd_flow_features(self, uni_flow):
        pass

    def _combine_bidirec_flow_features(self, fwd, bwd):
        pass

