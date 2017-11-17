<template>
<div>
    <div v-if="state=='start'">
        <whr-navbar></whr-navbar>
        <errors ref="errors" slot="errors"></errors>
    </div>
    <div v-else-if="state=='not_signed_in'">
        <signin @signedIn="token => login(token)"></signin>
        <errors ref="errors" slot="errors"></errors>
    </div>
    <!--Setting the key as below reloads the page on path change-->
    <router-view v-else class="view" :key="$route.fullPath" :googleToken="googleToken" :api="api">
        <button type="button" class="btn btn-outline-warning" slot="logoutButton" @click="logout">Logout</button>
        <errors ref="errors" slot="errors"></errors>
    </router-view>
</div>
</template>
<script lang="ts">
/// <reference types="gapi.auth2" />
import Vue from "vue";
import VueRouter from "vue-router";
import DisplayRoutesComponent from "./display-routes.vue";
import CreateRouteComponent from "./create-route.vue";
import AddExistingRouteComponent from "./add-existing-route.vue";
import ModifyRouteComponent from "./modify-route.vue";
import SignInComponent from "./signin.vue";
import NavBarComponent from "./whr-navbar.vue";
import NotFoundComponent from "./404-not-found.vue";
import Component from 'vue-class-component';
import ErrorsComponent from "./errors.vue";
import * as swaggerAPI from "../api";
import * as utils from "../utils";
var Mprogress = require("mprogress/mprogress.min.js"); // Do this, as the main module is not exported
import {auto} from 'browser-unhandled-rejection';

// pollyfill the event unhandledrejection
auto();

const router = new VueRouter({
    mode: "hash",
    base: __dirname,
    routes: [
        {path: "/", component: DisplayRoutesComponent, name: "home"},
        {path: "/create-route", component: CreateRouteComponent, name: "create-route"},
        {path: "/add-existing-route", component: AddExistingRouteComponent, name: "add-existing-route"},
        {path: "/routes/:uuid", component: ModifyRouteComponent, props: true, name: "modify-route"},
        {path: "*", component: NotFoundComponent}
    ]
})

@Component({
    components: {
        "whr-navbar": NavBarComponent,
        "signin": SignInComponent,
        "errors": ErrorsComponent
    },
    router: router,
    watch: {
        "$route": function () {
            (<any>this).progressBar.end();
        }
    }
})
export default class extends Vue {
    signedin = false
    state = "start"
    private googleToken = ""
    auth: gapi.auth2.GoogleAuth;
    api: swaggerAPI.DefaultApi;
    tokenExpiration: number;
    progressBar = new Mprogress({
        template: 3, // 3 = indeterminate progress bar
        parent: 'body'
    });

    /**
     * Padding time for a reload of a token.
     * Half of this value will also be when the brower checks for the token being refreshed
     */
    readonly reloadPadding = 10 * 60 * 1000; // 10 mins

    $refs: {
        errors: ErrorsComponent;
    }

    private async fetchWrapper(input: RequestInfo, init?: RequestInit){
        this.progressBar.start();
        
        try{
            return await fetch(input, init);
        }
        catch(e){
            if(e instanceof Error && e.message == "Failed to fetch"){
                e.message += ` ${input}`
            }
            throw e
        }
        finally{
            this.progressBar.end();
        }
    }

    async tryReloadToken(){
        if(this.tokenExpiration - this.reloadPadding < Date.now()){
            let newAuthResp = await this.auth.currentUser.get().reloadAuthResponse();

            this.googleToken = newAuthResp.id_token;
            this.tokenExpiration = newAuthResp.expires_at;
        }
    }

    login(token: string){
        this.googleToken = token;
        this.state = "signed_in";
    }

    logout(){
        this.auth.signOut().then(() => {
            this.state = "not_signed_in";
        })
    }

    async getErrorString(error: any){
        let errorText: string;

        if(error instanceof Response){
            let respText: string | undefined = undefined;
            try{
                respText = (await error.json()).error;
            }
            catch{}

            errorText = `Failed to get ${error.url}, ${error.statusText}` + 
                (respText == undefined?"":`: ${respText}`)
        }
        else if(error instanceof Error){
            errorText = error.toString()
        }
        else if(error instanceof Object){
            errorText = JSON.stringify(error);
        }
        else{
            errorText = error.toString();
        }

        return errorText;
    }
    
    async mounted() {
        this.progressBar.start();
        window.addEventListener("unhandledrejection", async (e) => {
            this.$refs.errors.addError(await this.getErrorString((<any>e).reason));
        })

        let configJSON = (await (await fetch("config.json")).json());
        this.api = new swaggerAPI.DefaultApi(this.fetchWrapper.bind(this), configJSON.configServer);

        // let google tell us when it's loaded (look in index.html for the definition of this)
        await (<any>window).gapiLoadPromise;

        gapi.load('auth2', () => {
            gapi.auth2.init({
                client_id: configJSON.clientId,
                fetch_basic_profile: false,
                scope: 'profile',
                hosted_domain: "sanger.ac.uk"
            }).then(auth => {
                this.progressBar.end();
                this.auth = auth;
                if(this.auth.isSignedIn.get()){
                    let authResponse = this.auth.currentUser.get().getAuthResponse();
                    this.tokenExpiration = authResponse.expires_at;

                    this.login(authResponse.id_token);

                    // Reload the token when it expires
                    // I cannot just use setInterval on the expiration date, as
                    // javascript timers stop running when the computer is sleeping 

                    setInterval(() => this.tryReloadToken(), this.reloadPadding / 2);
                    window.addEventListener("focus", () => this.tryReloadToken());
                }
                else{
                    this.state = "not_signed_in"
                }
            })
        })
    }
}
</script>
