# Firefox

Installs firefox on Ubuntu systems and optionally creates profiles with extensions.

Extensions are installed but need to be manually enabled from firefox.

## Requirements

[xmltodict][0] and [requests][1] are needed to install extensions.

## Role Variables

```yaml
firefox_home: ~/.mozilla/firefox
```

Default directory for profiles.

```yaml
firefox_packages:
  - firefox
  - firefox-locale-en
  - firefox-locale-es
```

Packages to install.

```yaml
firefox_profiles: []
#  - name: alice
#    extensions:
#      - random-agent-spoofer
#  - name: bob
#    extensions: []
```

List of profiles with extensions. `extensions` is a list of extension names to
download and it needs to be defined (use an empty list if you don't want to
install any extensions).

## Example Playbook

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

```yaml
- hosts: localhost

  vars:
    firefox_profiles:
      - name: alice
        extensions:
          - https://addons.mozilla.org/firefox/downloads/latest/random-agent-spoofer/addon-473878-latest.xpi
      - name: bob
        extensions: []

  pre_tasks:
    - name: install role requirements
      pip: name={{ item }} state=present
      with_items:
        - xmltodict
        - requests

  roles:
     - firefox
```

License
-------

GPLv2



[0]: https://github.com/martinblech/xmltodict "xmltodict"
[1]: http://docs.python-requests.org/en/master "requests"
