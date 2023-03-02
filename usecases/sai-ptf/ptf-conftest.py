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


# Map from strings to debugging levels
DEBUG_LEVELS = {
    "debug"              : logging.DEBUG,
    "verbose"            : logging.DEBUG,
    "info"               : logging.INFO,
    "warning"            : logging.WARNING,
    "warn"               : logging.WARNING,
    "error"              : logging.ERROR,
    "critical"           : logging.CRITICAL,
}

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

def import_base_modules():
    sys.path.insert(0, '/sai-challenger/ptf/src')

import_base_modules()


@pytest.fixture(scope="session", autouse=True)
def set_ptf_params(request):
    if request.config.option.testbed:
        tb_params = SaiTestbedMeta("/sai-challenger", request.config.option.testbed)
        ports = to_ptf_int_list(tb_params.config['dataplane'][0]['port_groups'])
    else:
        ports = ""
    
    # provide required PTF runner params to avoid exiting with an error
    # sys.argv = ['ptf.py','--test-dir', '/sai-challenger/usecases/sai-ptf/SAI/ptf', *ports]
    # import_base_modules()

    # load PTF runner module to let it collect test params into ptf.config
    import imp
    print("PTF params: ", config)
    
    import ptf

    ptf.config.update(config_default)
    logging_setup(config)
    xunit_setup(config)
    logging.info("++++++++ " + time.asctime() + " ++++++++")

    # import after logging is configured so that scapy error logs (from importing
    # packet.py) are silenced and our own warnings are logged properly.
    import ptf.testutils

    # Try parsing test params and log them
    # We do this before importing the test modules in case test parameters are being
    # accessed at test import time.
    #ptf.testutils.TEST_PARAMS = test_params_parse(config)

    # Initiallize port information
    ptf.testutils.PORT_INFO = config["port_info"]

    if config["platform_dir"] is None:
        from ptf import platforms

    config["platform_dir"] = os.path.dirname(os.path.abspath(platforms.__file__))

    # Allow platforms to import each other
    sys.path.append(config["platform_dir"])

    # Load the platform module
    platform_name = config["platform"]
    logging.info("Importing platform: " + platform_name)

    if platform_name == "nn":
        try:
            import nnpy
        except:
            logging.critical("Cannot use 'nn' platform if nnpy package is not installed")
            sys.exit(1)

    platform_mod = None
    try:
        platform_mod = imp.load_module(
            platform_name, *imp.find_module(platform_name, [config["platform_dir"]])
        )
    except:
        logging.warn("Failed to import " + platform_name + " platform module")
        raise

    try:
        platform_mod.platform_config_update(config)
    except:
        logging.warn("Could not run platform host configuration")
        raise

    if config["port_map"] is None:
        logging.critical("Interface port map was not defined by the platform. Exiting.")
        sys.exit(1)

    logging.debug("Configuration: " + str(config))
    logging.info("port map: " + str(config["port_map"]))

    ptf.ptfutils.default_timeout = config["default_timeout"]
    ptf.ptfutils.default_negative_timeout = config["default_negative_timeout"]
    ptf.testutils.MINSIZE = config["minsize"]

    if os.getuid() != 0 and not config["allow_user"] and platform_name != "nn":
        logging.critical("Super-user privileges required. Please re-run with sudo or as root.")
        sys.exit(1)

    if config["random_seed"] is not None:
        logging.info("Random seed: %d" % config["random_seed"])
        random.seed(config["random_seed"])
    else:
        # Generate random seed and report to log file
        seed = random.randrange(100000000)
        logging.info("Autogen random seed: %d" % seed)
        random.seed(seed)

    # Remove python's signal handler which raises KeyboardError. Exiting from an
    # exception waits for all threads to terminate which might not happen.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    #---------------------------------
    # Set up the dataplane
    ptf.dataplane_instance = ptf.dataplane.DataPlane(config)
    pcap_setup(config)

    for port_id, ifname in config["port_map"].items():
        device, port = port_id
        ptf.dataplane_instance.port_add(ifname, device, port)

    yield

    ptf.dataplane_instance.stop_pcap()
    ptf.dataplane_instance.kill()
    ptf.dataplane_instance = None


def pytest_addoption(parser):
    parser.addoption("--testbed", action="store", default=None, help="Testbed name")
    
def to_ptf_int_list(port_map):
    ports = [f"{m['alias']}@{m['name']}" for m in port_map]
    return " ".join([f"--interface {port}" for port in ports]).split(" ")

def logging_setup(config):
    """
    Set up logging based on config
    """

    logging.getLogger().setLevel(DEBUG_LEVELS[config["debug"]])

    if config["log_dir"] != None:
        if os.path.exists(config["log_dir"]):
            import shutil

            shutil.rmtree(config["log_dir"])
        os.makedirs(config["log_dir"])
    else:
        if os.path.exists(config["log_file"]):
            os.remove(config["log_file"])

    ptf.open_logfile("main")

def xunit_setup(config):
    """
    Set up xUnit output based on config
    """

    if not config["xunit"]:
        return

    if os.path.exists(config["xunit_dir"]):
        import shutil

        shutil.rmtree(config["xunit_dir"])
    os.makedirs(config["xunit_dir"])

def pcap_setup(config):
    """
    Set up dataplane packet capturing based on config
    """

    if config["log_dir"] == None:
        filename = os.path.splitext(config["log_file"])[0] + ".pcap"
        ptf.dataplane_instance.start_pcap(filename)
    else:
        # start_pcap is called per-test in base_tests
        pass
