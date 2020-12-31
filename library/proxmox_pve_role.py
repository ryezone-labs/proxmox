#!/usr/bin/python3
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: proxmox_pve_role
short_description: management of Proxmox PVE Roles
description:
  - allows you to create, modify and delete Proxmox PVE Roles
options:
  api_host:
    description:
      - the host of the Proxmox VE Cluster
      - required.
    type: str
  api_password:
    description:
      - the password to authenticate with
      - can be supplied with the PROXMOX_PASSWORD environment variable.
      - not necessary if api_token_id and api_token_secret are specified.
    type: str
  api_token_id:
    description:
      - the api token id to authenticate with
      - can be supplied with the PROXMOX_TOKEN_ID environment variable.
      - not necessary if api_password is specified.
      - if specified, api_token_secret must also be specified.
    type: str
  api_token_secret:
    description:
      - the api token secret to authenticate with
      - can be supllied with the PROXMOX_TOKEN_SECRET environment variable.
      - not necessary if api_password is specified.
      - if specified, api_token_id must also be specified.
    type: str
  api_user:
    description:
      - the user to authenticate with.
      - required.
    type: str
  roleid:
    description:
      - the Proxmox VE roleid to create, modify or delete.
      - required.
    type: str
  append:
    description:
      - when true, tells Proxmox VE API to append to the current value rather
        than overwrite it.
      - optional, default: false
  privs:
    description:
      - list of Proxmox Privileges to grant to the role.
      - optional, default: []
author: Esten Rye
'''

import os
import json

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

def get_role(proxmox, roleid):
  roles = []
  try:
    roles = proxmox.access.roles.get()
  except Exception as e:
    return {
      'failed': True,
      'msg': 'API failure encoutered. %s' % str(e),
      'result': None
    }

  role = list(filter(lambda x: x['roleid'] == roleid, roles))
  if len(role) == 0:
    return {
      'failed': False,
      'result': None
    }
  return {
    'failed': False,
    'result': role[0]
  }

def present(proxmox, role_object):
  roleid = role_object['roleid']
  current_role_object = get_role(proxmox, roleid)
  if current_role_object['failed']:
    return current_role_object
  
  if current_role_object['result']:
    HAS_CHANGED = False
    try:
      proxmox_role = proxmox.access.roles(roleid)
      proxmox_role.put(
        append=role_object['append'],
        privs=role_object['privs']
      )      
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }
    updated_role_object = get_role(proxmox, roleid)
    if updated_role_object['failed']:
      return updated_role_object
    
    HAS_CHANGED = False
    for key in updated_role_object['result'].keys():
      if key == 'keys':
        continue
      elif current_role_object['result'][key] == updated_role_object['result'][key]:
        continue
      else:
        HAS_CHANGED = True
        break
  
    return {
      'changed': HAS_CHANGED,
      'msg': 'Proxmox PVE Role %s already exists.' % roleid
    }
  else:
    try:
      proxmox.access.roles.post(
        roleid=role_object['roleid'],
        privs=role_object['privs']
      )
      return {
        'changed': True, 
        'msg': 'created Proxmox PVE Role %s' % roleid
      }
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }

def absent(proxmox, role_object):
  roleid = role_object['roleid']
  current_role_object = get_role(proxmox, roleid)
  if current_role_object['failed']:
    return current_role_object

  if current_role_object['result']:
    try:
      proxmox_role = proxmox.access.roles(roleid)
      proxmox_role.delete()
      return {
        'changed': True, 
        'msg': 'deleted Proxmox PVE User %s' % roleid
      }
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }
  else:
    return {
      'changed': False,
      'msg': 'Proxmox PVE User %s does not exist.' % roleid
    }

def main():
  module = AnsibleModule(
    argument_spec=dict(
      state=dict(type='str', default='present', choices=['present', 'absent']),
      api_host=dict(type='str', required=True),
      api_password=dict(type='str', no_log=True),
      api_token_id=dict(type='str', no_log=True),
      api_token_secret=dict(type='str', no_log=True),
      api_user=dict(type='str', required=True),
      api_validate_certs=dict(type='bool', default=True),
      roleid=dict(type='str', required=True),
      append=dict(type='bool', default=False, required=False),
      privs=dict(type='list', default=[], required=False),
    )
  )

  if not HAS_PROXMOXER:
    module.fail_json(msg='proxmoxer required for this module')
  
  state = module.params['state']
  api_host = module.params['api_host']
  api_password = module.params['api_password']
  api_token_id = module.params['api_token_id']
  api_token_secret = module.params['api_token_secret']
  api_user = module.params['api_user']
  api_validate_certs = module.params['api_validate_certs']
  privs = list(module.params['privs'])
  append = 1 if module.params['append'] else 0
  role_object = {
    'roleid': module.params['roleid'],
    'append': append,
    'privs': ",".join(privs),
  }

  auth_args = {'user': api_user}

  if api_token_id and not api_token_secret:
    try:
      api_token_secret = os.environ['PROXMOX_TOKEN_SECRET']
    except KeyError as e:
      module.fail_json(msg='You should set api_token_secret param or use PROXMOX_TOKEN_SECRET environment variable')
  
  if not (api_token_id and api_token_secret):
    # If password not set get it from PROXMOX_PASSWORD env
    if not api_password:
      try:
        api_password = os.environ['PROXMOX_PASSWORD']
      except KeyError as e:
        module.fail_json(msg='You should set api_password param or use PROXMOX_PASSWORD environment variable')
    auth_args['password'] = api_password
  else:
    auth_args['token_name'] = api_token_id
    auth_args['token_value'] = api_token_secret

  proxmox = None
  try:
    proxmox = ProxmoxAPI(api_host, verify_ssl=api_validate_certs, **auth_args)
  except Exception as e:
    module.fail_json(msg='authorization on proxmox cluster failed with exception: %s' % e)
  
  result = {}
  if state == 'present':
    result = present(proxmox, role_object)
  elif state == 'absent':
    result = absent(proxmox, role_object)
  else:
    module.fail_json(msg='invalid state `%s`.  Expected `present` or `absent`.' % state)
    return
  
  if 'changed' in result:
    module.exit_json(changed=result['changed'], msg=result['msg'])
  else:
    module.fail_json(msg=result['msg'])

if __name__ == '__main__':
    main()