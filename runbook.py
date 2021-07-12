#!/usr/bin/env python

"""
Author: Nick Russo (njrusmc@gmail.com)
Purpose: Provision new Umbrella SIG tunnels or rekey existing ones then
configure the Cisco device side using IOS or ASA platforms. Also performs
a validation to ensure the tunnel was formed successfully.
"""

from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_scrapli.tasks import send_command

def build_tunnel(task):
    result = task.run(send_command, command="show inventory")

def main():

    nr = InitNornir()
    aresult = nr.run(task=build_tunnel)
    print_result(aresult)


if __name__ == "__main__":
    main()
