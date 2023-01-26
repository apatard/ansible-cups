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
module: cups_pr_options
author: "Arnaud Patard"
short_description: Add/Remove printer to cups
description:
   - Set printer options
   - Warning: It can't unset options, only replace values.
options:
   name:
     description:
        - name of printer
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
   options:
     description:
        - dictionary of options to set
     required: true

"""


def set_printer_option(conn, module, name, attributes, option, value, check_mode):
    changed = False

    if option == "shared":
        cur_val = attributes["printer-is-shared"]
        if cur_val != value:
            if not check_mode:
                try:
                    cur_val = conn.setPrinterShared(name, value)
                except cups.IPPError as e:
                    del conn
                    module.fail_json(msg=f"Failed to set {option}: {e}")
            changed = True
            new_val = value
        else:
            changed = False
            new_val = cur_val
    elif option == "allowed_users":
        if "requesting-user-name-allowed" in attributes:
            cur_val = attributes["requesting-user-name-allowed"]
        else:
            cur_val = []
        if set(cur_val) != set(value):
            if not check_mode:
                try:
                    conn.setPrinterUsersAllowed(name, value)
                except cups.IPPError as e:
                    del conn
                    module.fail_json(msg=f"Failed to set {option}: {e}")
            changed = True
            new_val = ",".join(value)
        else:
            changed = False
            new_val = ",".join(cur_val)
        cur_val = ",".join(cur_val)
    elif option == "location":
        cur_val = attributes["printer-location"]
        if cur_val != value:
            if not check_mode:
                try:
                    cur_val = conn.setPrinterLocaltion(name, value)
                except cups.IPPError as e:
                    del conn
                    module.fail_json(msg=f"Failed to set {option}: {e}")
            changed = True
            new_val = value
        else:
            changed = False
            new_val = cur_val
    elif option == "enabled":
        cur_val = attributes["printer-state"] != cups.IPP_PRINTER_STOPPED
        if cur_val != value:
            if not check_mode:
                try:
                    if value is True:
                        conn.enablePrinter(name)
                    else:
                        conn.disablePrinter(name)
                except cups.IPPError as e:
                    del conn
                    module.fail_json(msg=f"Failed to set {option}: {e}")
            changed = True
            new_val = value
        else:
            changed = False
            new_val = cur_val
    elif option == "accept_jobs":
        cur_val = attributes["printer-is-accepting-jobs"]
        if cur_val != value:
            if not check_mode:
                try:
                    if value is True:
                        conn.acceptJobs(name)
                    else:
                        conn.rejectJobs(name)
                except cups.IPPError as e:
                    del conn
                    module.fail_json(msg=f"Failed to set {option}: {e}")
            changed = True
            new_val = value
        else:
            changed = False
            new_val = cur_val
    else:
        del conn
        module.fail_json(msg=f"Unknown/unhandeld attribute {option}")
    before = f"{option}: {cur_val}"
    after = f"{option}: {new_val}"
    return (changed, before, after)


def set_printer_options(conn, module):
    try:
        printers = conn.getPrinters()
    except cups.IPPError as e:
        del conn
        module.fail_json(msg=f"Failed to get printers list: {e}")

    name = module.params["name"]
    options = module.params["options"]

    if name not in printers:
        del conn
        module.fail_json(msg=f"Printer {name} not known to cups")

    if len(options) == 0:
        del conn
        module.fail_json(msg="Options list should not be empty")

    try:
        attrs = conn.getPrinterAttributes(name)  # noqa: F821
    except cups.IPPError as e:
        del conn  # noqa: F821
        module.fail_json(msg=f"Failed to get printers attributes: {e}")

    changed = False
    state_before = []
    state_after = []

    for k, v in options.items():
        (c, b, a) = set_printer_option(
            conn, module, name, attrs, k, v, module.check_mode  # noqa: F821
        )
        changed |= c
        state_before.append(b)
        state_after.append(a)

    diff = {
        "before": f"{','.join(state_before)}\n",
        "after": f"{','.join(state_after)}\n",
    }
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
            options=dict(type="dict", required=True),
        ),
        supports_check_mode=True,
    )

    conn = cups_login(module)

    set_printer_options(conn, module)

    del conn
    module.fail_json(msg="Should not be reached")


if __name__ == "__main__":
    main()
