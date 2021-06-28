import logging
import os
import json
import math
import time
import decimal
from influxdb import InfluxDBClient

class FlowFeatureGeneration:
    def __init__(self, config_file) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')

        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        self._logger.addHandler(sh)

        self._cfg = self._load_config(config_file)
        self._tower_cfg = self._cfg["vCenter"]
        self._cache_cfg = self._tower_cfg["flow-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._active_table_name = self._cache_cfg["table-map"]["flow.measure.active"]
        self._staged_table_name = self._cache_cfg["table-map"]["flow.measure.staged"]
        self._interval = 1
        self._query_time_offset = 0.5

        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)


        self._tuples = ["where", "dip", "sip", "dport", "sport", "proto"]

        self._fields = ["start_ts", "last_ts", "pkt_cnt", 
                    "pkt_bytes_total", "pkt_bytes_sqr_total", "pkt_bytes_min", "pkt_bytes_max",
                    "ipat_total", "ipat_sqr_total", "ipat_min", "ipat_max",
                    "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]
        
        self._features = ["flow_duration", 
                    "pkt_cnt", "pkt_per_sec",
                    "pkt_bytes_per_sec", "pkt_bytes_total", "pkt_bytes_sqr_total", "pkt_bytes_std", "pkt_bytes_mean", "pkt_bytes_min", "pkt_bytes_max",
                    "ipat_total", "ipat_sqr_total", "ipat_mean", "ipat_std", "ipat_min", "ipat_max",
                    "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

    def _load_config(self, file_name):
        _file_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)
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
                                        password=cache_cfg["password"],
                                        database=cache_cfg["database"])
            self._create_db_if_not_exist(_db_cli, cache_cfg["database"]) 
            self._logger.info("InfluxDB Client was initialized")

        else:
            self._logger.error("Multi-Sec supports only InfluxDB for Flow cache, at this time")
            exit(1)

        return _db_cli    

    def _create_db_if_not_exist(self, _db_client, _db_name):
        _db_list = _db_client.get_list_database()

        if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
            self._logger.info("Create database: {}".format(_db_name))
            _db_client.create_database(_db_name)

    def run(self):
        # Read all expired flows
        self._logger.info("Flow Feature Generation module started")

        try:
            while True:
                _start_time = time.time()
                ts = decimal.Decimal((_start_time - self._query_time_offset) * (10 ** 9))

                active_flows =  self._read_all_flows(self._active_table_name, ts)
                if len(active_flows) > 0:
                    # Clear expired table of flow cache
                    self._clear_flow_table(self._active_table_name, ts)

                    # Changed to Influx Message Format
                    # expired_flows = self._format_influx_msg(expired_flows)

                    # Generate Flow Features
                    flows_with_features = self._format_msgs_with_new_features(active_flows)

                    # Store to "Staged" Flow cache
                    self._store_flows(flows_with_features)
                    self._logger.info("Staged Flow Features: {}".format(flows_with_features))

                _end_time = time.time()
                _next_interval = self._interval - (_end_time - _start_time)
                if _next_interval > 0:
                    time.sleep(_next_interval)
                    
        except KeyboardInterrupt:
            self._logger.info("Terminated by keyboard interrupt")

    def _read_all_flows(self, table_name, ts):
        _query = 'SELECT * FROM "{}" WHERE time < {}'.format(table_name, ts)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)

        _flows = list(_res.get_points(measurement=table_name))
        return _flows

    def _clear_flow_table(self, table_name, ts):
        _query = 'DELETE FROM "{}" WHERE time < {}'.format(table_name, ts)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)
        return _res
        # self._cache_cli.drop_measurement(table_name)

    def _format_msgs_with_new_features(self, flows):
        _msgs = []
        
        for flow in flows:
            flow_with_features = self._generate_flow_features(flow)
            _msgs.append(flow_with_features)

        return _msgs

    def _generate_flow_features(self, flow):
        self._logger.debug("Before: {}".format(flow))

        _flow_wf = {}
        _flow_wf["measurement"] = self._staged_table_name

        _tuple = {}
        for t in self._tuples:
            _tuple[t] = flow[t]
        _flow_wf["tags"] = _tuple
        
        
        _flow_duration = flow["last_ts"] - flow["start_ts"]
        _flow_duration_in_sec = int(_flow_duration / (10 ** 6))
        _pkt_cnt = flow["pkt_cnt"]

        _features = {}
        for f in self._features:
            f_tok = f.split("_")
            f_suffix = f_tok.pop(-1)

            if f_suffix == "std":
                key_prefix = "_".join(f_tok)
                sqr_total = flow[key_prefix + "_sqr_total"]
                total = flow[key_prefix + "_total"]

                self._logger.debug(f)
                if "ipat" in f_tok:
                    _div = _pkt_cnt - 1
                else:
                    _div = _pkt_cnt

                if _div > 0:
                    total_exp = total / _div
                    variance = (sqr_total / _div) - (total_exp * total_exp)

                    self._logger.debug("div: {} / sqr_exp: {} / exp: {} / var: {}".format(_div, (sqr_total / _div), total_exp, variance))
                    sqrt = math.sqrt(variance)
                    _features[f] = sqrt

                else:
                    _features[f] = 0.0

            elif f_suffix == "mean":
                total_key = "_".join(f_tok) + "_total"
                total = flow[total_key]

                if "ipat" in f_tok:
                    _div = _pkt_cnt - 1
                else:
                    _div = _pkt_cnt

                if _div > 0:
                    mean = total / _div
                    _features[f] = mean

                else:
                    _features[f] = 0.0

            elif f == "pkt_per_sec":
                if _flow_duration_in_sec == 0:
                    _features[f] = _pkt_cnt / 1.0
                else:
                    _features[f] = _pkt_cnt / _flow_duration_in_sec

            elif f == "pkt_bytes_per_sec":
                if _flow_duration_in_sec == 0:
                    _features[f] = flow["pkt_bytes_total"] / 1.0
                else:
                    _features[f] = flow["pkt_bytes_total"] / _flow_duration_in_sec

            elif f == "flow_duration":
                _features[f] = _flow_duration

            else:
                _features[f] = flow[f]

        _flow_wf["fields"] = _features

        self._logger.debug("After: {}".format(_flow_wf))
        return _flow_wf

    def _store_flows(self, msgs):
        self._cache_cli.write_points(msgs, database=self._cache_db_name, time_precision='u')

if __name__ == "__main__":
    fg = FlowFeatureGeneration("../../MultiView-Configurations/k-one/config.json")
    fg.run()