#!/usr/bin/env python

from nornir.core.task import Result
import httpx

def _extract_data(task):
    data = task.host.data

    url = (
        f"https://management.api.umbrella.com/v1/"
        f"organizations/{data['org_id']}/tunnels"
    )

    auth = (data["api_key"], data["api_secret"])

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    return {"url": url, "auth": auth, "headers": headers}


def get_tunnels(task):
    """
    Nornir task to issue a NETCONF get_config RPC with optional keyword
    arguments. The source argument uses "running" by default.
    """

    kwargs = _extract_data(task)
    get_resp = httpx.get(**kwargs)
    if not get_resp.is_error:
        return Result(host=task.host, result=get_resp.json())

    return Result(host=task.host, result=False)
