import pytest
from saichallenger.common.sai_data import SaiObjType
from saichallenger.common.sai import Sai

port_attrs = Sai.get_obj_attrs(SaiObjType.PORT)
port_attrs_default = {}
port_attrs_updated = {}


@pytest.fixture(scope="module", autouse=True)
def skip_all(testbed_instance):
    testbed = testbed_instance
    if testbed is not None and len(testbed.phy) != 1:
        pytest.skip("invalid for \"{}\" testbed".format(testbed.meta.name))

@pytest.mark.parametrize(
    "attr,attr_type",
    port_attrs
)
def test_get_before_set_attr(phy, dataplane, attr, attr_type):#, attr_val):
    status, entry_oid = phy.create(SaiObjType.PORT, port_attrs, do_assert=False)

@pytest.mark.parametrize(
    "attr,attr_value",
    [
        ("SAI_PORT_ATTR_OPER_STATUS", "true"),
        ("SAI_PORT_ATTR_ADMIN_STATE",               "true"),
        ("SAI_PORT_ATTR_ADMIN_STATE",               "false"),
        ("SAI_PORT_ATTR_PORT_VLAN_ID",              "100"),
        ("SAI_PORT_ATTR_DEFAULT_VLAN_PRIORITY",     "3"),
        ("SAI_PORT_ATTR_DROP_UNTAGGED",             "true"),
        ("SAI_PORT_ATTR_DROP_UNTAGGED",             "false"),
        ("SAI_PORT_ATTR_DROP_TAGGED",               "true"),
        ("SAI_PORT_ATTR_DROP_TAGGED",               "false"),
        ("SAI_PORT_ATTR_INTERNAL_LOOPBACK_MODE",    "SAI_PORT_INTERNAL_LOOPBACK_MODE_PHY"),
        ("SAI_PORT_ATTR_INTERNAL_LOOPBACK_MODE",    "SAI_PORT_INTERNAL_LOOPBACK_MODE_NONE"),
        ("SAI_PORT_ATTR_INTERNAL_LOOPBACK_MODE",    "SAI_PORT_INTERNAL_LOOPBACK_MODE_MAC"),
        ("SAI_PORT_ATTR_UPDATE_DSCP",               "true"),
        ("SAI_PORT_ATTR_UPDATE_DSCP",               "false"),
        ("SAI_PORT_ATTR_MTU",                       "9000"),
        ("SAI_PORT_ATTR_TPID",                      "37120"),   # TPID=0x9100
    ],
)
def test_set_attr(phy, dataplane, sai_port_obj, attr, attr_value):
    import pdb; pdb.set_trace()
    status = phy.set(sai_port_obj, [attr, attr_value], False)
    phy.assert_status_success(status)

    if status == "SAI_STATUS_SUCCESS":
        port_attrs_updated[attr] = attr_value
