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

class PBoxSpecInspection:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def measure(self):
        pBoxSpec = dict()

        pBoxSpec["cpu"] = self._collect_cpu_status()
        pBoxSpec["memory"] = self._collect_mem_status()
        pBoxSpec["os"] = self._collect_os_default()
        pBoxSpec["disk"] = self._collect_disk_default()
        pBoxSpec["network"] = self._collect_network_default()
    
        return pBoxSpec

    def _collect_cpu_status(self):
        cpu_info = dict()
        cpu_info["physical_count"] = psutil.cpu_count(logical=False)
        cpu_info["logical_count"] = psutil.cpu_count(logical=True)

        data_from_cpuinfo = cpuinfo.get_cpu_info()
        self._logger.debug(data_from_cpuinfo)
        
        cpu_info["model"] = data_from_cpuinfo["brand_raw"]
        cpu_info["vendor"] = data_from_cpuinfo["vendor_id_raw"]
        cpu_info["advertised_hertz"] = data_from_cpuinfo["hz_advertised"]
        cpu_info["actual_hertz"] = data_from_cpuinfo["hz_actual"]
        cpu_info["instruction_bits"] = data_from_cpuinfo["bits"]
        cpu_info["architecture"] = data_from_cpuinfo["arch"]
        cpu_info["flags"] = data_from_cpuinfo["flags"]

        cache_dict = dict()
        cache_dict["l1_instruction_cache_size"] = data_from_cpuinfo["l1_instruction_cache_size"]
        cache_dict["l1_data_cache_size"] = data_from_cpuinfo["l1_data_cache_size"]
        cache_dict["l2_cache_line_size"] = data_from_cpuinfo["l2_cache_line_size"]
        cache_dict["l2_cache_size"] = data_from_cpuinfo["l2_cache_size"]
        cache_dict["l3_cache_size"] = data_from_cpuinfo["l3_cache_size"]

        cpu_info["cache"] = cache_dict

        self._logger.debug(cpu_info)
        return cpu_info

    def _collect_mem_status(self):
        mem_info = dict()
        mem_info["memory_size_byte"] = str(psutil.virtual_memory().__getattribute__("total"))
        mem_info["swap_size_byte"] = str(psutil.swap_memory().__getattribute__("total"))

        self._logger.debug(mem_info)
        return mem_info

    def _collect_os_default(self):
        os_info = dict()
        os_info["system"] = platform.system()
        os_info["release"] = platform.release()
        os_info["like"] = distro.like()
        os_info["build_number"] = distro.build_number()
        os_info["version"] = distro.version()
        os_info["name"] = distro.name()
        os_info["codename"] = distro.codename()

        self._logger.debug(os_info)
        return os_info

    def _collect_disk_default(self):
        partition_info = list()

        for existing_partition in psutil.disk_partitions():
            partition_dict = dict()

            partition_dict["device"] = existing_partition.__getattribute__("device")
            mounted_path = existing_partition.__getattribute__("mountpoint")
            partition_dict["mount_point"] = mounted_path
            partition_dict["disk_size_byte"] = str(psutil.disk_usage(mounted_path).__getattribute__("total"))
            partition_dict["filesystem"] = existing_partition.__getattribute__("fstype")

            partition_info.append(partition_dict)

        self._logger.debug("_collect_disk_default(): {}".format(partition_info))
        return partition_info

    def _collect_network_default(self):
        net_info = dict()
        if_list = list()

        data_from_if_addrs = psutil.net_if_addrs()
        data_from_if_stats = psutil.net_if_stats()

        for if_name in data_from_if_addrs.keys():
            if_info_dict = dict()

            if_stat = data_from_if_stats[if_name]
            if_info_dict["name"] = if_name
            if_info_dict["link_state"] = if_stat.__getattribute__("isup")
            if_info_dict["duplex_mode"] = if_stat.__getattribute__("duplex")
            if_info_dict["link_speed_gbps"] = if_stat.__getattribute__("speed")
            if_info_dict["mtu_size_byte"] = if_stat.__getattribute__("mtu")
            if_info_dict["address"] = self._get_addrs(if_name)
            if_list.append(if_info_dict)

        net_info["interface"] = if_list
        net_info["gateway"] = self._get_organized_gateways()

        self._logger.debug(net_info)
        return net_info

    def _get_addrs(self, if_name):
        new_addrs_dict = dict()
        addrs_dict_from_box = netifaces.ifaddresses(if_name)
        for proto_num in addrs_dict_from_box.keys():
            new_addrs_dict[self._get_proto_str_from(proto_num)] = addrs_dict_from_box[proto_num]
        return new_addrs_dict

    def _get_organized_gateways(self):
        new_gateways_list = list()

        gws_from_box = netifaces.gateways()
        for gw_type in gws_from_box.keys():
            if gw_type == 'default':
                continue
            new_gateway_dict = dict()
            gws_for_proto = gws_from_box[gw_type]
            for gw in gws_for_proto:
                new_gateway_dict["protocol"] = self._get_proto_str_from(gw_type)
                new_gateway_dict["gateway_address"] = gw[0]
                new_gateway_dict["gateway_interface"] = gw[1]
                new_gateway_dict["is_default"] = gw[2]
                new_gateways_list.append(new_gateway_dict)
        return new_gateways_list

    def _get_proto_str_from(self, proto_num):
        if proto_num == netifaces.AF_INET:  # IPv4
            proto_str = "IPv4"
        elif proto_num == netifaces.AF_INET6:  # IPv6
            proto_str = "IPv6"
        elif proto_num == netifaces.AF_LINK:  # MAC
            proto_str = "MAC"
        else:
            proto_str = "Unknown ({})".format(proto_num)
        return proto_str


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

    logging.getLogger(__name__).debug(encoded_key)
    logging.getLogger(__name__).debug(encoded_val)
    producer.send(topic, key=encoded_key, value=encoded_val)
    producer.close()

def format_msg(msg, msg_type, box_config):
    if msg_type in ["status", "performance"]:
        msg["name"] = box_config["name"] # Box name
        msg["where"] = box_config["where"] # Box Location
        msg["type"] = box_config["type"] # Box Type
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

    pBoxSpecInspection = PBoxSpecInspection()
    spec = pBoxSpecInspection.measure()
    msg = format_msg(spec, "status", _cube_config)
    publish_msg(mq_url, mq_topic, "status", msg)

    try:
        while True:
            pBoxPerfMeasure = PBoxPerformanceMeasure()
            perf = pBoxPerfMeasure.measure()

            msg = format_msg(perf, "performance", _cube_config)
            publish_msg(mq_url, mq_topic, "performance", msg)
            
            time.sleep(_interval)

    except KeyboardInterrupt:
        exit()

    # Gather pBox specification
    # Send through Kafka

    # while
    # Measure pBox performance metrics
    # Send through Kafka

    