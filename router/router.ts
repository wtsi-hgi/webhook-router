import http = require('http');
import https = require('https');
import url = require("url");
import fetch from "node-fetch";
import httpProxy = require("http-proxy");
var route = require("router")();
import argparse = require("argparse");

var writeNotFound = (resp: any) => writeError("Not found", 404, resp);
var writeInternalError = (resp: any) => writeError("Internal server error", 500, resp);

function writeError(message: string, code: number, response: http.ServerResponse){
    response.writeHead(code, {
        "Content-Type": "application/json; charset=utf-8"
    })

    response.end(JSON.stringify({error: message}, undefined, 4)) // Space out the response using 4 spaces
}

async function getDestinationFromToken(token: string){
    var configServerResp = await fetch(`${args.configServer}/routes/${token}`)
    try{
        var configServerJSON = await configServerResp.json();
    }
    catch(error){
        throw new Error(`Error in parsing config server response: ${error}`);
    }

    if(typeof configServerJSON.error == "string"){
        throw new Error(`Config server error: ${configServerJSON.error}`);
    }

    return <string>configServerJSON.destination;
}

let proxy = httpProxy.createProxyServer(<any>{
    changeOrigin: true,
    preserveHeaderKeyCase: true,
    ignorePath: true
})

function routeRequest(request: http.IncomingMessage, response: http.ServerResponse, destination: string){
    return new Promise((resolve, reject) => {
        (<any>request).resolvePromise = resolve;

        proxy.web(request, response, {
            target: destination
        }, (error: Error & {code: string}) => {
            reject(error);
        })
    })
}

proxy.on("end", (req, res, proxyRes) => {
    (<any>req).resolvePromise();
})

route.post("/:token", (request: http.IncomingMessage & {params: any}, response: http.ServerResponse) => {
    let token = request.params.token;

    (async () => {
        let destination = await getDestinationFromToken(token);
        await routeRequest(request, response, destination);

        console.error(`Correctly routed token "${token}" to location ${destination}`)
    })().catch(error => {
        console.error(`Failed routing of ${token}. ${error}`);

        writeInternalError(response);
    })
})

let parser = new argparse.ArgumentParser({
    description: "Webhook router"
})
parser.addArgument(["--port"], {help: "Port to serve the request", required: true})
parser.addArgument(["--host"], {help: "Host to serve the request from", defaultValue: "127.0.0.1"})
parser.addArgument(["--configServer"], {help: "Ip Address of the config server", required: true})
let args = parser.parseArgs();


http.createServer((request, response) => {
    route(request, response, (error: any) => {
        console.error(error);

        if(!error){
            writeNotFound(response)
        }
        else{
            writeInternalError(response);
        }
    })
}).listen(args.port, args.host);
