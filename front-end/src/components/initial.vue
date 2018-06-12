<template>
<div>
    <div v-if="isOnSangerCallback()">
    </div>
    <div v-else-if="state=='start'">
        <whr-navbar></whr-navbar>
        <errors ref="errors" slot="errors"></errors>
    </div>
    <div v-else-if="state=='not_signed_in'">
        <signin @googleLoginButtonPressed="googleLoginButtonPressed" @sangerLoginButtonPressed="sangerLoginButtonPressed">
            <errors ref="errors" slot="errors"></errors>
        </signin>
    </div>
    <!--Setting the key as below reloads the page on path change-->
    <router-view v-else class="view" :key="$route.fullPath" :adminAPI="adminAPI" :api="api">
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
import AdminPanelComponent from "./admin-panel.vue"
import Component from 'vue-class-component';
import ErrorsComponent from "./errors.vue";
import * as utils from "../utils";
var Mprogress = require("mprogress"); // Do this, as the main module is not exported
import {auto} from 'browser-unhandled-rejection';
import Swagger from 'swagger-client';
import * as ClientOAuth2 from "client-oauth2";
import OAuthHelper from "../OAuthHelper"
import {startsWith} from "lodash";
import {notEqual as assertNotEqual} from "assert";

// pollyfill the event unhandledrejection
auto();

const router = new VueRouter({
    mode: "hash",
    base: __dirname,
    routes: [
        {path: "/", component: DisplayRoutesComponent, name: "home"},
        {path: "/create-route", component: CreateRouteComponent, name: "create-route"},
        {path: "/admin", component: AdminPanelComponent, name: "admin"},
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
export default class Inital extends Vue {
    signedin = false
    state = "start";
    oAuthHelper: OAuthHelper;
    api: SwaggerAPI<BasicAPI>;
    adminAPI: SwaggerAPI<BasicAPI>;
    tokenExpiration: number;
    progressBar = new Mprogress({
        template: 3, // 3 = indeterminate progress bar
        parent: 'body'
    });
    configJSON: Promise</*typeof import("../../config.json")*/any> = (async () => await (await fetch("config.json")).json())()

    /**
     * Padding time for a reload of a token.
     * Half of this value will also be when the brower checks for the token being refreshed
     */
    readonly reloadPadding = 10 * 60 * 1000; // 10 mins

    $refs: {
        errors: ErrorsComponent;
    }

    isOnSangerCallback(){
        return window.location.search == "?oauth_callback";
    }

    private async logon(oAuthHelper: OAuthHelper){
        assertNotEqual(oAuthHelper.token, undefined);

        function getOpenAPIAuthFromToken(oAuthHelper: OAuthHelper){
            return  {
                oAuth: {
                    token: {
                        access_token: oAuthHelper.name + "=" + oAuthHelper.token
                    }
                }
            }
        }

        this.oAuthHelper = oAuthHelper;
        const configJSON = await this.configJSON;

        [this.api, this.adminAPI] = await Promise.all([`${configJSON.configServer}/swagger.json`, `${configJSON.adminServer}/swagger.json`].map(
            url => Swagger(url, {
                authorizations: getOpenAPIAuthFromToken(this.oAuthHelper),
                requestInterceptor: () => {
                    this.progressBar.start();
                },
                responseInterceptor: (resp) => {
                    this.progressBar.end();
                }
            }))
        )
        this.oAuthHelper.emitter.on(OAuthHelper.tokenChangeEvent, () => {
            [this.api, this.adminAPI].forEach(x => {
                x.authorizations = getOpenAPIAuthFromToken(this.oAuthHelper)
            })
        })

        this.state = "signed_in";
    }

    async sangerLoginButtonPressed(){
        const sangerOAuthHelper = new OAuthHelper(
            "sanger",
            (await this.configJSON).sangerClientId,
            "https://www.sanger.ac.uk/oa2/Auth",
            ["profile"]
        );
        this.progressBar.start();
        if(await sangerOAuthHelper.promptLogin() !== undefined)
            await this.logon(sangerOAuthHelper);
        this.progressBar.end();
    }

    async googleLoginButtonPressed() {
        const googleOAuthHelper = new OAuthHelper(
            "google",
            (await this.configJSON).googleClientId,
            "https://accounts.google.com/o/oauth2/auth",
            ["profile", "email"],
            {
                "hd": "sanger.ac.uk"
            }
        );
        this.progressBar.start();
        if(await googleOAuthHelper.promptLogin() !== undefined)
            await this.logon(googleOAuthHelper);
        this.progressBar.end();
    }


    async logout(){
        await this.oAuthHelper.logout();
        this.state = "not_signed_in";
    }

    getErrorString(error: any){
        if(error instanceof Error){
            if((<any>error).response != undefined){
                let resp = (<any>error).response;
                return `Failed to get ${resp.url}, ${resp.statusText}: ${resp.obj.error || ""}`;
            }
            else{
                return error.message
            }
        }
        else if(error instanceof ErrorEvent){
            if (error.message == "Script error."){
                return "Check the DevTools console for information"
            }
            else{
                return `${error.lineno}:${error.colno} ${error.message}`
            }
        }
        else if(error instanceof Object){
            return JSON.stringify(error);
        }
        else{
            return error.toString();
        }
    }

    onError(errorText: string){
        this.$refs.errors.addError(errorText);

        this.progressBar.end();
    }

    async mounted() {
        window.addEventListener("unhandledrejection", async (e) => {
            this.onError(this.getErrorString((<any>e).reason));
        })

        window.addEventListener("error", async (e) => {
            this.onError(this.getErrorString(e));
        })

        const configJSON = await this.configJSON;

        this.progressBar.start();

        const sangerOAuthHelper = new OAuthHelper(
            "sanger",
            (await this.configJSON).sangerClientId,
            "https://www.sanger.ac.uk/oa2/Auth",
            ["profile"]
        );

        const sangerToken = await sangerOAuthHelper.loadTryGetToken();
        if (sangerToken !== undefined){
            await this.logon(sangerOAuthHelper);
            this.state = "signed_in";

            return;
        }

        const googleOAuthHelper = new OAuthHelper(
            "google",
            (await this.configJSON).googleClientId,
            "https://accounts.google.com/o/oauth2/auth",
            ["profile", "email"],
            {
                "hd": "sanger.ac.uk"
            }
        );

        const googleToken = await googleOAuthHelper.loadTryGetToken();
        if (googleToken !== undefined){
            await this.logon(googleOAuthHelper);
            this.state = "signed_in";

            return;
        }

        this.state = "not_signed_in";
        this.progressBar.end();
    }
}
</script>
