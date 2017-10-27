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
        {path: "/", component: DisplayRoutesComponent, name: "home"},
        {path: "/add-route", component: AddRouteComponent, name: "add-route"},
        {path: "/routes/:uuid", component: ModifyRoute, props: true, name: "modify-route"}
    ]
})

const vue = new Vue({
    router,
    el: "#site"
})