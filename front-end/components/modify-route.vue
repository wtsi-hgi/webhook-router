<template>
<div>
<whr-navbar>
    <span class="divider">&nbsp; </span>
    <router-link to="/">
        <button type="button" class="btn btn-outline-secondary">
            <span class="oi oi-chevron-left"></span> Back
        </button>
    </router-link>
    <span class="mr-auto"></span>
    <slot name="logoutButton"></slot>
</whr-navbar>
<div id="base" class="container">
    <br />
    <slot name="errors" ref="errors"></slot>
    <div v-show="loaded">
        <h2>
            <span>
                Route: "{{currData.name}}"
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
                <button type="submit" class="btn btn-outline-success" :disabled="!modified">Save Changes</button>
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
        </div>
    </div>

    <div class="modal fade" id="deleteConfirm" tabindex="-1" role="dialog" aria-labelledby="deleteConfirmLabel" aria-hidden="true" ref="deleteModal">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="deleteConfirmLabel">Confirm route deletion</h5>
              <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body">
                Are you sure you want to delete "{{currData.name}}"?
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
              <button type="button" class="btn btn-danger" @click="deleteRoute">Delete Route</button>
            </div>
          </div>
        </div>
    </div>

    <div class="modal fade" id="regenerateConfirm" tabindex="-1" role="dialog" aria-labelledby="regenerateConfirmLabel" aria-hidden="true" ref="regenerateModal">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="regenerateConfirmLabel">Confirm token regeneration</h5>
              <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body">
                Are you sure you want to regenerate the token of "{{currData.name}}"?
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
<style scoped>
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
import ErrorsComponent from "./errors.vue";
import * as utils from "../utils";

@Component({
    props: {
        uuid: String,
        googleToken: String,
        api: Object
    },
    components: {
        "whr-navbar": NavBarComponent,
        "errors": ErrorsComponent
    }
})
export default class extends Vue {
    uuid: string
    errorText = ""
    name = ""
    destination = ""
    token = ""
    loaded = false
    routingServer = routingServer
    $refs: {
        errors: ErrorsComponent;
        deleteModal: HTMLElement;
        regenerateModal: HTMLElement;
    }

    currData = {
        name: "",
        destination: ""
    }

    googleToken: string;
    readonly authOptions = utils.getAuthOptions(this.googleToken);

    get modified () {
        return this.loaded && !(this.currData.name == this.name 
                  && this.currData.destination == this.destination)
    }

    api: swaggerAPI.DefaultApi;

    async postForm(){
        let patchResult = await this.api.patchRoute({
            uuid: this.uuid,
            newInfo: {
                name: this.name,
                destination: this.destination
            }
        }, this.authOptions)

        this.currData = {
            name: this.name,
            destination: this.destination
        }
    }

    async deleteRoute() {
        let success = false;
        try {
            await this.api.deleteRoute({uuid: this.uuid}, this.authOptions);
            success = true;
        }
        finally{
            await utils.closeModal(this.$refs.deleteModal);
        }

        if(success){
            this.$router.push("/");
        }
    }

    async regenerateToken() {
        let resp = await this.api.regenerateToken({
            uuid: this.uuid
        }, this.authOptions)
        
        this.token = resp.token;
    }

    async mounted() {
        try{
            var route = await this.api.getRoute({
                uuid: this.uuid
            }, this.authOptions)
        }
        catch(e){
            if(e instanceof Response){
                this.$refs.errors.addErrorText((await e.json()).error, true);
                return
            }

            throw e;
        }

        Object.keys(route).forEach(key => {
            (<any>this)[key] = (<any>route)[key];
        })

        this.currData.name = route.name;

        this.currData = {
            name: route.name,
            destination: route.destination
        }

        this.loaded = true
    }
}
</script>

