import http = require('http');
import https = require('https');
import url = require("url");
import fetch from "node-fetch";
import httpProxy = require("http-proxy");
var route = require("router")();
import argparse = require("argparse");
import winston = require("winston");
var ElasticSearch = require('winston-elasticsearch');

winston.remove(winston.transports.Console);

const logger = new winston.Logger({
    transports: [
        new winston.transports.Console({
            colorize: true
        }),
        new winston.transports.File({
            filename: "logs.log"
        })
    ]
})

var writeNotFound = (resp: any) => writeError("Not found", 404, resp);
var writeInternalError = (resp: any) => writeError("Internal server error", 500, resp);

function writeError(message: string, code: number, response: http.ServerResponse){
    response.writeHead(code, {
        "Content-Type": "application/json; charset=utf-8"
    })

    response.end(JSON.stringify({error: message}, undefined, 4)) // Space out the response using 4 spaces
}

async function getRouteFromToken(token: string){
    var configServerResp = await fetch(`${args.configServer}/routes/token/${token}`);

    try{
        var configServerJSON = await configServerResp.json();
    }
    catch(error){
        winston.error("Cannot parse config server response", {
            error: error
        });

        throw error
    }

    if(typeof configServerJSON.error == "string"){
        winston.error("Config server error", {
            error: configServerJSON.error
        });

        throw new Error(`Config server error: ${configServerJSON.error}`);
    }

    return configServerJSON;
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
        let destination = await getRouteFromToken(token);

        await routeRequest(request, response, destination);
        
        logger.info("Correctly routed", {
            token: token,
            destination: destination
        });
    })().catch(error => {
        logger.error("Failed routing", {
            token: token,
            error: error
        })

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
        logger.error("Routing exception", {
            error: error
        })

        if(!error){
            writeNotFound(response)
        }
        else{
            writeInternalError(response);
        }
    })
}).listen(args.port, args.host);

