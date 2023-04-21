import json

from saichallenger.common.sai import Sai
from saichallenger.common.sai_data import SaiData, SaiObjType
from saichallenger.common.sai_dataplane.sai_hostif_dataplane import SaiHostifDataPlane


class SaiPhy(Sai):

    def __init__(self, cfg):
        super().__init__(cfg)
        # TODO:

        self.switch_oid = "oid:0x0"
        self.dot1q_br_oid = "oid:0x0"
        self.default_vlan_oid = "oid:0x0"
        self.default_vlan_id = "0"
        self.default_vrf_oid = "oid:0x0"
        self.port_oids = []
        self.dot1q_bp_oids = []
        self.hostif_dataplane = None
        self.port_map = None
        self.hostif_map = None
        self.sku_config = None

    def get_switch_id(self):
        return self.switch_oid

    def init(self, attr):
        # Load SKU configuration if any
        if self.sku is not None:
            try:
                f = open(f"{self.asic_dir}/{self.target}/sku/{self.sku}.json")
                self.sku_config = json.load(f)
                f.close()
            except Exception as e:
                assert False, f"{e}"

        sw_attr = attr.copy()
        sw_attr.append("SAI_SWITCH_ATTR_INIT_SWITCH")
        sw_attr.append("true")
        sw_attr.append("SAI_SWITCH_ATTR_TYPE")
        sw_attr.append("SAI_SWITCH_TYPE_PHY")

        self.switch_oid = self.create(SaiObjType.SWITCH, sw_attr)
        self.rec2vid[self.switch_oid] = self.switch_oid

        port_num = self.get(self.switch_oid, ["SAI_SWITCH_ATTR_NUMBER_OF_ACTIVE_PORTS", ""]).uint32()
        print(f"==TK12==port_num={port_num}")
        if port_num > 0:
            self.port_oids = self.get(self.switch_oid,
                                     ["SAI_SWITCH_ATTR_PORT_LIST", self.make_list(port_num, "oid:0x0")]).oids()

        port_attrs = Sai.get_obj_attrs(SaiObjType.PORT)
        status, entry_oid = self.create(self.switch_oid, port_attrs, do_assert=False)

        port_num = self.get(self.switch_oid, ["SAI_SWITCH_ATTR_NUMBER_OF_ACTIVE_PORTS", ""]).uint32()
        print(f"==TK13==port_num={port_num}")

        # Update SKU
        if self.sku_config is not None:
            self.set_sku_mode(self.sku_config)

    def reset(self):
        self.cleanup()
        attr = []
        self.init(attr)