import json

from server import Server, test_auth
from flask.testing import FlaskClient
import pytest
from peewee import SqliteDatabase

auth = {
    "headers": {
        "Google-Auth-Token": "test_user"
    }
}

@pytest.fixture()
def webhook_server():
    server = Server(
        debug=True,
        db=SqliteDatabase(':memory:'),
        auth=test_auth
    )
    yield server
    server.close()

@pytest.fixture()
def router_app(webhook_server):
    return webhook_server.app.app.test_client()  # type: FlaskClient

@pytest.fixture()
def test_token(router_app: FlaskClient, webhook_server: Server) -> str:
    new_route = webhook_server.add_route({
        "name": "route",
        "destination": "127.0.0.1"
    })
    
    return new_route[0]["token"]

def test_add_route(router_app: FlaskClient):
    add_route_resp = router_app.post(
        "/add-route",
        data=json.dumps({
            "name": "route",
            "destination": "127.0.0.1"
        }),
        content_type='application/json',
        **auth
    )

    assert add_route_resp.status_code == 201

def test_get(router_app: FlaskClient, test_token: str):
    assert router_app.get(f"/routes/{test_token}").status_code == 200


def test_patch(router_app: FlaskClient, test_token: str):
    assert router_app.patch(
        f"/routes/{test_token}",
        data=json.dumps({
            "name": "new-name"
        }),
        content_type='application/json',
        **auth
    ).status_code == 204

    assert json.loads(router_app.get(f"/routes/{test_token}").data)["name"] == "new-name"

@pytest.mark.usefixtures("test_token")
def test_get_all(router_app: FlaskClient):
    all_routes_resp = router_app.get("/routes", **auth)

    assert all_routes_resp.status_code == 200

    data = json.loads(all_routes_resp.data)
    assert len(data) == 1 and data[0]["name"] == "route"


def test_delete(router_app: FlaskClient, test_token: str):
    assert router_app.delete(f"/routes/{test_token}", **auth).status_code == 204

    assert len(json.loads(router_app.get("/routes", **auth).data)) == 0


def test_regenerate(router_app: FlaskClient, test_token: str):
    resp = router_app.post(f"/routes/{test_token}/regenerate", **auth)

    assert resp.status_code == 200
    assert json.loads(resp.data)["token"] != test_token
