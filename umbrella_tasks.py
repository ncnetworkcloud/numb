#!/usr/bin/env python

from nornir.core.task import Result
import httpx


class Umbrella:
    def __init__(self, mgmt_api_dict):

        # Copy constructor inputs for reference
        self.org_id = mgmt_api_dict["org_id"]
        self.api_key = mgmt_api_dict["api_key"]
        self.api_secret = mgmt_api_dict["api_secret"]
        self.sites = mgmt_api_dict["sites"]

        # Build API-relevant attributes to simplify interaction
        self.base_url = (
            f"https://management.api.umbrella.com/v1/"
            f"organizations/{self.org_id}/tunnels"
        )

        self.basic_auth = (self.api_key, self.api_secret)

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # self.client = httpx.Client()  # comparable to requests.session()

    def get_tunnels(self):
        resp = httpx.get(
            url=self.base_url, auth=self.basic_auth, headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()

    def create_tunnel(self, name, secret):

        # Assemble tunnel body
        body = {
            "name": name,
            "deviceType": "ISR",
            "transport": {"protocol": "IPSec"},
            "authentication": {
                "type": "PSK",
                "parameters": {"idPrefix": name, "secret": secret},
            },
        }

        # Issue HTTP POST request to create new tunnel
        resp = httpx.post(
            url=self.base_url, auth=self.basic_auth, headers=self.headers, json=body
        )

        resp.raise_for_status()
        return resp.json()

    def rekey_tunnel(self, name, secret, tunnel_id):

        # Assemble rekey body
        body = {
            "deprecateCurrentKeys": True,
            "autoRotate": False,
            "psk": {"idPrefix": name, "secret": secret},
        }

        # Issue HTTP POST request to rekey tunnel specified by ID
        resp = httpx.post(
            url=f"{self.base_url}/{tunnel_id}/keys",
            auth=self.basic_auth,
            headers=self.headers,
            json=body,
        )

        resp.raise_for_status()
        return resp.json()
