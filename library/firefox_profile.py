#!/usr/bin/python

from ansible.module_utils.basic import *
import glob
import os.path
import subprocess

def profile_path(name, path):
    path = os.path.expanduser(path)
    profile = glob.glob(os.path.join(path, '*.%s' % name))
    if profile:
        return profile[0]
    raise Exception('Profile %s not found' % name)

def profile_exists(name, path):
    path = os.path.expanduser(path)
    if glob.glob(os.path.join(path, '*.%s' % name)):
        return True
    return False

def create_profile(name, path):
    command = 'firefox -no-remote -CreateProfile %s' % name
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if p.returncode != 0 or not profile_exists(name, path):
        raise Exception(stderr)

def main():
    fields = {
        'name': {'required': True, 'type': 'str'},
        'path': {'default': '~/.mozilla/firefox', 'type': 'str'},
        'state': {
            'default': 'present',
            'choices': ['present', 'absent'],
            'type': 'str',
        },
    }
    module = AnsibleModule(argument_spec=fields)

    if profile_exists(module.params['name'], module.params['path']):
        changed = False
    else:
        try:
            create_profile(module.params['name'], module.params['path'])
            changed = True
        except Exception as e:
            module.fail_json(msg=e.message)

    result = {'profile_path': profile_path(module.params['name'], module.params['path'])}
    module.exit_json(changed=changed, meta=result)


if __name__ == '__main__':
    main()
