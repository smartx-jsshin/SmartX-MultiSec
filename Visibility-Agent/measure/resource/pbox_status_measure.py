import logging
import sys
import json
import signal
from datetime import datetime
from pytz import timezone

import socket
import netifaces
import platform
import psutil
import distro
import cpuinfo
from kafka import KafkaProducer


class ResourcePBoxStatusMeasure:
    def __init__(self, config_file):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)
        self._config = self.load_config(config_file)

        self._topic = self._config["kafka"]["kafka_topic"]
        self._kakfa_url = "{}:{}".format(self._config["kafka"]["kafka_broker_ip"], self._config["kafka"]["kafka_broker_port"])

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def load_config(self, config_file = "config.json"):
        with open(config_file) as f:
            read_data = f.read()
            read_json = json.loads(read_data)
        return read_json

    def measure(self):
        pBoxStatus = dict()

        pBoxStatus["name"] = socket.gethostname()
        pBoxStatus["cpu"] = self._collect_cpu_status()
        pBoxStatus["memory"] = self._collect_mem_status()
        pBoxStatus["os"] = self._collect_os_default()
        pBoxStatus["disk"] = self._collect_disk_default()
        pBoxStatus["network"] = self._collect_network_default()

        pBoxStatus["timestamp"] = datetime.now(timezone('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')
        
        msg = self._prepare_msg(pBoxStatus)

        self._logger.info(msg)
        self.send_msg(msg)

    def _collect_cpu_status(self):
        cpu_info = dict()
        cpu_info["physical_count"] = psutil.cpu_count(logical=False)
        cpu_info["logical_count"] = psutil.cpu_count(logical=True)

        data_from_cpuinfo = cpuinfo.get_cpu_info()
        cpu_info["model"] = data_from_cpuinfo["brand"]
        cpu_info["vendor"] = data_from_cpuinfo["vendor_id"]
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

        self._logger.debug(json.dumps(cpu_info))
        return cpu_info

    def _collect_mem_status(self):
        mem_info = dict()
        mem_info["memory_size_byte"] = str(psutil.virtual_memory().__getattribute__("total"))
        mem_info["swap_size_byte"] = str(psutil.swap_memory().__getattribute__("total"))

        self._logger.debug(json.dumps(mem_info))
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

        self._logger.debug(json.dumps(os_info))
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

        self._logger.debug("_collect_disk_default(): {}".format(json.dumps(partition_info)))
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

        self._logger.debug(json.dumps(net_info))
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

    def _prepare_msg(self, org_msg):
        _formatted_msg = json.dumps(org_msg)
        return _formatted_msg

    def send_msg(self, msg):
        _producer = KafkaProducer(bootstrap_servers=self._kakfa_url)
        _producer.send(msg.encode('utf-8'))
        _producer.close()

    def signal_handler(self, signal, frame):
        self._logger.info("Visibility Point {} was finished successfully".format(self.__class__.__name__))
        sys.exit(0)
    

if __name__ == "__main__":
    logging.basicConfig(format="[%(asctime)s / %(levelname)s] %(filename)s,%(funcName)s(#%(lineno)d): %(message)s",
                        level=logging.INFO)

    if len(sys.argv) == 1:
        config_file = "config.json"
    elif len(sys.argv) == 2:
        # Load configuration from a file passed by second argument in the command
        config_file = sys.argv[1]
    else:
        exit(1)

    measure = ResourcePBoxStatusMeasure(config_file)
    measure.measure()