import re
from itertools import zip_longest
import ipaddress
import json
from sai_thrift import sai_headers
from sai_thrift.ttypes import *
from sai_thrift import ttypes
from sai_thrift.sai_headers import *
from saichallenger.common.sai_client.sai_thrift_client.sai_thrift_metadata import SaiMetadata
from saichallenger.common.sai_data import SaiObjType, SaiStatus


class ThriftConverter():
    def convert_attributes_to_thrift(attributes, obj_type):
        """
        [ "SAI_SWITCH_ATTR_PORT_LIST", "2:oid:0x0,oid:0x0" ] => { "port_list": sai_thrift_object_list_t(count=2, idlist=[0x0, 0x0]) }
        """
        for name, value in ThriftConverter.chunks(attributes, 2):
            yield ThriftConverter.convert_attribute_name_to_thrift(name), ThriftConverter.convert_value_to_thrift(value, ThriftConverter.get_attribute_type(name), name, obj_type)

    def convert_key_to_thrift(object_type, key = None):
        """
        Converts dictionary 'key' to the thrift key entry according to 'object_type':
        "vip_entry", { "switch_id": oid:0x0, "vip": "192.168.0.1" } => { "vip_entry": sai_thrift_vip_entry_t(switch_id = 0x0, vip = sai_ip_address_t("192.168.0.1"...)) }
        """
        if key is None:
            return {}

        key_t = getattr(ttypes, f'sai_thrift_{object_type}_t')
        if "vr" in key:
            key['vr_id'] = key['vr']
            del key['vr']
        if "dest" in key:
            key['destination'] = key['dest']
            del key['dest']
        return { object_type: key_t(**ThriftConverter.convert_key_values_to_thrift(object_type, key)) }

    def convert_attributes_from_thrift(attributes, attr_name, obj_type):
        """
        TODO:
        [ ("SAI_SWITCH_ATTR_PORT_LIST", sai_thrift_object_list_t(...)), ("port_list", sai_thrift_object_list_t(...)) ] => [ "SAI_SWITCH_ATTR_PORT_LIST", "2:0x0,0x0" }
        """
        result_attrs = []
        for name, value in (attributes or {}).items():
            if not name.startswith('SAI'):
                continue
            result_attrs.append(name)
            #result_attrs.append(ThriftConverter.convert_value_from_thrift(value, ThriftConverter.get_attribute_type(name)))
            result_attrs.append(ThriftConverter.convert_value_from_thrift(value, ThriftConverter.get_attribute_type(name), attr_name, obj_type))

        return result_attrs


    # CONVERT TO THRIFT
    @staticmethod
    def convert_attribute_name_to_thrift(attr):
        """
        "SAI_SWITCH_ATTR_PORT_LIST" => "port_list"
        """
        return re.search('SAI_.*_ATTR_(.*)', attr).group(1).lower()

    @staticmethod
    def convert_value_to_thrift(value, value_type, attr_name=None, obj_type=None):
        """
        "100", "s32" => 100
        """
        if value_type in [ 's8', 'u8', 's16', 'u16', 's32',
                           'u32', 's64', 'u64', 'ptr',
                           'encrypt_key', 'authkey',
                           'macsecsak', 'macsecauthkey', 'macsecsalt' ]:
            if isinstance(value, str):
                actual_value = getattr(sai_headers, value, None)
                if actual_value != None:
                    return actual_value
                #else:
                #    actual_value = ThriftConverter.get_str_by_enum(obj_type, attr_name, value)
                #    if actual_value != None:
                #        return actual_value
            return 0 if value == '' else int(value)
        if value_type in [ 'booldata' ]:
            return value.lower() == "true" or value == "0"
        if value_type in [ 'mac', 'ipv4', 'ipv6', 'chardata' ]:
            return str(value)
        if value_type in [ 'oid' ]:
            return ThriftConverter.object_id(value)
        if value_type in [ 'ipaddr' ]:
            return ThriftConverter.sai_ipaddress(value)
        if value_type in [ 'ipprefix' ]:
            return ThriftConverter.sai_ipprefix(value)
        if value_type in [ 'objlist' ]:
            return ThriftConverter.sai_object_list(value)
        if value_type in [ 'u8list', 'u16list', 'u32list', 's8list', 's16list', 's32list' ]:
            return ThriftConverter.sai_int_list(value_type, value, attr_name, obj_type)
        if value_type in [ 'u32range' , 's32range', 'u16range' ]:
            return ThriftConverter.sai_int_range(value_type, value)
        if value_type in [ 'maplist' ]:
            return ThriftConverter.sai_map_list(value)
        # TODO: add more string->thrift converters here
        raise NotImplementedError

    @staticmethod
    def convert_key_values_to_thrift(object_type, key):
        """
        "vip_entry", { "switch_id": "oid:0x0", "vip": "192.186.0.1" } => { "switch_id": 0, "vip": sai_thrift_ip_address_t('192.168.0.1'...) }
        """
        key_spec = getattr(ttypes, f'sai_thrift_{object_type}_t').thrift_spec

        result = {}
        for spec_entry in key_spec[1:]:
            key_attr_name = spec_entry[2]
            key_attr_type = spec_entry[3]
            result[key_attr_name] = ThriftConverter.convert_value_to_thrift(key[key_attr_name], ThriftConverter.get_value_type_by_thrift_spec(key_attr_type))
        return result

    @staticmethod
    def get_attribute_type(attr_name):
        """
        "SAI_SWITCH_ATTR_PORT_LIST" => "objlist"
        """
        if attr_name == 'SAI_FDB_FLUSH_ATTR_ENTRY_TYPE':
            return "s32"
        elif attr_name == 'SAI_FDB_FLUSH_ATTR_BRIDGE_PORT_ID':
            return "oid"
        elif attr_name == 'SAI_FDB_FLUSH_ATTR_BV_ID':
            return "oid"
        return SaiMetadata[attr_name]

    @staticmethod
    def sai_object_list(object_list):
        """
        "2:oid:0x1,oid:0x2" => sai_thrift_object_list_t(count=2, idlist=[1,2])
        """
        splitted = object_list.split(':', 1)
        count = int(splitted[0])
        idlist = [ ThriftConverter.object_id(item) for item in splitted[1].split(',') ]
        return sai_thrift_object_list_t(count=count, idlist=idlist)

    @staticmethod
    def sai_int_list(value_type, value_data, attr_name, obj_type):
        """
        "4:1,2,3,4" => sai_thrift_{type}_list_t(count=4, {type}list=[1,2,3,4])
        """
        splitted = value_data.split(':', 1)
        count = int(splitted[0])
        thrift_list = [ int(item) for item in splitted[1].split(',') ]
        sai_thrift_class = getattr(ttypes, 'sai_thrift_{}_list_t'.format(value_type[:-4]))
        return sai_thrift_class(count, thrift_list)

    @staticmethod
    def sai_int_range(value_type, range):
        """
        "1,7" => sai_thrift_{}_range_t(min=1, max=7)
        """
        splitted = range.split(',')
        sai_thrift_class = getattr(ttypes, 'sai_thrift_{}_range_t'.format(value_type[:-5]))
        return sai_thrift_class(min=splitted[0], max=splitted[1])

    @staticmethod
    def sai_map_list(value):
        """
        {"count":1,"list":[{"key":0,"value":0}]} =>  sai_thrift_map_list_t(count=1, maplist=[{"key":0,"value":0}])
        """
        thrift_list = []
        val = json.loads(value)
        cnt = val["count"]
        thrift_list = val["list"]
        prio_to_pg = sai_thrift_map_t(thrift_list)
        map_list = sai_thrift_map_list_t(maplist=[prio_to_pg], count=cnt)

    @staticmethod
    def sai_ipaddress(addr_str):
        """
        "192.168.0.1" => sai_thrift_ip_address_t('192.168.0.1'...)
        """

        if '.' in addr_str:
            family = SAI_IP_ADDR_FAMILY_IPV4
            addr = sai_thrift_ip_addr_t(ip4=addr_str)
        elif ':' in addr_str:
            family = SAI_IP_ADDR_FAMILY_IPV6
            addr = sai_thrift_ip_addr_t(ip6=addr_str)
        else:
            return None

        return sai_thrift_ip_address_t(addr_family=family, addr=addr)

    @staticmethod
    def sai_ipprefix(prefix_str):
        """
        "192.168.1.0/24" => sai_thrift_ip_prefix_t(ip='192.168.1.0', mask='255.255.255.0')
        """
        if '/' not in prefix_str:
            print("Invalid IP prefix format")
            return None

        if '.' in prefix_str:
            family = SAI_IP_ADDR_FAMILY_IPV4
            ip = ipaddress.IPv4Network(prefix_str)
            addr = sai_thrift_ip_addr_t(ip4=str(ip.network_address))
            mask = sai_thrift_ip_addr_t(ip4=str(ip.netmask))
        elif ':' in prefix_str:
            family = SAI_IP_ADDR_FAMILY_IPV6
            ip = ipaddress.IPv6Network(prefix_str)
            addr = sai_thrift_ip_addr_t(ip6=ip.network_address.exploded)
            mask = sai_thrift_ip_addr_t(ip6=ip.netmask.exploded)
        else:
            return None

        ip_prefix = sai_thrift_ip_prefix_t(
            addr_family=family, addr=addr, mask=mask)
        return ip_prefix

    @staticmethod
    def object_id(oid):
        """
        None       => 0
        16         => 16
        "16"       => 16
        "oid:0x10" => 16
        """
        if oid == None or oid == 'null':
            return 0
        if isinstance(oid, str) and oid.startswith('oid:0x'):
            return int(oid[4:], 16)

        # FIXME: The OID always must be in "oid:0x0" format.
        #        We need this temporary workaround to handle the issue
        #        described in get_value_type_by_thrift_spec()
        return int(oid)

    # CONVERT FROM THRIFT
    @staticmethod
    def get_value_type_by_thrift_spec(thrift_spec):
        """
        sai_thrfit_ip_address_t => "ipaddr"
        """
        # FIXME: Sometimes, thrift_spec returns "None" for both "oid" and "int"
        #        E.g., For SAI_OBJECT_TYPE_DIRECTION_LOOKUP_ENTRY, thrift_spec will be
        #        (1, 10, 'switch_id', None, None), (2, 8, 'vni', None, None)
        if thrift_spec == None:
            return "oid"

        attribute_value_spec = getattr(ttypes, f'sai_thrift_attribute_value_t').thrift_spec
        for spec in attribute_value_spec[1:]:
            if spec[3] == thrift_spec:
                return spec[2]

        assert True, "Should not get here"

    @staticmethod
    def convert_value_from_thrift(value, value_type, attr_name=None, obj_type=None):
        """
        sai_thrift_ip_address_t('192.168.0.1'...), "ipaddr" => "192.168.0.1"
        """
        if value_type in [ 's8', 'u8', 's16', 'u16',
                           'u32', 's64', 'u64',
                           'ptr', 'mac', 'ipv4', 'ipv6',
                           'chardata' ]:
            return str(value)
        elif value_type in [ 's32' ]:
            actual_value = ThriftConverter.get_enum_by_str(obj_type, attr_name, value)
            return str(actual_value)
        elif value_type in [ 'booldata' ]:
            return str(value).lower()
        elif value_type in [ 'objlist' ]:
            return ThriftConverter.from_sai_object_list(value)
        elif value_type == "oid":
            return "oid:" + hex(value)
        elif value_type in [ 'u8list', 'u16list', 'u32list',
                             's8list', 's16list', 's32list' ]:
            return ThriftConverter.from_sai_int_list(value_type, value)

        # TODO: Add more thrift->string convertes here
        raise NotImplementedError

    @staticmethod
    def from_sai_object_list(object_list):
        """
        sai_thrift_object_list_t(count=2, idlist=[1,2]) => "2:oid:0x1,oid:0x2"
        """
        if object_list.count == 0:
            return '0:null'
        result = f'{object_list.count}:'
        for ii in range(object_list.count):
            result += "oid:" + hex(object_list.idlist[ii])
            result += ","
        return result[:-1]

    @staticmethod
    def from_sai_int_list(value_type, object_list):
        """
        sai_thrift_{type}_list_t(count=2, {type}list=[1,2]) => "2:1,2"
        """
        prefix = "uint" if value_type.startswith("u") else "int"
        listvar = getattr(object_list, prefix + value_type[1:])
        result = f'{object_list.count}:'
        for ii in range(object_list.count):
            result += str(listvar[ii])
            result += ","
        return result[:-1]

    @staticmethod
    def chunks(iterable, n, fillvalue=None):
        """
        Split iterable to chunks of length n
        [1, 2, 3, 4], 2 => [1, 2], [3, 4]
        """
        return zip_longest(*[iter(iterable)] * n, fillvalue=fillvalue)

    @staticmethod
    def convert_to_sai_obj_type(obj_type):
        """
        SaiObjType.PORT        => SaiObjType.PORT
        "PORT"                 => SaiObjType.PORT
        "SAI_OBJECT_TYPE_PORT" => SaiObjType.PORT
        1                      => SaiObjType.PORT
        """
        if isinstance(obj_type, SaiObjType):
            return obj_type
        elif isinstance(obj_type, str):
            prefix = 'SAI_OBJECT_TYPE_'
            obj_type_without_prefix = obj_type
            if obj_type.startswith(prefix):
                obj_type_without_prefix = obj_type[len(prefix):]
            try:
                return getattr(SaiObjType, obj_type_without_prefix)
            except AttributeError:
                return None
        elif isinstance(obj_type, int):
            return SaiObjType(obj_type)
        return None

    @staticmethod
    def convert_to_sai_status_str(status):
        """
        15                        => "SAI_STATUS_NOT_IMPLEMENTED"
        "15"                      => "SAI_STATUS_NOT_IMPLEMENTED"
        SaiStatus.NOT_IMPLEMENTED => "SAI_STATUS_NOT_IMPLEMENTED"
        """
        name = None
        if isinstance(status, SaiStatus):
            name = status.name
        elif isinstance(status, str):
            name = SaiStatus(int(status)).name
        elif isinstance(status, int):
            name = SaiStatus(status).name
        return 'SAI_STATUS_' + name

    @staticmethod
    def get_sai_meta(obj_type, attr_name):
        """Get enum member value by enum member name"""
        try:
            with open("/etc/sai/sai.json", "r") as f:
                sai_json = json.loads(f.read())
        except IOError:
            return None
        if obj_type is not None:
            if type(obj_type) == SaiObjType:
                obj_type = "SAI_OBJECT_TYPE_" + SaiObjType(obj_type).name
            else:
                assert type(obj_type) == str
                assert obj_type.startswith("SAI_OBJECT_TYPE_")
            for item in sai_json:
                if obj_type not in item.values(): continue
                attrs = item.get('attributes')
                for attr in attrs:
                    if attr_name == attr.get('name'):
                        return attr
        return sai_json

    def get_str_by_enum(obj_type, attr_name, enum_name):
        """Get enum member value by enum member name"""
        attr = ThriftConverter.get_sai_meta(obj_type, attr_name)
        if attr is None:
            return None
        try:
            return attr['properties']['values'][enum_name]
        except KeyError:
            return None

    @staticmethod
    def get_enum_by_str(obj_type, attr_name, enum_value):
        meta = ThriftConverter.get_sai_meta(obj_type, attr_name)
        if meta is None:
            return None
        if obj_type:
            try:
                values = meta['properties']['values']
                enum_name = [k for k, v in values.items() if v == enum_value]
                if enum_name:
                    return enum_name[0]
            except KeyError:
                pass
        else:
            attr_name = 'SAI_' + attr_name.upper()
            for attrs in meta:
                attr = attrs.get('attributes')
                for item in attr:
                    try:
                        val = item['properties']['values']
                        if attr_name in str(val):
                            enum_name = [k for k, v in val.items() if v == enum_value]
                            return enum_name[0]
                    except KeyError:
                        pass
        return None
