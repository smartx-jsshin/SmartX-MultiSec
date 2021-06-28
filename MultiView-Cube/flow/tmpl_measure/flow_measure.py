#!/usr/bin/python3
import time
import uptime

import socket
import os
import logging

from datetime import datetime, timedelta
import pytz

import yaml
import json

from bcc import BPF
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable


# Executing this file requires installing below python packages
# pytz, psutil, PyYAML, kafka-pythons

class FlowMeasure():
    def __init__(self) -> None:
        super().__init__()
        self.setting = self.load_function_setting()

        # Initialize variables
        # self.function_name = self.setting["function_name"]
        self.networking_port = self.setting["networking_port"]
        self.where = self.setting["where"]

        self.map_name = "flow_measure_{}".format(self.networking_port)
        self.kafka_url = "{}:{}".format(self.setting["post"]["ipaddr"], self.setting["post"]["kafka_port"])
        self.kafka_topic = self.setting["post"]["kafka_topic"]

        # Initialize a logging instance
        self._logger = logging.getLogger(self.map_name)
        self._logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')

        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        self._logger.addHandler(sh)

        fh = logging.FileHandler(filename="./flow_measure.log")
        fh.setFormatter(fm)
        fh.setLevel(logging.DEBUG)
        self._logger.addHandler(fh)

        # Definition of Flow features
        self._flow_tags = ["where", "dip", "sip", "dport", "sport", "proto"]
        self._flow_fields = ["start_ts", "last_ts", "pkt_cnt",
                             "pkt_bytes_total", "pkt_bytes_sqr_total", "pkt_bytes_min", "pkt_bytes_max",
                             "ipat_total", "ipat_sqr_total", "ipat_min", "ipat_max",
                             "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

    def load_function_setting(self):
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "setting.yaml")
        return self._read_yaml_file(file_path)

    def _read_yaml_file(self, _file_path):
        # Parse the data from YAML template.
        with open(_file_path, 'r') as stream:
            try:
                file_str = stream.read()
                # logging.debug("Parse YAML from the file: \n" + file_str)
                if file_str:
                    return yaml.load(file_str)
                else:
                    return None
            except yaml.YAMLError as exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    # logging.error(("YAML Format Error: " + _file_path
                    #                     + " (Position: line %s, column %s)" %
                    #                     (mark.line + 1, mark.column + 1)))
                    return None

    def run(self):
        # ENABLE THIS PART TO ENABLE SINGLE PACKET MONITOR - END (2/1)
        bpf_text = self.get_bpf_text_file(self.map_name)
        self._logger.debug(bpf_text)

        bpf = BPF(text=bpf_text)
        # bpf = BPF(src_file="flow_measure.c", cflags=["-w", "-DMAPNAME=%s" % map_name])
        function_skb_matching = bpf.load_func("flow_measure", BPF.SOCKET_FILTER)
        BPF.attach_raw_socket(function_skb_matching, self.networking_port)
        flow_cnt_table = bpf.get_table(self.map_name)  # retrieve packet_cnt map

        self._logger.info("Measurement Function {} was successfully loaded.".format(self.networking_port))

        try:
            while True:
                start_time = time.time()

                flow_tuples = flow_cnt_table.items()

                if len(flow_tuples) != 0:
                    flow_cnt_table.clear()

                    msgs = self.create_message(flow_tuples)
                    # self._logger.debug(msgs)

                    try:
                        producer = KafkaProducer(bootstrap_servers=[self.kafka_url])

                        _bucket = []
                        for msg in msgs:
                            _bucket.append(msg)
                            if len(_bucket) > 5000:
                                producer.send(self.kafka_topic, json.dumps(_bucket).encode('utf-8'))
                                self._logger.info("Measured Flows: {}".format(_bucket))
                                _bucket.clear()
                        if len(_bucket) > 0:
                            producer.send(self.kafka_topic, json.dumps(_bucket).encode('utf-8'))
                            self._logger.info("Measured Flows: {}".format(_bucket))
                            _bucket.clear()

                        producer.close()
                        self._logger.info("Send kafka message successfully")

                    except NoBrokersAvailable as noBrokerExt:
                        self._logger.error("Kafka Broker in Security Post is not accessible")

                end_time = time.time()
                next_sleep_interval = float(self.setting["output_interval"]) - (end_time - start_time)
                if next_sleep_interval > 0:
                    time.sleep(float(self.setting["output_interval"]))

        except KeyboardInterrupt:
            flow_cnt_table.clear()
            self._logger.warning("Keyboard Interrupted")
            exit()

    def get_bpf_text_file(self, _map_name):
        _bpf_text = None
        with open('flow_measure.c') as f:
            _bpf_text = f.read()

        _bpf_text = _bpf_text.replace("<map_name>", _map_name)
        return _bpf_text

    def transform_ip_readable(self, ip_u32):
        ip_readable = None

        t = ip_u32
        for _ in range(0, 4):
            cur_octet = str(t & 0xFF)
            if not ip_readable:
                ip_readable = cur_octet
            elif len(ip_readable) > 0:
                ip_readable = "{}.{}".format(cur_octet, ip_readable)  # Fourth
            t = t >> 8
        return ip_readable

    def create_message(self, _flow_tuples):
        # Calcuate the absolute values of start and last timestamp
        # Current time since the epoch - Current time since the last boot + start/last timestamp in flow (since boot)
        # datetime.datetime.fromtimestamp( time.time() - uptime.uptime() + flow.last_ts/start_ts, pytz.timezone('Asia/Seoul') )

        # variables for debugs
        # debug_pkt_cnt = 0
        # debug_total_pkt_bytes = 0
        # debug_msg_bytes = 0

        # cur_time_since_epoch_in_usec = int(time.time() * 1000000)
        # uptime_in_usec = int((uptime.uptime() * 1000000), 0 )
        # boot_time_since_epoch_in_msec = cur_time_since_epoch_in_usec - uptime_in_usec
        _msgs = []

        # _flow_cnt = len(_flow_tuples)
        for k, v in _flow_tuples:
            m = self.to_json(k, v)
            # debug_pkt_cnt += v.pkt_cnt
            # debug_total_pkt_bytes += v.pkt_bytes_total
            # debug_msg_bytes += len(m.encode('utf-8'))
            _msgs.append(m)
            # debug_msg_bytes += len(json.dumps(flow_msg).encode('utf-8'))

        # self._logger.info("# Flows: {} / # Packets: {} / Original packet size: {} / Message Size: {}".format(
        # _flow_cnt, debug_pkt_cnt, debug_total_pkt_bytes, debug_msg_bytes))
        return _msgs

    def to_json(self, k, v):
        _json_msg = dict()

        # Flow's five tuples
        for t in self._flow_tags:
            if t == "where":
                # _json_msg[t] = "{}.{}".format(self.where, self.networking_port)
                _json_msg[t] = self.where
            else:
                _tag_val = getattr(k, t)
                if t in ["dip", "sip"]:
                    _json_msg[t] = self.transform_ip_readable(_tag_val)
                else:
                    _json_msg[t] = _tag_val

        for f in self._flow_fields:
            _field_val = getattr(v, f)
            _json_msg[f] = _field_val

        return _json_msg

    def to_csv(self, k, v):
        _csv_msg = ""

        for t in self._flow_tags:
            if t == "where":
                _csv_msg = _csv_msg + "{}.{},".format(self.where, self.networking_port)
            else:
                _tag_val = getattr(k, t)
                if t in ["dip", "sip"]:
                    _csv_msg = _csv_msg + "{},".format(self.transform_ip_readable(_tag_val))
                else:
                    _csv_msg = _csv_msg + "{},".format(_tag_val)

        for f in self._flow_fields:
            _field_val = getattr(v, f)
            _csv_msg = _csv_msg + "{},".format(_field_val)

        # Remove the last comma character
        _csv_msg = _csv_msg[:-1]

        return _csv_msg


if __name__ == "__main__":
    measure = FlowMeasure()
    measure.run()

