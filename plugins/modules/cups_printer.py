#!/usr/bin/python
# Copyright (c) 2022, Arnaud Patard <apatard@hupstream.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.apatard.cups.plugins.module_utils.cups_utils import (
    cups_login,
)

import cups

DOCUMENTATION = """
---
module: cups_printer
author: "Arnaud Patard"
short_description: Add/Remove printer to cups
description:
   - Add/Remove printer to cups
   - This module is only adding or removing so if some attribute has to be changed,
     it can't be done with this module.
options:
   name:
     description:
        - name of printer
     required: true
   state:
     description:
        - state of the key (present / absent)
     required: true
   server:
     description:
        - host running CUPS
     required: true
   port:
     description:
        - host port CUPS is listening to
     required: false
   ssl:
     description:
        - Use SSL for connecting
     required: false
   login:
     description:
        - account
     required: true
   password:
     description:
        - password of account
     required: true
   device_uri:
     description:
        - printer uri
   filename:
     description:
        - local filename of PPD file
   ppdname:
     description:
        - name of an PPD known to cups
   info:
     description:
        - human-readable information about the printe
   location:
     description:
        - human-readable printer location

"""


def add_printer(conn, module):
    try:
        printers = conn.getPrinters()
    except cups.IPPError as e:
        del conn
        module.fail_json(msg=f"Failed to get printers list: {e}")

    try:
        devices = conn.getDevices()  # noqa: F821
    except cups.IPPError as e:
        del conn  # noqa: F821
        module.fail_json(msg=f"Failed to get device list: {e}")

    name = module.params["name"]
    uri = module.params["device_uri"]
    filename = module.params["filename"]
    ppdname = module.params["ppdname"]
    info = module.params["info"]
    location = module.params["location"]

    if name in printers:
        del conn
        module.exit_json(changed=False)

    if uri not in devices:
        del conn
        module.fail_json(msg=f"Device {name} not known to cups")

    kwargs = {"name": name, "device": uri}
    if filename is not None:
        kwargs["filename"] = filename
    if ppdname is not None:
        kwargs["ppdname"] = ppdname
    if info is not None:
        kwargs["info"] = info
    if location is not None:
        kwargs["location"] = location
    if not module.check_mode:
        try:
            conn.addPrinter(**kwargs)  # noqa: F821
        except cups.IPPError as e:
            del conn
            module.fail_json(msg=f"Failed to add printer {name}: {e}")
    module.exit_json(changed=True)


def rm_printer(conn, module):
    name = module.params["name"]

    try:
        printers = conn.getPrinters()
    except cups.IPPError as e:
        del conn
        module.fail_json(msg=f"Failed to get printers list: {e}")

    if name not in printers:
        del conn
        module.exit_json(changed=False)

    if not module.check_mode:
        try:
            conn.deletePrinter(name=name)  # noqa: F821
        except cups.IPPError as e:
            del conn
            module.fail_json(msg=f"Failed to delete printer {name}: {e}")
    module.exit_json(changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(
                required=True,
                choices=["present", "absent"],
            ),
            server=dict(required=True),
            port=dict(required=False, default=631, type='int'),
            ssl=dict(required=False, default=False, type='bool'),
            login=dict(required=True),
            password=dict(required=True, no_log=True),
            device_uri=dict(required=False),
            filename=dict(required=False),
            ppdname=dict(required=False),
            info=dict(required=False),
            location=dict(required=False),
        ),
        required_if=[
            ("state", "present", ["device_uri"], True),
        ],
        mutually_exclusive=[("ppdname", "filename")],
        supports_check_mode=True,
    )

    conn = cups_login(module)

    if module.params["state"] == "present":
        add_printer(conn, module)
    else:
        rm_printer(conn, module)

    del conn
    module.fail_json(msg="Should not be reached")


if __name__ == "__main__":
    main()
