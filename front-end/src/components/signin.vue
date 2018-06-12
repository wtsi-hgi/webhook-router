<template>
<div>
    <whr-navbar></whr-navbar>
    <slot name="errors"></slot>
    <div class="container" style="align-text:center">
        <br />
        <h5>Please sign in to continue:</h5>
        <br />
          <span @click="$emit('googleLoginButtonPressed')" class="btn btn-social btn-lg btn-google">
                <span class="fa fa-google"></span> Sign in with Google
          </span>
          <span @click="$emit('sangerLoginButtonPressed')" class="btn btn-social btn-lg btn-sanger">
                <span>
                    <img class="sanger-login-button" src="img/minimal-logo.png" />
                </span>
                <span>Sign in with Sanger</span>
          </span>
        <br />
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
export default class SignIn extends Vue {
    trySignIn(){
        let nonse = utils.getRandomHex();

        let sangerAuth = new ClientOAuth2({
            clientId: '-4d8mHm_RF2OnaqJgczhqA',
            authorizationUri: 'https://www.sanger.ac.uk/oa2/Auth',
            redirectUri: window.location.origin + "/#sanger_callback",
            scopes: ['profile'],
            state: nonse
        });

        localStorage.setItem("sangerAuthNonse", nonse);

        window.location.href = sangerAuth.token.getUri();
    }
}
</script>

