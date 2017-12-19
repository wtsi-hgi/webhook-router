<template>
    <form novalidate @submit.prevent="postForm">
        <p>
            <label for="route-name">Name:</label>
            <input type="text" required class="form-control" placeholder="Route Name"
                id="route-name" required v-model="formData.name">
            <div class="invalid-feedback">Please fill out this field.</div>
        </p>
        <p>
            <label for="route-destination">Destination:</label>
            <input type="url" class="form-control" placeholder="Route Destination"
                id="route-destination" v-model="formData.destination"
                required pattern="^(https?):\/\/.*">
            <div v-if="destination_error == 'blank'" class="invalid-feedback">Please fill out this field.</div>
            <div v-else-if="destination_error == 'invalid_url'" class="invalid-feedback">Please enter a correct URL.</div>
            <div v-else-if="destination_error == 'no_scheme'" class="invalid-feedback">Please enter a scheme (e.g. http or https)</div>
            <div v-else-if="destination_error == 'invalid_scheme'" class="invalid-feedback">Scheme is not supported (only http and https are supported).</div>
            <div v-else-if="destination_error == 'firewall_validation_fail'" class="invalid-feedback">Resolved IP doesn't pass firewall rules.</div>
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
import { Prop } from 'vue-property-decorator';
import { isEqual, cloneDeep } from "lodash";
import { defaultFormData } from "../utils";

enum DestinationError{
    NO_ERROR,
    BLANK_FIELD,
    NO_SCHEME,
    INVALID_SCHEME,
    INVALID_URL,
    FIREWALL_VALIDATION_FAIL
}

@Component
export default class extends Vue {
    @Prop({default: () => defaultFormData}) initalData: object;

    @Prop() squashed: boolean; // whether the form should have less padding in it (for inline views)

    /**
     * Data structure containing the data that is currently stored on the server
     * , for computing when the form is modified
     */
    formData = {
        ...this.initalData
    };

    async isDestinationCorrect(url: string){
        if(url == ""){
            return DestinationError.BLANK_FIELD;
        }
        else if(/^[a-z]+:/.test(url)){
            return DestinationError.NO_SCHEME;
        }
        else if(!/^(https?):\/\//.test(url)){
            return DestinationError.INVALID_SCHEME;
        }
        else if(!/[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/.exec(url)){
            // ^ from https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
            return DestinationError.INVALID_URL;
        }
        else{
            // query network for validity of url
        }
    }

    postForm(){
        this.$emit("formSubmitted", this.formData);
    }

    get modified () {
        return !isEqual(this.formData, this.initalData)
    }
}
</script>
