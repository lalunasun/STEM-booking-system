<template>
  <a-config-provider :locale="enUS">
    <router-view />
  </a-config-provider>
</template>
<script setup lang="ts">

import enUS from 'ant-design-vue/es/locale/en_US';

</script>

<style>

  #app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  height: 100vh;
}
</style>
