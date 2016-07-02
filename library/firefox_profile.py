#!/usr/bin/python

from ansible.module_utils.basic import *
from collections import OrderedDict
import os.path
import subprocess
import ConfigParser
import shutil

class FirefoxConfigWrapper:
    """Wrapper around file object to remove spaces around .ini file delimiters.

    Taken from http://stackoverflow.com/a/25084055.
    """

    output_file = None
    def __init__(self, new_output_file):
        self.output_file = new_output_file

    def write(self, what):
        self.output_file.write(what.replace(" = ", "="))


class FirefoxProfiles:
    """Class to manage firefox profiles."""

    def __init__(self, path):
        self.path = os.path.expanduser(path)
        self.profiles_ini = os.path.join(self.path, 'profiles.ini')
        self.config = ConfigParser.RawConfigParser()
        # Make options case sensitive
        self.config.optionxform = str
        self.read()

    def read(self):
        self.config.read(self.profiles_ini)
        self.sections = OrderedDict()
        for section in self.config.sections():
            if section != 'General':
                profile = dict(self.config.items(section))
                self.sections[profile['Name']] = section

    def write(self):
        # Reorder the current sections, otherwise firefox deletes them on start.
        new = ConfigParser.ConfigParser()
        new.optionxform = str
        new.add_section('General')
        for item in self.config.items('General'):
            new.set('General', item[0], item[1])

        index = 0
        for section in self.sections.values():
            new_section = 'Profile%d' % index
            new.add_section(new_section)
            for item in self.config.items(section):
                new.set(new_section, item[0], item[1])
            index += 1

        with open(self.profiles_ini, 'wb') as config_file:
            new.write(FirefoxConfigWrapper(config_file))

        # Update state with the new file.
        self.read()

    def get(self, name):
        if name in self.sections:
            return dict(self.config.items(self.sections[name]))

    def get_path(self, name):
        profile = self.get(name)
        if profile is not None:
            if (bool(profile['IsRelative'])):
                return os.path.join(self.path, profile['Path'])
            return profile['Path']

    def delete(self, name):
        profile = self.get(name)
        if profile is not None:
            shutil.rmtree(self.get_path(name))
            self.sections.pop(name)
            self.write()

    def create(self, name):
        command = 'firefox -no-remote -CreateProfile %s' % name
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        self.read()



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
    profiles = FirefoxProfiles(module.params['path'])
    name = module.params['name']
    path = profiles.get_path(name)
    changed = False
    if module.params['state'] == 'present' and profiles.get(name) is None:
        profiles.create(name)
        changed = True
        path = profiles.get_path(name)
    elif module.params['state'] == 'absent' and profiles.get(name) is not None:
        profiles.delete(name)
        changed = True
    module.exit_json(changed=changed, profile_name=name, profile_path=path)


if __name__ == '__main__':
    main()
