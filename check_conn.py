#!/usr/bin/env python

"""
Author: Nick Russo (njrusmc@gmail.com)
Purpose: Test SSH/CLI connectivity to all devices by issuing
the "show inventory" command and printing the AggregateResult.
"""

from nornir import InitNornir
from nornir.core.filter import F
from nornir_utils.plugins.functions import print_result
from nornir_scrapli.tasks import send_command
from umbrella_tasks import Umbrella, get_tunnels


def main():

    nr = InitNornir()

    umbrella = Umbrella(nr.inventory.hosts["umbrella"].data)
    tunnels = umbrella.get_tunnels()
    print(tunnels)

    nr_devices = nr.filter(~F(name="umbrella"))
    print_result(nr_devices.run(task=send_command, command="show crypto session brief"))


if __name__ == "__main__":
    main()
