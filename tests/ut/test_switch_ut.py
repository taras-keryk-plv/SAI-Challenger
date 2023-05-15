import pytest
from saichallenger.common.sai import Sai

switch_attrs = Sai.get_obj_attrs("SAI_OBJECT_TYPE_SWITCH")

@pytest.mark.parametrize(
    "attr,attr_type",
    switch_attrs
)
def test_get_attr(asic_type, dataplane, attr, attr_type):
    status, data = asic_type.get_by_type(asic_type.switch_oid, attr, attr_type, do_assert = False)
    asic_type.assert_status_success(status)
