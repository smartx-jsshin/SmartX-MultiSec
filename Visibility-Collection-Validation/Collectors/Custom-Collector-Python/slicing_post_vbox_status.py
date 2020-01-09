import os
import subprocess
import json
from pymongo import MongoClient


collector_name = "slicing-post-vbox-status"

def get_config():
    with open('config.json') as f:
        read_data = f.read()
        read_json = json.loads(read_data)
    return read_json


def os_command(_cmd):
    custom_env = os.environ
    openstack_cfg = config["openstack"]
    for key in openstack_cfg.keys():
        custom_env[key] = openstack_cfg[key]

    p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, env=custom_env)
    outs = p.communicate()[0]

    outs_json = json.loads(outs.decode('utf-8'))
    return outs_json


def get_active_vm_list():
    os_cmd = ["openstack", "server", "list", "--all-projects", "-f", "json"]
    _vm_list = os_command(os_cmd)

    _active_vm_list = []
    for vm in _vm_list:
        if vm.get("Status").lower() != "active":
            continue
        _active_vm_list.append(vm)

    return _active_vm_list


def user_list_to_dicts(ul):
    ud = dict()
    for u in ul:
        ud[u["ID"]] = u["Name"]
    return ud


def map_user_to_vms(_vm_list):
    os_cmd = ["openstack", "user", "list", "-f", "json"]
    ul = os_command(os_cmd)
    ud = user_list_to_dicts(ul)

    for vm in _vm_list:
        os_cmd = ["openstack", "server", "show", vm["ID"], "-f", "json"]
        vm_detail = os_command(os_cmd)
        vm_user_id = vm_detail["user_id"]
        vm["User"] = ud[vm_user_id]

    return _vm_list


def vm_list_to_docs(_vm_list):
    _docs = []
    for vm in _vm_list:
        _active_vm = dict()
        _active_vm["name"] = vm.get("Name")
        _active_vm["status"] = vm.get("Status")
        _active_vm["tenant"] = vm.get("User").split("-")[0].upper()
        _docs.append(_active_vm)

    return _docs


def insert_docs_to_db(_docs):
    mongo_cfg = config["mongo"]

    if mongo_cfg.get("id") is not None and mongo_cfg.get("password") is not None:
        mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"],
                                   username=mongo_cfg["id"],
                                   password=mongo_cfg["password"],
                                   authSource=mongo_cfg["database"],
                                   authMechanism='SCRAM-SHA-256')
    else:
        mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"])

    db = mongo_client[mongo_cfg["database"]]

    db_col = mongo_cfg["collection_map"][collector_name]
    db.drop_collection(db_col)
    coll = db[db_col]
    coll.insert_many(_docs)


config = get_config()
active_vms = get_active_vm_list()
print(active_vms)
vm_with_user = map_user_to_vms(active_vms)
print (vm_with_user)
vm_docs = vm_list_to_docs(vm_with_user)
print(vm_docs)
insert_docs_to_db(vm_docs)
