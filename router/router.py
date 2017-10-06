import requests
import connexion
from connexion.resolver import Resolver
from bravado.client import SwaggerClient
import flask

client = SwaggerClient.from_url('http://127.0.0.1:8080/swagger.json')

def route_webhook():
    route = client.get_route().result()

    requests.post(route.destination,
        headers=flask.request.headers,
        data=flask.request.data)

def resolveSwaggerName(name):
    return globals()[name]

# TODO connect to the database on request sent
app = connexion.FlaskApp(__name__, specification_dir=".")
app.add_api('swagger.yaml', resolver=Resolver(resolveSwaggerName))
app.run(port=8080, host="127.0.0.1")