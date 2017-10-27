/// <reference path="vue-shims.d.ts" />

import Vue from "vue";
import VueRouter from "vue-router";
import InitialComponent from "./components/initial.vue";


Vue.use(VueRouter);

const vue = new Vue({
    components: {
        "initial": InitialComponent
    },
    template: `<initial/>`,
    el: "#site"
})