import os
import logging

import json
from kafka import KafkaConsumer
from influxdb import InfluxDBClient


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(fm)
_logger.addHandler(sh)

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
        _formatted_msg = dict()
        _formatted_msg["measurement"] = table_name

        _tags = {}
        # _tags["pbox"] = value["pbox"]
        # _tags["net_point"] = value["net_point"]
        # _tags["func"] = value["func"]
        _tags["dip"] = f["dip"]
        _tags["sip"] = f["sip"]
        _tags["dport"] = f["dport"]
        _tags["sport"] = f["sport"]
        _tags["proto"] = f["proto"]
        _formatted_msg["tags"] = _tags

        _formatted_msg["time"] = value["timestamp"] 

        flows = f.split(",")
        _fields = dict()
        # _fields["dest_ip"] = flows[0]
        # _fields["src_ip"] = flows[1]
        # _fields["dest_port"] = flows[2]
        # _fields["src_port"] = flows[3]
        # _fields["l4_proto"] = flows[4]
        # _fields["flow_cnt"] = flows[5]
        # _fields["flow_bytes"] = flows[6]
        _formatted_msg["fields"] = _fields

        _msgs.append(_formatted_msg)


        # msg_dict["pbox"] = socket.gethostname()
        # msg_dict["where"] = where
        # msg_dict["net_point"] = networking_point
        # msg_dict["func"] = function_name
        # msg_dict["timestamp"] = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")


        # flow_msg["dip"] = transform_ip_readable(k.dip)
        # flow_msg["sip"] = transform_ip_readable(k.sip)
        # flow_msg["dport"] = k.dport
        # flow_msg["sport"] = k.sport
        # flow_msg["l4_proto"] = k.l4_proto

        # # Timestamp
        # start_ts_since_epoch_in_usec = (v.start_ts // 1000) + boot_time_since_epoch_in_msec
        # flow_msg["start_ts"] = start_ts_since_epoch_in_usec

        # last_ts_since_epoch_in_usec = (v.last_ts // 1000) + boot_time_since_epoch_in_msec
        # flow_msg["last_ts"] = last_ts_since_epoch_in_usec

        # _logger.debug("start_ts: {} / last_ts: {}".format(start_ts_since_epoch_in_usec, last_ts_since_epoch_in_usec))

        # # 
        # flow_msg["pkt_cnt"] = v.pkt_cnt

        # flow_msg["pkt_bytes_total"] = v.pkt_bytes_total
        # flow_msg["pkt_bytes_min"] = v.pkt_bytes_min
        # flow_msg["pkt_bytes_max"] = v.pkt_bytes_max

        # # Inter-packet arrival time (IPAT)
        # flow_msg["ipat_total"] = v.ipat_total
        # flow_msg["ipat_min"] = v.ipat_min
        # flow_msg["ipat_max"] = v.ipat_max

        # # TCP Flags
        # flow_msg["tcp_syn_cnt"] = v.tcp_syn_cnt
        # flow_msg["tcp_ack_cnt"] = v.tcp_ack_cnt
        # flow_msg["tcp_fin_cnt"] = v.tcp_fin_cnt
        # flow_msg["tcp_rst_cnt"] = v.tcp_rst_cnt
        # flow_msg["tcp_psh_cnt"] = v.tcp_psh_cnt
        # flow_msg["tcp_urg_cnt"] = v.tcp_urg_cnt

    return _msgs


def store_collected_messages(_db_client, _db_name, _msg):
    _db_list = _db_client.get_list_database()

    if not next((_db for _db in _db_list if _db["name"] == _db_name), None):
        _logger.info("Create database: {}".format(_db_name))
        _db_client.create_database(_db_name)

    _db_client.write_points(_msg, database=_db_name)
    

if __name__ == "__main__":

    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "post.yaml")
    _setting = load_setting(file_path)
    _post_setting = _setting["post"]
    # _vcenter_setting = _setting["vCenter"]

    mq_cli = None
    db_cli = None

    if _post_setting["message-queue"]["type"] == "kafka":
        kafka_url = "{}:{}".format(_post_setting["message-queue"]["ipaddr"], _post_setting["message-queue"]["port"])

        # To consume latest messages and auto-commit offsets
        mq_cli = KafkaConsumer(_post_setting["message-queue"]["topic-map"]["flow.measure"],
                                group_id="multi-sec",
                                bootstrap_servers=[kafka_url])

    if _post_setting["flow-db"]["type"] == "influxdb":
        db_cli = InfluxDBClient(host=_post_setting["flow-db"]["ipaddr"], 
                                    port=_post_setting["flow-db"]["port"], 
                                    username=_post_setting["flow-db"]["id"],
                                    password=_post_setting["flow-db"]["password"])

    for message in mq_cli:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        # print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                     message.offset, message.key,
        #                                     message.value))
    
        formatted_msg = format_influx_msg(message, _post_setting["flow-db"]["table-map"]["raw"])
        _logger.info(formatted_msg)
        store_collected_messages(db_cli, _post_setting["flow-db"]["database"], formatted_msg)
    