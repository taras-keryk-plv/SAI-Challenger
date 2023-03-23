import ipaddress
import pytest
import time
from saichallenger.common.sai_data import SaiObjType
from ptf.testutils import simple_tcp_packet, send_packet, verify_packets, verify_packet, verify_no_packet_any, verify_no_packet, verify_any_packet_any_port

def test_l2_trunk_to_trunk_vlan_dd(npu, dataplane):
    """
    Description:
    Check trunk to trunk VLAN members forwarding

    #1. Create a VLAN 10
    #2. Add two ports as tagged members to the VLAN
    #3. Setup static FDB entries for port 1 and port 2
    #4. Send a simple vlan tag (10) packet on port 1 and verify packet on port 2
    #5. Clean up configuration
    """
    vlan_id = "10"
    macs = ['00:11:11:11:11:11', '00:22:22:22:22:22']

    create_vlan = {
                "name": "vlan_10",
                "op": "create",
                "type": "SAI_OBJECT_TYPE_VLAN",
                "attributes": [
                    "SAI_VLAN_ATTR_VLAN_ID", vlan_id
                ]
    }
    vlan_oid = npu.command_processor.process_command(create_vlan)
    create_vlan_member1 = {
                "name": "vlan_member1",
                "op": "create",
                "type": "SAI_OBJECT_TYPE_VLAN_MEMBER",
                "attributes": [
                    "SAI_VLAN_MEMBER_ATTR_VLAN_ID", vlan_oid,
                    "SAI_VLAN_MEMBER_ATTR_BRIDGE_PORT_ID", npu.dot1q_bp_oids[0],
                    "SAI_VLAN_MEMBER_ATTR_VLAN_TAGGING_MODE", "SAI_VLAN_TAGGING_MODE_TAGGED"
                ]
    }
    npu.command_processor.process_command(create_vlan_member1)
    create_vlan_member2 = {
                "name": "vlan_member2",
                "op": "create",
                "type": "SAI_OBJECT_TYPE_VLAN_MEMBER",
                "attributes": [
                    "SAI_VLAN_MEMBER_ATTR_VLAN_ID", vlan_oid,
                    "SAI_VLAN_MEMBER_ATTR_BRIDGE_PORT_ID", npu.dot1q_bp_oids[1],
                    "SAI_VLAN_MEMBER_ATTR_VLAN_TAGGING_MODE", "SAI_VLAN_TAGGING_MODE_TAGGED"
                ]
    }
    npu.command_processor.process_command(create_vlan_member2)
    create_fdb1 = {
                "name": "fdb1",
                "op": "create",
                "type": "SAI_OBJECT_TYPE_FDB_ENTRY",
                "key": {
                    "bv_id": vlan_oid,
                    "mac_address": macs[0],
                    "switch_id" : npu.switch_oid
                },
                "attributes": [
                    "SAI_FDB_ENTRY_ATTR_TYPE", "SAI_FDB_ENTRY_TYPE_STATIC",
                    "SAI_FDB_ENTRY_ATTR_BRIDGE_PORT_ID", npu.dot1q_bp_oids[0],
                    "SAI_FDB_ENTRY_ATTR_PACKET_ACTION", "SAI_PACKET_ACTION_FORWARD"
                ]
    }
    npu.command_processor.process_command(create_fdb1)
    create_fdb2 = {
                "name": "fdb2",
                "op": "create",
                "type": "SAI_OBJECT_TYPE_FDB_ENTRY",
                "key": {
                    "bv_id": vlan_oid,
                    "mac_address": macs[1],
                    "switch_id" : npu.switch_oid
                },
                "attributes": [
                    "SAI_FDB_ENTRY_ATTR_TYPE", "SAI_FDB_ENTRY_TYPE_STATIC",
                    "SAI_FDB_ENTRY_ATTR_BRIDGE_PORT_ID", npu.dot1q_bp_oids[1],
                    "SAI_FDB_ENTRY_ATTR_PACKET_ACTION", "SAI_PACKET_ACTION_FORWARD"
                ]
    }
    npu.command_processor.process_command(create_fdb2)

    try:
        if npu.run_traffic:
            pkt = simple_tcp_packet(eth_dst=macs[1],
                                    eth_src=macs[0],
                                    dl_vlan_enable=True,
                                    vlan_vid=10,
                                    ip_dst='10.0.0.1',
                                    ip_id=101,
                                    ip_ttl=64)

            send_packet(dataplane, 0, pkt)
            verify_packets(dataplane, pkt, [1])
    finally:
        remove_fdb2 = {
                "name": "fdb2",
                "op": "remove",
                "type": "SAI_OBJECT_TYPE_FDB_ENTRY"
        }
        res = npu.command_processor.process_command(remove_fdb2)
        assert res == "SAI_STATUS_SUCCESS"
        remove_fdb1 = {
                "name": "fdb1",
                "op": "remove",
                "type": "SAI_OBJECT_TYPE_FDB_ENTRY"
        }
        res = npu.command_processor.process_command(remove_fdb1)
        assert res == "SAI_STATUS_SUCCESS"
        remove_vlan_member2 = {
                "name": "vlan_member2",
                "op": "remove",
                "type": "SAI_OBJECT_TYPE_VLAN_MEMBER"
        }
        res = npu.command_processor.process_command(remove_vlan_member2)
        assert res == "SAI_STATUS_SUCCESS"
        remove_vlan_member1 = {
                "name": "vlan_member1",
                "op": "remove",
                "type": "SAI_OBJECT_TYPE_VLAN_MEMBER"
        }
        res = npu.command_processor.process_command(remove_vlan_member1)
        assert res == "SAI_STATUS_SUCCESS"
        remove_vlan = {
                "name": "vlan_10",
                "op": "remove",
                "type": "SAI_OBJECT_TYPE_VLAN"
        }
        res = npu.command_processor.process_command(remove_vlan)
        assert res == "SAI_STATUS_SUCCESS"
