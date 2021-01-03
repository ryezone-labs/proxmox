ryezone_labs/proxmox
=========

This role configures a Proxmox PVE host for my personal lab.

Requirements
------------

proxmoxer library must be installed.

Role Variables
--------------

## API Connection Variables

| variable | required | type | description | environment |
| --- | --- | --- | --- | --- |
| `pve_api_host` | yes | string | Fully qualified hostname of the Proxmox VE Server. | |
| `pve_api_user` | yes | string | Proxmox VE User to use for API authentication. | |
| `pve_api_password` | no | string | Proxmox VE User password to use for API authentication.  Not required when `pve_api_token_id` and `pve_api_token_secret` are provided. | PROXMOX_PASSWORD |
| `pve_api_token_id` | no | string | Proxmox VE User token id to use for API authentication.  Not required when `pve_api_password` is provided. | |
| `pve_api_token_secret` | no | string | Proxmox VE User token secret to use for API authentication.  Not required when `pve_api_password` is provided. | PROXMOX_TOKEN_SECRET |

## Top Level variables

| variable | required | type | description | default |
| --- | --- | --- | --- | --- |
| `pve_roles` | yes | list[role_object] | List of Proxmox VE roles to create. | null |
| `pve_removed_roles` | yes | list[string] | List of Proxmox VE roles to remove. | null |
| `pve_users` | yes | list[user_object] | List of Proxmox VE users to create. | null |
| `pve_removed_users` | yes | list[string] | List of Proxmox VE users to remove. | null |
| `pve_acls` | yes | list[acl_object] | List of Proxmox VE ACLs to set. | null |
| `pve_removed_acls` | yes | list[acl_object] | List of Proxmox VE ACLs to set. | null |
| `pve_user_passwords` | yes | list[password_object] | List of Proxmox VE User Passwords to set. | null |

## role_object

| variable | required | type | description | default |
| --- | --- | --- | --- | --- |
| `roleid` | yes | string | Name of the role to create. | |
| `append` | no | bool | When `true` appends privileges to role, otherwise overwrites. | `false` |
| `privs` | no | list[string] | List of Proxmox VE Privileges to add to the role. | null |

## user_object

| variable | required | type | description | default |
| --- | --- | --- | --- | --- |
| `userid` | yes | string | Name of the user to create. | |
| `comment` | no | string | Comment describing the user. | |
| `email` | no | string | Email address of the user. | |
| `enable` | no | bool | When `true` marks the user as enabled, otherwise marks user as disabled. | `true` |
| `expire` | no | int | Account expiration date (seconds since epoch).  `0` means no expiration date. | `0` |
| `firstname` | no | string | First name of the user. | |
| `groups` | no | list[string] | Groups to assign to the user. | |
| `keys` | no | string | Comma separated list of Yubico keys for two factor authentication. | |
| `lastname` | no | string | Last name of the user. | |

## acl_object

| variable | required | type | description | default |
| --- | --- | --- | --- | --- |
| `path` | yes | string | ACL Path to modify. | |
| `roleid` | yes | string | Role name to grant to user, roles and tokens. | |
| `users` | no | list[string] | List of users to grant `roleid`.  Not required if `groups` or `tokens` is provided. | |
| `groups` | no | list[string] | List of groups to grant `roleid`.  Not required if `users` or `tokens` is provided. | |
| `propagate` | no | bool | When `true` allows ACL permission to be inherited. | `true` |
| `tokens` | no | list[string] | List of tokens to grant `roleid`.  Not required if `users` or `groups` is provided. | |

## password_object

 variable | required | type | description | default |
| --- | --- | --- | --- | --- |
| `userid` | yes | string | Proxmox VE User to set the password for. | |
| `password` | yes | string | Proxmox VE User Password | |

Dependencies
------------

None.

Example Playbook
----------------

```yaml
- hosts: 127.0.0.1
  gather_facts: false
  roles:
    - ryezone_labs.proxmox
  vars:
    pve_api_user: root@pam
    pve_api_password: r00t_P@$$w0rd!
    pve_api_host: proxmox.example.com
    pve_roles:
      - roleid: Packer
        privs:
          - VM.Config.Disk
          - VM.Config.CPU
          - VM.Config.Memory
          - Datastore.AllocateSpace
          - Sys.Modify
          - VM.Config.Options
          - VM.Allocate
          - VM.Audit
          - VM.Console
          - VM.Config.CDROM
          - VM.Config.Network
          - VM.PowerMgmt
          - VM.Config.HWType
          - VM.Monitor
    pve_users:
      - userid: packer_automation@pve
    pve_acls:
      - path: / 
        roleid: Packer
        users:
          - packer_automation@pve
    pve_user_passwords:
      - userid: packer_automation@pve
        password: packer
```

License
-------

GPL-2.0-or-later

Author Information
------------------

Esten Rye
- [LinkedIn](https://www.linkedin.com/in/estenrye/)
- [GitHub: estenrye](https://github.com/estenrye/)
- [GitHub: ryezone-labs](https://github.com/ryezone-labs)
