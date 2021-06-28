import os
import json
import logging
import time

from influxdb import InfluxDBClient

class FlowClustering:
    def __init__(self) -> None:
        super().__init__()

        # Initialize Logger
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        self._logger.addHandler(sh)

        # Load the configuration from a file
        _cfg = self._load_setting("../config.post.json")
        self._post_cfg = _cfg["post"]

        self._cache_cfg = self._post_cfg["flow-db"]
        self._cache_db_name = self._cache_cfg["database"]
        self._raw_table_name = self._cache_cfg["table-map"]["raw"]
        self._active_table_name = self._cache_cfg["table-map"]["active"]
        self._clustering_interval = self._cache_cfg["clustering_interval"]

        # Initialize InfluxDB Client to access flow cache
        self._cache_cli = self._get_flow_cache_client(self._cache_cfg)

        # Define InfluxDB Message Format
        self._tag_map = ["point", "dip", "sip", "dport", "sport", "proto"]

        self._old_field_map = ["time", "start_ts", "last_ts", "pkt_cnt", 
                    "pkt_bytes_total", "pkt_bytes_min", "pkt_bytes_max",
                    "ipat_total", "ipat_min", "ipat_max",
                    "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

        self._fwd_field_map = [ 
            "fwd_ipat_total", "fwd_ipat_min", "fwd_ipat_max", 
            "fwd_pkt_bytes_total", "fwd_pkt_bytes_min", "fwd_pkt_bytes_max", 
            "fwd_pkt_cnt"
        ]
        self._bwd_field_map = [
            "bwd_ipat_total", "bwd_ipat_min", "bwd_ipat_max",
            "bwd_pkt_bytes_total", "bwd_pkt_bytes_min", "bwd_pkt_bytes_max",
            "bwd_pkt_cnt"
        ]
        
        

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

    def execute(self):
        try:
            while True:
                _start_time = time.time()

                _raw_flows = self._read_all_flows(self._raw_table_name)

                if len(_raw_flows) != 0:
                    self._logger.debug("raw flows: {}". format(_raw_flows))
                    self._delete_all_flows(self._raw_table_name)

                    _clustered_flows = self._pairing_flows(_raw_flows)
                    self._logger.debug("clustered flows: {}". format(_clustered_flows))

                    _existing_active_flows = self._read_all_flows(self._active_table_name)
                    self._logger.debug("existing active flows: {}". format(_existing_active_flows))

                    _new_active_flows = self._combine_fields_active_to_raw(_clustered_flows, _existing_active_flows)
                    self._logger.debug("aggreagted active flows: {}". format(_new_active_flows))

                    _msg = self._format_influx_msgs(_new_active_flows, self._active_table_name)
                    self._delete_flows_from_cache(_msg, self._active_table_name)

                    self._logger.debug("formatted influx messages: {}".format(_msg))
                    self._cache_cli.write_points(_msg, database=self._cache_db_name, time_precision='u')

                _end_time = time.time()
                _next_interval = self._clustering_interval - (_end_time - _start_time)
                time.sleep(_next_interval)
                
        except KeyboardInterrupt:
            self._logger.info("Terminated by keyboard interrupt")

    def _read_all_flows(self, table_name):
        _query = 'SELECT * FROM "{}"'.format(table_name)
        _res = self._cache_cli.query(_query, database=self._cache_db_name)

        _raw_flows = list(_res.get_points(measurement=table_name))
        return _raw_flows
    
    def _delete_all_flows(self, table_name):
        self._cache_cli.delete_series(database=self._cache_db_name, measurement=table_name)

    def _pairing_flows(self, raw_flows):
        _paired_flows = []

        while True:
            found = False

            f1 = raw_flows.pop()

            for f2 in raw_flows:
                if f1["dip"] == f2["sip"] and f1["sip"] == f2["dip"] and \
                    f1["dport"] == f2["sport"] and f1["sport"] == f2["dport"] and \
                    f1["proto"] == f2["proto"]:

                    found = True
                    raw_flows.remove(f2)

                    _paired_flow = None
                    if f1["start_ts"] < f2["start_ts"]:
                        f1 = self._fill_fwd_flow_fields(f1)
                        _paired_flow = self._combine_fields_of_flow_pair(f1, f2)
                    else:
                        self._fill_fwd_flow_fields(f2)
                        _paired_flow = self._combine_fields_of_flow_pair(f2, f1)
                        
                    _paired_flows.append(_paired_flow)

                    break
            
            if f1 and not found:
                f1 = self._fill_fwd_flow_fields(f1)
                f1 = self._dummy_bwd_flow_fields(f1)
                _paired_flows.append(f1)

            if len(raw_flows) == 0:
                break

        return _paired_flows

    def _fill_fwd_flow_fields(self, flow):
        for fwd_key in self._fwd_field_map:
            org_key = fwd_key.replace("fwd_", "")
            flow[fwd_key] = flow[org_key]

        return flow

    def _dummy_bwd_flow_fields(self, flow):
        for bwd_key in self._bwd_field_map:
            flow[bwd_key] = 0
        return flow

    def _combine_fields_of_flow_pair(self, fwd_flow, bwd_flow):
        _paired_flow = fwd_flow
        for bwd_key in self._bwd_field_map:
            org_key = bwd_key.replace("bwd_", "")
            _paired_flow[bwd_key] = bwd_flow[org_key]

        for k in self._old_field_map:
            k_suffix = k.split("_")[-1]
            if k_suffix in ["cnt", "total"]:
                _paired_flow[k] = fwd_flow[k] + bwd_flow[k]
            elif k_suffix in ["min"]:
                if fwd_flow[k] > bwd_flow[k]: _paired_flow[k] = bwd_flow[k]
            elif k_suffix in ["max"]:
                if fwd_flow[k] < bwd_flow[k]: _paired_flow[k] = bwd_flow[k]
            elif k in ["last_ts"]:
                if fwd_flow[k] < bwd_flow[k]: _paired_flow[k] = bwd_flow[k]
            else:
                self._logger.warn("Unknwon Key in old_field_map: {}".format(k))

        return _paired_flow

    def _format_influx_msgs(self, flows, table_name):
        _msgs = []
        _all_field_map = self._old_field_map + self._fwd_field_map + self._bwd_field_map

        for f in flows:
            _msg = {}
            _msg["measurement"] = table_name
            _msg["time"] = f["last_ts"]
            
            _tags = {}
            for _tkey in self._tag_map:
                _tags[_tkey] = f[_tkey]
            _msg["tags"] = _tags

            _fields = {}
            for _fkey in _all_field_map:
                _fields[_fkey] = f[_fkey]
            _msg["fields"] = _fields

            _msgs.append(_msg)

        return _msgs

    def _delete_flows_from_cache(self, flows, table_name):
        for f in flows:
            self._cache_cli.delete_series(database=self._cache_db_name, 
                                        measurement=table_name, 
                                        tags=f["tags"])

    def _combine_fields_active_to_raw(self, new_all_flows, old_all_flows):
        _all_field_map = self._old_field_map + self._fwd_field_map + self._bwd_field_map

        for nf in new_all_flows:

            for of in old_all_flows:

                if nf["dip"] == of["dip"] and nf["sip"] == of["sip"] and \
                    nf["dport"] == of["dport"] and nf["sport"] == of["sport"] and \
                    nf["proto"] == of["proto"]:
                    old_all_flows.remove(of)
                    self._fill_ipat_if_empty(nf, of)
                    self._add_old_to_new_flow(nf, of, _all_field_map)

                elif nf["dip"] == of["sip"] and nf["sip"] == of["dip"] and \
                    nf["dport"] == of["sport"] and nf["sport"] == of["dport"] and \
                    nf["proto"] == of["proto"]:

                    old_all_flows.remove(of)
                    self._convert_flow_direction(nf)
                    self._fill_ipat_if_empty(nf, of)
                    self._add_old_to_new_flow(nf, of, _all_field_map)
                    
        return new_all_flows

    def _convert_flow_direction(self, flow):
        for fwd_key, bwd_key in zip(self._fwd_field_map, self._bwd_field_map):
            fwd_val = flow[fwd_key]
            bwd_val = flow[bwd_key]
            flow[fwd_key] = bwd_val
            flow[bwd_key] = fwd_val
        return flow
    
    def _fill_ipat_if_empty(self, new_flow, old_flow):
        of_last_ts = old_flow["last_ts"]
        nf_start_ts = new_flow["start_ts"]
        ipat = nf_start_ts - of_last_ts

        if ipat <= 0:
            self._logger.warn("IPAT is lower than zero. Something goes wrong.")
            return

        for k in new_flow.keys():
            k_token = k.split("-")

            if "ipat" in k_token and new_flow[k] == 0:
                new_flow[k] = ipat

    def _add_old_to_new_flow(self, new_flow, old_flow, all_field_map):
        for k in all_field_map:
            k_suffix = k.split("_")[-1]
            if k_suffix in ["cnt", "total"]:
                new_flow[k] = new_flow[k] + old_flow[k]
            elif k_suffix in ["min"]:
                if new_flow[k] > old_flow[k]: new_flow[k] = old_flow[k]
            elif k_suffix in ["max"]:
                if new_flow[k] < old_flow[k]: new_flow[k] = old_flow[k]
            elif k in ["start_ts"]:
                new_flow["start_ts"] = old_flow["start_ts"]
            else:
                self._logger.warn("Unknwon Key in old_field_map: {}".format(k))


if __name__ == "__main__":
    clustering = FlowClustering()
    clustering.execute()
