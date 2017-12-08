<template>
    <form @submit.prevent="postForm">
        <p>
            <label for="route-name">Name:</label>
            <input type="text" required class="form-control" placeholder="Route Name"
                id="route-name" required v-model="formData.name">
        </p>
        <p>
            <label for="route-destination">Destination:</label>
            <input type="url" class="form-control" placeholder="Route Destination"
                id="route-destination" v-model="formData.destination"
                required pattern="^(https?):\/\/.*"
                title="This must be in the format (http|https)://*">
        </p>
        <label for="check-certificates">Don't verify certificates</label>
        <input type="checkbox" id="check-certificates" class="form-control-inline" v-model="formData.no_ssl_verification">
        <br />
        <br v-if="!squashed" />
        <slot name="submitButton" :disableButton="!modified"></slot>
        <slot name="cancelButton"></slot>
    </form>
</template>
<script lang="ts">
import Vue from "vue";
import Component from 'vue-class-component'
import { Prop, Model } from 'vue-property-decorator';
import { isEqual, cloneDeep } from "lodash";
import { defaultFormData } from "../utils";

@Component
export default class extends Vue {
    @Prop({default: defaultFormData}) initalData: object;

    @Prop() squashed: boolean; // whether the form should have less padding in it (for inline views)

    /**
     * Data structure containing the data that is currently stored on the server
     * , for computing when the form is modified
     */
    formData = {
        ...this.initalData
    };

    postForm(){
        this.$emit("formSubmitted", this.formData);

        this.initalData = cloneDeep(this.formData);
    }

    get modified () {
        return !isEqual(this.formData, this.initalData)
    }
}
</script>
