<template>
  <a-layout id="components-layout-demo-custom-trigger">
    <a-layout-header style="background: #fff; padding: 0">
      <div class="header">
        <img class="header-logo" :src="logo">
        <span class="header-title">CSAA Manage System</span>
        <div class="empty"></div>
        <a
          class="guide-link"
          href="/downloads/CSAA_Manage_System_User_Guide.pdf"
          download="CSAA_Manage_System_User_Guide.pdf"
        >
          <download-outlined />
          <span>User Guide</span>
        </a>
        <a class="preview-link" href="/index/portal" target="_blank" rel="noopener noreferrer">Link</a>
        <span>{{ adminRoleLabel }}[{{ userStore.admin_user_name }}]</span>
        <a class="header-quit" @click="handleLogout">Log out</a>
      </div>
    </a-layout-header>
    <a-layout>
      <a-layout-sider v-model:collapsed="collapsed" :collapsed-width="64" collapsible>
        <a-menu style="overflow:auto; overflow-x: hidden;" v-model:selectedKeys="selectedKeys" v-model:openKeys="openKeys" theme="dark" mode="inline" @click="handleClick">
          <a-menu-item key="schedule">
            <schedule-outlined />
            <span>Schedule</span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="weeklyOverview">
            <calendar-outlined />
            <span>Weekly Overview</span>
          </a-menu-item>
          <a-menu-item key="classroom">
            <tablet-outlined />
            <span>Classroom for iPad</span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="campCheckin">
            <calendar-outlined/>
            <span>Camp Sign-in/out</span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="order">
            <dollar-outlined/>
            <span class="menu-label">
              Order
              <span v-if="newOrderCount > 0" class="menu-dot" :title="`${newOrderCount} order(s) waiting for admin action`"></span>
            </span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="classPass">
            <calendar-outlined/>
            <span>Class Pass</span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="courseAdjustment">
            <schedule-outlined/>
            <span>Course Adjustments</span>
          </a-menu-item>
          <a-menu-item v-if="false" key="comment">
            <comment-outlined/>
            <span>Comment(St2)</span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="user">
            <user-outlined/>
            <span>User</span>
          </a-menu-item>
          <a-menu-item key="student">
            <team-outlined/>
            <span>Student</span>
          </a-menu-item>
          <a-menu-item key="userGuide">
            <download-outlined/>
            <span>User Guide</span>
          </a-menu-item>
          <a-menu-item v-if="isAdminRole" key="term">
            <calendar-outlined/>
            <span>Terms</span>
          </a-menu-item>
          <a-sub-menu v-if="isAdminRole" key="setup">
            <template #icon>
              <setting-outlined/>
            </template>
            <template #title>Setup</template>
            <a-menu-item key="time">
              <clock-circle-outlined/>
              <span>Time Slots</span>
            </a-menu-item>
            <a-menu-item key="course">
              <database-outlined/>
              <span>Courses</span>
            </a-menu-item>
            <a-menu-item key="classification">
              <layout-outlined/>
              <span>Categories</span>
            </a-menu-item>
            <a-menu-item key="tag">
              <tag-outlined/>
              <span>Rooms</span>
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
  CalendarOutlined,
  TabletOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue';

import {computed, ref, watch, onMounted, onUnmounted, nextTick} from 'vue';
import {useUserStore} from "/@/store";
import { listApi as listOrderApi } from '/@/api/admin/order';

const userStore = useUserStore();

const selectedKeys = ref<any[]>([])
const openKeys = ref<any[]>(['setup'])
const collapsed = ref<boolean>(false)
const newOrderCount = ref(0)
const ORDER_BADGE_REFRESH_EVENT = 'admin-order-badge-refresh'
const teacherAllowedRoutes = new Set(['schedule', 'classroom', 'lesson', 'student'])
const setupRoutes = new Set(['course', 'thing', 'classification', 'tag', 'time', 'term'])
const isTeacherRole = computed(() => userStore.admin_user_role === '2')
const isAdminRole = computed(() => !isTeacherRole.value)
const adminRoleLabel = computed(() => isTeacherRole.value ? 'Teacher' : 'Administrator')

const syncSidebarForViewport = () => {
  collapsed.value = window.innerWidth <= 768
}

const router = useRouter()
const route = useRoute()

const handleClick = ({item, key, keyPath}) => {
  console.log('点击路由===>', key)
  if (key === 'userGuide') {
    const link = document.createElement('a')
    link.href = '/downloads/CSAA_Manage_System_User_Guide.pdf'
    link.download = 'CSAA_Manage_System_User_Guide.pdf'
    link.click()
    selectedKeys.value = [route.name]
    return
  }
  if (isTeacherRole.value && !teacherAllowedRoutes.has(String(key))) {
    router.push({ name: 'schedule' })
    return
  }
  if (window.innerWidth <= 768) {
    collapsed.value = true
  }
  router.push({
    name: key,
  })
}

const syncOpenKeys = (name) => {
  if (setupRoutes.has(String(name))) {
    openKeys.value = ['setup']
  }
}

const scrollSelectedMenuItemIntoView = async () => {
  await nextTick()
  const selectedItem = document.querySelector('#components-layout-demo-custom-trigger .ant-menu-item-selected')
  selectedItem?.scrollIntoView({block: 'nearest'})
}

onMounted(() => {
  console.log('当前路由===>', route.name)
  syncSidebarForViewport()
  window.addEventListener('resize', syncSidebarForViewport)
  selectedKeys.value = [route.name]
  syncOpenKeys(route.name)
  scrollSelectedMenuItemIntoView()
  loadMenuBadges()
  window.addEventListener(ORDER_BADGE_REFRESH_EVENT, loadMenuBadges)
  window.addEventListener('focus', loadMenuBadges)
})

onUnmounted(() => {
  window.removeEventListener('resize', syncSidebarForViewport)
  window.removeEventListener(ORDER_BADGE_REFRESH_EVENT, loadMenuBadges)
  window.removeEventListener('focus', loadMenuBadges)
})

watch(
  () => route.name,
  (name) => {
    selectedKeys.value = [name]
    syncOpenKeys(name)
    scrollSelectedMenuItemIntoView()
    loadMenuBadges()
  }
)

const loadMenuBadges = () => {
  if (!isAdminRole.value) {
    newOrderCount.value = 0
    return
  }
  listOrderApi({})
    .then((res) => {
      const orders = res.data || []
      // Red dot means: new parent orders waiting for admin payment review.
      // Paid or scheduled orders stay in the order page, but no longer trigger the menu alert.
      newOrderCount.value = orders.filter((order) =>
        Number(order.status) === 1 &&
        Number(order.child) > 0 &&
        Number(order.thing) > 0
      ).length
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

  .guide-link,
  .preview-link {
    display: inline-flex;
    align-items: center;
    height: 32px;
    padding: 0 16px;
    margin-right: 12px;
    color: #111827;
    border: 1px solid #d9d9d9;
    background: #fff;
    line-height: 30px;
  }

  .guide-link {
    gap: 6px;
  }

  .guide-link:hover,
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

@media (max-width: 768px) {
  .header {
    min-width: 0;
    padding-left: 12px;
    padding-right: 12px;

    .header-logo {
      width: 28px;
      height: 28px;
    }

    .header-title {
      margin-left: 8px;
      font-size: 15px;
      white-space: nowrap;
    }

    .guide-link,
    .preview-link {
      display: none;
    }

    > span:not(.header-title) {
      max-width: 92px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 12px;
    }

    .header-quit {
      margin-left: 8px;
      white-space: nowrap;
      font-size: 12px;
    }
  }

  :deep(.ant-layout-content) {
    margin: 8px !important;
  }
}

:deep(.ant-layout-sider) {
  padding: 16px 0 0;
  background-color: #f0f2f5;
}

:deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

:deep(.ant-menu) {
  padding-top: 16px;
  margin-bottom: 48px;
  flex: 1;
  min-height: 0;
  height: auto;
  overflow-y: auto !important;
  overflow-x: hidden;
}

//:deep(.ant-layout-sider-trigger) {
//  background-color: #fff;
//  height: 0px; // 设置0 隐藏
//}
</style>
