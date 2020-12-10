#!/usr/bin/python3
import time
import uptime

import socket
import os
import logging

from datetime import datetime, timedelta, timezone
import pytz

import yaml
import json

from bcc import BPF
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

# Executing this file requires installing below python packages
# pytz, psutil, PyYAML, kafka-pythons

_logger = None

def get_bpf_text_file(_map_name):
    _bpf_text = None
    with open('flow_measure.c') as f:
        _bpf_text = f.read()

    _bpf_text = _bpf_text.replace("<map_name>", _map_name)
    return _bpf_text


def load_function_setting():
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "setting.yaml")
    return _read_yaml_file(file_path)


def _read_yaml_file(_file_path):
    # Parse the data from YAML template.
    with open(_file_path, 'r') as stream:
        try:
            file_str = stream.read()
            # logging.debug("Parse YAML from the file: \n" + file_str)
            if file_str:
                return yaml.load(file_str, Loader=yaml.FullLoader)
            else:
                return None
        except yaml.YAMLError as exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                # logging.error(("YAML Format Error: " + _file_path
                #                     + " (Position: line %s, column %s)" %
                #                     (mark.line + 1, mark.column + 1)))
                return None


def transform_ip_readable(ip_u32):
    ip_readable = None

    t = ip_u32
    for _ in range(0, 4):
        cur_octet = str(t & 0xFF)
        if not ip_readable:
            ip_readable = cur_octet
        elif len(ip_readable) > 0:
            ip_readable = "{}.{}".format(cur_octet, ip_readable) # Fourth
        t = t >> 8
    return ip_readable


def create_message(_flow_tuples):
    # Calcuate the absolute values of start and last timestamp
    # Current time since the epoch - Current time since the last boot + start/last timestamp in flow (since boot)
    # datetime.datetime.fromtimestamp( time.time() - uptime.uptime() + flow.last_ts/start_ts, pytz.timezone('Asia/Seoul') )

    # variables for debugs
    debug_total_pkt_bytes = 0
    debug_msg_bytes = 0
    
    #
    msg_dict = {}
    msg_dict["flows"] = []

    cur_time_since_epoch_in_usec = int(round(time.time() * 1000000, 0))
    uptime_in_usec = int(round( (uptime.uptime() * 1000000), 0 ))
    boot_time_since_epoch_in_msec = cur_time_since_epoch_in_usec - uptime_in_usec

    for k, v in _flow_tuples:
        # flow_duration = round((v.last_ts - v.start_ts) / 10 ** 3, 0)  # in microseconds
        # pps = round(v.pkt_cnt / flow_duration * 10 ** 6, 2)
        # bps = round(v.pkt_bytes_total / flow_duration * 10 ** 6, 0)
        # pkt_bytes_mean = round(v.pkt_bytes_total / v.pkt_cnt, 0)
        # ipat_mean = round(v.ipat_total / (v.pkt_cnt - 1), 2)

        flow_msg = dict()

        # Flow's five tuples
        flow_msg["dip"] = transform_ip_readable(k.dip)
        flow_msg["sip"] = transform_ip_readable(k.sip)
        flow_msg["dport"] = k.dport
        flow_msg["sport"] = k.sport
        flow_msg["proto"] = k.proto

        # Timestamp
        start_ts_since_epoch_in_usec = (v.start_ts // 1000) + boot_time_since_epoch_in_msec
        flow_msg["start_ts"] = start_ts_since_epoch_in_usec

        last_ts_since_epoch_in_usec = (v.last_ts // 1000) + boot_time_since_epoch_in_msec
        flow_msg["last_ts"] = last_ts_since_epoch_in_usec

        _logger.debug("start_ts: {} / last_ts: {}".format(start_ts_since_epoch_in_usec, last_ts_since_epoch_in_usec))

        # 
        flow_msg["pkt_cnt"] = v.pkt_cnt

        flow_msg["pkt_bytes_total"] = v.pkt_bytes_total
        flow_msg["pkt_bytes_min"] = v.pkt_bytes_min
        flow_msg["pkt_bytes_max"] = v.pkt_bytes_max

        # Inter-packet arrival time (IPAT)
        flow_msg["ipat_total"] = v.ipat_total
        flow_msg["ipat_min"] = v.ipat_min
        flow_msg["ipat_max"] = v.ipat_max

        # TCP Flags
        flow_msg["tcp_syn_cnt"] = v.tcp_syn_cnt
        flow_msg["tcp_ack_cnt"] = v.tcp_ack_cnt
        flow_msg["tcp_fin_cnt"] = v.tcp_fin_cnt
        flow_msg["tcp_rst_cnt"] = v.tcp_rst_cnt
        flow_msg["tcp_psh_cnt"] = v.tcp_psh_cnt
        flow_msg["tcp_urg_cnt"] = v.tcp_urg_cnt
        
        # flow_msg = ""
        # flow_msg = flow_msg + "{},{},{},{},{}".format(dip, sip, dport, sport, l4_proto)
        # flow_msg = flow_msg + ",{},{}".format(v.start_ts, v.last_ts)
        
        # flow_msg = flow_msg + ",{}".format(v.pkt_cnt)

        # flow_msg = flow_msg + ",{},{},{}".format(v.pkt_bytes_total,
        #                                         v.pkt_bytes_min, v.pkt_bytes_max)

        # flow_msg = flow_msg + ",{},{},{}".format(v.ipat_total, v.ipat_min, v.ipat_max)

        # flow_msg = flow_msg + ",{},{},{},{},{},{}".format(v.tcp_syn_cnt,
        #                                                   v.tcp_ack_cnt,
        #                                                   v.tcp_fin_cnt,
        #                                                   v.tcp_rst_cnt,
        #                                                   v.tcp_psh_cnt,
        #                                                   v.tcp_urg_cnt)
        msg_dict["flows"].append(flow_msg)

        debug_total_pkt_bytes += v.pkt_bytes_total
        debug_msg_bytes += len(json.dumps(flow_msg).encode('utf-8'))
        

    _logger.info("Original packet size: {} / Message Size: {}".format(debug_total_pkt_bytes, debug_msg_bytes))
    return msg_dict


if __name__ == "__main__":
    setting = load_function_setting()

    # Initialize variables
    function_name = setting["function_name"]
    networking_point = setting["networking_point"]
    where = setting["where"]

    map_name = "flow_{}".format(function_name)
    kafka_url = "{}:{}".format(setting["post"]["ipaddr"], setting["post"]["kafka_port"])
    kafka_topic = setting["post"]["kafka_topic"]

    # Initialize a logging instance
    _logger = logging.getLogger(function_name)
    _logger.setLevel(logging.DEBUG)
    fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(fm)
    _logger.addHandler(sh)

    # ENABLE THIS PART TO ENABLE SINGLE PACKET MONITOR - END (2/1)
    bpf_text = get_bpf_text_file(map_name)
    _logger.debug(bpf_text)

    bpf = BPF(text=bpf_text)
    # bpf = BPF(src_file="flow_measure.c", cflags=["-w", "-DMAPNAME=%s" % map_name])
    function_skb_matching = bpf.load_func("flow_measure", BPF.SOCKET_FILTER)
    BPF.attach_raw_socket(function_skb_matching, networking_point)
    flow_cnt_table = bpf.get_table(map_name)  # retrieve packet_cnt map

    _logger.info("Measurement Function {} was successfully loaded.".format(function_name))

    try:
        while True:
            start_time = time.time()

            flow_tuples = flow_cnt_table.items()

            if len(flow_tuples) != 0:
                flow_cnt_table.clear()

                msg_dict = create_message(flow_tuples)
                msg_dict["where"] = where
                msg_dict["net_point"] = networking_point
                msg_dict["func"] = function_name
                msg_dict["timestamp"] = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")

                msg_val = json.dumps(msg_dict).encode('utf-8')

                # try:
                #     producer = KafkaProducer(bootstrap_servers=[kafka_url])
                #     producer.send(kafka_topic, msg_val)
                #     _logger.debug("Send kafka message successfully")
                #     producer.close()

                # except NoBrokersAvailable as noBrokerExt:
                #     _logger.error("Kafka Broker in Security Post is not accessible")

                _logger.debug("[Length: {}] {}".format(len(msg_val), msg_val))

            else:
                _logger.debug("No flows are captured")

            end_time = time.time()
            next_sleep_interval = setting["output_interval"] - (end_time - start_time)
            if next_sleep_interval > 0:
                time.sleep(setting["output_interval"])

    except KeyboardInterrupt:
        flow_cnt_table.clear()
        _logger.warning("Keyboard Interrupted")
        exit()
