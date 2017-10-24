import _Vue from "vue";
var Vue = <typeof _Vue>require("vue");
import swaggerAPI = require("../api");
import Component from 'vue-class-component'
import * as config from "../config";

const uuid = "001b9608-615f-42e8-97c2-e3766cc2465b"

var vue = new Vue({
    el: "#base",
    data: {
        errorText: "",
        name: "",
        initName: "",
        destination: "",
        token: "",
        uuid: "",
        init: false,
        routingServer: config.routingServer
    },
    methods: {
        postForm: async function () {
            let api = new swaggerAPI.DefaultApi(fetch, config.configServer);
            api.patchRoute({
                uuid: uuid,
                newInfo: {
                    name: this.name,
                    destination: this.destination
                }
            }).then(result => {
                console.log(result)
            }).catch(e => {
                this.errorText = "Error: " + e.toString()
            })
        },
        cancelForm: function () {
            location.href = '/'
        },
        deleteRoute: function () {
            let api = new swaggerAPI.DefaultApi(fetch, config.configServer);
            api.deleteRoute({
                uuid: uuid
            })
            location.href = '/'
        },
        regenerateToken: function() {
            let api = new swaggerAPI.DefaultApi(fetch, config.configServer);
            api.regenerateToken({
                uuid: uuid
            }).then(x => {
                this.token = x.token;
            })
        }
    },
    mounted: function () {
        this.api = new swaggerAPI.DefaultApi(fetch, config.configServer);
        this.api.getRoute({
            uuid: uuid
        }).then(route => {
            Object.keys(route).forEach(key => {
                this[key] = route[key];
            })

            this.initName = route.name;

            this.initData = {
                name: route.name,
                destination: route.destination
            }

            this.init = true
        }).catch(e => {
            this.errorText = e.toString()
        })
    },
    computed: {
        modified: function() {
            console.log(this.initData != undefined)
            return this.init && !(this.initData.name == this.name 
                  && this.initData.destination == this.destination)
        }
    }
})
