import json

from configserver import ConfigServer, test_auth, get_postgres_db
from configserver.errors import InvalidRouteUUIDError
from flask.testing import FlaskClient
import pytest
from peewee import SqliteDatabase

auth = {
    "headers": {
        "user": "test_user@sanger.ac.uk"
    }
}

@pytest.fixture()
def webhook_server():
    with open("config.json") as config_file:
        config_JSON = json.load(config_file)

    server = ConfigServer(
        debug=False,
        db=get_postgres_db(),
        auth=test_auth,
        config_JSON=config_JSON
    )
    yield server
    server.close()

@pytest.fixture()
def router_app(webhook_server):
    return webhook_server.app.app.test_client()  # type: FlaskClient

@pytest.fixture()
def test_route_uuid(webhook_server: ConfigServer, router_app: FlaskClient) -> str:
    new_route = webhook_server.depatcher.resolve_name("create_route")({
        "name": "route",
        "destination": "http://127.0.0.1"
    })

    uuid = new_route[0]["uuid"]

    try:
        yield uuid
    finally:
        router_app.delete(f"/routes/{uuid}")

def test_create_route(router_app: FlaskClient):
    create_route_resp = router_app.post(
        "/create-route",
        data=json.dumps({
            "name": "route",
            "destination": "http://127.0.0.1"
        }),
        content_type='application/json',
        **auth
    )

    assert create_route_resp.status_code == 201

def test_get(router_app: FlaskClient, test_route_uuid: str):
    assert router_app.get(f"/routes/{test_route_uuid}").status_code == 200

def test_get_by_token(router_app: FlaskClient, test_route_uuid: str):
    token = json.loads(router_app.get(f"/routes/{test_route_uuid}").data)["token"]

    assert router_app.get(f"/routes/token/{token}").status_code == 200


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

    assert router_app.get(f"/routes/{test_route_uuid}").status_code == 404


def test_regenerate(router_app: FlaskClient, test_route_uuid: str):
    prev_token = json.loads(router_app.get(f"/routes/{test_route_uuid}").data)["token"]

    resp = router_app.post(f"/routes/{test_route_uuid}/regenerate")

    assert resp.status_code == 200
    assert json.loads(resp.data)["token"] != prev_token

def test_add_user_link(router_app: FlaskClient, test_route_uuid: str):
    test_auth = {
        "headers": {
            "user": "other_user-p@sanger.ac.uk"
        }
    }

    assert router_app.post(f"/links/{test_route_uuid}", **test_auth).status_code == 201

    assert len(json.loads(router_app.get("/routes", **test_auth).data)) == 1

def test_get_user_link(router_app: FlaskClient, test_route_uuid: str):
    test_auth = {
        "headers": {
            "user": "other_user-p@sanger.ac.uk"
        }
    }

    assert router_app.get(f"/links/{test_route_uuid}", **test_auth).status_code == 404

    assert router_app.get(f"/links/{test_route_uuid}").status_code == 200

def test_remove_user_link(router_app: FlaskClient, test_route_uuid: str):
    test_auth = {
        "headers": {
            "user": "other_user-p@sanger.ac.uk"
        }
    }

    test_add_user_link(router_app, test_route_uuid)

    assert router_app.delete(f"/links/{test_route_uuid}", **test_auth).status_code == 204

    assert len(json.loads(router_app.get("/routes", **test_auth).data)) == 0

def test_get_route_stats(router_app: FlaskClient, test_route_uuid: str):
    assert router_app.get(f"/routes/{test_route_uuid}/statistics").status_code == 200

def test_get_route_logs(router_app: FlaskClient, test_route_uuid: str):
    assert router_app.get(f"/routes/{test_route_uuid}/logs").status_code == 200

@pytest.mark.usefixtures("test_route_uuid")
def test_all_routes_stats(router_app: FlaskClient):
    assert router_app.get(f"/routes/statistics").status_code == 200