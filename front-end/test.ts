import Vue from "vue";
import DisplayRoutesComponent from "./src/components/display-routes.vue";

describe("DisplayRoutesComponent", () => {
    it("is ok", () => {
        let cons = Vue.extend(DisplayRoutesComponent);
        new cons().$mount();
    })
})