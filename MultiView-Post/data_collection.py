import os
import logging
import json
from kafka import KafkaConsumer
from influxdb import InfluxDBClient


class DataCollection:
    def __init__(self, config_file) -> None:
        self._logger = self._init_logger()

        self._config = self._load_config(config_file)
        self._post_config = self._config["post"]

        self.mq_cli = self._get_mq_client(self._post_config["message-queue"])
        self.cache_cli = self._get_flow_cache_client(self._post_config["flow-db"])
        self._create_db_if_not_exist(self._post_config["flow-db"]["database"])

        self._flow_tags = ["where", "dip", "sip", "dport", "sport", "proto"]
        self._flow_fields = ["start_ts", "last_ts", "pkt_cnt", 
                            "pkt_bytes_total", "pkt_bytes_sqr_total", "pkt_bytes_min", "pkt_bytes_max",
                            "ipat_total", "ipat_sqr_total", "ipat_min", "ipat_max",
                            "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

        self._logger.debug("Initialization was completed")

    def _init_logger(self):
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.DEBUG)

        fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')

        sh = logging.StreamHandler()
        sh.setFormatter(fm)
        sh.setLevel(logging.INFO)
        _logger.addHandler(sh)

        fh = logging.FileHandler(filename="./data_collection.log")
        fh.setFormatter(fm)
        fh.setLevel(logging.DEBUG)
        _logger.addHandler(fh)

        return _logger

    def _load_config(self, _file_path):
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), _file_path)
        with open(file_path, 'r') as stream:
            file_str = stream.read()
            if file_str:
                return json.loads(file_str)
            else:
                return None

    def _get_mq_client(self, _mq_config):
        if _mq_config["type"].lower() == "kafka":
            kafka_url = "{}:{}".format(_mq_config["ipaddr"], _mq_config["port"])

            # To consume latest messages and auto-commit offsets
            mq_cli = KafkaConsumer(_mq_config["topic-map"]["flow.measure"],
                                    group_id="multi-sec",
                                    bootstrap_servers=[kafka_url])

            self._logger.debug("KafkaConsumer was initialized")
            return mq_cli

        else:
            self._logger.error("For message queue, Kafka is only supported")
            exit(1)

    def _get_flow_cache_client(self, _cache_config):
        if _cache_config["type"].lower() == "influxdb":
            _cache_cli = InfluxDBClient(host=_cache_config["ipaddr"], 
                                        port=_cache_config["port"], 
                                        username=_cache_config["id"],
                                        password=_cache_config["password"])
            self._logger.debug("InfluxDB Client was initialized")
            return _cache_cli

        else:
            self._logger.error("For flow database, InfluxDB is only supported")
            exit(1)

    def _create_db_if_not_exist(self, _db_name):
        _db_list = self.cache_cli.get_list_database()

        if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
            self._logger.info("Create database: {}".format(_db_name))
            self.cache_cli.create_database(_db_name)

    def run(self):
        try:
            self._logger.info("Data Collection module started")
            for message in self.mq_cli:
                # Messages obtained from Kafka MQ are raw bytes -> value and key should be decoded!
                # e.g., for unicode: `message.value.decode('utf-8')`
                # print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                #                                     message.offset, message.key,
                #                                     message.value))
                self._logger.debug("Received Msg: {}".format(message))
                formatted_msg = self.format_influx_msg(message, self._post_config["flow-db"]["table-map"]["raw"])
                self.store_collected_messages(formatted_msg)

        except KeyboardInterrupt:
            self._logger.info("Terminated by Keyboard Interrupt")
            exit(1)


    def format_influx_msg(self, _msgs, table_name):
        # measurement -> table / tags -> index / fields -> values
        # key = _msg.key.decode('utf-8')
        value = json.loads(_msgs.value.decode('utf-8'))
        # self._logger.info(value)

        _formatted_msgs = []
        # _formatted_msg = _from_json(value)
        for m in value:
            # _formatted_msg = self._from_csv(m)
            _formatted_msg = self._from_json(m)
            # _formatted_msg["time"] = value["time"]
            _formatted_msg["measurement"] = table_name
            _formatted_msgs.append(_formatted_msg)
        return _formatted_msgs

    def _from_json(self, flow_json):
        # flow_json = json.load(flow_json)
        # self._logger.info(flow_json)
        _formatted_msg = dict()

        _tags = {}
        for _t in self._flow_tags:
            _tags[_t] = str(flow_json[_t])
        _formatted_msg["tags"] = _tags
        
        _fields = {}
        for _f in self._flow_fields:
            _fields[_f] = flow_json[_f]
        _formatted_msg["fields"] = _fields

        return _formatted_msg

    def _from_csv(self, flow_csv):
        _formatted_msg = {}

        _tag_map_len = len(self._flow_tags)
        _field_map_len = len(self._flow_tags)
        self._logger.debug(flow_csv)

        _flow = flow_csv.split(",")
        # if len(_flow) != (_tag_map_len + _field_map_len):
        #     _logger.warning("Received CSV format is not correct")
        #     return None

        _tags = {}
        for _t, _tag_val in zip(self._flow_tags, _flow[:_tag_map_len]):
            _tags[_t] = str(_tag_val)
        _formatted_msg["tags"] = _tags

        _fields = {}
        for _f, _field_val in zip(self._flow_fields, _flow[_tag_map_len:]):
            _fields[_f] = int(_field_val)
        _formatted_msg["fields"] = _fields

        return _formatted_msg

    def store_collected_messages(self, msgs):
        self._logger.info("Stored flows into the raw flow cache: {}".format(msgs))
        _db_name = self._post_config["flow-db"]["database"]
        self.cache_cli.write_points(msgs, database=_db_name, time_precision='u')

    # def _aggregate_flows(self, new_flow, old_flow):
    #     self._logger.debug("new_flow: {} / old_flow: {}".format(new_flow, old_flow))
    #     _new_flow_fields = new_flow["fields"]

    #     # Calculate IPAT between the last packet stored in flow cache and the new packet
    #     _ipat = _new_flow_fields["start_ts"] - old_flow["last_ts"]
    #     if _ipat <= 0:
    #         self._logger.warn("ipat is lower than zero: {}".format(_ipat))
    #         _ipat = _ipat * -1
        
    #     _new_flow_fields["ipat_total"] += _ipat
    #     _new_flow_fields["ipat_sqr_total"] += (_ipat ** 2)
    #     if _new_flow_fields["ipat_min"] == 0 or \
    #         _new_flow_fields["ipat_min"] > _ipat: _new_flow_fields["ipat_min"] = _ipat
    #     if _new_flow_fields["ipat_max"] == 0 or \
    #         _new_flow_fields["ipat_max"] < _ipat: _new_flow_fields["ipat_max"] = _ipat

    #     # Set start timestamp from old flow
    #     if _new_flow_fields["start_ts"] > old_flow["start_ts"]: 
    #         _new_flow_fields["start_ts"] = old_flow["start_ts"]
    #     else: 
    #         self._logger.warn("New flow is older than old flow")

    #     # Aggregate the attributes, related to the amount of packets, from old flow
    #     _new_flow_fields["pkt_cnt"] += old_flow["pkt_cnt"]
    #     _new_flow_fields["pkt_bytes_total"] += old_flow["pkt_bytes_total"]
    #     _new_flow_fields["pkt_bytes_sqr_total"] += old_flow["pkt_bytes_sqr_total"]
    #     if _new_flow_fields["pkt_bytes_min"] > old_flow["pkt_bytes_min"]: _new_flow_fields["pkt_bytes_min"] = old_flow["pkt_bytes_min"]
    #     if _new_flow_fields["pkt_bytes_max"] < old_flow["pkt_bytes_max"]: _new_flow_fields["pkt_bytes_max"] = old_flow["pkt_bytes_max"]

    #     # Aggregate the attributes, inter-packet arrival time, from old flow to new flow
    #     _new_flow_fields["ipat_total"] += old_flow["ipat_total"]
    #     _new_flow_fields["ipat_sqr_total"] += old_flow["ipat_sqr_total"]
    #     if old_flow["ipat_min"] > 0 and \
    #         _new_flow_fields["ipat_min"] > old_flow["ipat_min"]: _new_flow_fields["ipat_min"] = old_flow["ipat_min"]
    #     if old_flow["ipat_max"] > 0 and \
    #         _new_flow_fields["ipat_max"] < old_flow["ipat_max"]: _new_flow_fields["ipat_max"] = old_flow["ipat_max"]

    #     # Aggregate the attributes, the number of TCP flags appeared in packets, from old flow
    #     _new_flow_fields["tcp_syn_cnt"] += old_flow["tcp_syn_cnt"]
    #     _new_flow_fields["tcp_ack_cnt"] += old_flow["tcp_ack_cnt"]
    #     _new_flow_fields["tcp_fin_cnt"] += old_flow["tcp_fin_cnt"]
    #     _new_flow_fields["tcp_rst_cnt"] += old_flow["tcp_rst_cnt"]
    #     _new_flow_fields["tcp_psh_cnt"] += old_flow["tcp_psh_cnt"]
    #     _new_flow_fields["tcp_urg_cnt"] += old_flow["tcp_urg_cnt"]

    #     self._logger.debug("aggregated_flow: {}".format(new_flow))


if __name__ == "__main__":
    data_collector = DataCollection("config.post.json")
    data_collector.run()
    