import time
from saichallenger.common.sai_phy import SaiPhy


class SaiPhyImpl(SaiPhy):

    def __init__(self, cfg):
        super().__init__(cfg)

    def reset(self):
        self.cleanup()
        attr = [
            # values from SONiC
            "SAI_SWITCH_ATTR_SWITCH_PROFILE_ID", "0",
            "SAI_SWITCH_ATTR_FIRMWARE_LOAD_METHOD", "SAI_SWITCH_FIRMWARE_LOAD_METHOD_INTERNAL",
            "SAI_SWITCH_ATTR_FIRMWARE_PATH_NAME", "21:47,116,109,112,47,112,104,121,45,115,101,115,116,111,45,49,46,98,105,110,0",
            "SAI_SWITCH_ATTR_FIRMWARE_LOAD_TYPE", "SAI_SWITCH_FIRMWARE_LOAD_TYPE_AUTO",
            "SAI_SWITCH_ATTR_REGISTER_READ", "0x55da28c967f0",
            "SAI_SWITCH_ATTR_REGISTER_WRITE", "0x55da28c96930",
            "SAI_SWITCH_ATTR_HARDWARE_ACCESS_BUS",  "SAI_SWITCH_HARDWARE_ACCESS_BUS_MDIO",
            "SAI_SWITCH_ATTR_PLATFROM_CONTEXT", "0"
        ]
        self.init(attr)
