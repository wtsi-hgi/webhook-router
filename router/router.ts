import http = require('http');
import https = require('https');
import url = require("url");
import fetch from "node-fetch";
import httpProxy = require("http-proxy");
var route = require("router")();
import argparse = require("argparse");
import winston = require("winston");

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

/** Error code from the config server of an invalid route */
const INVALID_ROUTE_TOKEN_ERROR = 2;
/** Log code for a successful log in elasticsearch */
const SUCCESS_LOG_CODE = 1;

var writeBadRequest = (resp: any) => writeError("400 Bad Request", 400, resp);
var writeNotFound = (resp: any) => writeError("404 Not found", 404, resp);
var writeMethodNotAllowed = (resp: any) => writeError("405 Method Not Allowed", 405, resp);
var writeInternalError = (resp: any) => writeError("500 Internal server error", 500, resp);

function writeError(message: string, code: number, response: http.ServerResponse){
    response.writeHead(code, {
        "Content-Type": "application/json; charset=utf-8"
    })

    response.end(JSON.stringify({error: message}, undefined, 4)) // Space out the response using 4 spaces
}

abstract class AbstractRouterError extends Error {
    constructor(private errorMessage: string, private metadata = {}){
        super(errorMessage);
    }

    /**
     * Writes a the expected http response for the given error
     * to the response object
     */
    abstract writeHttpResponse: (response: any) => void;

    /**
     * Logs the exception
     * @param extraData Extra data to log
     */
    public logException(extraData = {}){
        winston.error(this.errorMessage, {
            ...this.metadata,
            success: false,
            ...extraData
        });
    }
}

class InvalidTokenError extends AbstractRouterError{
    constructor(requestedToken: string){
        super("Invalid token", {requestedToken});
    }

    logCode = 2;
    writeHttpResponse = writeNotFound;
}

/** NOTE: This is to be raised if the uuid is found, but the user tries to push to  */
class RouteMethodNotAllowed extends AbstractRouterError{
    constructor(uuid: string, attemptedMethod: string){
        super("Incorrect http method, only POST requests are supported", {uuid, attemptedMethod});
    }

    writeHttpResponse = writeMethodNotAllowed;
}

class ConfigServerError extends AbstractRouterError{
    constructor(error: string){
        super("Config server error", {error})
    }

    writeHttpResponse = writeInternalError;
}

class InvalidConfigServerResponseError extends AbstractRouterError{
    constructor(error: string, serverResponse: string){
        super("Error parsing config server response", {error, serverResponse})
    }

    writeHttpResponse = writeInternalError;
}

class RoutingError extends AbstractRouterError{
    constructor(error: Error & {code: string}, uuid: string){
        super("Routing error", {message: error.message, code: error.code, uuid});
    }

    writeHttpResponse = writeBadRequest;
}

export interface Route {
    "name": string;
    "destination": string;
    "token": string;
    "uuid": string;
    "owner": string;
}

async function getRouteFromToken(token: string){
    var configServerResp = await fetch(`${args.configServer}/routes/token/${token}`);

    try{
        var configServerJSON = await configServerResp.json();
    }
    catch(error){
        throw new InvalidConfigServerResponseError(error, await configServerResp.text())
    }

    if(typeof configServerJSON.error == "string"){
        if(configServerJSON.error_num == INVALID_ROUTE_TOKEN_ERROR){
            throw new InvalidTokenError(token);
        }
        else{
            throw new ConfigServerError(configServerJSON.error)
        }
    }

    return <Route>configServerJSON;
}

let proxy = httpProxy.createProxyServer(<any>{
    changeOrigin: true,
    preserveHeaderKeyCase: true,
    ignorePath: true
})

function routeRequest(request: http.IncomingMessage, response: http.ServerResponse, route: Route){
    return new Promise((resolve, reject) => {
        // define resolvePromise as a callback for when the route has been successful
        (<any>request).resolvePromise = resolve;

        proxy.web(request, response, {
            target: route.destination
        }, (error: Error & {code: string}) => {
            reject(new RoutingError(error, route.uuid));
        });
    })
}

proxy.on("end", (req, res, proxyRes) => {
    // see above
    (<any>req).resolvePromise();
})

function getRequestLogData(request: http.IncomingMessage){
    return {
        ip: request.connection.remoteAddress,
        userAgent: request.headers["user-agent"]
    }
}

function delay(time: number){
    return new Promise((resolve, reject) => {
        setTimeout(resolve, time);
    })
}

route.all("/:token", (request: http.IncomingMessage & {params: any}, response: http.ServerResponse) => {
    let token = request.params.token;

    (async () => {
        try{
            let route = await getRouteFromToken(token);
            
            if(request.method != "POST"){
                throw new RouteMethodNotAllowed(route.uuid, request.method || "<METHOD MISSING>");
            }

            await routeRequest(request, response, route);
            
            logger.info("Correctly routed", {
                uuid: route.uuid,
                destination: route.destination
            });
        }
        catch(error){
            if(error instanceof AbstractRouterError){
                error.logException(getRequestLogData(request));
                error.writeHttpResponse(response);
            }
        }
    })()
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
        if(!error){
            logger.error("404 not found", {
                url: request.url,
                success: false,
                ...getRequestLogData(request)
            })

            writeNotFound(response)
        }
        else{
            logger.error("Internal error", {
                error: error.toString(),
                url: request.url,
                success: false,
                ...getRequestLogData(request)
            })

            writeInternalError(response);
        }
    })
}).listen(args.port, args.host);

logger.info("Router running", {
    port: args.port,
    host: args.host
})