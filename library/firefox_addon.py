#!/usr/bin/python

from ansible.module_utils.basic import *
from tempfile import mkdtemp
from urlparse import urlsplit
from zipfile import ZipFile
from collections import OrderedDict
import ConfigParser
import shutil
import os
import xmltodict
import requests

class FirefoxExtension:
    def __init__(self, uri, profile_path):
        self.uri = uri
        self.profile_path = profile_path
        self.filename = urlsplit(self.uri).path.split('/')[-1]
        self.download_path = os.path.join(mkdtemp(), self.filename)
        self._download()
        self._parse_rdf()
        self.destination = os.path.join(profile_path, 'extensions', '%s.xpi' % self.id)

    def _download(self):
        r = requests.get(self.uri, stream=True)
        if r.status_code == 200:
            with open(self.download_path, 'wb') as f:
                for chunk in r:
                    f.write(chunk)

    def _parse_rdf(self):
        xpi = ZipFile(self.download_path)
        self.rdf = xmltodict.parse(xpi.open('install.rdf').read())
        self.id = self.rdf['RDF']['Description']['em:id']

    def is_installed(self):
        return os.path.isfile(self.destination)

    def install(self):
        path = os.path.dirname(self.destination)
        try:
            os.makedirs(path, 0700)
        except OSError:
            if not os.path.isdir(path):
                raise
        shutil.move(self.download_path, self.destination)

    def uninstall(self):
        os.remove(self.destination)


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
        'uri': {'required': True, 'type': 'str'},
        'profile': {'default': 'default', 'type': 'str'},
        'path': {'default': '~/.mozilla/firefox', 'type': 'str'},
        'state': {
            'default': 'present',
            'choices': ['present', 'absent'],
            'type': 'str',
        },
    }
    module = AnsibleModule(argument_spec=fields)
    profiles = FirefoxProfiles(module.params['path'])
    profile = profiles.get(module.params['profile'])

    if profile is None:
        module.fail_json(msg='Profile %s not found' % module.params['profile'])

    path = profiles.get_path(module.params['profile'])
    addon = FirefoxExtension(module.params['uri'], path)
    changed = False
    result = None

    try:
        if module.params['state'] == 'present' and not addon.is_installed():
            addon.install()
            changed = True
            result = {'id': addon.id, 'uri': addon.uri, 'name': addon.filename}
        elif module.params['state'] == 'absent' and addon.is_installed():
            addon.uninstall()
            changed = True
        module.exit_json(changed=changed, meta=result)
    except Exception as e:
        module.fail_json(msg=e.message)


if __name__ == '__main__':
    main()
