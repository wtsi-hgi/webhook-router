import json

from configserver import ConfigServer, test_auth
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
    server = ConfigServer(
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
def test_route_uuid(webhook_server: ConfigServer) -> str:
    new_route = webhook_server.depatcher.resolve_name("create_route")({
        "name": "route",
        "destination": "127.0.0.1"
    })
    
    return new_route[0]["uuid"]

def test_create_route(router_app: FlaskClient):
    create_route_resp = router_app.post(
        "/create-route",
        data=json.dumps({
            "name": "route",
            "destination": "127.0.0.1"
        }),
        content_type='application/json',
        **auth
    )

    assert create_route_resp.status_code == 201

def test_get(router_app: FlaskClient, test_route_uuid: str):
    assert router_app.get(f"/routes/{test_route_uuid}").status_code == 200


def test_patch(router_app: FlaskClient, test_route_uuid: str):
    assert router_app.patch(
        f"/routes/{test_route_uuid}",
        data=json.dumps({
            "name": "new-name"
        }),
        content_type='application/json',
        **auth
    ).status_code == 204

    assert json.loads(router_app.get(f"/routes/{test_route_uuid}").data)["name"] == "new-name"

@pytest.mark.usefixtures("test_route_uuid")
def test_get_all(router_app: FlaskClient):
    all_routes_resp = router_app.get("/routes")

    assert all_routes_resp.status_code == 200

    data = json.loads(all_routes_resp.data)
    assert len(data) == 1 and data[0]["name"] == "route"


def test_delete(router_app: FlaskClient, test_route_uuid: str):
    assert router_app.delete(f"/routes/{test_route_uuid}").status_code == 204

    assert len(json.loads(router_app.get("/routes").data)) == 0


def test_regenerate(router_app: FlaskClient, test_route_uuid: str):
    prev_token = json.loads(router_app.get(f"/routes/{test_route_uuid}").data)["token"]

    resp = router_app.post(f"/routes/{test_route_uuid}/regenerate")

    assert resp.status_code == 200
    assert json.loads(resp.data)["token"] != prev_token

def test_add_user_link(router_app: FlaskClient, test_route_uuid: str):
    test_auth = {
        "headers": {
            "user": "other_user@sanger.ac.uk"
        }
    }

    assert router_app.post(f"/links/{test_route_uuid}", **test_auth).status_code == 201

    assert len(json.loads(router_app.get("/routes", **test_auth).data)) == 1

def test_remove_user_link(router_app: FlaskClient, test_route_uuid: str):
    test_auth = {
        "headers": {
            "user": "other_user@sanger.ac.uk"
        }
    }

    test_add_user_link(router_app, test_route_uuid)

    assert router_app.delete(f"/links/{test_route_uuid}", **test_auth).status_code == 204

    assert len(json.loads(router_app.get("/routes", **test_auth).data)) == 0

def test_stats(router_app: FlaskClient, test_route_uuid: str):
    pass
    # TODO get elasticsearch running on test
    # assert router_app.get(f"/routes/{test_route_uuid}/statistics").status_code == 200