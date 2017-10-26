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
    <form @submit.prevent="postForm">
        <h2>
            Create a new route
        </h2>
        <br/>
        <label for="route-name">Name:</label>
        <input type="text" required class="form-control" placeholder="Route Name" 
            id="route-name" v-model="name" required>
        <br />
        <label for="route-destination">Destination:</label>
        <input type="url" class="form-control" placeholder="Route Destination"
            id="route-destination" v-model="destination" required>
        <br/>
        <br />
        <button type="submit" class="btn btn-success">Create Route</button>
        <button type="reset" @click="cancelForm" class="btn">Cancel</button>
        <br />
        <br />
        <div id="error-element" class="text-danger">{{errorText}}</div>
    </form>
</div>
</div>
</template>
<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import {configServer} from "../config";
import NavBarComponent from "./whr-navbar.vue";

@Component({
    components: {
        "whr-navbar": NavBarComponent
    }
})
export default class extends Vue {
    errorText = ""
    name = ""
    destination = ""

    private api = new swaggerAPI.DefaultApi(fetch, configServer);

    postForm(){
        this.api.addRoute({
            newRoute: {
                destination: this.destination,
                name: this.name
            },
    
        }).then(result => {
            console.log(result)
            this.$router.push("/");
        }).catch(e => {
            this.errorText = "Error: " + e.toString()
        })
    }

    cancelForm() {
        this.$router.push("/");
    }
}
</script>

