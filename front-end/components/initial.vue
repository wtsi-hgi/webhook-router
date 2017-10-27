<template>
<div>
    <div v-if="state=='start'">
        <whr-navbar></whr-navbar>
    </div>
    <signin v-else-if="state=='not_signed_in'" @signedIn="token => login(token)"></signin>
    <router-view v-else class="view" :key="$route.fullPath" :googleToken="googleToken" thing="2">
        <button type="button" class="btn btn-outline-warning" slot="logoutButton" @click="logout">Logout</button>
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
import Component from 'vue-class-component'

const router = new VueRouter({
    mode: "hash",
    base: __dirname,
    routes: [
        {path: "/", component: DisplayRoutesComponent, name: "home"},
        {path: "/add-route", component: AddRouteComponent, name: "add-route"},
        {path: "/routes/:uuid", component: ModifyRoute, props: true, name: "modify-route"}
    ]
})

@Component({
    components: {
        "whr-navbar": NavBarComponent,
        "signin": SignInComponent
    },
    router: router
})
export default class extends Vue {
    signedin = false
    state = "start"
    googleToken = ""
    auth: gapi.auth2.GoogleAuth;

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
