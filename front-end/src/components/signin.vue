<template>
<div>
    <whr-navbar></whr-navbar>
    <div class="container" style="align-text:center">
        <br />
        <h5>Please sign in to continue:</h5>
        <br />
        <div id="google-signin"></div>
        <br />
        <button @click="trySignIn" type="button" class="btn btn-outline-secondary">
            <span>
                <img class="sanger-logo" src="img/logo.png" />
            </span>
            <span>
                Sign in with Sanger
            </span>
        </button>
    </div>
</div>
</template>
<script lang="ts">
/// <reference types="gapi.auth2" />
import Vue from "vue";
import Component from 'vue-class-component';
import NavBarComponent from "./whr-navbar.vue";
import * as utils from "../utils";
import ErrorsComponent from "./errors.vue";

const ClientOAuth2 = require('client-oauth2')

@Component({
    components: {
        "whr-navbar": NavBarComponent,
        "errors": ErrorsComponent
    }
})
export default class extends Vue {
    mounted(){
        gapi.signin2.render("google-signin", {
            scope: "profile email",
            theme: 'light',
            width: 250,
            height: 50,
            longtitle: true,
            onsuccess: user => {
                this.$emit("signedIn", user.getAuthResponse().id_token)
            }
        });
    }

    trySignIn(){
        let nonse = utils.getRandomHex();

        let sangerAuth = new ClientOAuth2({
            clientId: '-4d8mHm_RF2OnaqJgczhqA',
            authorizationUri: 'https://www.sanger.ac.uk/oa2/Auth',
            redirectUri: window.location,
            scopes: ['profile'],
            state: nonse
        });

        window.location.href = sangerAuth.token.getUri();
    }
}
</script>

