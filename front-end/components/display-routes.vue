<template>
<div>
    <whr-navbar>
        <span class="divider">&nbsp; </span>
        <router-link to="add-route">
            <button type="button" class="btn btn-outline-primary"><span class="oi oi-plus"></span> New Route</button>
        </router-link>
        <span class="mr-auto"></span><!--Move the other elements to the left-->
        <!--<input class="form-inline form-control mr-sm-2" id="search" type="search" placeholder="Search" aria-label="Search">
        <span class="divider">&nbsp; </span>-->
        <slot name="logoutButton"></slot>
    </whr-navbar>
    <errors ref="errors"></errors>
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
import ErrorsComponent from "./errors.vue";

@Component({
    components: {
        "whr-navbar": NavBarComponent,
        "errors": ErrorsComponent
    },
    props: {
        googleToken: String
    }
})
export default class extends Vue {
    errorText = ""
    filteredRoutes:swaggerAPI.Routes = []
    loaded = false
    googleToken: string;
    readonly authOptions = utils.getAuthOptions(this.googleToken);

    $refs: {
        errors: ErrorsComponent;
    }

    api = new swaggerAPI.DefaultApi(fetch, configServer);

    async mounted(){
        try{
            var routes = await this.api.getAllRoutes(this.authOptions);
        }
        catch(e){
            this.$refs.errors.addError(e, true);
            throw e;
        }

        this.loaded = true;
        this.filteredRoutes = routes;
    }

    onRouteClick(uuid: string){
        this.$router.push(`/routes/${uuid}`)
    }
}
</script>
