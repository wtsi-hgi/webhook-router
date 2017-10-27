<template>
<div>
<whr-navbar>
    <span class="divider">&nbsp; </span>
    <router-link to="/">
        <button type="button" class="btn btn-outline-secondary">
            <span class="oi oi-chevron-left"></span> Back
        </button>
    </router-link>
</whr-navbar>
  <div class="container">
    <br/>
    <errors ref="errors"></errors>
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
import {configServer} from "../config";
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
    errorText = ""
    name = ""
    destination = ""

    $refs: {
        errors: ErrorsComponent;
    }

    api = new swaggerAPI.DefaultApi(utils.fetchErrorWrapper((e) => {
        this.$refs.errors.addError(e);
    }), configServer);

    async postForm(){
        await this.api.addRoute({
            newRoute: {
                destination: this.destination,
                name: this.name
            },
    
        })

        this.$router.push("/");
    }

    cancelForm() {
        this.$router.push("/");
    }
}
</script>

