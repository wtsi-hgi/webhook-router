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
            <h4>Location</h4>
            <hr>
            <div class="form-section">
                <code ref="routeLocation" @click="selectRouteLocation">
                    {{routingServerLocation}}/{{token}}
                </code>
                <div style="display: inline-block" data-trigger="manual" ref="copyButton" title="Copied!" @click="copyRouteLocation">
                    <!--
                        From https://octicons.github.com/icon/clippy/
                        MIT License

                        Copyright (c) 2012-2016 GitHub, Inc.

                        Permission is hereby granted, free of charge, to any person obtaining a copy
                        of this software and associated documentation files (the "Software"), to deal
                        in the Software without restriction, including without limitation the rights
                        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
                        copies of the Software, and to permit persons to whom the Software is
                        furnished to do so, subject to the following conditions:

                        The above copyright notice and this permission notice shall be included in all
                        copies or substantial portions of the Software.

                        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
                        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
                        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
                        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
                        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
                        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
                        SOFTWARE.

                    -->
                <svg class="octicon octicon-clippy" viewBox="0 0 14 16" version="1.1" width="14" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M2 13h4v1H2v-1zm5-6H2v1h5V7zm2 3V8l-3 3 3 3v-2h5v-2H9zM4.5 9H2v1h2.5V9zM2 12h2.5v-1H2v1zm9 1h1v2c-.02.28-.11.52-.3.7-.19.18-.42.28-.7.3H1c-.55 0-1-.45-1-1V4c0-.55.45-1 1-1h3c0-1.11.89-2 2-2 1.11 0 2 .89 2 2h3c.55 0 1 .45 1 1v5h-1V6H1v9h10v-2zM2 5h8c0-.55-.45-1-1-1H8c-.55 0-1-.45-1-1s-.45-1-1-1-1 .45-1 1-.45 1-1 1H3c-.55 0-1 .45-1 1z"></path></svg>
                </div>
            </div>
            <br />
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
            <br />
            <small>This will not delete the route, but remove it from the list of your routes.</small>
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
        routeLocation: HTMLElement;
        copyButton: HTMLElement;
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

    selectRouteLocation() {
        window.getSelection().selectAllChildren(this.$refs.routeLocation);
    }

    async copyRouteLocation(){
        this.selectRouteLocation();
        document.execCommand("copy");
        let copyButton = $(this.$refs.copyButton);

        copyButton.tooltip("show");
        await utils.delay(1000);
        copyButton.tooltip("hide");
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

