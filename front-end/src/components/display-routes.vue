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
        <input class="form-inline form-control mr-sm-2" id="search" type="search" placeholder="Search routes" v-model="searchBar" aria-label="Search">
        <span class="divider" innerHTML="&nbsp;"></span>
        <slot name="logoutButton"></slot>
    </whr-navbar>
    <slot name="errors"></slot>
    <div v-show="loaded">
        <table class="table table-hover table-striped">
            <thead>
                <tr>
                    <th width="20%">
                        Name
                    </th>
                    <th width="30%">
                        Token
                    </th>
                    <th width="25%">
                        Destination
                    </th>
                    <th>
                        Statistics
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr style="cursor: pointer" @click="onRouteClick(route.uuid)" :key="route.token" v-for="route in filteredRoutes">
                    <td>
                        <span>{{ route.name }}</span>
                    </td>
                    <td>
                        <code>{{ route.token }}</code>
                    </td>
                    <td>
                        {{ route.destination }}
                    </td>
                    <td>
                        <span>{{ route.stats.successes }}</span>
                        <span class="oi oi-check text-success"></span>
                        <span>{{ route.stats.failures }}</span>
                        <span class="oi oi-x text-danger"></span>
                    </td>
                </tr>
            </tbody>
        </table>
        <p v-if="filteredRoutes.length == 0" class="lead text-muted" style="text-align: center;font-size:18px">
            <template v-if="routes.length == 0">No routes added</template>
            <template v-else>No search results</template>
        </p>
    </div>
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

.routeDivider{
    border-left-style: solid;
    border-left-color: rgba(0, 0, 0, 0.2);
    border-left-width: 1px;
    margin-left: 4px;
}

#search {
    width: 200px;
}
</style>

<script lang="ts">
import Vue from "vue";
import * as swaggerAPI from "../api";
import Component from 'vue-class-component'
import NavBarComponent from "./whr-navbar.vue";
import * as utils from "../utils";
import * as Fuse from "fuse.js";
import { merge } from "lodash";

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
    routes: (swaggerAPI.Route & {stats: swaggerAPI.RouteStatistics})[] = []

    loaded = false;

    googleToken: string;
    searchBar = ""
    
    readonly authOptions = utils.getAuthOptions(this.googleToken);

    api: swaggerAPI.DefaultApi;

    async mounted(){
        let statsError: undefined | string;

        let [routes, stats] = <[swaggerAPI.Routes, swaggerAPI.RoutesStatistics]>await Promise.all([
            await this.api.getAllRoutes(this.authOptions),
            await this.api.getAllRoutesStats(this.authOptions).catch(e => {statsError = e; throw e;})
        ]);

        this.routes = <any>routes.map((route, i) => ({
            ...route,
            stats: stats[i]
        }))

        this.loaded = true;
    }


    get filteredRoutes(){
        if(this.searchBar == ""){
            return this.routes;
        }
        else{
            let fuse = new Fuse(this.routes, {
                keys: ["name", "destination"]
            });

            return fuse.search(this.searchBar);
        }
    }

    onRouteClick(uuid: string){
        this.$router.push(`/routes/${uuid}`)
    }
}
</script>
