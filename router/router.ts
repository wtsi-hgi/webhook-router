import http = require('http');
import https = require('https');
import url = require("url");
import axios from "axios";
import httpProxy = require("http-proxy");
var route = require("router")();
import argparse = require("argparse");
import winston = require("winston");
var Limiter = require("ratelimit.js").RateLimit;

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
});

/** Error code from the config server of an invalid route */
const INVALID_ROUTE_TOKEN_ERROR = 2;
/** Log code for a successful log in elasticsearch */
const SUCCESS_LOG_CODE = 1;

var writeNotFound = (resp: any) => writeError("404 Not found", 404, resp);
var writeMethodNotAllowed = (resp: any) => writeError("405 Method Not Allowed", 405, resp);
var writeTooManyRequests = (resp: any) => writeError("429 Too Many Requests", 429, resp);
var writeInternalError = (resp: any) => writeError("500 Internal server error", 500, resp);
var writeBadGateway = (resp: any) => writeError("502 Bad Gateway", 502, resp);

function writeError(message: string, code: number, response: http.ServerResponse){
    response.writeHead(code, {
        "Content-Type": "application/json; charset=utf-8"
    })

    response.end(JSON.stringify({error: message}, undefined, 4) + "\n") // Space out the response using 4 spaces
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
        logger.error(this.errorMessage, {
            ...this.metadata,
            success: false,
            ...extraData
        });
    }
}

class InvalidTokenError extends AbstractRouterError{
    constructor(requestedToken: string){
        super("Invalid token.", {requestedToken});
    }

    writeHttpResponse = writeNotFound;
}

/** NOTE: This is to be raised if the uuid is found, but the user tries to push to  */
class RouteMethodNotAllowed extends AbstractRouterError{
    constructor(uuid: string, attemptedMethod: string){
        super("Incorrect http method, only POST requests are supported.", {uuid, attemptedMethod});
    }

    writeHttpResponse = writeMethodNotAllowed;
}

class ConfigServerError extends AbstractRouterError{
    constructor(error: string){
        super("Config server error.", {error})
    }

    writeHttpResponse = writeInternalError;
}

class RoutingError extends AbstractRouterError{
    constructor(error: Error & {code: string}, uuid: string){
        super("Routing error.", {message: error.message, code: error.code, uuid});
    }

    writeHttpResponse = writeBadGateway;
}

class TooManyRequestsError extends AbstractRouterError{
    constructor(uuid: string){
        super(`Too many requests issued. Only ${RATE_LIMIT} requests are allowed per second`, {uuid});
    }

    writeHttpResponse = writeTooManyRequests;
}

export interface Route {
    "name": string;
    "destination": string;
    "token": string;
    "uuid": string;
    "no_ssl_verification": boolean;
}

async function getRouteFromToken(token: string){
    var configServerJSON = (await axios.get(`${args.configServer}/routes/token/${token}`)).data

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
            target: route.destination,
            secure: !route.no_ssl_verification
        }, error => {
            reject(new RoutingError(<Error & {code: string}>error, route.uuid));
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

const RATE_LIMIT = 30;

var limitTable = new Map<string, number>();
setInterval(() => {
    for(let [key, _] of limitTable){
        limitTable.set(key, 0);
    }
}, 1000);

function isRateLimited(uuid: string){
    if(limitTable.has(uuid)){
        limitTable.set(uuid, 1);
    }
    else{
        limitTable.set(uuid, <number>limitTable.get(uuid) + 1)
    }
    
    return <number>limitTable.get(uuid) < RATE_LIMIT
}

route.all("/:token", (request: http.IncomingMessage & {params: any}, response: http.ServerResponse) => {
    let token = request.params.token;

    (async () => {
        try{
            let route = await getRouteFromToken(token);

            if(request.method != "POST"){
                throw new RouteMethodNotAllowed(route.uuid, request.method || "<METHOD MISSING>");
            }

            if(isRateLimited(route.uuid)){
                throw new TooManyRequestsError(route.uuid);
            }

            let routePromise = routeRequest(request, response, route);

            // Warn if the request takes longer than a timeout
            let timeoutSymbol = Symbol("timeout");
            
            if(await Promise.race([
                await routePromise,
                (async () => {
                    await delay(args.warningDelay)
                    return timeoutSymbol;
                })()
            ]) == timeoutSymbol){
                logger.warn(`Long running request. Request is taking more than ${args.warningDelay / 1000} seconds`, {
                    uuid: route.uuid,
                    ...getRequestLogData(request)
                })
            }
            
            await routePromise;
            
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
            else{
                handleInternalError(error, request, response);
            }
        }
    })()
})

function handleInternalError(error: Error, request: http.IncomingMessage, response: http.ServerResponse){
    logger.error("Internal error", {
        error: error.toString(),
        url: request.url,
        success: false,
        ...getRequestLogData(request),
        stack: error.stack
    })

    writeInternalError(response);
}

let parser = new argparse.ArgumentParser({
    description: "Webhook router"
})
parser.addArgument(["--port"], {help: "Port to serve the request", required: true});
parser.addArgument(["--host"], {help: "Host to serve the request from", defaultValue: "127.0.0.1"});
parser.addArgument(["--warningDelay"], {help: "How many milliseconds before a long request warning is issued",
    defaultValue: 10000, type: "int"});
parser.addArgument(["--configServer"], {help: "Ip Address of the config server", required: true});
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
            handleInternalError(error, request, response);            
        }
    })
}).listen(args.port, args.host);

logger.info("Router running", {
    port: args.port,
    host: args.host
})