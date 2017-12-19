import Vue from "vue";
import VueRouter from "vue-router";
import InitialComponent from "./components/initial.vue";
import BootstrapVue from 'bootstrap-vue';

import "bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import "open-iconic/font/css/open-iconic-bootstrap.min.css"
import "../index.css";
import "mprogress/build/css/mprogress.min.css";
import "bootstrap-social";
import 'bootstrap-vue/dist/bootstrap-vue.css'

Vue.use(VueRouter);
Vue.use(BootstrapVue);

const vue = new Vue({
    components: {
        "initial": InitialComponent
    },
    template: `<initial/>`,
    el: "#site"
})