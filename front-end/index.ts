import swaggerAPI = require("./api");
import _Vue from "vue";
var Vue = <typeof _Vue>require("vue");
const configServerLocation = "http://127.0.0.1:8081";

function onSuccess(googleUser) {
    console.log('Logged in as: ' + googleUser.getBasicProfile().getName());
}

function onFailure(error) {
    console.log(error);
}

interface IRoute{
    name: string;
    destination: string;
    token: string;
}

class Client{
    private api = new swaggerAPI.DefaultApi(fetch, configServerLocation);
    private authOptions: object;

    constructor(google_token: string){
        this.authOptions = {
            headers: {
                "Google-Auth-Token": google_token
            }
        }
    }
    
    displayRoute(route: swaggerAPI.Route){
        console.log(route);
    }

    async displayAllRoutes(){
        let routes = await this.api.getAllRoutes();
        routes.forEach(x => this.displayRoute(x));
    }
}

function signedIn(google_token: string){
    document.querySelector(<"div">"#main").style.display = "initial"
    document.querySelector(<"div">"#sign-in").style.display = "none";

    (async () => {
        let client = new Client(google_token);
        client.displayAllRoutes();
    })()
}

var vue = new Vue({
    el: "#site",
    data: {
        filteredRoutes: [
            {
                name: "Route",
                token: "lsjnflsd",
                destination: "kjsndflk"
            },
        ],
        signedIn: true
    }
})

export function googleStart() {
    gapi.load('auth2', async () => {
        gapi.auth2.init({
            client_id: '859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.apps.googleusercontent.com',
            fetch_basic_profile: false,
            scope: 'profile',
            hosted_domain: "sanger.ac.uk"
        }).then(auth => {
            if(auth.isSignedIn.get()){
                signedIn(auth.currentUser.get().getAuthResponse().id_token)
            }
    
            gapi.signin2.render("google-signin", {
                scope: "profile email",
                theme: 'dark',
                longtitle: true,
                onsuccess: (user) => {
                    signedIn(user.getAuthResponse().id_token)
                }
            })
        })
    });
}

googleStart();