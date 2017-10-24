import _Vue from "vue";
var Vue = <typeof _Vue>require("vue");
import swaggerAPI = require("../api");

const configServerLocation = "http://127.0.0.1:8081";

var vue = new Vue({
    el: "#base",
    data: {
        errorText: "",
        name: "",
        destination: ""
    },
    methods: {
        postForm: async function () {
            let api = new swaggerAPI.DefaultApi(fetch, configServerLocation);
            api.addRoute({
                newRoute: {
                    destination: this.destination,
                    name: this.name
                },
        
            }).then(result => {
                console.log(result)
            }).catch(e => {
                this.errorText = "Error: " + e.toString()
            })
        },
        cancelForm: function () {
            console.log("hello")
            location.href = '/'
        }
    }
})