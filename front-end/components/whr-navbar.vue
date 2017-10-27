<template>
<nav class="navbar navbar-expand-md navbar-dark bg-dark">
    <img class="sanger-logo" src="https://avatars3.githubusercontent.com/u/2567468?s=200&v=4" />
    <router-link class="navbar-brand" to="home">
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
