import json
from saichallenger.common.sai import Sai
from saichallenger.common.sai_data import SaiData, SaiObjType
from saichallenger.common.sai_dataplane.sai_hostif_dataplane import SaiHostifDataPlane


class SaiPhy(Sai):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.switch_oid = "oid:0x0"
        self.port_oids = []

    def get_switch_id(self):
        return self.switch_oid

    def init(self, attr):

        sw_attr = attr.copy()
        sw_attr.append("SAI_SWITCH_ATTR_INIT_SWITCH")
        sw_attr.append("true")
        sw_attr.append("SAI_SWITCH_ATTR_TYPE")
        sw_attr.append("SAI_SWITCH_TYPE_PHY")

        self.switch_oid = self.create(SaiObjType.SWITCH, sw_attr)
        self.rec2vid[self.switch_oid] = self.switch_oid

        #system-side
        sys_side_oid = self.create(SaiObjType.PORT,
                            [
                                "SAI_PORT_ATTR_HW_LANE_LIST", "2:202,203",
                                "SAI_PORT_ATTR_SPEED",        "40000",
                            ])
        #line-side
        line_side_oid = self.create(SaiObjType.PORT,
                            [
                                "SAI_PORT_ATTR_HW_LANE_LIST", "2:2,3",
                                "SAI_PORT_ATTR_SPEED",        "40000",
                            ])
        #system-line port connector
        status = self.create(SaiObjType.PORT_CONNECTOR,
                            [
                                "SAI_PORT_CONNECTOR_ATTR_SYSTEM_SIDE_PORT_ID",        sys_side_oid,
                                "SAI_PORT_CONNECTOR_ATTR_LINE_SIDE_PORT_ID",          line_side_oid
                            ])
        port_num = self.get(self.switch_oid, ["SAI_SWITCH_ATTR_NUMBER_OF_ACTIVE_PORTS", ""]).uint32()
        if port_num > 0:
            self.port_oids = self.get(self.switch_oid,
                                     ["SAI_SWITCH_ATTR_PORT_LIST", self.make_list(port_num, "oid:0x0")]).oids()

    def cleanup(self):
        super().cleanup()

    def reset(self):
        self.cleanup()
        attr = []
        self.init(attr)
