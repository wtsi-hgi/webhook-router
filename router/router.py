import aiohttp
from aiohttp.web_response import StreamResponse, Response
from aiohttp_swagger import *
from bravado.client import SwaggerClient

client = SwaggerClient.from_url('http://127.0.0.1:8081/swagger.json')

async def route_webhook(request):
    """
    ---
    parameters:
    - name: token
        in: path
        required: true
        description: The token of the route
        type: string
    post:
    summary: Routes the post request to the specified location, according to the webhook \\
        settings from a configuration server 
    operationId: route_webhook
    responses:
        default:
        description: The response of the routed webhook
    """
    route = client.routes.get_route(token=request.match_info.get("token")).result()
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            route.destination,
            headers=request.headers,
            data=await request.read()
        )

    my_resp = Response(
        status=resp.status,
        reason=resp.reason,
        headers=resp.headers
    )

    my_resp.body = await resp.read()

    return my_resp


app = aiohttp.web.Application()
app.router.add_route('POST', "/{token}", route_webhook)

setup_swagger(app)

aiohttp.web.run_app(app, host="127.0.0.1")
