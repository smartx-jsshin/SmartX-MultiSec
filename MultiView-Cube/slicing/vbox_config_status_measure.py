#!/usr/bin/python3

import os
import subprocess
import json
import logging
import sys
import time
from datetime import datetime
from pytz import timezone

import libvirt
from kafka import KafkaProducer
from xml.dom import minidom

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(fm)
_logger.addHandler(sh)

box_nicknames = {
    "K1-GJ1-Tower1": "k1-gj1-post",
    "K1-KU1-Tower1": "k1-ku1-post",
    "K1-SSU1-Tower1": "k1-ssu1-post",
    "K1-PO1-Tower1": "k1-po1-post",
    "K1-KAIST1-Tower1": "k1-ka1-post"
}

where = {
    "k1-gj1-post": "gj.k1-gj1-post",
    "k1-ku1-post": "ku.k1-ku1-post",
    "k1-ssu1-post": "ssu.k1-ssu1-post",
    "k1-po1-post": "po.k1-po1-post",
    "k1-ka1-post": "ka.k1-ka1.post"
}

class LibvirtVBoxStatusMeasure:
    def __init__(self, cube_config):
        self._libvirt_conn = None
        self._cube_config = cube_config
        self._prepare_libvirt_conn()

    def _prepare_libvirt_conn(self):
        self._libvirt_conn = libvirt.openReadOnly("qemu:///system")
        if self._libvirt_conn is None:
            _logger.error("Failed to open connection to qemu:///system")
            exit(1)

    def measure(self):
        all_vbox_status = list()
        domList = self._libvirt_conn.listAllDomains(0)
        _state_def = ["NOSTATE", "RUNNING", "BLOCKED", "PAUSED", "SHUTDOWN", "SHUTOFF", "CRASHED", "PMSUSPENDED"]

        # self._libvirt_conn.close()
        for dom in domList:
            vbox_status = dict()
            vbox_status["name"] = dom.name()
            # vm_status["os"] = dom.OSType()

            # try:
            #     vm_status["hostname"] = dom.hostname()
            # except libvirt.libvirtError:
            #     _logger.debug("Cannot get the hostname of the VM {}".format(dom.name()))
            vbox_status["where"] = "{}.{}".format(self._cube_config["where"], self._cube_config["name"])
            vbox_status["tier"] = "{}.{}".format(self._cube_config["tier"], "vcbox")

            vm_info = dom.info()
            if vm_info[0] == 1:
                vbox_status["status"] = 2
            else:
                vbox_status["status"] = 0

            vbox_status["memory"] = vm_info[1]
            vbox_status["cpu"] = vm_info[3]
            vbox_status["disk"] = self._get_disk(dom)

            vbox_status["tenant"] = self._cube_config["tenant"]
            vbox_status["security_level"] = None
            vbox_status["timestamp"] = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")

            all_vbox_status.append(vbox_status)
        
        return all_vbox_status

    def _get_disk(self, dom):
        # <disk type='file' device='disk'>
        #     <driver name='qemu' type='qcow2' cache='none'/>
        #     <source file='/var/lib/nova/instances/b370eee7-6481-4893-a2f9-a6138cedd9bb/disk'/>
        #     <backingStore type='file' index='1'>
        #         <format type='raw'/>
        #         <source file='/var/lib/nova/instances/_base/c8c4947a1a9ea063b0f02a8ca0491b036a7228cc'/>
        #         <backingStore/>
        #     </backingStore>
        #     <target dev='vda' bus='virtio'/>
        #     <alias name='virtio-disk0'/>
        #     <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
        # </disk>
        disk_list = []

        raw_xml = dom.XMLDesc(0)
        xml = minidom.parseString(raw_xml)

        disks = xml.getElementsByTagName('disk')
        for disk in disks:
            if disk.getAttribute('type') == "file" and disk.getAttribute('device') == "disk":
                disk_name = None
                alloc_blk_path = None
                max_blk_path = None

                diskattrs = disk.childNodes
                for diskattr in diskattrs:
                    if diskattr.nodeName[0:1] != '#':

                        if diskattr.nodeName == "source":
                            alloc_blk_path = diskattr.attributes["file"].value

                        if diskattr.nodeName == "target":
                            disk_name = diskattr.attributes["dev"].value
                        
                        if diskattr.nodeName == "backingStore":
                            bss = diskattr.childNodes
                            for bs in bss:
                                if bs.nodeName == "source":
                                    max_blk_path = bs.attributes["file"].value

                disk_info = {}
                disk_info["name"] = disk_name
                if max_blk_path:
                    disk_info["max_size"] = os.path.getsize(max_blk_path)
                else:
                    disk_info["alloc_size"] = os.path.getsize(alloc_blk_path)

                disk_list.append(disk_info)

        return disk_list


    def _collect_vm(self, vm_id, vm_info):
        dom = self._libvirt_conn.lookupByID(vm_id)
        # _logger.debug("looku8pByID(): {}".format(dom))
        _logger.debug(dom)
        _logger.debug(dom.__str__)

        if not dom.isActive():
            return None

        vm_info["vbox"] = dom.name()

        infos = dom.info()
        vm_info["mem_total"] = infos[1]
        vm_info["cpu_cores"] = infos[3]

        cpu_status = dom.getCPUStats(True)[0]
        for key in cpu_status:
            vm_info["cpu_{}".format(key)] = cpu_status[key]

        mem_status = dom.memoryStats()
        for key in mem_status:
            vm_info["mem_{}".format(key)] = mem_status[key]


class LibVirtVBoxPerformanceMeasure:
    def __init__(self):
        pass

class OpenStackVBoxStatusMeasure:
    def __init__(self, _cube_config):
        self._cube_config = _cube_config
        self._os_config = _cube_config["openstack"]

        self._shell_envvar = os.environ
        for key in self._os_config.keys():
            self._shell_envvar[key] = self._os_config[key]

    def measure(self):
        # openstack server list => [ID, Name, Status, Networks]
        # openstack server show {serverId} => {OS-EXT-SRV-ATTR:host, flavor, userId, image}
        # openstack user list => [ID, Name]
        # openstack flavor list => [ID, Name, RAM, Disk, Ephemeral, VCPUs]

        vboxes_status = []

        vms_list = self.get_vms_list()
        users_list = self.get_users_list()
        flavors_list = self.get_flavors_list()

        for vm in vms_list:
            vbox_status = dict()
            vbox_status["name"] = vm["Name"]

            if vm["Status"] == "ACTIVE":
                vbox_status["status"] = 2
            else:
                vbox_status["status"] = 0

            # Obtain Management Plane IP
            vbox_status["management_ip"] = None
            nets = vm["Networks"].split()
            for net in nets:
                _logger.debug(net)
                plane_name, plane_ip = net.split("=")
                if "MGMT" in plane_name:
                    vbox_status["management_ip"] = plane_ip

            # Obtain the detail information of the VM
            _detail = self.get_vm_detail(vm["ID"])

            pbox_name = _detail["OS-EXT-SRV-ATTR:host"]
            if pbox_name in box_nicknames.keys():
                pbox_name = box_nicknames[pbox_name]
            vbox_status["where"] = where[pbox_name]

            # Find user name from the user ID stored in VM detail
            r = {"ID": _detail["user_id"]}
            user_dict = self.find_dict_from_list(users_list, r)               
            vbox_status["tenant"] = user_dict["Name"]

            # Obtain VM spec (CPU, MEM, DISK) from the matched flavor
            flavor_name = _detail["flavor"].split()[0]
            r = {"Name": flavor_name}
            flavor_dict = self.find_dict_from_list(flavors_list, r)
            vbox_status["cpu"] = flavor_dict["VCPUs"]
            vbox_status["memory"] = flavor_dict["RAM"]
            vbox_status["disk"] = flavor_dict["Disk"]

            vbox_status["security_level"] = None
            vbox_status["timestamp"] = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")
            vboxes_status.append(vbox_status)

        measured_msgs = self._format_msg(vboxes_status)

        return measured_msgs

    def get_vms_list(self):
        os_cmd = ["openstack", "server", "list", "--all-projects", "-f", "json"]
        _vm_list = self.os_command(os_cmd)

        return _vm_list

    def get_users_list(self):
        os_cmd = ["openstack", "user", "list", "-f", "json"]
        ul = self.os_command(os_cmd)
        return ul

    def get_flavors_list(self):
        os_cmd = ["openstack", "flavor", "list", "-f", "json"]
        fl = self.os_command(os_cmd)
        return fl

    def get_vm_detail(self, vm_id):
        os_cmd = ["openstack", "server", "show", vm_id, "-f", "json"]
        vm_detail = self.os_command(os_cmd)
        return vm_detail

    def find_dict_from_list(self, _list, _rule):
        for d in _list:
            flag = True
            for k, v in _rule.items():
                if d[k] != v:
                    flag = False
                    break

            if flag:
                return d
        return None
    
    def _format_msg(self, org_data):
        _msgs = list()

        for _vbox in org_data:
            _msg = dict()
            _msg["name"] = _vbox.pop("name")
            _msg["where"] = _vbox.pop("where")
            _msg["tier"] = "{}.{}".format(self._cube_config["tier"], "vcbox")
            for k, v in _vbox.items():
                _msg[k] = v

            _msgs.append(_msg)

        return _msgs

    def os_command(self, _cmd):
        p = subprocess.Popen(_cmd, stdout=subprocess.PIPE, env=self._shell_envvar)
        outs = p.communicate()[0]

        # _logger.debug(outs)

        outs_json = json.loads(outs.decode('utf-8'))
        return outs_json


def publish_msg(_msg_key, _msg_val, _mq_url, _mq_topic):
    _vcenter_mq_cli = KafkaProducer(bootstrap_servers=_mq_url)
    _vcenter_mq_cli.send(_mq_topic, key=_msg_key.encode('utf-8'), value=_msg_val.encode('utf-8'))
    _vcenter_mq_cli.close()
    _logger.info("Message Published to {} / {}".format(_mq_url, _mq_topic))
    _logger.info("Published Message: {}".format(_msg_val))


def _load_config(file_path):
    with open(file_path) as fp:
        config_str = fp.read()

        if config_str:
            return json.loads(config_str)
        else:
            return None


if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../config.cube.json")
    _config = _load_config(file_path)

    if not _config:
        print("1")
        _logger.error("Cannot open the configuration file: {}".format(file_path))
        exit()

    _cube_config = _config["cube"]
    # _post_config = _config["post"]
    _vcenter_config = _config["vCenter"]
    
    vcenter_mq_url = "{}:{}".format(_vcenter_config["message-queue"]["ipaddr"], _vcenter_config["message-queue"]["port"])
    vcenter_mq_topic = _vcenter_config["message-queue"]["topicMap"]["slicing.status"]

    vbox_status_measure = None

    if _cube_config["vbox-measure"] == "openstack":
        vbox_status_measure = OpenStackVBoxStatusMeasure(_cube_config)
    elif _cube_config["vbox-measure"] == "libvirt":
        vbox_status_measure = LibvirtVBoxStatusMeasure(_cube_config)

    _interval = 30
    
    while True:
        start = datetime.now()
        msg = vbox_status_measure.measure()
        # "name": "MAAS-GJ-Post", "where": "gj.k1-gj1-post", "tier": "edge-cloud.post.vcbox", "status": 0, "management_ip": "210.117.251.32", "tenant": "gist-jsshin", "cpu": 1, "memory": 2048, "disk": 20, "timestamp": "2020-09-21T18:53:47Z"}

        if isinstance(msg, list):
            if len(msg) > 0:
                for m in msg:
                    publish_msg("status", json.dumps(m), vcenter_mq_url, vcenter_mq_topic)        
            else:
                _logger.info("No v/cBoxes to publish")
        elif isinstance(msg, dict):
            publish_msg("status", json.dumps(msg), vcenter_mq_url, vcenter_mq_topic)
        elif isinstance(msg, str):
            publish_msg("status", msg, vcenter_mq_url, vcenter_mq_topic)

        end = datetime.now()
        _o = _interval - (end-start).total_seconds()
        if _o > 0:
            time.sleep(_o)
            
    