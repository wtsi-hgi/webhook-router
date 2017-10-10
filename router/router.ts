import http = require('http');
import https = require('https');
import url = require("url");
import fetch from "node-fetch";

const configServer = "http://127.0.0.1:8081"

function writeError(message: string, code: number, response: http.ServerResponse){
    response.writeHead(code, {
        "Content-Type": "application/json; charset=utf-8"
    })

    response.end(
`{
    "error": "${message}"
}
`)
}

class RoutingException extends Error{
    constructor(public message: string, public httpErrorCode: number, public logMessage?: string) {
        super();
    }
}

function routeRequest(request: http.IncomingMessage, response: http.ServerResponse, destination: string){
    return new Promise((resolve, reject) => {
        let parsedUrl = url.parse(destination);
        
        var httpProtocol = http; // for the type checker
        if (parsedUrl.protocol == "http:"){
            httpProtocol = http;
        }
        else if (parsedUrl.protocol == "https:"){
            httpProtocol = <any>https;
        }
        else{
            throw new RoutingException("Invalid client protocol", 400);
        }

        // have to use `.rawHeaders` as `.headers` makes all properties lower case 
        var headers = <any>{};
        for(var i = 0;i < request.rawHeaders.length;i += 2){
            let headerKey = request.rawHeaders[i];
            if(headerKey.toLowerCase() != "host"){ // let node.js set this
                // hope there are no duplicate headers, otherwise they'll be overwritten
                headers[headerKey] = request.rawHeaders[i + 1];
            }
        }

        var forwardedReq = httpProtocol.request(<any>{
            ...parsedUrl,
            method: "POST",
            headers: {
                ...headers
            }
        }, (forwardedResp) => {
            forwardedResp.addListener("data", (chunk) => {
                response.write(chunk, 'binary');
            })

            forwardedResp.addListener("end", () => {
                response.end();
                resolve();
            })

            response.removeHeader("Connection");

            response.writeHead(<number>forwardedResp.statusCode, forwardedResp.headers);
        });

        forwardedReq.addListener("error", (e) => {
            reject(new RoutingException("Cannot connect to server", 500, e.toString()))
        })

        request.addListener('data', (chunk) => {
            forwardedReq.write(chunk, 'binary');
        });

        request.addListener('end', () => {
            forwardedReq.end();
        });

        request.addListener('error', (e) => {
            reject(e);
        })
    })
}

async function getDestinationFromToken(token: string){
    var configServerResp = await fetch(`${configServer}/routes/${token}`)
    try{
        var configServerJSON = await configServerResp.json();
    }
    catch(e){
        throw new RoutingException("Invalid response from config server", 500, e);
    }

    if(typeof configServerJSON.error == "string"){
        throw new RoutingException("Config server error: " + configServerJSON.error, configServerResp.status);
    }

    return configServerJSON.destination;
}

async function handleRequest(request: http.IncomingMessage, response: http.ServerResponse){
    // see if the request is correct and extract the token
    // should be POST request of the form /{token}
    let requestUrl = url.parse(<string>request.url);
    if(request.method !== "POST"){
        writeError("Method Not Allowed", 405, response);
    }

    let path = requestUrl.path!.split("/").filter(x => x != "");
    if(path.length != 1){
        writeError("Not Found", 404, response);
        return;
    }

    await routeRequest(request, response, await getDestinationFromToken(path[0]));
}

http.createServer(async (request, response) => {
    try{
        await handleRequest(request, response);
    }
    catch(e){
        if (e instanceof RoutingException){
            if (e.logMessage){
                console.log(e.logMessage);
            }
            writeError(e.message, e.httpErrorCode, response);
        }
        else{
            writeError("Internal Server Error", 500, response);
            console.log(e);
        }
    }
}).listen(8080);

process.on('uncaughtException', function (err) {
    console.error("Uncaught exception:");
    console.error(err.stack);
});