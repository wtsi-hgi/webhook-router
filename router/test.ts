import cp = require("child_process");
import http = require("http");
import net = require("net");
import https = require("https");
import os = require("os");
import axios, {AxiosError} from "axios";

var testServerHandle: net.Server;

let configServer: string = "http://configserver";
let routingServer: string = "http://router";
let testServer: string = "http://127.0.0.1:8081";

function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

beforeAll(async () => {
    testServerHandle = http.createServer((req, res) => {
        res.end("response");
    }).listen(8081, "127.0.0.1");
}, 5500)

async function createRoute(dest: string, options = {}){
    let createRouteResp = await axios.post(`${configServer}/create-route`, {
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

    return await axios.post(`${routingServer}/${token}`)
}

it("Routes to test server", async () => {
    let resp = await testRoutingToAddress(testServer)

    expect(resp.data).toBe("response");
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
        await axios.post(`${routingServer}/${token}`, undefined, {
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
    let token = await createRoute(routingServer);

    let timeTaken = await time(async () => {
        for(var i = 0;i < 5;i++){
            await timeToken(token);
        }
    })

    expect(timeTaken).toBeLessThan(1000);
})

const numbersTo = (limit: number) => Array.from(Array(limit).keys())

it("rate limits requests", async () => {
    let token = await createRoute(routingServer, {
        rateLimit: 30
    });
    let responses = await Promise.all(numbersTo(60).map(_ => axios.post(`${routingServer}/${token}`, undefined, {
        validateStatus: () => true // get the status codes back
    })));

    expect(responses.map(x => x.status)).toContain(503 /*= Service Unavailable*/)
})

afterAll(() => {
    testServerHandle.close();
})