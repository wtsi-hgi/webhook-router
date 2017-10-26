<template>
<div>
<whr-navbar></whr-navbar>
<div id="base" class="container">
    <br />
    <h2>
        <span>
            Route: "{{initName}}"
        </span>
        <button type="button" class="btn btn-outline-danger btn-sm" data-toggle="modal" data-target="#deleteConfirm"
            id="deleteButton" style="margin-left: 10px; ">Delete Route</button>
    </h2>
    <hr>
    <div style="padding-left: 10px">
        <form @submit.prevent="postForm">
            <p>
                <label for="route-name">Name:</label>
                <input type="text" required class="form-control" placeholder="Route Name" 
                    id="route-name" required v-model="name">
            </p>
            <p>
                <label for="route-destination">Destination:</label>
                <input type="url" class="form-control" placeholder="Route Destination"
                    id="route-destination" required v-model="destination">
            </p>
            <button type="submit" class="btn btn-success" :disabled="!modified">Save Changes</button>
        </form>
        <hr>
        <div style="padding-left: 10px">
            <label for="route-destination">Token:</label>
            <code>{{token}}</code>
            <button type="button" class="btn btn-outline-danger btn-sm" data-toggle="modal" data-target="#regenerateConfirm">
                Regenerate Token</button>
            <br />
            <label for="route-destination">UUID:</label>
            <code>{{uuid}}</code>
        </div>
        <hr>
        <div style="padding-left: 10px">
            Route location: 
            <code>
                {{routingServer}}/{{token}}
            </code>
        </div>
        <hr>
    </div>
    <br />
    <router-link to="/">
        <button type="button" class="btn btn-outline-secondary">
            <span class="oi oi-chevron-left"></span> Back
        </button>
    </router-link>

    <div class="modal fade" id="deleteConfirm" tabindex="-1" role="dialog" aria-labelledby="deleteConfirmLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="deleteConfirmLabel">Confirm route deletion</h5>
              <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body">
                Are you sure you want to delete "{{initName}}"?
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
              <button type="button" class="btn btn-danger" @click="deleteRoute">Delete Route</button>
            </div>
          </div>
        </div>
    </div>

    <div class="modal fade" id="regenerateConfirm" tabindex="-1" role="dialog" aria-labelledby="regenerateConfirmLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="regenerateConfirmLabel">Confirm token regeneration</h5>
              <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body">
                Are you sure you want to regenerate the token of "{{initName}}"?
                <br />
                <small>Regenerating tokens will break all links to this route.</small>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
              <button type="button" class="btn btn-danger" data-dismiss="modal" @click="regenerateToken">Regenerate Token</button>
            </div>
          </div>
        </div>
    </div>
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
import {configServer, routingServer} from "../config"
import NavBarComponent from "./whr-navbar.vue";

@Component({
    props: {
        uuid: String
    },
    components: {
        "whr-navbar": NavBarComponent
    }
})
export default class extends Vue {
    uuid: string
    errorText = ""
    name = ""
    initName = ""
    destination = ""
    token = ""
    init = false
    routingServer = routingServer

    initData: {
        name: string
        destination: string
    }

    get modified () {
        return this.init && !(this.initData.name == this.name 
                  && this.initData.destination == this.destination)
    }

    api = new swaggerAPI.DefaultApi(fetch, configServer);

    postForm(){
        this.api.patchRoute({
            uuid: this.uuid,
            newInfo: {
                name: this.name,
                destination: this.destination
            }
        }).then(result => {
            console.log(result)
        }).catch(e => {
            this.errorText = "Error: " + e.toString()
        })
    }

    cancelForm() {
        this.$router.push("/");
    }

    deleteRoute() {
        this.api.deleteRoute({
            uuid: this.uuid
        })

        this.$router.push("/");
    }

    regenerateToken() {
        let api = new swaggerAPI.DefaultApi(fetch, configServer);
        api.regenerateToken({
            uuid: this.uuid
        }).then(resp => {
            this.token = resp.token;
        })
    }

    mounted() {
        this.api.getRoute({
            uuid: this.uuid
        }).then(route => {
            Object.keys(route).forEach(key => {
                (<any>this)[key] = (<any>route)[key];
            })

            this.initName = route.name;

            this.initData = {
                name: route.name,
                destination: route.destination
            }

            this.init = true
        }).catch(e => {
            this.errorText = e.toString()
        })
    }
}
</script>

