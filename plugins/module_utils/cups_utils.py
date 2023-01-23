# Copyright (c) 2022, Arnaud Patard <apatard@hupstream.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

import cups


def cups_login(module):
    def login_callback(prompt):
        return module.params["password"]

    cups.setServer(module.params["server"])
    cups.setPort(module.params["port"])
    if module.params["ssl"] is True:
        cups.setEncryption(cups.HTTP_ENCRYPT_ALWAYS)

    cups.setUser(module.params["login"])
    cups.setPasswordCB(login_callback)

    try:
        conn = cups.Connection()
    except RuntimeError as e:
        module.fail_json(msg=f"Failed to connect : {e}")

    return conn
