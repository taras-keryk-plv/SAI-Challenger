import sys
import os
import sys
import pytest
import ptf.dataplane
from ptf import config
import random
import time
import signal
import logging
from saichallenger.common.sai_testbed import SaiTestbedMeta
from saichallenger.common.sai_dataplane.ptf.sai_ptf_dataplane import SaiPtfDataPlane

# The default configuration dictionary for PTF
config_default = {
    # Miscellaneous options
    "list"               : False,
    "list_test_names"    : False,
    "allow_user"         : False,
    
    # Test selection options
    "test_spec"          : "",
    "test_file"          : None,
    "test_dir"           : None,
    "test_order"         : "default",
    "test_order_seed"    : 0xABA,
    "num_shards"         : 1,
    "shard_id"           : 0,
    
    # Switch connection options
    "platform"           : "eth",
    "platform_args"      : None,
    "platform_dir"       : None,
    "interfaces"         : [],
    "port_info"          : {},
    "device_sockets"     : [],  # when using nanomsg
    
    # Logging options
    "log_file"           : "ptf.log",
    "log_dir"            : None,
    "debug"              : "verbose",
    "profile"            : False,
    "profile_file"       : "profile.out",
    "xunit"              : False,
    "xunit_dir"          : "xunit",
    
    # Test behavior options
    "relax"              : False,
    "test_params"        : None,
    "failfast"           : False,
    "fail_skipped"       : False,
    "default_timeout"    : 2.0,
    "default_negative_timeout": 0.1,
    "minsize"            : 0,
    "random_seed"        : None,
    "disable_ipv6"       : False,
    "disable_vxlan"      : False,
    "disable_erspan"     : False,
    "disable_geneve"     : False,
    "disable_mpls"       : False,
    "disable_nvgre"      : False,
    "disable_igmp"       : False,
    "disable_rocev2"     : False,
    "qlen"               : 100,
    "test_case_timeout"  : None,
    
    # Socket options
    "socket_recv_size": 4096,
    
    # Packet manipulation provider module
    "packet_manipulation_module": "ptf.packet_scapy",
    
    # Other configuration
    "port_map": None,
}

def pytest_addoption(parser):
    parser.addoption("--testbed", action="store", default=None, help="Testbed name")

    
def to_ptf_int_list(port_map):
    ports = [f"{m['alias']}@{m['name']}" for m in port_map]
    return " ".join([f"--interface {port}" for port in ports]).split(" ")

@pytest.fixture(scope="session", autouse=True)
def set_ptf_params(request):
    sai_ptf_dataplane = SaiPtfDataPlane()
    sai_ptf_dataplane.setConfig(config_default)
    sai_ptf_dataplane.init()

    yield

    sai_ptf_dataplane.deinit()
