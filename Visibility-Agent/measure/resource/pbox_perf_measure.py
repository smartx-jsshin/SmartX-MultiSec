import logging
import sys
import json
import time
import signal
from datetime import datetime
from pytz import timezone

import socket
import psutil
from kafka import KafkaProducer

class PBoxPerformanceMeasure:
    def __init__(self, config_file):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)
        self._config = self.load_config(config_file)

        self._topic = self._config["kafka"]["kafka_topic"]
        _kakfa_url = "{}:{}".format(self._config["kafka"]["kafka_broker_ip"], self._config["kafka"]["kafka_broker_port"])
        self._producer = KafkaProducer(bootstrap_servers=_kakfa_url)

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def load_config(self, config_file = "config.json"):
        with open(config_file) as f:
            read_data = f.read()
            read_json = json.loads(read_data)
        return read_json
    
    def measure(self):
        comp_all_info = dict()

        self._collect_cpu_perf(comp_all_info)
        self._collect_mem_perf(comp_all_info)
        msg = self.prepare_influx_msg(comp_all_info)
        self._logger.info(msg)
        # self.send_msg(msg)

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

    def prepare_influx_msg(self, comp_all_info):
        # measurement: physical_compute (self._type)
        # tags: Box Name
        # fields:
        msg = dict()
        # msg["measurement"] = self._type

        msg["time"] = datetime.now(timezone('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')

        tags = dict()
        tags["box"] = socket.gethostname()
        msg["tags"] = tags
        msg["fields"] = comp_all_info

        influx_msg = json.dumps([msg])
        return influx_msg

    def send_msg(self, msg):
        self._producer.send(msg)

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

    measure = PBoxPerformanceMeasure(config_file)
    measure.measure()