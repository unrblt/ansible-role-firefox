# Firefox

Installs firefox and optionally creates profiles with extensions.
Extensions are installed but need to be manually enabled from firefox.
It's only been tested in Ubuntu, but should work on other systems as long as
you set the right packages in `firefox_packages`.

## Requirements

[xmltodict][0] and [requests][1] are required on the remote host to install
extensions.

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

```yaml
firefox_preferences: {}
#  alice:
#    browser.safebrowsing.enabled: 'false'
#    browser.safebrowsing.malware.enabled: 'false'
```

Dictionary with preference and value (keyed by profile name). This preferences
are written to a `user.js` file in the profile directory which means any change
you make to that setting in the options and preference dialogs or via
`about:config` will be lost when you restart firefox.

## Example Playbook

```yaml
- hosts: localhost

  vars:
    firefox_profiles:
      - name: alice
        extensions:
          - random-agent-spoofer
          - https-everywhere
          - noscript
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
