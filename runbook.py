#!/usr/bin/env python

"""
Author: Nick Russo (njrusmc@gmail.com)
Purpose: Provision new Umbrella SIG tunnels or rekey existing ones then
configure the Cisco device side using IOS or ASA platforms. Also performs
a validation to ensure the tunnel was formed successfully.
"""

from nornir import InitNornir
from nornir.core.filter import F
from nornir_utils.plugins.functions import print_result
from nornir_scrapli.tasks import send_command, send_config
from umbrella_tasks import Umbrella

from jinja2 import Environment, FileSystemLoader

import string
import random
import time


def manage_tunnel(task, umbrella, tunnels):
    """
    Three step process:
    1. Configure tunnel on Umbrella
    2. Configure tunnel on router
    3. Perform verification checks
    """

    # No matter what, a new secret is needed, so generate it first
    secret = _generate_secret()

    # Umbrella SIG names must be at least 8 characters, so
    # append the org's domain name (helps with uniqueness, too)
    name = f"{task.host.name}.{task.host['domain_name']}"

    # Tunnel to device does not exist; create a new one
    if not name in tunnels.keys():
        print(f"{name}: SIG tunnel not present; adding new")
        resp = umbrella.create_tunnel(name, secret)
        print(f"{name}: SIG tunnel created with ID {resp['id']}")
        config_type = "full"

    # Tunnel to device already exists; perform an IKEv2 key refresh
    else:
        tunnel_id = tunnels[name]
        print(f"{name}: SIG tunnel present with ID {tunnel_id}; rekeying")
        resp = umbrella.rekey_tunnel(name, secret, tunnel_id)
        config_type = "rekey"

    # print(json.dumps(sig, indent=2))

    # Setup the jinja2 templating environment and render the template
    j2_env = Environment(
        loader=FileSystemLoader("."), trim_blocks=True, autoescape=True
    )
    template = j2_env.get_template(f"templates/isr_{config_type}.j2")

    # Assemble the data necessary for the templating process
    data = {
        "sig": resp,
        "umbrella_sites": umbrella.sites,
        "tunnel": task.host["tunnel"],
    }

    new_config = template.render(data=data)
    # print(new_config)

    # Send configuration to device
    task.run(task=send_config, config=new_config)
    tun_dest = data["tunnel"]["dest_ip"]

    # Verify tunnel on IOS side, could take a few minutes
    for i in range(30):
        time.sleep(10)
        print(f"{name}: Attempt {i+1} to verify client tunnel connectivity")
        sess_resp = task.run(
            task=send_command,
            command=f"show crypto session remote {tun_dest} | include ^Session_status",
        )

        # If the crypto session is up, continue
        if "UP-ACTIVE" in sess_resp.result:
            print(f"{name}: OK - Client tunnel to {tun_dest} is up")

            # If the FIB entry to the Internet looks correct, continue
            cef_resp = task.run(
                task=send_command, command="show ip cef 8.8.8.8"
            )
            if "attached to Tunnel100" in cef_resp.result:
                print(f"{name}: OK - Upstream default route is correct")

                # If the ping test through the SIG tunnel succeeds, break loop
                ping_resp = task.run(
                    task=send_command,
                    command="ping 8.8.8.8 size 1440 df-bit",
                )
                if "100 percent" in ping_resp.result:
                    print(f"{name}: OK - Ping to 8.8.8.8 succeeded")
                    break

                # Else, the ping failed and traffic isn't flowing
                print(f"{name}: FAIL - Ping to 8.8.8.8 failed")

            # Else, the FIB entry was not correct
            else:
                print(f"{name}: FAIL - Upstream default route is incorrect")


def main():

    nr = InitNornir()

    # Get the currently configured Umbrella tunnels
    umbrella = Umbrella(nr.inventory.hosts["umbrella"].data)
    raw_tunnels = umbrella.get_tunnels()

    # Extract only the "name" of each tunnel, which is equal to the
    # Nornir "task.host.name" attribute from the inventory
    tunnels = {tunnel["name"]: tunnel["id"] for tunnel in raw_tunnels}

    # Get all non-Umbrella devices (remote sites) and build the tunnels
    nr_devices = nr.filter(~F(name="umbrella"))
    aresult = nr_devices.run(
        task=manage_tunnel, umbrella=umbrella, tunnels=tunnels
    )


def _generate_secret(length=16):
    """
    Generate password of specified length with at least one digit,
    uppercase letter, and lowercase letter. This is used as the
    IKEv2 PSK on both sides of the tunnel.
    """

    # Need 1 each: uppercase, lowercase, digit
    pw_minimum = [
        random.choice(string.digits),
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
    ]

    # Fill in the remaining N-3 characters
    pw_rest = [
        random.choice(string.digits + string.ascii_letters)
        for i in range(length - 3)
    ]

    # Randomize the letters and return the password as a string
    pw_list = pw_minimum + pw_rest
    random.shuffle(pw_list)
    return "".join(pw_list)


if __name__ == "__main__":
    main()
