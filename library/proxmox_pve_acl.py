#!/usr/bin/python3
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: proxmox_pve_acl
short_description: management of Proxmox PVE ACLs
description:
  - allows you to create, modify and delete Proxmox PVE ACLs
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
  path:
    description:
      - the Proxmox VE Access Control PATH to modify.
      - required.
    type: str
  roleid:
    description:
      - Proxmox VE role to grant to users or groups.
      - required.
    type: string
  state:
    description:
      - when `absent` deletes roles from Proxmox VE ACL, otherwise roles are added.
      - optional, default: present, choices[present, absent]
    type: bool
  groups:
    description:
      - List of Proxmox VE Groups to be granted `roles`.
      - optional, default: []
    type: list
  propagate:
    description:
      - when true enables permissions inheritance, otherwise inheritance is
        disabled.
      - optional, default: true
    type: bool
  tokens:
    description:
      - List of Proxmox VE API Tokens to be granted `roles`.
      - optional, default: []
    type: list
  users:
    description:
      - List of Proxmox VE Users to be granted `roles`.
      - optional, default: []
    type: list
  
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

def get_acl_object(acls, acl_path, roleid):
  return dict(
    acl_path=acl_path,
    roleid=roleid,
    users=[ acl['ugid'] for acl in list(
      filter(lambda x: filter_acl(x, acl_path, roleid, 'user'), acls)
    )],
    groups=[ acl['ugid'] for acl in list(
      filter(lambda x: filter_acl(x, acl_path, roleid, 'group'), acls)
    )],
    tokens=[ acl['ugid'] for acl in list(
      filter(lambda x: filter_acl(x, acl_path, roleid, 'token'), acls)
    )],
  )

def filter_acl(acl, path, roleid, identity_type):
  return acl['path'] == path and acl['roleid'] == roleid and acl['type'] == identity_type

def get_acl(proxmox, acl_path, roleid):
  try:
    acls = proxmox.access.acl.get()
  except Exception as e:
    return {
      'failed': True,
      'msg': 'API failure encoutered. %s' % str(e),
      'result': None
    }
  
  acl = get_acl_object(acls, acl_path, roleid)

  return {
    'failed': False,
    'result': acl
  }

def present(proxmox, args):
  current_acl = get_acl(proxmox, args['acl_path'], args['roleid'])
  
  if current_acl['failed']:
    return current_acl
  
  try:
    proxmox.access.acl.put(
      path=args['acl_path'],
      roles=[args['roleid']],
      delete=0,
      groups=args['groups'],
      propagate=args['propagate'],
      tokens=args['tokens'],
      users=args['users']
    )      
  except Exception as e:
    return {
      'failed': True,
      'msg': 'API failure encountered.  %s' % str(e)
    }
  updated_acl = get_acl(proxmox, args['acl_path'], args['roleid'])
  if updated_acl['failed']:
    return updated_acl
    
  HAS_CHANGED = False
  for key in updated_acl['result'].keys():
    if key == 'keys':
      continue
    elif current_acl['result'][key] == updated_acl['result'][key]:
      continue
    else:
      HAS_CHANGED = True
      break
  
  return {
    'changed': HAS_CHANGED,
    'msg': 'Proxmox PVE ACL on path %s for roleid %s already exists.' % (args['acl_path'], args['roleid'])
  }

def absent(proxmox, args):
  current_acl = get_acl(proxmox, args['acl_path'], args['roleid'])
  
  if current_acl['failed']:
    return current_acl

  if current_acl['result']:
    try:
      proxmox.access.acl.put(
        path=args['acl_path'],
        roles=[args['roleid']],
        delete=1,
        groups=args['groups'],
        propagate=args['propagate'],
        tokens=args['tokens'],
        users=args['users']
      )      
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }
    updated_acl = get_acl(proxmox, args['acl_path'], args['roleid'])

    HAS_CHANGED = False
    for key in updated_acl['result'].keys():
      if key == 'keys':
        continue
      elif current_acl['result'][key] == updated_acl['result'][key]:
        continue
      else:
        HAS_CHANGED = True
        break

    return {
      'changed': HAS_CHANGED,
      'msg': 'Proxmox PVE ACL on path %s for roleid %s was removed.' % (args['acl_path'], args['roleid'])
    }
  else:
    return {
      'changed': False,
      'msg': 'Proxmox PVE ACL on path %s for roleid %s does not exist.' % (args['acl_path'], args['roleid'])
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
      path=dict(type='str', required=True),
      roleid=dict(type='str', required=True),
      groups=dict(type='list', default=[], required=False),
      propagate=dict(type='bool', default=True, required=False),
      tokens=dict(type='list', default=[], required=False),
      users=dict(type='list', default=[], required=False)
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
  args = {
    'acl_path': module.params['path'],
    'roleid': module.params['roleid'],
    'groups': module.params['groups'],
    'propagate': 1 if module.params['propagate'] else 0,
    'tokens': module.params['tokens'],
    'users': module.params['users']
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
    result = present(proxmox, args)
  elif state == 'absent':
    result = absent(proxmox, args)
  else:
    module.fail_json(msg='invalid state `%s`.  Expected `present` or `absent`.' % state)
    return
  
  if 'changed' in result:
    module.exit_json(changed=result['changed'], msg=result['msg'])
  else:
    module.fail_json(msg=result['msg'])

if __name__ == '__main__':
    main()