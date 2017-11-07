<template>
<div>
<whr-navbar>
    <span class="divider" innerHTML="&nbsp;"></span>
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
        <p>Error: Invalid URL</p>
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

