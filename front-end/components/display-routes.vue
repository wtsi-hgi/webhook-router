<template>
<div>
    <whr-navbar>
        <span class="divider">&nbsp; </span>
        <router-link to="add-route">
            <button type="button" class="btn btn-outline-primary"><span class="oi oi-plus"></span> New Route</button>
        </router-link>
        <span class="mr-auto"></span><!--Move the other elements to the left-->
        <input class="form-inline form-control mr-sm-2" style="width: 200px" type="search" placeholder="Search" aria-label="Search">
    </whr-navbar>
    <table class="table table-hover table-striped">
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

<style>
.divider {
    border-left-style: solid;
    border-left-color: rgba(255, 255, 255, 0.2);
    border-left-width: 1px;
    margin-left: 0px;
    margin-right: 5px;
}
</style>

<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import {configServer} from "../config"
import NavBarComponent from "./whr-navbar.vue";

@Component({
    beforeRouteEnter: async function (to, from, next) {   
        let api = new swaggerAPI.DefaultApi(fetch, configServer);
        let routes = await api.getAllRoutes();
        next((vue: any) => vue.filteredRoutes = routes);
    },
    components: {
        "whr-navbar": NavBarComponent
    }
})
export default class extends Vue {
    errorText = ""
    filteredRoutes:swaggerAPI.Routes = []

    private api = new swaggerAPI.DefaultApi(fetch, configServer);

    watch: {
        // call again the method if the route changes
        '$route': 'created'
    }

    onRouteClick(uuid: string){
        this.$router.push(`/routes/${uuid}`)
    }

    async fetchData() {
        let routes = await this.api.getAllRoutes()
        this.filteredRoutes = routes;
    }
}
</script>
