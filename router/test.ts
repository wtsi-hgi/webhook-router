import cp = require("child_process");
import http = require("http")
import os = require("os");
import axios from "axios";

var configServer: cp.ChildProcess;
var routerServer: cp.ChildProcess;

var [configPort, routerPort, receiverPort] = [8080, 8081, 8082];

function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

beforeAll(async () => {
    configServer = cp.spawn(`python ../config/server.py --port ${configPort} --host 127.0.0.1 --debug`, 
        [], {shell: true, stdio: "inherit"});
    routerServer = cp.spawn(`node ./router.js --port ${routerPort} --host 127.0.0.1 --configServer http://127.0.0.1:${configPort}`,
        [], {shell: true, stdio: "inherit"});
    await delay(5000);
}, 5500)

async function addRoute(dest: string){
    let addRouteResp = await axios.post(`http://127.0.0.1:${configPort}/add-route`, {
        body: JSON.stringify({
            name: "route",
            destination: dest
        }),
        headers: {
            "Content-Type": "application/json"
        }
    })

    let token: string = addRouteResp.data.token;
    expect(addRouteResp.data.token).not.toBeUndefined;

    return token;
}

async function testRoutingToAddress(location: string){
    let token = await addRoute(location);
    
    return await axios.post(`http://127.0.0.1:${routerPort}/${token}`)
}

it("Routes to test server", async () => {
    http.createServer((req, res) => {
        res.end("response");
    }).listen(receiverPort, "127.0.0.1");

    let resp = await testRoutingToAddress(`127.0.0.1:${receiverPort}`)

    expect(resp.data).toBe("response");
});

describe("example.com", () => {
    it("routes to http", async () => {
        let resp = await testRoutingToAddress("http://www.example.com")

        expect(resp.data).toBeTruthy;
        expect(resp.status).toEqual(200);
    })

    it("routes to https", async () => {
        let resp = await testRoutingToAddress("https://www.example.com")

        expect(resp.data).toBeTruthy;
        expect(resp.status).toEqual(200);
    })
})

afterAll(() => {
    configServer.kill();
    routerServer.kill();
})