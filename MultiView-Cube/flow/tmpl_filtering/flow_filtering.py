#!/usr/bin/python3

from bcc import BPF
import yaml
import logging
from flask import Flask, request, make_response, jsonify
import os
import ctypes
import json
import os

# Todo: dynamically generate setting.yaml file

# Todo: separate configuration from this source file
# Todo: change function name and networking points at starting time
# Todo: translate human-readable IP addresses into raw numeral value
# Todo: (if possible) do not use subprocess to update and delete bpf map


class FilteringRule(ctypes.Structure):
    _fields_ = [
        ('dip', ctypes.c_uint32),
        ('sip', ctypes.c_uint32),
        ('dport', ctypes.c_uint16),
        ('sport', ctypes.c_uint16),
        ('proto', ctypes.c_uint8)
    ]


class FlowFiltering:
    def __init__(self, func_cfg):
        self._logger = logging.getLogger(__name__)

        # initialize configuration variables
        self.func_cfg = func_cfg
        self.func_name = self.func_cfg["function_name"]
        self.net_point = self.func_cfg["networking_point"]
        self.xdp_flags = self._get_xdp_flags(self.func_cfg["xdp_mode"])
        self.map_name = "flow_{}".format(self.func_name)

        if not self.func_name \
                or not self.net_point \
                or not self.xdp_flags \
                or not self.map_name:
            self._logger.error("")

        # XDP-related variables
        self.xdp = None
        self.rule_map = None

    def _get_xdp_flags(self, xdp_mode):
        # XDP flags: generic -> 1 << 1, native -> 1 << 2, hw offload -> 1 << 3
        flags = 0
        if xdp_mode == "generic":
            flags |= (1 << 1)
        elif xdp_mode == "native":
            flags |= (1 << 2)
        elif xdp_mode == "offload":
            flags |= (1 << 3)

        if flags == 0:
            return None
        else:
            return flags

    def _read_xdp_code(self, file_name):
        with open(file_name, "r") as fp:
            xdp_code = fp.read()

            if not xdp_code:
                return None

            xdp_code = xdp_code.replace("<map_name>", self.map_name)
        return xdp_code

    def _print_kernel_event(self, cpu, data, size):
        event = ctypes.cast(data, ctypes.POINTER(FilteringRule)).contents
        dip = event.dip
        sip = event.sip

        if dip != 0:
            dip = self._translate_ip_int_to_string(dip)
        if sip != 0:
            sip = self._translate_ip_int_to_string(sip)
        print("A Packet Blocked: DIP {} / SIP {} / DPORT {} / SPORT {} / PROTOCOL {}".format(dip, sip, event.dport, event.sport, event.proto))


    #
    # Public methods
    #
    def execute(self):
        # read BPF/XDP C codes
        # xdp_text = self._read_xdp_code("flow_filtering.c")

        # create BPF instance, load filtering function, attach
        xdp_text = self._read_xdp_code("flow_filtering.c")
        self._logger.debug(xdp_text)

        if not xdp_text:
            self._logger.error("Failed to read XDP C code (flow_filtering.c)")
            exit(1)

        # self.xdp = BPF(text=xdp_text, cflags=["-w", "-DKBUILD_MODNAME=%s" % self.func_name])
        self.xdp = BPF(text=xdp_text)
        # self.xdp = BPF(src="flow_filtering.c", cflags=["-w", "MAPNAME=%s" % self.map_name])
        xdp_func = self.xdp.load_func("flow_filtering", BPF.XDP)
        self.xdp.attach_xdp(self.net_point, xdp_func, self.xdp_flags)

        self.rule_map = self.xdp.get_table(self.map_name, ctypes.c_uint8, FilteringRule)

        # inject initial rules to BPF map
        self.update_rules(self.func_cfg["rules"], "add")
        self.xdp["events"].open_perf_buffer(self._print_kernel_event)
        while True:
            try:
                self.xdp.perf_buffer_poll()
            except KeyboardInterrupt:
                self.stop()
                return

    def update_rules(self, rules, task):
        # Create a JSON instance from the received rules
        # Create a rule instance (translate human-readable IP addresses into integer values)
        # Inject the rule to the XDP map
        total_res = []
        for rule in rules:
            new_rule = self._get_rule_instance(rule)

            self._logger.info(self._translate_ip_int_to_string(new_rule.dip))

            res = None
            if task in ["add", "insert"]:
                res = self._add_rule(new_rule)
            elif task in ["delete", "remove"]:
                res = self._remove_rule(new_rule)

                total_res.append("The task {} was completed: {}".format(task, rule))

        return res

    def stop(self):
        self.xdp.remove_xdp(self.net_point)
        if self.func_cfg["xdp_mode"] == "generic":
            os.system("ip link set dev {} xdpgeneric off".format(self.net_point))
        self._logger.info("Filtering function \'{}\' was terminated by keyboard interrupt".format(self.func_name))

    #
    # Private helper methods used by public functions
    #
    def _get_rule_instance(self, rule_dict):
        new_rule = FilteringRule()

        dest_ip = rule_dict.get("dest_ip", 0)
        if dest_ip != 0:
            dest_ip = self._translate_ip_string_to_int(dest_ip)
        new_rule.dip = ctypes.c_uint32(dest_ip)

        src_ip = rule_dict.get("src_ip", 0)
        if src_ip != 0:
            src_ip = self._translate_ip_string_to_int(src_ip)
        new_rule.sip = ctypes.c_uint32(src_ip)

        new_rule.dport = ctypes.c_uint16(rule_dict.get("dest_port", 0))
        new_rule.sport = ctypes.c_uint16(rule_dict.get("src_port", 0))
        new_rule.proto = ctypes.c_uint8(rule_dict.get("proto", 0))

        return new_rule

    def _translate_ip_string_to_int(self, ip_str):
        ip_str_tok = ip_str.split(".")

        ip_int = 0
        for tok in ip_str_tok:
            ip_int = (ip_int << 8) | int(tok)

        return ip_int

    def _translate_ip_int_to_string(self, ip_u32):
        ip_readable = None

        t = ip_u32
        for _ in range(0, 4):
            cur_octet = str(t & 0xFF)
            if not ip_readable:
                ip_readable = cur_octet
            elif len(ip_readable) > 0:
                ip_readable = "{}.{}".format(cur_octet, ip_readable)  # Fourth
            t = t >> 8
        return ip_readable

    def _add_rule(self, rule):
        # for k, v in sorted(self.rule_map.items(), key=lambda rule_map: rule_map[0]):
        idx = ctypes.c_uint8(len(self.rule_map) + 1)
        self.rule_map[idx] = rule
        return True

    def _remove_rule(self, rule):
        matched_rule = self.rule_map.get(rule, None)
        if matched_rule:
            self.rule_map.pop(matched_rule)
            return True
        else:
            return False


def _init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fm = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(fm)
    logger.addHandler(sh)
    return logger


def _load_function_setting():
    _file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "setting.yaml")

    with open(_file_path, 'r') as stream:
        try:
            file_str = stream.read()
            # logging.debug("Parse YAML from the file: \n" + file_str)
            if file_str:
                return yaml.load(file_str)
            else:
                return None
        except yaml.YAMLError:
            return None


if __name__ == "__main__":
    logger = _init_logger()
    func_cfg = _load_function_setting()
    if not func_cfg:
        logger.error("Failed to load \"setting.yaml\" correctly")
        exit(-1)

    filter = None
    filter = FlowFiltering(func_cfg)
    filter.execute()
    
        # app = Flask(__name__)

        # @app.route("/", methods=["GET"])
        # def check_health():
        #     resp = make_response("Flow Filter {} is activating".format(filter.func_name), 200)
        #     return resp

        # @app.route('/update', methods=['PUT'])
        # def update_rules():
        #     logging.debug("Received Data from Security Post: {}".format(request.data))
        #     req_msg = json.loads(request.data)
        #     res = filter.update_rules(req_msg["rules"], "add")

        #     resp = None
        #     if res:
        #         resp = make_response(res, 200)
        #     else:
        #         resp = make_response("Failed to update any rules", 400)
        #     return resp

        # app.run(host="0.0.0.0", port=func_cfg["api_port"])
