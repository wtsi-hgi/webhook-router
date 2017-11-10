<template>
<div>
    <whr-navbar>
        <span class="divider" v-html="'&nbsp;'"></span>
        <router-link to="create-route">
            <button type="button" class="btn btn-outline-primary"><span class="oi oi-file"></span> Create Route</button>
        </router-link>
        <router-link style="margin-left: 5px" to="add-existing-route">
            <button type="button" class="btn btn-outline-secondary"><span class="oi oi-plus"></span> Add Existing Route</button>
        </router-link>
        <span class="mr-auto"></span><!--Move the other elements to the left-->
        <!--<input class="form-inline form-control mr-sm-2" id="search" type="search" placeholder="Search" aria-label="Search">
        <span class="divider" innerHTML="&nbsp;"></span>-->
        <slot name="logoutButton"></slot>
    </whr-navbar>
    <slot name="errors"></slot>
    <table v-show="loaded" class="table table-hover table-striped">
        <thead>
            <tr>
                <th width="20%">
                    Name
                </th>
                <th width="30%">
                    Token
                </th>
                <th>
                    Destination
                </th>
            </tr>
        </thead>
        <tbody>
        <tr @click="onRouteClick(route.uuid)" :key="route.token" v-for="route in filteredRoutes">
            <td>
                <span>{{ route.name }}</span>
            </td>
            <td>
                <code>{{ route.token }}</code>
            </td>
            <td>
                {{ route.destination }}
            </td>
        </tr>
        </tbody>
    </table>
</div>
</template>

<style scoped>
.divider {
    border-left-style: solid;
    border-left-color: rgba(255, 255, 255, 0.2);
    border-left-width: 1px;
    margin-left: 0px;
    margin-right: 5px;
}

#search {
    width: 200px;
    transition-property: width;
    transition-duration: 0.2s;
}

#search:focus{
    width: 300px;
    
}
</style>

<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import {configServer} from "../config"
import NavBarComponent from "./whr-navbar.vue";
import * as utils from "../utils";

@Component({
    components: {
        "whr-navbar": NavBarComponent
    },
    props: {
        googleToken: String,
        api: Object
    }
})
export default class extends Vue {
    errorText = ""
    filteredRoutes:swaggerAPI.Routes = []
    loaded = false
    googleToken: string;
    readonly authOptions = utils.getAuthOptions(this.googleToken);

    api: swaggerAPI.DefaultApi;

    async mounted(){
        var routes = await this.api.getAllRoutes(this.authOptions);

        this.loaded = true;
        this.filteredRoutes = routes;
        
    }

    onRouteClick(uuid: string){
        this.$router.push(`/routes/${uuid}`)
    }
}
</script>
