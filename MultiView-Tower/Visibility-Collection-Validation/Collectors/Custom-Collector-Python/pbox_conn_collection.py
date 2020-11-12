#!/usr/bin/python3

import os
import logging
import json
import subprocess

import socket
import time
from multiprocessing import Process, Queue
from datetime import datetime
from pytz import timezone

from pymongo import MongoClient, ReturnDocument
from ping3 import ping

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(fm)
_logger.addHandler(sh)


def load_setting(_file_path):
    with open(_file_path, 'r') as stream:
        file_str = stream.read()
        _logger.debug("Parse JSON from the file: \n" + file_str)

        if file_str:
            return json.loads(file_str)
        else:
            return None

def format_msg(pbox_config, status):
    # Box name, box type, where, box status, mangement plane, security status
    _msg_dict = dict()
    _msg_dict["name"] = pbox_config["name"]
    _msg_dict["tier"] = pbox_config["tier"]
    _msg_dict["where"] = pbox_config["where"]
    _msg_dict["resource"] = status
    # _msg_dict["timestamp"] = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ") 
    _msg_dict["security"] = None

    return _msg_dict

def isOpen(ip, port, timeout=0.3):
    _logger.debug("Port checking started: {}, {}".format(ip, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
            s.connect((ip, int(port)))
            s.shutdown(socket.SHUT_RDWR)
            return True
    except:
            return False
    finally:
            _logger.debug("Port checking finished: {}, {}".format(ip, port))
            s.close()

def isPingable(_ipaddr, timeout=0.3):
    # ping_count = 1
    _logger.debug("Ping started: {}".format(_ipaddr))
    res = ping(_ipaddr, timeout=timeout)
    _logger.debug("Ping finished: {} {}".format(_ipaddr, res))
    return res

def isAccessible(_pbox_config, _docs_queue, _unavail_queue):
    for net in _pbox_config["network"]:
        if net["plane"].lower() == "management" and net.get("ipaddr", None):
            check = 0

            if isPingable(net["ipaddr"]):
                check += 1

            if isOpen(net["ipaddr"], 22):
                check += 1

            _msg = format_msg(_pbox_config, check)
            if check > 0:
                _docs_queue.put(_msg)
            else:
                _unavail_queue.put(_msg)

if __name__ == "__main__":
    interval = 10 #in seconds

    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.tower.collection.json")
    _setting = load_setting(file_path).get("vCenter", None)

    if not _setting:
        raise FileNotFoundError(file_path)

    _mongo_setting = _setting["document-db"]
    _mongo_cli = MongoClient(host=_mongo_setting["ipaddr"], 
                            port=int(_mongo_setting["port"]), 
                            username=_mongo_setting["userId"], 
                            password=_mongo_setting["userPassword"], 
                            authSource=_mongo_setting["authDb"])

    db = _mongo_cli[_mongo_setting["multiviewDb"]]
    conf_col = db[_mongo_setting["collectionMap"]["boxConfig"]]
    status_col = db[_mongo_setting["collectionMap"]["boxStatus"]]

    try:
        while True:
            begin = datetime.now()

            procs = list()
            avail_queue = Queue()
            unavail_queue = Queue()

            for box_config in conf_col.find():
                if box_config["tier"].split(".")[-1] in ["vbox", "cbox", "vcbox"]:
                    continue

                proc = Process(target=isAccessible, args=(box_config, avail_queue, unavail_queue,))
                procs.append(proc)
                proc.start()

                for proc in procs:
                    proc.join()

            _msg = {"name": box_config["name"], "where": box_config["where"]}

            while not unavail_queue.empty():
                unavail_box = unavail_queue.get()
                # Set the status "INACTIVE" of the unavailable physical boxes                 
                updatedDoc = status_col.find_one_and_update(
                    filter={"name": unavail_box["name"], "where": unavail_box["where"]},
                    update={ "$set": {"resource": unavail_box["resource"]}}
                )
                if updatedDoc:
                    _logger.info("Set the status INACTIVE of the physical box: {}".format(updatedDoc))

                # Set the status "INACTIVE" of all virtual boxes in the unavailable physical boxes
                where_val = "{}.{}".format(unavail_box["where"], unavail_box["name"])
                vbox_docs = status_col.find({"where": where_val})

                for vbox_doc in vbox_docs:
                    matching = {"name": vbox_doc["name"], "where": vbox_doc["where"]}
                    updatedDoc = status_col.find_one_and_update(
                        filter={"name": vbox_doc["name"], "where": vbox_doc["where"]},
                        update={ "$set": {"resource": 0}},
                        return_document=ReturnDocument.AFTER
                    )

                    if updatedDoc:
                        _logger.info("Set the status INACTIVE of the virtual box: {}".format(updatedDoc))


            while not avail_queue.empty():
                avail_box = avail_queue.get()
                updatedDoc = status_col.find_one_and_update(
                    filter={"name": avail_box["name"], "where": avail_box["where"]},
                    update={ "$set": {"resource": avail_box["resource"]}})
                    
                if updatedDoc:
                     _logger.info("Set the status ACTIVE of the physical box: {}".format(updatedDoc))

                else:
                    status_col.insert(avail_box)
                    _logger.info("Insert a new doc: {}".format(avail_box))

            end = datetime.now()
            sleep_duration = interval - (end - begin).total_seconds()
            if sleep_duration < 0:
                sleep_duration = 0

            time.sleep(sleep_duration)
    finally:
        _mongo_cli.close()
    