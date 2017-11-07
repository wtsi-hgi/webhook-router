import cp = require("child_process");
import http = require("http");
import https = require("https");
import os = require("os");
import axios, {AxiosError} from "axios";

var configServer: cp.ChildProcess;
var routerServer: cp.ChildProcess;

var [configPort, routerPort, receiverPort] = [8080, 8081, 8082];

function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

beforeAll(async () => {
    configServer = cp.spawn(`python ../config-server/configserver/server.py --port ${configPort} --host 127.0.0.1 --debug`, 
        [], {shell: true, stdio: "inherit"});
    routerServer = cp.spawn(`node ./router.js --port ${routerPort} --host 127.0.0.1 --configServer http://127.0.0.1:${configPort}`,
        [], {shell: true, stdio: "inherit"});
    await delay(5000);
}, 5500)

async function addRoute(dest: string, options = {}){
    let addRouteResp = await axios.post(`http://127.0.0.1:${configPort}/add-route`, {
        name: "route",
        destination: dest,
        ...options
    })

    let token: string = addRouteResp.data.token;
    expect(addRouteResp.data.token).not.toBeUndefined;

    return token;
}

async function testRoutingToAddress(location: string, options = {}){
    let token = await addRoute(location, options);
    
    return await axios.post(`http://127.0.0.1:${routerPort}/${token}`)
}

it("Routes to test server", async () => {
    let server = http.createServer((req, res) => {
        res.end("response");
    }).listen(receiverPort, "127.0.0.1");

    let resp = await testRoutingToAddress(`http://127.0.0.1:${receiverPort}`)

    expect(resp.data).toBe("response");

    server.close()
})

describe("no_ssl_verification", () => {
    it("= false fails with insecure site", async () => {
        let error: undefined | AxiosError;
        
        try{
            await testRoutingToAddress(`https://self-signed.badssl.com/`)
        }
        catch(e){
            error = e;
        }
    
        expect(error).not.toBeUndefined;
        expect(error!.response!.status).toBe(502);
    })
    
    it("= true succeeds with insecure site", async () => {
        try{
            await testRoutingToAddress(`https://self-signed.badssl.com/`, {
                no_ssl_verification: true
            })
        }
        catch(error){
            expect(error.response.status).not.toBe(502);
        }
    })
})


describe("httpbin", () => {
    it("routes to http", async () => {
        let resp = await testRoutingToAddress("http://httpbin.org/post")
        
        expect(resp.data).toBeTruthy;
        expect(resp.status).toEqual(200);
    })

    it("routes to https", async () => {
        let resp = await testRoutingToAddress("https://httpbin.org/post")

        expect(resp.data).toBeTruthy;
        expect(resp.status).toEqual(200);
    })
})

afterAll(() => {
    configServer.kill();
    routerServer.kill();
})