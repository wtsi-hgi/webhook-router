<template>
<div>
<whr-navbar>
    <span class="divider" v-html="'&nbsp;'"></span>
    <router-link to="/">
        <button type="button" class="btn btn-outline-secondary">
            <span class="oi oi-chevron-left"></span> Back
        </button>
    </router-link>
    <span class="mr-auto"></span>
    <slot name="logoutButton"></slot>
</whr-navbar>
  <div class="container">
    <br/>
    <slot name="errors"></slot>
    <h2>
        Create a new route
    </h2>
    <hr>
    <form @submit.prevent="postForm">
        <div style="margin-left: 10px">
            <label for="route-name">Name:</label>
            <input type="text" required class="form-control" placeholder="Route Name" 
                id="route-name" v-model="name" required>
            <br />
            <label for="route-destination">Destination:</label>
            <input type="url" class="form-control" placeholder="Route Destination"
                id="route-destination" v-model="destination" required>
            <br />
            <label for="check-certificates">Don't verify certificates</label>
            <input type="checkbox" id="check-certificates" class="form-control-inline" v-model="no_ssl_verification">
            <br/>
            <br />
            <button type="submit" class="btn btn-outline-success">Create Route</button>
            <button type="reset" @click="cancelForm" class="btn btn-outline-secondary">Cancel</button>
            <br />
        </div>
    </form>
</div>
</div>
</template>
<style>
input{
    margin-left: 10px;
}
</style>
<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import NavBarComponent from "./whr-navbar.vue";
import * as utils from "../utils";

@Component({
    components: {
        "whr-navbar": NavBarComponent,
    },
    props: {
        googleToken: String,
        api: Object
    }
})
export default class extends Vue {
    errorText = ""
    name = ""
    destination = "";
    no_ssl_verification = false;
    googleToken: string;
    readonly authOptions = utils.getAuthOptions(this.googleToken);

    api: swaggerAPI.DefaultApi;

    async postForm(){
        await this.api.createRoute({
            newRoute: {
                destination: this.destination,
                name: this.name,
                no_ssl_verification: this.no_ssl_verification
            }
        }, this.authOptions)

        this.$router.push("/");
    }

    cancelForm() {
        this.$router.push("/");
    }
}
</script>

