<!-- 底部广告和版权 -->

<template>
  <hr>
  <div class="footer-view">
   

    <div class="address">
      <p>
        <!--<span>Copyright (C). create by BHML 2023, All Rights Reserved</span>&nbsp;&nbsp;-->
        <a href="/admin" target="_blank">Access to CSAA Manage System</a>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { listApi } from '/@/api/index/ad'
import { BASE_URL, USER_NAME } from "/@/store/constants";

let msgData = ref([] as any)
const router = useRouter();

onMounted(() => {
  getAdList()
})

let loading = ref(false)
const getAdList = () => {
  loading.value = true
  listApi({}).then(res => {
    msgData.value = res.data
    loading.value = false
  }).catch(err => {
    console.log(err)
    loading.value = false
  })
}

const handleAd = (item) => {
  // 跳转广告页面
  window.open(item.link, '_blank')
}

</script>

<style scoped lang="less">
.flex-view {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
}

.footer-view {
  max-width: 1108px;
  margin: 0 auto;
  padding: 24px 0 20px 54px;

  h1 {
    font-weight: bolder;
    font-family: 楷体;
    font-style: oblique;
    color: orange;
  }

  .addiv img {
    width: 20%;
    height: 200px;
    margin-bottom: 20px;
  }

  .foot-link-box {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    overflow: hidden;
    margin: 60px auto 16px;
    -webkit-box-pack: center;
    -ms-flex-pack: center;
    justify-content: center;

    .foot-link {
      margin: 0 16px;
      color: #2a4f88;
    }

    a {
      background-color: transparent;
      text-decoration: none;
      color: var(--mid-blue);
    }
  }

  .footer-infos {
    height: 16px;
    line-height: 16px;
    font-size: 12px;
    padding-left: 63px;
    color: #aeaeae;
    margin-top: 16px;
    text-align: center;
  }

  .address {
    text-align: center;
    height: 16px;
    line-height: 16px;
    font-size: 12px;
    color: #aeaeae;
    margin-top: 250px;
  }
}
</style>
