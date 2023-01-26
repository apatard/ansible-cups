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
short_description: Set default printer to cups
description:
   - Set printer as default one
options:
   name:
     description:
        - name of printer
     required: true
   port:
     description:
        - host port CUPS is listening to
     required: false
   ssl:
     description:
        - Use SSL for connecting
     required: false
   server:
     description:
        - host running CUPS
     required: true
   login:
     description:
        - account
     required: true
   password:
     description:
        - password of account
     required: true
"""


def set_def_printer(conn, module):

    name = module.params["name"]
    try:
        printers = conn.getPrinters()
    except cups.IPPError as e:
        del conn
        module.fail_json(msg=f"Failed to get printers list: {e}")

    if name not in printers:
        del conn
        module.fail_json(msg="Printer doesn't exist")

    cur_val = conn.getDefault()  # noqa: F821
    if cur_val != name:
        if not module.check_mode:
            try:
                conn.setDefault(name)  # noqa: F821
            except cups.IPPError as e:
                del conn
                module.fail_json(msg=f"Failed to get printers list: {e}")
        changed = True
        new_val = name
    else:
        changed = False
        new_val = cur_val

    diff = {"before": cur_val, "after": new_val}
    module.exit_json(changed=changed, diff=diff)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            server=dict(required=True),
            port=dict(required=False, default=631, type="int"),
            ssl=dict(required=False, default=False, type="bool"),
            login=dict(required=True),
            password=dict(required=True, no_log=True),
        ),
        supports_check_mode=True,
    )

    conn = cups_login(module)

    set_def_printer(conn, module)

    del conn
    module.fail_json(msg="Should not be reached")


if __name__ == "__main__":
    main()
