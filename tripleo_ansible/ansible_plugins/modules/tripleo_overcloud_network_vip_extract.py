#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import yaml

try:
    from ansible.module_utils import network_data_v2 as n_utils
except ImportError:
    from tripleo_ansible.ansible_plugins.module_utils import network_data_v2 as n_utils  # noqa
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.openstack.cloud.plugins.module_utils.openstack import openstack_full_argument_spec
from ansible_collections.openstack.cloud.plugins.module_utils.openstack import openstack_module_kwargs
from ansible_collections.openstack.cloud.plugins.module_utils.openstack import openstack_cloud_from_module


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tripleo_overcloud_network_vip_extract

short_description: Extract information on provisioned overcloud Virtual IPs

version_added: "2.8"

description:
    - Extract information about provisioned network Virtual IP resources in
      overcloud heat stack.

options:
  stack_name:
    description:
      - Name of the overcloud heat stack
    type: str
author:
    - Harald Jensås <hjensas@redhat.com>
'''

RETURN = '''
vip_data:
- dns_name: overcloud
  ip_address: 172.19.0.36
  name: storage_mgmt_virtual_ip
  network: storage_mgmt
  subnet: storage_mgmt_subnet
- dns_name: overcloud
  ip_address: 172.17.0.167
  name: internal_api_virtual_ip
  network: internal_api
  subnet: internal_api_subnet
- dns_name: overcloud
  ip_address: 172.18.0.83
  name: storage_virtual_ip
  network: storage
  subnet: storage_subnet
- dns_name: overcloud
  ip_address: 10.0.0.82
  name: external_virtual_ip
  network: external
  subnet: external_subnet
- dns_name: overcloud
  ip_address: 192.168.25.13
  name: control_virtual_ip
  network: ctlplane
  subnet: ctlplane-leaf1
'''

EXAMPLES = '''
- name: Get Overcloud Virtual IPs data
  tripleo_overcloud_network_vip_extract:
    stack_name: overcloud
  register: overcloud_vip_data
- name: Write Virtual IPs data to output file
  copy:
    content: "{{ overcloud_vip_data.network_data | to_yaml }}"
    dest: /path/exported-vip-data.yaml
'''


def find_net_vips(conn, stack):
    return [
        (dict(name=vip.name,
              network=conn.network.get_network(vip['network_id'])['name'],
              subnet=conn.network.get_subnet(vip.fixed_ips[0]['subnet_id'])['name'],
              ip_address=vip.fixed_ips[0]['ip_address'],
              dns_name=vip.dns_name))
        if vip.dns_name is not None else
        (dict(name=vip.name,
              network=conn.network.get_network(vip['network_id'])['name'],
              subnet=conn.network.get_subnet(vip.fixed_ips[0]['subnet_id'])['name'],
              ip_address=vip.fixed_ips[0]['ip_address']))
        for vip in conn.network.ports(tags='tripleo_stack_name={}'.format(stack))
        if [x for x in vip['tags'] if x.startswith('tripleo_vip_net=')]
    ]


def run_module():

    result = dict(
        success=False,
        changed=False,
        error="",
        vip_data=list()
    )

    argument_spec = openstack_full_argument_spec(
        **yaml.safe_load(DOCUMENTATION)['options']
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=False,
        **openstack_module_kwargs()
    )

    stack = module.params['stack_name']

    try:
        _, conn = openstack_cloud_from_module(module)

        result['vip_data'] = find_net_vips(conn, stack)
        result['changed'] = True if result['vip_data'] else False
        result['success'] = True if result['vip_data'] else False
        module.exit_json(**result)
    except Exception as err:
        result['error'] = str(err)
        result['msg'] = ("Error getting Virtual IPs data from overcloud stack "
                         "{stack_name}: %{error}".format(stack_name=stack,
                                                         error=err))
        module.fail_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
