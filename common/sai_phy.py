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

        # Update PHY SKU
        if self.sku_config is not None:
            self.set_sku_mode(self.sku_config)

        port_num = self.get(self.switch_oid, ["SAI_SWITCH_ATTR_NUMBER_OF_ACTIVE_PORTS", ""]).uint32()
        if port_num > 0:
            self.port_oids = self.get(self.switch_oid,
                                     ["SAI_SWITCH_ATTR_PORT_LIST", self.make_list(port_num, "oid:0x0")]).oids()

    def set_sku_mode(self, sku):
        for port in sku["interfaces"]:
            name = port["name"]
            # system side
            port_attr = []
            lanes = ""
            lane_list = port["system_lanes"]
            for lane in lane_list:
                lanes += str(lane)
                lanes += ","
            lanes = str(len(lane_list)) + ":" + lanes[:-1]
            port_attr.append("SAI_PORT_ATTR_HW_LANE_LIST")
            port_attr.append(lanes)
            speed = str(port["system_speed"])
            port_attr.append("SAI_PORT_ATTR_SPEED")
            port_attr.append(speed)
            system_port_oid = self.create(SaiObjType.PORT, port_attr)

            # line side
            port_attr = []
            lanes = ""
            lane_list = port["line_lanes"]
            for lane in lane_list:
                lanes += str(lane)
                lanes += ","
            lanes = str(len(lane_list)) + ":" + lanes[:-1]
            port_attr.append("SAI_PORT_ATTR_HW_LANE_LIST")
            port_attr.append(lanes)
            speed = str(port["line_speed"])
            port_attr.append("SAI_PORT_ATTR_SPEED")
            port_attr.append(speed)
            line_port_oid = self.create(SaiObjType.PORT, port_attr)

            #system-line port connector
            conn_port_oid = self.create(SaiObjType.PORT_CONNECTOR,
                                [
                                    "SAI_PORT_CONNECTOR_ATTR_SYSTEM_SIDE_PORT_ID", system_port_oid,
                                    "SAI_PORT_CONNECTOR_ATTR_LINE_SIDE_PORT_ID",   line_port_oid
                                ])
            self.port_oids.append(conn_port_oid)

    def cleanup(self):
        super().cleanup()

    def reset(self):
        self.cleanup()
        attr = []
        self.init(attr)
