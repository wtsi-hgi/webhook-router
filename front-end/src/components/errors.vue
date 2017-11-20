<template>
    <div>
        <div role="alert" class="alert alert-danger" v-for="(error, index) in errors" :key="error.key">
            <strong>Error:</strong> {{error.text}}
            <button type="button" class="close" aria-label="Close" v-if="!error.persist">
                <span @click="closeError(index)" aria-hidden="true" innerHTML="&times;"></span>
            </button>
        </div>
    </div>
</template>
<script lang="ts">
import Vue from "vue";
import Component from 'vue-class-component';

interface WHRError{
    text: string;
    persist: boolean
}

@Component
export default class extends Vue {
    errors = <(WHRError & {key:number})[]>[]
    maxKey = 0

    addErrorText(text: string, persist = false){
        this.errors.push({
            text: text,
            persist: persist,
            key: this.maxKey++
        })
    }

    addError(error: any, persist = false){
        this.addErrorText(error.toString(), persist);
    }

    closeError(errorIndex: number){
        this.errors.splice(errorIndex, 1);
    }
}
</script>
