import Vue from "vue";
import VueRouter from "vue-router";
import InitialComponent from "./components/initial.vue";

import "bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "open-iconic/font/css/open-iconic-bootstrap.min.css"
import "../index.css";
import "mprogress/build/css/mprogress.min.css"

Vue.use(VueRouter);

const vue = new Vue({
    components: {
        "initial": InitialComponent
    },
    template: `<initial/>`,
    el: "#site"
})