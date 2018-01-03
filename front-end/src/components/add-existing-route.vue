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
        Add an existing route
    </h2>
    <hr>
    <form @submit.prevent="postForm">
        <div style="margin-left: 10px">
            <div @click="radioSelect = 'uuid'">
                <input class="form-check-input" type="radio" name="example_route_radio" value="uuid" v-model="radioSelect">
                <label for="route-name">UUID:</label>
                <input type="text" required class="form-control" placeholder="Route UUID"
                    id="route-name" v-model="uuid" :disabled="radioSelect == 'token'" ref="routeUUIDInput" autofocus>
            </div>
            <br />
            <b>OR</b>
            <br />
            <br />
            <div @click="radioSelect = 'token'">
                <input class="form-check-input" type="radio" name="example_route_radio" value="token" v-model="radioSelect">
                <label for="route-destination">Token:</label>
                <input type="text" class="form-control" placeholder="Route Token"
                    id="route-destination" v-model="token" required :disabled="radioSelect == 'uuid'" ref="routeTokenInput">
            </div>
            <br/>
            <br />
            <button type="submit" class="btn btn-outline-success">Add route</button>
            <button type="reset" @click="cancelForm" class="btn btn-outline-secondary">Back</button>
            <br />
        </div>
    </form>
</div>
</div>
</template>
<style>
.radioDisabled{
    color: grey
}
</style>
<script lang="ts">
import Vue from "vue";
import Component from 'vue-class-component'
import NavBarComponent from "./whr-navbar.vue";
import * as utils from "../utils";
import { Prop, Watch } from 'vue-property-decorator';

@Component({
    components: {
        "whr-navbar": NavBarComponent,
    }
})
export default class extends Vue {
    radioSelect = "uuid"
    token = ""
    uuid = ""

    $refs: {
        routeUUIDInput: HTMLInputElement,
        routeTokenInput: HTMLInputElement
    }

    @Prop() api: SwaggerAPI<BasicAPI>;

    @Watch("radioSelect") onRadioSelect() {
        setTimeout(() => {
            if((<any>this).radioSelect == "uuid"){
                this.$refs.routeUUIDInput.focus()
            }
            else{
                this.$refs.routeTokenInput.focus()
            }
        }, 0) // focus on next tick
    }

    async postForm(){
        let uuid = this.uuid;
        if(this.radioSelect == "token"){
            let resp = await this.api.apis.routes.get_by_token({token: this.token});
            uuid = resp.obj.uuid;
        }

        await this.api.apis.links.add_route_link({uuid: uuid});

        this.$router.push(`/routes/${uuid}`);
    }

    cancelForm() {
        this.$router.push("/");
    }
}
</script>

