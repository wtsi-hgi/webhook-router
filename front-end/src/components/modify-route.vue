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
<div id="base" class="container">
    <br />
    <slot name="errors"></slot>
    <div v-show="loaded">
        <h2>
            <span>
                Route: "{{configServerFormData.name}}"
            </span>
            <button type="button" class="btn btn-outline-danger btn-sm" data-toggle="modal" data-target="#deleteConfirm" style="margin-left: 10px; ">
                Delete Route</button>
            <button type="button" class="btn btn-outline-secondary btn-sm" data-toggle="modal" data-target="#removeConfirm">
                Remove from my routes</button>
        </h2>
        <hr>
        <div class="form-section">
            <h4>Configuration</h4>
            <hr>
            <div class="form-section">
                <route-details-form @formModified="formModified" v-if="loaded" @formSubmitted="postForm" :squashed="true" :initalData="configServerFormData">
                    <button type="submit" slot="submitButton" slot-scope="props" :disabled="props.disableButton" class="btn btn-outline-success">Save Changes</button>
                </route-details-form>
            </div>
            <h4>References</h4>
            <hr>
            <div class="form-section">
                <label for="route-destination">Token:</label>
                <code>{{token}}</code>
                <button type="button" class="btn btn-outline-danger btn-sm" data-toggle="modal" data-target="#regenerateConfirm">
                    Regenerate Token</button>
                <br />
                <label for="route-destination">UUID:</label>
                <code>{{uuid}}</code>
                <hr>
                Route location: 
                <code>
                    {{routingServerLocation}}/{{token}}
                </code>
            </div>
            <br />
            <h4>Statistics</h4>
            <hr>
            <div class="form-section">
                {{stats.successes}} webhook{{stats.successes == 1?"":"s"}} correctly routed. {{stats.failures}} error{{stats.failures == 1?"":"s"}}.
            </div>
            <br />
            <div v-show="errorLogs != ''">
                <h4>Recent Errors</h4>
                <hr>
                <div class="form-section">
                    <pre><code>{{errorLogs}}</code></pre>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="deleteConfirm" tabindex="-1" role="dialog" aria-labelledby="deleteConfirmLabel" aria-hidden="true" ref="deleteModal">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title" id="deleteConfirmLabel">Confirm route deletion</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true" v-html="'&times;'"></span>
            </button>
        </div>
        <div class="modal-body">
            Are you sure you want to delete "{{configServerFormData.name}}"?
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            <button type="button" class="btn btn-danger" @click="deleteRoute">Delete Route</button>
        </div>
        </div>
    </div>
</div>

<div class="modal fade" id="removeConfirm" tabindex="-1" role="dialog" aria-labelledby="removeConfirmLabel" aria-hidden="true" ref="removeModal">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title" id="removeConfirmLabel">Confirm route removal</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true" v-html="'&times;'"></span>
            </button>
        </div>
        <div class="modal-body">
            Are you sure you want to remove "{{configServerFormData.name}}" from your routes?
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            <button type="button" class="btn btn-danger" @click="removeRoute">Remove Route</button>
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
            <span aria-hidden="true" v-html="'&times;'"></span>
            </button>
        </div>
        <div class="modal-body">
            Are you sure you want to regenerate the token of "{{configServerFormData.name}}"?
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
.form-section{
    padding-left: 10px
}
</style>


<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import NavBarComponent from "./whr-navbar.vue";
import ErrorsComponent from "./errors.vue";
import * as utils from "../utils";
import {isEqual, cloneDeep, property, pick} from "lodash";
import RouteDetailsForm from "./route-details-form.vue";

@Component({
    props: {
        uuid: String,
        googleToken: String,
        api: Object
    },
    components: {
        "whr-navbar": NavBarComponent,
        "errors": ErrorsComponent,
        "route-details-form": RouteDetailsForm
    }
})
export default class extends Vue {
    /**
     * Props passed to the object
     */
    uuid: string;
    api: swaggerAPI.DefaultApi;
    googleToken: string;

    token = "";
    loaded = false;
    routingServerLocation = "";
    $refs: {
        deleteModal: HTMLElement;
        removeModal: HTMLElement;
        regenerateModal: HTMLElement;
    }

    formModified = false

    /**
     * State for statistics
     */
    stats = {
        successes: 0,
        failures: 0
    }
    errorLogs = "";

    /**
     * Data structure containing the data that is currently stored in
     * the config server (populated on mount), that is used in the details form
     */
    configServerFormData = utils.defaultFormData;

    readonly authOptions = utils.getAuthOptions(this.googleToken);

    async postForm(formData: any){
        let patchResult = await this.api.patchRoute({
            uuid: this.uuid,
            newInfo: formData
        }, this.authOptions);

        this.configServerFormData = cloneDeep(formData);
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

    async removeRoute(){
        let success = false;
        try {
            await this.api.deleteRouteLink({uuid: this.uuid}, this.authOptions);
            success = true;
        }
        finally{
            await utils.closeModal(this.$refs.removeModal);
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

    formatError(error: any){
        let excludeProps = new Set([
            "message",
            "level",
            "@timestamp",
            "uuid",
            "success"
        ]);

        let propertyStr = Object.entries(error)
            .filter(x => !excludeProps.has(x[0]))
            .map(propPair => `\t${propPair[0]}=${propPair[1]}`);
        
        let timestamp = (new Date(error["@timestamp"])).toLocaleString()

        return `[${timestamp}] ${error.level}: ${error.message} \n${propertyStr.join("\n")}`
    }

    async displayRouteStats(){
        let [stats, logs] = await Promise.all([
            await this.api.getRouteStats({
                uuid: this.uuid
            }, this.authOptions),
            await this.api.getRouteLogs({
                uuid: this.uuid
            }, this.authOptions)
        ])

        this.stats = stats;
        this.errorLogs = logs.map(x => this.formatError(x)).join("\n");
    }

    async getRouteInfo(){
        var route = await this.api.getRoute({
            uuid: this.uuid
        }, this.authOptions);

        this.uuid = route.uuid;
        this.token = route.token;

        this.configServerFormData = <any>pick(route, utils.formAttributes);
    }

    async mounted() {
        this.routingServerLocation = (await (await fetch("config.json")).json()).routingServer;

        try{
            await Promise.all([this.getRouteInfo(), this.displayRouteStats()]);
        }
        finally{
            // load the bits that we can load
            this.loaded = true;
        }
    }
}
</script>

