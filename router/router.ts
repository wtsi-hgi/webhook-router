import http = require('http');
import https = require('https');
import url = require("url");
import fetch from "node-fetch";
import httpProxy = require("http-proxy")

const configServer = "http://127.0.0.1:8081"

function writeError(message: string, code: number, response: http.ServerResponse){
    response.writeHead(code, {
        "Content-Type": "application/json; charset=utf-8"
    })

    response.end(JSON.stringify({error: message}))
}

class RoutingException extends Error{
    constructor(public message: string, public httpErrorCode: number, public logMessage?: string) {
        super();
    }
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

    return <string>configServerJSON.destination;
}

let proxy = httpProxy.createProxyServer({
    changeOrigin: true
})

function handleRequest(request: http.IncomingMessage, response: http.ServerResponse, onError: (error: any) => any){
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

    getDestinationFromToken(path[0]).then((destination) => {
        proxy.web(request, response, {
            target: destination
        }, (error) => {
            onError(error)
        })
    }).catch((error) => {
        onError(error)
    })
}

proxy.on("end", (req, res, proxyRes) => {
    // TODO: log successful route
})

http.createServer(async (request, response) => {
    handleRequest(request, response, (error) => {
        if (error instanceof RoutingException){
            if (error.logMessage){
                console.log(error.logMessage);
            }
            writeError(error.message, error.httpErrorCode, response);
        }
        else{
            writeError("Internal Server Error", 500, response);
            console.log(error);
        }
    });
}).listen(8080);

process.on('uncaughtException', function (err) {
    console.error("Uncaught exception:");
    console.error(err.stack);
});