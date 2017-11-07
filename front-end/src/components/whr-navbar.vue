<template>
<nav class="navbar navbar-expand-md navbar-dark bg-dark">
    <img class="sanger-logo" src="img/logo.png" />
    <router-link class="navbar-brand" to="/">
        Webhook Router
    </router-link>
    <!--Extra bits on the navbar -->
    <slot></slot>
</nav>
</template>

<style>
.sanger-logo{
    width: 30px;
    border-radius: 2px;
    margin-right: 6px;
}

.navbar > * {
    vertical-align: middle;
}
</style>

<script lang="ts">
export default {
  
}
</script>
