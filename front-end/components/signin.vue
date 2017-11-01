<template>
<div>
    <whr-navbar></whr-navbar>
    <div class="container">
        <br />
        <h5>Please sign in to continue:</h5>
        <br />
        <div id="google-signin"></div>
    </div>
</div>
</template>
<script lang="ts">
import Vue from "vue";
import Component from 'vue-class-component';
import NavBarComponent from "./whr-navbar.vue";
import * as utils from "../utils";
import ErrorsComponent from "./errors.vue";

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
            theme: 'dark',
            longtitle: true,
            onsuccess: user => {
                this.$emit("signedIn", user.getAuthResponse().id_token)
            }
        });
    }
}
</script>

