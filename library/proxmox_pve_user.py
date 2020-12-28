#!/usr/bin/python3
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: proxmox_pve_user
short_description: management of Proxmox PVE Users
description:
  - allows you to create, modify and delete Proxmox PVE Users
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
  userid:
    description:
      - the Proxmox VE userid to create, modify or delete.
      - required.
    type: str
  realm:
    description:
      - the Proxmox VE authentication ream the user is a member of.
      - required.
    type: str
  firstname:
    description:
      - the Proxmox VE user's first name.
      - optional, default: ''
    type: str
  lastname:
    description:
      - the Proxmox VE user's last name.
      - optional, default: ''
    type: str
  email:
    description:
      - the Proxmox VE user's email address.
      - optional, default: ''
    type: str
  comment:
    description:
      - a comment describing the Proxmox VE user.
  enable:
    description:
      - enables or disables a Proxmox VE user.
      - optional, default: true
    type: bool
    default: true
  expire:
    description:
      - Account expiration date (seconds since epoch).
      - '0' means no expiration date.
      - optional, default: 0
    type: int
  keys:
    description:
      - Yubico Key Ids for two factor authentication.
      - optional, default: ''
  timeout:
    description:
      - timeout for Proxmox API operations
      - optional, default: 30 seconds
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

def get_user(proxmox, userid):
  users = []
  try:
    users = proxmox.access.users.get()
  except Exception as e:
    return {
      'failed': True,
      'msg': 'API failure encoutered. %s' % str(e),
      'result': None
    }

  user = list(filter(lambda x: x['userid'] == userid, users))
  if len(user) == 0:
    return {
      'failed': False,
      'result': None
    }
  return {
    'failed': False,
    'result': user[0]
  }

def present(proxmox, user_object):
  userid = user_object['userid']
  current_user_object = get_user(proxmox, userid)
  if current_user_object['failed']:
    return current_user_object
  
  if current_user_object['result']:
    HAS_CHANGED = False
    try:
      proxmox_user = proxmox.access.users(userid)
      proxmox_user.put(
        comment=user_object['comment'],
        email=user_object['email'],
        enable=user_object['enable'],
        firstname=user_object['firstname'],
        groups=user_object['groups'],
        keys=user_object['keys'],
        lastname=user_object['lastname']
      )      
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }
    updated_user_object = get_user(proxmox, userid)
    if updated_user_object['failed']:
      return updated_user_object
    
    HAS_CHANGED = False
    for key in updated_user_object['result'].keys():
      if key == 'keys':
        continue
      elif current_user_object['result'][key] == updated_user_object['result'][key]:
        continue
      else:
        HAS_CHANGED = True
        break
  
    return {
      'changed': HAS_CHANGED,
      'msg': 'Proxmox PVE User %s already exists.' % userid
    }
  else:
    try:
      proxmox.access.users.post(
        userid=user_object['userid'],
        comment=user_object['comment'],
        email=user_object['email'],
        enable=user_object['enable'],
        expire=user_object['expire'],
        firstname=user_object['firstname'],
        groups=user_object['groups'],
        keys=user_object['keys'],
        lastname=user_object['lastname']
      )
      return {
        'changed': True, 
        'msg': 'created Proxmox PVE User %s' % userid
      }
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }

def absent(proxmox, user_object):
  userid = user_object['userid']
  current_user_object = get_user(proxmox, userid)
  if current_user_object['failed']:
    return current_user_object

  if current_user_object['result']:
    try:
      proxmox_user = proxmox.access.users(userid)
      proxmox_user.delete()
      return {
        'changed': True, 
        'msg': 'deleted Proxmox PVE User %s' % userid
      }
    except Exception as e:
      return {
        'failed': True,
        'msg': 'API failure encountered.  %s' % str(e)
      }
  else:
    return {
      'changed': False,
      'msg': 'Proxmox PVE User %s does not exist.' % userid
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
      userid=dict(type='str', required=True),
      comment=dict(type='str', required=False),
      email=dict(type='str', required=False),
      enable=dict(type='bool', required=False, default=True),
      expire=dict(type='int', required=False, default=0),
      firstname=dict(type='str', required=False),
      groups=dict(type='list', default=[], required=False),
      keys=dict(type='str', required=False),
      lastname=dict(type='str', required=False),
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
  user_object = {
    'userid': module.params['userid'],
    'comment': module.params['comment'],
    'email': module.params['email'],
    'enable': 1 if module.params['enable'] else 0,
    'expire': module.params['expire'],
    'firstname': module.params['firstname'],
    'groups': module.params['groups'],
    'keys': module.params['keys'],
    'lastname': module.params['lastname'],
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
    result = present(proxmox, user_object)
  elif state == 'absent':
    result = absent(proxmox, user_object)
  else:
    module.fail_json(msg='invalid state `%s`.  Expected `present` or `absent`.' % state)
    return
  
  if 'changed' in result:
    module.exit_json(changed=result['changed'], msg=result['msg'])
  else:
    module.fail_json(msg=result['msg'])

if __name__ == '__main__':
    main()