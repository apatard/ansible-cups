import os
import pytest

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_package(host):
    pkg = host.package("cups")
    assert pkg.is_installed


@pytest.mark.parametrize("name", [
    ("cups.service"),
    ("cups.path"),
    ("cups.socket")
])
def test_svc(host, name):
    with host.sudo():
        s = host.service(name)
        assert s.is_enabled
        if name != "cups.path":
            assert s.is_running
        v = host.ansible.get_variables()
        socket = f"tcp://{v['ansible_host']}:631"
        assert host.socket(socket).is_listening


def test_ssl(host):
    v = host.ansible.get_variables()
    with host.sudo():
        socket = f"tcp://{v['ansible_host']}:632"
        assert host.socket(socket).is_listening
    cmd = "wget -O /dev/null https://instance-cups-ssl-libvirt:632"
    host.run_expect([0], cmd)


def test_printers(host):
    with host.sudo():
        f = host.file("/etc/cups/printers.conf")
        assert b"<DefaultPrinter PDF>" in f.content
        assert b"DeviceURI cups-pdf:/" in f.content
        assert b"AllowUser root" in f.content
        assert b"AllowUser vagrant" in f.content
        assert b"Shared Yes" in f.content
