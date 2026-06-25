<template>
  <a-layout id="components-layout-demo-custom-trigger">
    <a-layout-header style="background: #fff; padding: 0">
      <div class="header">
        <img class="header-logo" :src="logo">
        <span class="header-title">CSAA Manage System</span>
        <div class="empty"></div>
        <a class="preview-link" href="/index/portal" target="_blank" rel="noopener noreferrer">Link</a>
        <span>Administrator[{{ userStore.admin_user_name }}]</span>
        <a class="header-quit" @click="handleLogout">Log out</a>
      </div>
    </a-layout-header>
    <a-layout>
      <a-layout-sider v-model="collapsed" collapsible >
        <a-menu style="overflow:auto; overflow-x: hidden;" v-model:selectedKeys="selectedKeys" theme="dark" mode="inline" @click="handleClick">
          <a-menu-item key="schedule">
            <schedule-outlined />
            <span>Schedule</span>
          </a-menu-item>
          <a-menu-item key="order">
            <dollar-outlined/>
            <span class="menu-label">
              Order
              <span v-if="newOrderCount > 0" class="menu-dot" :title="`${newOrderCount} paid order(s) waiting for scheduling`"></span>
            </span>
          </a-menu-item>
          <a-menu-item key="courseAdjustment">
            <schedule-outlined/>
            <span>Course Adjustments</span>
          </a-menu-item>
          <a-menu-item v-if="false" key="comment">
            <comment-outlined/>
            <span>Comment(St2)</span>
          </a-menu-item>
          <a-menu-item key="user">
            <user-outlined/>
            <span>User</span>
          </a-menu-item>
          <a-menu-item key="student">
            <team-outlined/>
            <span>Student</span>
          </a-menu-item>
          <a-sub-menu key="setup">
            <template #icon>
              <setting-outlined/>
            </template>
            <template #title>Setup</template>
            <a-menu-item key="thing">
              <database-outlined/>
              <span>Classes</span>
            </a-menu-item>
            <a-menu-item key="classification">
              <layout-outlined/>
              <span>Categories</span>
            </a-menu-item>
            <a-menu-item key="tag">
              <tag-outlined/>
              <span>Rooms</span>
            </a-menu-item>
            <a-menu-item key="time">
              <clock-circle-outlined/>
              <span>Time Slots</span>
            </a-menu-item>
            <a-menu-item key="term">
              <calendar-outlined/>
              <span>Terms</span>
            </a-menu-item>
          </a-sub-menu>
          <a-sub-menu v-if="false">
            <template #icon>
              <folder-outlined/>
            </template>
           
            <template #title>Log(St2/3)</template>
            <a-menu-item key="loginLog">
              <appstore-outlined/>
              <span>登录日志</span>
            </a-menu-item>
            <a-menu-item key="opLog">
              <appstore-outlined/>
              <span>操作日志</span>
            </a-menu-item>
            <a-menu-item key="errorLog">
              <appstore-outlined/>
              <span>错误日志</span>
            </a-menu-item>
          </a-sub-menu>
          <a-menu-item v-if="false" key="overview">
            <home-outlined/>
            <span>Analysis(St2/3)</span>
          </a-menu-item>
         <!-- <a-menu-item key="sysInfo">
            <info-circle-outlined/>
            <span>系统信息</span>
          </a-menu-item>-->
        </a-menu>
      </a-layout-sider>
      <a-layout-content :style="{ margin: '16px 16px', minHeight: '200px' }">
        <router-view/>
      </a-layout-content>
    </a-layout>
  </a-layout>

</template>
<script setup lang="ts">
import {useRouter, useRoute} from 'vue-router'
import logo from '/@/assets/images/k-logo.png'

import {
  ScheduleOutlined,
  HomeOutlined,
  AppstoreOutlined,
  FolderOutlined,
  UserOutlined,
  TeamOutlined,
  CommentOutlined,
  InfoCircleOutlined,
  TagOutlined,
  PieChartOutlined,
  DollarOutlined,
  LayoutOutlined,
  DatabaseOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  CalendarOutlined
} from '@ant-design/icons-vue';

import {ref, watch, onUnmounted} from 'vue';
import {useUserStore} from "/@/store";
import { listApi as listOrderApi } from '/@/api/admin/order';

const userStore = useUserStore();

const selectedKeys = ref<any[]>([])
const collapsed = ref<boolean>(false)
const newOrderCount = ref(0)
const ORDER_BADGE_REFRESH_EVENT = 'admin-order-badge-refresh'

const router = useRouter()
const route = useRoute()

const handleClick = ({item, key, keyPath}) => {
  console.log('点击路由===>', key)
  router.push({
    name: key,
  })
}

onMounted(() => {
  console.log('当前路由===>', route.name)
  selectedKeys.value = [route.name]
  loadMenuBadges()
  window.addEventListener(ORDER_BADGE_REFRESH_EVENT, loadMenuBadges)
  window.addEventListener('focus', loadMenuBadges)
})

onUnmounted(() => {
  window.removeEventListener(ORDER_BADGE_REFRESH_EVENT, loadMenuBadges)
  window.removeEventListener('focus', loadMenuBadges)
})

watch(
  () => route.name,
  (name) => {
    selectedKeys.value = [name]
    loadMenuBadges()
  }
)

const loadMenuBadges = () => {
  listOrderApi({})
    .then((res) => {
      const orders = res.data || []
      // Red dot means: paid orders waiting for admin scheduling only.
      // Once an order is scheduled, its status becomes 6 and the dot disappears.
      newOrderCount.value = orders.filter((order) => Number(order.status) === 2).length
    })
    .catch((err) => {
      console.log(err)
    })
}


const handleLogout = () => {
  userStore.adminLogout().then(res => {
    router.push({name: 'adminLogin'})
  })
}

</script>
<style scoped lang="less">

// header样式
.header {
  display: flex;
  flex-direction: row;
  align-items: center; // 垂直居中
  padding-left: 24px;
  padding-right: 24px;

  .header-logo {
    width: 32px;
    height: 32px;
    cursor: pointer;
  }

  .header-title {
    margin-left: 16px;
    font-size: 20px;
    font-weight: bold;
    text-align: center;
  }

  .empty {
    flex: 1;
  }

  .preview-link {
    display: inline-flex;
    align-items: center;
    height: 32px;
    padding: 0 16px;
    margin-right: 24px;
    color: #111827;
    border: 1px solid #d9d9d9;
    background: #fff;
    line-height: 30px;
  }

.preview-link:hover {
    color: #1890ff;
    border-color: #1890ff;
  }

  .header-quit {
    margin-left: 12px;
  }
}

.menu-label {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.menu-dot {
  position: absolute;
  top: 1px;
  right: -10px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f5222d;
  box-shadow: 0 0 0 2px rgba(245, 34, 45, 0.18);
}


#components-layout-demo-custom-trigger {
  height: 100%;
}

#components-layout-demo-custom-trigger .trigger {
  font-size: 18px;
  line-height: 64px;
  padding: 0 24px;
  cursor: pointer;
  transition: color 0.3s;
}

#components-layout-demo-custom-trigger .trigger:hover {
  color: #1890ff;
}


:deep(.ant-layout-content) {
  overflow-x: hidden;
}

:deep(.ant-layout-sider) {
  padding: 16px 0;
  background-color: #f0f2f5;
}

:deep(.ant-menu) {
  padding-top: 16px;
  height: 100%;
}

//:deep(.ant-layout-sider-trigger) {
//  background-color: #fff;
//  height: 0px; // 设置0 隐藏
//}
</style>
