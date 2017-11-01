<template>
<div>
    <div v-if="state=='start'">
        <whr-navbar></whr-navbar>
    </div>
    <signin v-else-if="state=='not_signed_in'" @signedIn="token => login(token)"></signin>
    <router-view v-else class="view" :key="$route.fullPath" :googleToken="googleToken" :api="api">
        <button type="button" class="btn btn-outline-warning" slot="logoutButton" @click="logout">Logout</button>
        <errors ref="errors" slot="errors"></errors>
    </router-view>
    <!--Setting the key as above reloads the page on path change-->
</div>
</template>
<script lang="ts">

import Vue from "vue";
import VueRouter from "vue-router";
import DisplayRoutesComponent from "./display-routes.vue";
import AddRouteComponent from "./add-route.vue";
import ModifyRoute from "./modify-route.vue";
import SignInComponent from "./signin.vue";
import NavBarComponent from "./whr-navbar.vue";
import NotFoundComponent from "./404-not-found.vue";
import Component from 'vue-class-component';
import ErrorsComponent from "./errors.vue";
import * as swaggerAPI from "../api";
import * as utils from "../utils";
import {configServer} from "../config"
var Mprogress = require("mprogress/mprogress.min.js"); // Do this, as the main module is not exported

const router = new VueRouter({
    mode: "hash",
    base: __dirname,
    routes: [
        {path: "/", component: DisplayRoutesComponent, name: "home"},
        {path: "/add-route", component: AddRouteComponent, name: "add-route"},
        {path: "/routes/:uuid", component: ModifyRoute, props: true, name: "modify-route"},
        {path: "*", component: NotFoundComponent, name: "home"}
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
    googleToken = ""
    auth: any;

    api = new swaggerAPI.DefaultApi(this.fetchWrapper.bind(this), configServer);

    progressBar = new Mprogress({
        template: 3, // 3 = indeterminate progress bar
        parent: 'body'
    });

    $refs: {
        errors: ErrorsComponent;
    }

    private async fetchWrapper(input: RequestInfo, init?: RequestInit){
        this.progressBar.start();
        
        try{
            return await fetch(input, init);
        }
        catch(e){
            this.$refs.errors.addError(e);
            throw e;
        }
        finally{
            this.progressBar.end();
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
    
    mounted() {
        gapi.load('auth2', () => {
            gapi.auth2.init({
                client_id: '859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.apps.googleusercontent.com',
                fetch_basic_profile: false,
                scope: 'profile',
                hosted_domain: "sanger.ac.uk"
            }).then(auth => {
                this.auth = auth;
                if(this.auth.isSignedIn.get()){
                    this.login(this.auth.currentUser.get().getAuthResponse().id_token)
                }
                else{
                    this.state = "not_signed_in"
                }
            })
        })
    }
}
</script>
