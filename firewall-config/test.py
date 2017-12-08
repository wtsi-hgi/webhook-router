import json

from flask.testing import FlaskClient
from firewallconfig import FirewallConfigServer, test_auth, ConfigInterface
import pytest

class InMemIO:
    def __init__(self, init_data: str):
        self.data = init_data

    def get(self):
        return self.data

    def set(self, new_data):
        self.data = new_data

@pytest.fixture()
def firewallconfig_server():
    server = FirewallConfigServer(test_auth, InMemIO(json.dumps(
        {
            "firewallRules": [],
            "adminUsers": ["test_user@sanger.ac.uk"]
        }
    )))

    return server.app.app.test_client()

@pytest.fixture()
def firewallconfig_server_other():
    server = FirewallConfigServer(test_auth, InMemIO(json.dumps(
        {
            "firewallRules": [],
            "adminUsers": ["other_user@sanger.ac.uk"]
        }
    )))

    return server.app.app.test_client()

auth = {
    "headers": {
        "user": "test_user@sanger.ac.uk"
    }
}

def test_put_and_get_config(firewallconfig_server: FirewallConfigServer):
    data = {
        "firewallRules": [],
        "adminUsers": ["test_user@sanger.ac.uk", "new_user@sanger.ac.uk"]
    }

    assert firewallconfig_server.put(
        "/config",
        data=json.dumps(data),
        content_type='application/json',
        **auth
    ).status_code == 204

    get_resp = firewallconfig_server.get(
        "/config",
        **auth
    )

    assert get_resp.status_code == 200
    assert json.loads(get_resp.data) == data

def test_is_admin_true(firewallconfig_server: FirewallConfigServer):
    isAdminResp = firewallconfig_server.get("/amIAdmin", **auth)

    assert isAdminResp.status_code == 200
    assert json.loads(isAdminResp.data) is True

def test_is_admin_false(firewallconfig_server_other: FirewallConfigServer):
    isAdminResp = firewallconfig_server_other.get("/amIAdmin", **auth)

    assert isAdminResp.status_code == 200
    assert json.loads(isAdminResp.data) is False

def test_ConfigInterface():
    interface = ConfigInterface({
        "firewallRules": [{
            "cidr": "127.0.0.0/24",
            "from_port": 1,
            "to_port": 90
        }, {
            "cidr": "128.0.0.0/31",
            "from_port": 300,
            "to_port": 400
        }],
        "adminUsers": []
    })

    assert interface.is_url_valid("http://localhost")
    assert not interface.is_url_valid("http://example.com")
    assert not interface.is_url_valid("http://localhost:100")

    assert interface.is_url_valid("http://128.0.0.1:350")