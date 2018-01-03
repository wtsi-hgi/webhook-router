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
            <b-btn v-b-modal.deleteModal variant="outline-danger" size="sm" style="margin-left: 10px">Delete Route</b-btn>
            <!--Note: change this to if-else when https://github.com/bootstrap-vue/bootstrap-vue/issues/1454 is resolved-->
            <b-btn v-b-modal.removeModal v-show="hasUserAddedRoute" variant="outline-secondary" size="sm">Remove from my routes</b-btn>
            <b-btn v-show="!hasUserAddedRoute" @click="addToMyRoutes" variant="outline-success" size="sm">Add to my routes</b-btn>
        </h2>
        <hr>
        <div class="form-section">
            <h4>Configuration</h4>
            <hr>
            <div class="form-section">
                <route-details-form v-if="loaded" @formSubmitted="postForm" :squashed="true" :initalData="configServerFormData">
                    <button type="submit" slot="submitButton" slot-scope="props" :disabled="props.disableButton" class="btn btn-success">Save Changes</button>
                </route-details-form>
            </div>
            <h4>Location</h4>
            <hr>
            <div class="form-section">
                <code ref="routeLocation">{{routingServerLocation}}/{{token}}</code>
                <div style="display: inline-block" data-trigger="manual" ref="copyButton" title="Copied!" @click="copyRouteLocation">
                <button type="button" class="btn btn-outline-secondary btn-sm">
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
                <svg class="octicon octicon-clippy" viewBox="0 0 14 16" version="1.1" width="14" height="16" aria-hidden="true"><path class="clipboard-icon" fill-rule="evenodd" d="M2 13h4v1H2v-1zm5-6H2v1h5V7zm2 3V8l-3 3 3 3v-2h5v-2H9zM4.5 9H2v1h2.5V9zM2 12h2.5v-1H2v1zm9 1h1v2c-.02.28-.11.52-.3.7-.19.18-.42.28-.7.3H1c-.55 0-1-.45-1-1V4c0-.55.45-1 1-1h3c0-1.11.89-2 2-2 1.11 0 2 .89 2 2h3c.55 0 1 .45 1 1v5h-1V6H1v9h10v-2zM2 5h8c0-.55-.45-1-1-1H8c-.55 0-1-.45-1-1s-.45-1-1-1-1 .45-1 1-.45 1-1 1H3c-.55 0-1 .45-1 1z"></path></svg>
                <span style="display:inline-block;vertical-align: text-bottom;padding-left: 1px;">Copy Route</span>
                </button>
                </div>
            </div>
            <br />
            <h4>References</h4>
            <hr>
            <div class="form-section">
                <label for="route-destination">Token:</label>
                <code>{{token}}</code>
                <b-btn v-b-modal.regenerateModal variant="outline-danger" size="sm">Regenerate Token</b-btn>
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

<b-modal
    id="deleteModal"
    title="Confirm route deletion"
    cancel-title="Close"
    ok-title="Delete Route"
    ok-variant="danger"
    @ok="deleteRoute">
    Are you sure you want to delete "{{configServerFormData.name}}"?
</b-modal>

<b-modal
    id="removeModal"
    title="Confirm route removal"
    cancel-title="Close"
    ok-title="Remove Route"
    ok-variant="danger"
    @ok="removeRoute">
    Are you sure you want to remove "{{configServerFormData.name}}" from your routes?
    <br />
    <small>This will not delete the route, but remove it from the list of your routes.</small>
</b-modal>


<b-modal
    id="regenerateModal"
    title="Confirm token regeneration"
    cancel-title="Close"
    ok-title="Regenerate Token"
    ok-variant="danger"
    @ok="regenerateToken">
    Are you sure you want to regenerate the token of "{{configServerFormData.name}}"?
    <br />
    <small>Regenerating tokens will break all links to this route.</small>
</b-modal>

</div>
</template>
<style>
.form-section{
    padding-left: 10px
}
.clipboard-icon{
    fill: rgb(134, 142, 150);
}
button:hover .clipboard-icon{
    fill: #fff;
}
</style>


<script lang="ts">
import Vue from "vue";
import Component from 'vue-class-component'
import NavBarComponent from "./whr-navbar.vue";
import ErrorsComponent from "./errors.vue";
import * as utils from "../utils";
import {isEqual, cloneDeep, property, pick} from "lodash";
import RouteDetailsForm from "./route-details-form.vue";

@Component({
    props: {
        uuid: String,
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
    api: SwaggerAPI<BasicAPI>;

    token = "";
    loaded = false;
    routingServerLocation = "";
    $refs: {
        routeLocation: HTMLElement;
        copyButton: HTMLElement;
    }

    /**
     * Whether the user has this route in their routes
     */
    hasUserAddedRoute = true;

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

    async postForm(formData: any){
        await this.api.apis.routes.patch_route({
            uuid: this.uuid,
            new_info: formData
        });

        this.configServerFormData = cloneDeep(formData);
    }

    async deleteRoute(event: any) {
        event.preventDefault();
        let success = false;
        try {
            await this.api.apis.routes.deleteRoute({uuid: this.uuid});
            success = true;
        }
        finally{
            await utils.closeModal(event.vueTarget);
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

    async removeRoute(event){
        event.preventDefault();
        let success = false;
        try {
            await this.api.apis.links.delete_route_link({uuid: this.uuid});
            success = true;
        }
        finally{
            await utils.closeModal(event.vueTarget);
        }

        if(success){
            this.hasUserAddedRoute = false;
        }
    }

    async addToMyRoutes(){
        await this.api.apis.links.add_route_link({
            uuid: this.uuid
        });

        this.hasUserAddedRoute = true;
    }

    async regenerateToken(event) {
        event.preventDefault();
        try {
            let resp = await this.api.apis.routes.regenerate_token({
                uuid: this.uuid
            })

            this.token = resp.obj.token;
        }
        finally {
            await utils.closeModal(event.vueTarget);
        }
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
        let [stats, logs] = <[any, any]>(await Promise.all([
            await this.api.apis.stats.get_route_stats({
                uuid: this.uuid
            }),
            await this.api.apis.logs.get_route_logs({
                uuid: this.uuid
            })
        ])).map(x => x.obj)

        this.stats = stats;
        this.errorLogs = logs.map(x => this.formatError(x)).join("\n");
    }

    async setRouteInfo(){
        let route = (await this.api.apis.routes.get_route({
            uuid: this.uuid
        })).obj;

        this.uuid = route.uuid;
        this.token = route.token;

        this.configServerFormData = <any>pick(route, utils.formAttributes);
    }

    async setHasUserAddedRoute(){
        try{
            let route = (await this.api.apis.links.get_route_link({
                uuid: this.uuid
            })).obj
        }
        catch(e){
            if(e instanceof Response && e.status == 404){
                this.hasUserAddedRoute = false;
            }
            else{
                throw e;
            }
        }
    }

    async mounted() {
        this.routingServerLocation = (await (await fetch("config.json")).json()).routingServer;

        try{
            await Promise.all([this.setRouteInfo(), this.displayRouteStats(), this.setHasUserAddedRoute()]);
        }
        finally{
            // load the bits that we can load
            this.loaded = true;
        }
    }
}
</script>

