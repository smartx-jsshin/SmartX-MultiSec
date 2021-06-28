#!/usr/bin/python3

import os
import logging
import sys
import json
import signal
import time
from datetime import datetime
from pytz import timezone

import socket
import netifaces
import platform
import psutil
import distro
import cpuinfo
from kafka import KafkaProducer

class PBoxPerformanceMeasure:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def measure(self):
        comp_all_info = dict()

        self._collect_cpu_perf(comp_all_info)
        self._collect_mem_perf(comp_all_info)
        return comp_all_info

    def _collect_cpu_perf(self, comp_all_info):
        cpu_percent = psutil.cpu_percent(interval=None)
        if cpu_percent == 0:
            cpu_percent = psutil.cpu_percent(interval=None)
        comp_all_info["cpu_percent"] = cpu_percent

        cpu_time_info = psutil.cpu_times()
        for key in cpu_time_info._fields:
            value = getattr(cpu_time_info, key)
            comp_all_info["cpu_{}".format(key)] = str(value)

        cpu_stat_info = psutil.cpu_stats()
        for key in cpu_stat_info._fields:
            value = getattr(cpu_stat_info, key)
            comp_all_info["cpu_{}".format(key)] = str(value)

    def _collect_mem_perf(self, comp_all_info):
        vmem_info = psutil.virtual_memory()
        swap_info = psutil.swap_memory()

        for key in vmem_info._fields:
            value = getattr(vmem_info, key)
            comp_all_info["mem_{}".format(key)] = value

        for key in swap_info._fields:
            value = getattr(swap_info, key)
            comp_all_info["swap_{}".format(key)] = value
    

def publish_msg(mq_url, topic, msg_key, msg_value):
    producer = KafkaProducer(bootstrap_servers=[mq_url])
    
    encoded_key = None
    if isinstance(msg_key, dict):
        encoded_key = json.dumps(msg_key).encode('utf-8')
    elif isinstance(msg_key, str):
        encoded_key = msg_key.encode('utf-8')
    
    encoded_val = None
    if isinstance(msg_value, dict):
        encoded_val = json.dumps(msg_value).encode('utf-8')
    elif isinstance(msg_value, str):
        encoded_val = msg_value.encode('utf-8')
    
    producer.send(topic, key=encoded_key, value=encoded_val)
    producer.close()
    
    logging.getLogger(__name__).info("Message Published to {} / {}".format(mq_url, topic))
    logging.getLogger(__name__).info("Published Message: {}".format(msg_value))

def format_msg(msg, msg_type, box_config):
    if msg_type in ["status", "performance"]:
        msg["name"] = box_config["name"] # Box name
        msg["where"] = box_config["where"] # Box Location
        msg["tier"] = box_config["tier"] # Box Type
        msg["tenant"] = box_config.get("tenant", "operator")
        msg["timestamp"] = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")
        return msg

    else:
        logging.getLogger(__name__).warn("The given message type is not supported: {}".format(msg_type))
        return None


def _load_setting(_file_path):
    with open(_file_path, 'r') as stream:
        file_str = stream.read()

        if file_str:
            return json.loads(file_str)
        else:
            return None


if __name__ == "__main__":
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.INFO)
    fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(fm)
    _logger.addHandler(sh)

    _interval = 1 # in seconds

    # Load configuration file
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../config.cube.json")
    _config = _load_setting(file_path)
    _cube_config = _config["cube"]
    _mq_config = _config["vCenter"]["message-queue"]

    mq_url = "{}:{}".format(_mq_config["ipaddr"], _mq_config["port"])
    mq_topic = _mq_config["topicMap"]["resource"]

    try:
        while True:
            pBoxPerfMeasure = PBoxPerformanceMeasure()
            perf = pBoxPerfMeasure.measure()

            msg = format_msg(perf, "performance", _cube_config)
            publish_msg(mq_url, mq_topic, "performance", msg)
            
            time.sleep(_interval)

    except KeyboardInterrupt:
        exit()


    