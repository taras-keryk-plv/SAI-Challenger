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
        for port_connector in sku["connector"]:
            system_side_port = port_connector["system_side"]
            line_side_port = port_connector["line_side"]
            for port in sku["port"]:
                if port["alias"] is not system_side_port and port["alias"] is not line_side_port:
                    continue

                # Create port for system or line side
                port_attr = []
                lanes = port["lanes"]
                lanes = str(lanes.count(',') + 1) + ":" + lanes
                port_attr.append("SAI_PORT_ATTR_HW_LANE_LIST")
                port_attr.append(lanes)

                # Speed
                speed = port["speed"] if "speed" in port else sku["speed"]
                port_attr.append("SAI_PORT_ATTR_SPEED")
                port_attr.append(speed)

                # Autoneg
                autoneg = port["autoneg"] if "autoneg" in port else sku["autoneg"]
                autoneg = "true" if autoneg == "on" else "false"
                port_attr.append("SAI_PORT_ATTR_AUTO_NEG_MODE")
                port_attr.append(autoneg)

                # FEC
                fec = port["fec"] if "fec" in port else sku["fec"]
                if fec == "rs":
                    fec = "SAI_PORT_FEC_MODE_RS"
                elif fec == "fc":
                    fec = "SAI_PORT_FEC_MODE_FC"
                else:
                    fec = "SAI_PORT_FEC_MODE_NONE"
                port_attr.append("SAI_PORT_ATTR_FEC_MODE")
                port_attr.append(fec)

                if port["alias"] == system_side_port:
                    system_port_oid = self.create(SaiObjType.PORT, port_attr)
                else:
                    line_port_oid = self.create(SaiObjType.PORT, port_attr)

            # Create port connector
            conn_port_oid = self.create(SaiObjType.PORT_CONNECTOR,
                                        [
                                            "SAI_PORT_CONNECTOR_ATTR_SYSTEM_SIDE_PORT_ID", system_port_oid,
                                            "SAI_PORT_CONNECTOR_ATTR_LINE_SIDE_PORT_ID",   line_port_oid
                                        ])

    def cleanup(self):
        super().cleanup()

    def reset(self):
        self.cleanup()
        attr = []
        self.init(attr)
