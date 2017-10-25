<template>
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
</template>

<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import {configServer} from "../config"

@Component({
    beforeRouteEnter: async function (to, from, next) {
        let api = new swaggerAPI.DefaultApi(fetch, configServer);
        let routes = await api.getAllRoutes();
        next((vue: any) => vue.filteredRoutes = routes);
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
