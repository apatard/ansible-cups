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
