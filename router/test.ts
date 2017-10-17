import cp = require("child_process");
import {routeRequest} from "./router";
import http = require("http")

function logOutput(error: Error, stdout: string, stderr: string){
    if(error !== null){
        throw error;
    }

    if(stdout !== ""){
        console.log(stdout);
    }

    if(stderr !== ""){
        console.error(stderr);
    }
}

it("routes correctly", (finish) => {
    var got_route = false;
    http.createServer((req, res) => {
        res.end("response");
        got_route = true;
    }).listen(3001);

    routeRequest(<any>{
        rawHeaders: {
            x: "y"
        },
        addListener: (type: string, func: () => void) => {
            if(type == "end"){
                func()
            }
        }
    }, <any>{
        write: () => {
        },
        writeHead: () => {
        },
        end: () => {
            if(got_route)
                finish()
        }
    }, "http://127.0.0.1:3001")
});
