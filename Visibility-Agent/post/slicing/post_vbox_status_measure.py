import os
import subprocess
import json
import logging
import sys

from kafka import KafkaProducer

class PostVBoxStatusMeasure:
    def __init__(self, config_file):
        self._name = "slicing-post-vbox-status"

        self._logger = logging.getLogger()
        self._logger.setLevel(logging.INFO)
        self._config = self.load_config(config_file)

        self._topic = self._config["kafka"]["kafka_topic"]
        _kakfa_url = "{}:{}".format(self._config["kafka"]["kafka_broker_ip"], self._config["kafka"]["kafka_broker_port"])
        self._producer = KafkaProducer(bootstrap_servers=_kakfa_url)

        self._shell_envvar = os.environ
        for key in self._config["openstack"].keys():
            self._shell_envvar[key] = self._config["openstack"][key]

    def load_config(self, config_file = "config.json"):
        with open(config_file) as f:
            read_data = f.read()
            read_json = json.loads(read_data)
        return read_json

    def measure(self):
        active_vms =  self.get_active_vm_list()
        #self._logger.info(active_vms)

        vm_with_user = self.map_user_to_vms(active_vms)
        #self._logger.info(vm_with_user)

        vmlist_json = self.vm_list_to_json(vm_with_user)
        #self._logger.info(vmlist_json)

        # self.send_msg(vmlist_json)

    def get_active_vm_list(self):
        os_cmd = ["openstack", "server", "list", "--all-projects", "-f", "json"]
        _vm_list = self.os_command(os_cmd)

        _active_vm_list = []
        for vm in _vm_list:
            # if vm.get("Status").lower() != "active":
            #     continue
            _active_vm_list.append(vm)

        return _active_vm_list

    def map_user_to_vms(self, _vm_list):
        os_cmd = ["openstack", "user", "list", "-f", "json"]
        ul = self.os_command(os_cmd)
        ud = self.user_list_to_dicts(ul)
        #self._logger.info(ud)

        for vm in _vm_list:
            os_cmd = ["openstack", "server", "show", vm["ID"], "-f", "json"]
            vm_detail = self.os_command(os_cmd)
            #self._logger.info(vm_detail)
            vm_user_id = vm_detail["user_id"]
            vm["User"] = ud[vm_user_id]

        #self._logger.info(_vm_list)
        return _vm_list

    def user_list_to_dicts(self, ul):
        ud = dict()
        for u in ul:
            ud[u["ID"]] = u["Name"]
        return ud

    def vm_list_to_json(self, _vm_list):
        _docs = []
        for vm in _vm_list:
            _active_vm = dict()
            _active_vm["name"] = vm.get("Name")
            _active_vm["status"] = vm.get("Status")
            #_active_vm["tenant"] = vm.get("User").split("-")[0].upper()
            _active_vm["tenant"] = vm.get("User")
            _docs.append(_active_vm)
        
        self._logger.info(json_str)
        
        return json_str

    def os_command(self, _cmd):
        p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, env=self._shell_envvar)
        outs = p.communicate()[0]

        outs_json = json.loads(outs.decode('utf-8'))
        return outs_json

    def send_msg(self, msg):
        self._producer.send(self._topic, msg)

    def signal_handler(self, signal, frame):
        self._logger.info("Visibility Point {} was finished successfully".format(self.__class__.__name__))
        self._producer.close()
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

    measure = PostVBoxStatusMeasure(config_file)
    measure.measure()

