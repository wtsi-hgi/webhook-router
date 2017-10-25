/// <reference path="vue-shims.d.ts" />

import Vue from "vue";
import VueRouter from "vue-router";
import DisplayRoutesComponent from "./components/display-routes.vue";
import AddRouteComponent from "./components/add-route.vue";
import ModifyRoute from "./components/modify-route.vue";

Vue.use(VueRouter);

const router = new VueRouter({
    mode: "hash",
    base: __dirname,
    routes: [
        {path: "/", component: DisplayRoutesComponent},
        {path: "/add-route", component: AddRouteComponent},
        {path: "/routes/:uuid", component: ModifyRoute, props: true}
    ]
})

const vue = new Vue({
    router,
    el: "#site",
    template: `<router-view class="view"></router-view>`
})