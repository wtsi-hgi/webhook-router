from swagger_tester import swagger_test
from server import Server
from flask import Response
import json
import pytest
from flask.testing import FlaskClient

auth = {
    "headers": {
        "Google-Auth-Token": "test_user"
    }
}

@pytest.fixture(autouse=True)
def test_token(router_app: FlaskClient) -> str:
    add_route_resp = router_app.post("/add-route",
        data=json.dumps({
            "name": "route",
            "destination": "127.0.0.1"
        }),
        content_type='application/json',
        **auth
    )

    assert add_route_resp.status_code == 201

    return json.loads(add_route_resp.data)["token"]

@pytest.fixture()
def router_app():
    server = Server(debug=True, memory_db=True)
    app = server.app.app.test_client() # type: FlaskClient
    yield app
    server.close()

def test_get(router_app: FlaskClient, test_token: str):
    assert router_app.get(f"/routes/{test_token}").status_code == 200

def test_patch(router_app: FlaskClient, test_token: str):
    assert router_app.patch(f"/routes/{test_token}",
        data=json.dumps({
            "name": "new-name"
        }),
        content_type='application/json',
        **auth).status_code == 200

    assert json.loads(router_app.get(f"/routes/{test_token}").data)["name"] == "new-name"

def test_get_all(router_app: FlaskClient):
    all_routes_resp = router_app.get("/routes", **auth)

    assert all_routes_resp.status_code == 200
    
    data = json.loads(all_routes_resp.data)
    assert len(data) == 1 and data[0]["name"] == "route"

def test_delete(router_app: FlaskClient, test_token: str):
    assert router_app.delete(f"/routes/{test_token}", **auth).status_code == 204
    
    assert len(json.loads(router_app.get("/routes", **auth).data)) == 0