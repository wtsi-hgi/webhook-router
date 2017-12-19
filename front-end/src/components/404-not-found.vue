<template>
<div>
<whr-navbar>
    <span class="divider" v-html="'&nbsp;'"></span>
    <router-link to="/">
        <button type="button" class="btn btn-outline-secondary">
            Home
        </button>
    </router-link>
    <span class="mr-auto"></span>
    <slot name="logoutButton"></slot>
</whr-navbar>
    <br />
    <div class="container-fluid">
        <p>404: Not Found</p>
    </div>
</div>
</template>
<script>
import NavBarComponent from "./whr-navbar.vue";

export default {
    components: {
        "whr-navbar": NavBarComponent
    },
}
</script>

