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
import Component from 'vue-class-component'
import NavBarComponent from "./whr-navbar.vue";
import RouteDetailsForm from "./route-details-form.vue";
import * as utils from "../utils";
import { pick } from "lodash";
import { Prop } from 'vue-property-decorator';

@Component({
    components: {
        "whr-navbar": NavBarComponent,
        "route-details-form": RouteDetailsForm
    }
})
export default class extends Vue {
    @Prop() api: SwaggerAPI<BasicAPI>;
    @Prop() adminAPI: SwaggerAPI<BasicAPI>;

    async postForm(data: any){
        /*let isValid = (await this.adminAPI.apis.default.is_url_valid({
            url: data.destination
        })).obj;

        if(!isValid){
            console.error("Incorrect route");

            return;
        }*/

        let newRoute = (await this.api.apis.routes.create_route({
            new_route: <any>pick(data, utils.formAttributes)
        })).obj

        this.$router.push(`/routes/${newRoute.uuid}`);
    }

    cancelForm() {
        this.$router.push("/");
    }
}
</script>

