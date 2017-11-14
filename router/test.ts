import cp = require("child_process");
import http = require("http");
import https = require("https");
import os = require("os");
import axios, {AxiosError} from "axios";
import _ = require("lodash");
var ttest = require("ttest");

var configServer: cp.ChildProcess;
var routerServer: cp.ChildProcess;

var [configPort, routerPort, receiverPort] = [8080, 8081, 8082];

function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

beforeAll(async () => {
    configServer = cp.spawn(`cd ../config-server && python -m configserver --port ${configPort} --host 127.0.0.1 --debug`, 
        [], {shell: true});
    routerServer = cp.spawn(`node ./router.js --port ${routerPort} --host 127.0.0.1 --configServer http://127.0.0.1:${configPort}`,
        [], {shell: true});
    await delay(5000);
}, 5500)

async function createRoute(dest: string, options = {}){
    let createRouteResp = await axios.post(`http://127.0.0.1:${configPort}/create-route`, {
        name: "route",
        destination: dest,
        ...options
    })

    let token: string = createRouteResp.data.token;
    expect(createRouteResp.data.token).not.toBeUndefined;

    return token;
}

async function testRoutingToAddress(location: string, options = {}){
    let token = await createRoute(location, options);
    
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

async function time(func: () => Promise<any>){
    let startTime = Date.now();
    await func();
    let endTime = Date.now();

    return endTime - startTime;
}

async function timeToken(token: string){
    return await time(async () => {
        await axios.post(`http://127.0.0.1:${routerPort}/${token}`, undefined, {
            validateStatus: () => true // make sure there is no exception time loss
        })
    })
}

/** Concurrent mapping over promises */
async function promiseMap<InputType, OutputType>(array: InputType[], promise: (item: InputType) => Promise<OutputType>){
    let result = <OutputType[]>[];
    
    await Promise.all(array.map((item, index) => {
        return promise(item).then(returnItem => {
            result[index] = returnItem
        })
    }))

    return result;
}

it("can route at least 5 routes per second", async () => {
    let token = await createRoute("http://httpbin.org/post");

    let timeTaken = await time(async () => {
        for(var i = 0;i < 5;i++){
            await timeToken(token);
        }
    })

    expect(timeTaken).toBeLessThan(1000);
})

afterAll(() => {
    configServer.kill();
    routerServer.kill();
})