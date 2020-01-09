import json
from maas.client import login
from pymongo import MongoClient


collector_name = "resource-box-pbox-status"

def get_config(fp):
    with open(fp) as f:
        read_data = f.read()
        read_json = json.loads(read_data)

    return read_json


def get_maas_client():
    maas_cfg = config["maas"]
    url = "http://{}:{}/MAAS/".format(maas_cfg["host"], maas_cfg["port"])
    client = login(url, username=maas_cfg["id"], password=maas_cfg["password"])
    return client


def get_boxes_list(cli):
    pb_lists = []

    for m in cli.machines.list():
        pb_dict = dict()
        pb_dict["name"] = m.hostname
        pb_dict["status"] = m.status_name
        pb_dict["power_status"] = m.power_state.value
        pb_dict["zone"] = m.zone.name

        if m.owner is None:
            pb_dict["tenant"] = None
        else:
            pb_dict["tenant"] = m.owner.username
        pb_lists.append(pb_dict)

    return pb_lists


def insert_docs_to_db(_docs):
    mongo_cfg = config["mongo"]
    mongo_client = MongoClient(mongo_cfg["host"] + ":" + mongo_cfg["port"],
                               username=mongo_cfg["id"],
                               password=mongo_cfg["password"],
                               authSource=mongo_cfg["database"],
                               authMechanism='SCRAM-SHA-256')

    db = mongo_client[mongo_cfg["database"]]

    db_col_name = mongo_cfg["collection_map"][collector_name]
    db.drop_collection(db_col_name)
    coll = db[db_col_name]
    coll.insert_many(_docs)


config = get_config("config.json")
print(config)
maas_client = get_maas_client()
pbox_lists = get_boxes_list(maas_client)
insert_docs_to_db((pbox_lists))