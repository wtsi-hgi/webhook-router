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
    <div style="margin-left: 10px">
        <route-details-form @formSubmitted="postForm" :squashed="false">
            <button type="submit" slot="submitButton" slot-scope="props" :disabled="props.disableButton" class="btn btn-outline-success">Create Route</button>
            <button type="reset" slot="cancelButton" @click="cancelForm" class="btn btn-outline-secondary">Back</button>
        </route-details-form>
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
import NavBarComponent from "./whr-navbar.vue";
import RouteDetailsForm from "./route-details-form.vue";
import * as utils from "../utils";
import { pick } from "lodash";

@Component({
    components: {
        "whr-navbar": NavBarComponent,
        "route-details-form": RouteDetailsForm
    },
    props: {
        googleToken: String,
        api: Object
    }
})
export default class extends Vue {
    googleToken: string;
    readonly authOptions = utils.getAuthOptions(this.googleToken);

    api: swaggerAPI.DefaultApi;

    async postForm(data: any){
        let newRoute = await this.api.createRoute({
            newRoute: <any>pick(data, utils.formAttributes)
        }, this.authOptions)

        this.$router.push(`/routes/${newRoute.uuid}`);
    }

    cancelForm() {
        this.$router.push("/");
    }
}
</script>

