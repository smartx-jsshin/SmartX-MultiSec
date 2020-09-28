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
_logger.setLevel(logging.INFO)
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
    _msg_dict["status"] = status
    _msg_dict["timestamp"] = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")


    for net in pbox_config["network"]:
        if net["plane"].lower() == "management":
            _msg_dict["management_ip"] = net["ipaddr"]
    
    _msg_dict["security_level"] = None

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
    for net in pbox_config["network"]:
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
    interval = 60 #in seconds

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

    db = _mongo_cli[_mongo_setting["userDb"]]
    conf_col = db[_mongo_setting["collectionMap"]["pBoxConfig"]]
    status_col = db[_mongo_setting["collectionMap"]["pvBoxStatus"]]

    try:
        while True:
            begin = datetime.now()
            procs = list()
            docs_queue = Queue()
            unavail_queue = Queue()

            for pbox_config in conf_col.find():
                proc = Process(target=isAccessible, args=(pbox_config, docs_queue, unavail_queue,))
                procs.append(proc)
                proc.start()

                for proc in procs:
                    proc.join()

            _msg = {"name": pbox_config["name"], "where": pbox_config["where"]}
            unavail_queries = list()
            while not unavail_queue.empty():
                unavail_box = unavail_queue.get()
                # Set the status "INACTIVE" of the unavailable physical boxes                 
                # delDocs = status_col.find_one_and_delete(matching)
                newDoc = status_col.find_one_and_update(
                    filter={"name": unavail_box["name"], "where": unavail_box["where"]},
                    update={ "$set": {"status": unavail_box["status"]}}
                )

                # Set the status "INACTIVE" of all virtual boxes in the unavailable physical boxes
                if newDoc:
                    _logger.info("Set the status INACTIVE of the physical box: {}".format(newDoc))

                where_val = "{}.{}".format(unavail_box["where"], unavail_box["name"])
                vbox_docs = status_col.find({"where": where_val})

                for vbox_doc in vbox_docs:
                    matching = {"name": vbox_doc["name"], "where": vbox_doc["where"]}
                    newDoc = status_col.find_one_and_update(
                        filter={"name": vbox_doc["name"], "where": vbox_doc["where"]},
                        update={ "$set": {"status": 0}},
                        return_document=ReturnDocument.AFTER
                    )

                    if newDoc:
                        _logger.info("Set the status INACTIVE of the virtual box: {}".format(newDoc))


            while not docs_queue.empty():
                pbox_doc = docs_queue.get()
                oldDoc = status_col.find_one_and_update(
                    filter={"name": pbox_doc["name"], "where": pbox_doc["where"]},
                    update={ "$set": {"status": pbox_doc["status"]}})
                    
                if oldDoc:
                    _logger.info("Find and update the matched doc: {}, {}, {}".format(pbox_doc["name"], pbox_doc["where"], pbox_doc["status"]))
                else:
                    status_col.insert(pbox_doc)
                    _logger.info("Insert a new doc: {}".format(pbox_doc))

            end = datetime.now()
            sleep_duration = interval - (end - begin).total_seconds()
            if sleep_duration < 0:
                sleep_duration = 0

            time.sleep(sleep_duration)
    finally:
        _mongo_cli.close()
    