import os
import logging

import json
from kafka import KafkaConsumer
from influxdb import InfluxDBClient


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

_flow_tag_map = ["point", "dip", "sip", "dport", "sport", "proto"]
_flow_field_map = ["start_ts", "last_ts", "pkt_cnt", 
                    "pkt_bytes_total", "pkt_bytes_min", "pkt_bytes_max",
                    "ipat_total", "ipat_min", "ipat_max",
                    "tcp_syn_cnt", "tcp_ack_cnt", "tcp_fin_cnt", "tcp_rst_cnt", "tcp_psh_cnt", "tcp_urg_cnt"]

_logger.info("Initialization was completed")

def load_setting(_file_path):
    with open(_file_path, 'r') as stream:
        file_str = stream.read()
        if file_str:
            return json.loads(file_str)
        else:
            return None

def format_influx_msg(_msg, table_name):
    _msgs = list()

    # measurement -> table / tags -> index / fields -> values
    # key = _msg.key.decode('utf-8')
    value = json.loads(_msg.value.decode('utf-8'))

    for f in value["flows"]:
        f["point"] = value["point"]

        _formatted_msg = _from_json(f)
        _formatted_msg["time"] = value["time"]
        _formatted_msg["measurement"] = table_name
        _msgs.append(_formatted_msg)
    return _msgs

def _from_json(flow_json):
    _formatted_msg = dict()

    _tags = {}
    for _t in _flow_tag_map:
        _tags[_t] = str(flow_json[_t])
    _formatted_msg["tags"] = _tags
    
    _fields = {}
    for _f in _flow_field_map:
        _fields[_f] = flow_json[_f]
    _formatted_msg["fields"] = _fields

    return _formatted_msg

def _from_csv(flow_csv):
    _formatted_msg = {}

    _tag_map_len = len(_flow_tag_map)
    _field_map_len = len(_flow_tag_map)

    _flow = flow_csv.split(",")
    if len(_flow) != (_tag_map_len + _field_map_len):
        _logger.warning("Received CSV format is not correct")
        return None

    idx = 0
    _tags = {}
    for _t in _flow_tag_map:
        _tags[_t] = str(_flow[idx])
        idx += 1
    _formatted_msg["tags"] = _tags

    idx = 0
    _fields = {}
    for _f in _flow_field_map:
        _fields[_f] = _flow[idx]
        idx += 1
    _formatted_msg["fields"] = _fields

    return _formatted_msg

def _create_db_if_not_exist(_db_client, _db_name):
    _db_list = _db_client.get_list_database()

    if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
        _logger.info("Create database: {}".format(_db_name))
        _db_client.create_database(_db_name)

def store_collected_messages(_db_client, _db_name, _msgs):
    _logger.debug("org msg: {}".format(json.dumps(_msgs)))
    for _m in _msgs:
        _query = 'SELECT * FROM "{}" WHERE point=$point AND dip=$dip AND sip=$sip AND dport=$dport AND sport=$sport AND proto=$proto'.format(_m["measurement"])
        _bind_params = _m["tags"]

        _res = _db_client.query(_query, bind_params=_bind_params, database=_db_name, raise_errors=False)

        # _logger.debug("From influxdb: {}".format(_res))
        _matched_flows = list(_res.get_points(measurement=_m["measurement"]))

        if len(_matched_flows) > 0:
            _db_client.delete_series(database=_db_name, 
                                    measurement=_m["measurement"], 
                                    tags=_m["tags"])

            for _matched in _matched_flows:
                _aggregate_flows(_m, _matched)

    # _logger.debug("aggregated msg: {}".format(json.dumps(_msgs)))
    _db_client.write_points(_msgs, database=_db_name, time_precision='u')

def _aggregate_flows(new_flow, old_flow):
    _logger.debug("new_flow: {} / old_flow: {}".format(new_flow, old_flow))
    _new_flow_fields = new_flow["fields"]

    # Calculate IPAT between the last packet stored in flow cache and the new packet
    _ipat = _new_flow_fields["start_ts"] - old_flow["last_ts"]
    if _ipat <= 0:
        _logger.warn("ipat is lower than zero: {}".format(_ipat))
        _ipat = _ipat * -1
    
    _new_flow_fields["ipat_total"] += _ipat
    if _new_flow_fields["ipat_min"] == 0 or \
        _new_flow_fields["ipat_min"] > _ipat: _new_flow_fields["ipat_min"] = _ipat
    if _new_flow_fields["ipat_max"] == 0 or \
        _new_flow_fields["ipat_max"] < _ipat: _new_flow_fields["ipat_max"] = _ipat

    # Set start timestamp from old flow
    if _new_flow_fields["start_ts"] > old_flow["start_ts"]: 
        _new_flow_fields["start_ts"] = old_flow["start_ts"]
    else: 
        _logger.warn("New flow is older than old flow")

    # Aggregate the attributes, related to the amount of packets, from old flow
    _new_flow_fields["pkt_cnt"] += old_flow["pkt_cnt"]
    _new_flow_fields["pkt_bytes_total"] += old_flow["pkt_bytes_total"]
    if _new_flow_fields["pkt_bytes_min"] > old_flow["pkt_bytes_min"]: _new_flow_fields["pkt_bytes_min"] = old_flow["pkt_bytes_min"]
    if _new_flow_fields["pkt_bytes_max"] < old_flow["pkt_bytes_max"]: _new_flow_fields["pkt_bytes_max"] = old_flow["pkt_bytes_max"]

    # Aggregate the attributes, inter-packet arrival time, from old flow to new flow
    _new_flow_fields["ipat_total"] += old_flow["ipat_total"]
    if old_flow["ipat_min"] > 0 and \
        _new_flow_fields["ipat_min"] > old_flow["ipat_min"]: _new_flow_fields["ipat_min"] = old_flow["ipat_min"]
    if old_flow["ipat_max"] > 0 and \
        _new_flow_fields["ipat_max"] < old_flow["ipat_max"]: _new_flow_fields["ipat_max"] = old_flow["ipat_max"]

    # Aggregate the attributes, the number of TCP flags appeared in packets, from old flow
    _new_flow_fields["tcp_syn_cnt"] += old_flow["tcp_syn_cnt"]
    _new_flow_fields["tcp_ack_cnt"] += old_flow["tcp_ack_cnt"]
    _new_flow_fields["tcp_fin_cnt"] += old_flow["tcp_fin_cnt"]
    _new_flow_fields["tcp_rst_cnt"] += old_flow["tcp_rst_cnt"]
    _new_flow_fields["tcp_psh_cnt"] += old_flow["tcp_psh_cnt"]
    _new_flow_fields["tcp_urg_cnt"] += old_flow["tcp_urg_cnt"]

    _logger.debug("aggregated_flow: {}".format(new_flow))


if __name__ == "__main__":

    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.post.json")
    _setting = load_setting(file_path)
    _post_setting = _setting["post"]

    mq_cli = None
    db_cli = None

    if _post_setting["message-queue"]["type"].lower() == "kafka":
        kafka_url = "{}:{}".format(_post_setting["message-queue"]["ipaddr"], _post_setting["message-queue"]["port"])

        # To consume latest messages and auto-commit offsets
        mq_cli = KafkaConsumer(_post_setting["message-queue"]["topic-map"]["flow.measure"],
                                group_id="multi-sec",
                                bootstrap_servers=[kafka_url])

        _logger.debug("KafkaConsumer was initialized")

    else:
        _logger.error("For message queue, Kafka is only supported")
        exit(1)

    if _post_setting["flow-db"]["type"].lower() == "influxdb":
        db_cli = InfluxDBClient(host=_post_setting["flow-db"]["ipaddr"], 
                                    port=_post_setting["flow-db"]["port"], 
                                    username=_post_setting["flow-db"]["id"],
                                    password=_post_setting["flow-db"]["password"])
        _create_db_if_not_exist(db_cli, _post_setting["flow-db"]["database"]) 
        _logger.debug("InfluxDB Client was initialized")

    else:
        _logger.error("For flow database, InfluxDB is only supported")
        exit(1)

    try:
        _logger.info("Data Collection module started")
        for message in mq_cli:
            _logger.info("Retrieved flows from the message queue")
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            # print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
            #                                     message.offset, message.key,
            #                                     message.value))
        
            _logger.debug("Received Msg: {}".format(message))
            formatted_msg = format_influx_msg(message, _post_setting["flow-db"]["table-map"]["raw"])
            _logger.debug(formatted_msg)
            store_collected_messages(db_cli, _post_setting["flow-db"]["database"], formatted_msg)
            _logger.info("Stored flows into the raw flow cache")

    except KeyboardInterrupt:
        _logger.info("Terminated by Keyboard Interrupt")
        exit(1)
    