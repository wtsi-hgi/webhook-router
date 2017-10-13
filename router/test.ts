import cp = require("child_process");
import {routeRequest} from "./router";

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
    var processes = <cp.ChildProcess[]>[];
    require("./router.js");
    processes.push(cp.exec("python ../config/server.py --debug --port 8001 --host 127.0.0.1", logOutput))

    setTimeout(() => {
        var token = cp.execSync(`curl 127.0.0.1:8001/add-route -H "Content-Type: application/json" -X POST -d '{"name":"route","destination": "127.0.0.1:8002"}' -s | jq -r ".token"`)
            .toString().replace("\n", "");
        
        var stdout = "";
        processes.push(cp.exec("nc -l 8002", (error, _stdout, stderr) => {/*
            if(error !== null){
                throw error;
            }

            console.error(stderr);
            console.log(_stdout);*/
            stdout += _stdout;
            if(stdout.search("header: value") != -1){
                finish()
            }
        }))
        
        processes.push(cp.exec(`curl 127.0.0.1:8080/${token} -X POST -H "header: value"`, logOutput))
    }, 3000)

    setTimeout(() => processes.forEach(process => process.kill()), 5000)
});
