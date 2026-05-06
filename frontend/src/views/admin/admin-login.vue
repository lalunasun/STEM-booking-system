<template>
  <div id="userLayout">
    <div class="user-layout-header">
      <img class="logo" :src="logoImage" alt="">
      <span>CSAA Manage System</span>
    </div>
    <div class="main-container">
      <div class="main">
        <div class="main_right">
          <h2 class="sys_title">Admin Login</h2>
          <a-form ref="myform" layout="vertical" :model="data.loginForm" :rules="data.rules" :hideRequiredMark="true">
            <a-form-item name="username" label="Account" :colon="false">
              <a-input size="large" placeholder="Enter your Account" v-model:value="data.loginForm.username"
                @pressEnter="handleSubmit">
                <a-icon slot="prefix" type="user" />
              </a-input>
            </a-form-item>
            <a-form-item name="password" label="Password" :colon="false">
              <a-input size="large" type="password" placeholder="Enter your Password" v-model:value="data.loginForm.password"
                @pressEnter="handleSubmit">
                <a-icon slot="prefix" type="lock" />
              </a-input>
            </a-form-item>
            <a-form-item style="padding-top: 24px">
              <a-button class="login-button" type="primary" :loading="loginBtn" size="large" block @click="handleSubmit">
                Login
              </a-button>
            </a-form-item>
          </a-form>
          <div class="error-tip"></div>
        </div>
      </div>

    </div>
    <footer class="footer">
      <div class="copyright">
        <span></span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '/@/store';
import logoImage from '/@/assets/images/k-logo.png';

const router = useRouter();
const userStore = useUserStore();

import { message } from "ant-design-vue";

const myform = ref()

const loginBtn = ref<Boolean>(false)
const checked = ref<Boolean>(false)
const data = reactive({
  loginForm: {
    username: 'admin123',
    password: 'admin123'
  },
  rules: {
    username: [
      { required: true, message: 'Please enter your account', trigger: 'blur' }
    ],
    password: [
      { required: true, message: 'Please enter your password', trigger: 'blur' }
    ]
  }
})

const handleSubmit = () => {
  myform.value?.validate().then(() => {
    handleLogin()
  }).catch(() => {
    message.warn('Cannot be blank')
  })
}

const handleLogin = () => {
  userStore.adminLogin({
    username: data.loginForm.username,
    password: data.loginForm.password
  }).then(res => {
    loginSuccess()
  }).catch(err => {
    message.warn(err.msg || 'Login Failed')
  })
}

const loginSuccess = () => {
  router.push({ path: '/admin' })
  message.success('Login Successful!')
}


</script>

<style lang="less" scoped>
#userLayout {
  position: relative;
  height: 100vh;
  width: 100%;
  height: 100%;
  background-image: url('../images/admin-bg.jpg');
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;

  .user-layout-header {
    height: 80px;
    padding: 0 24px;
    color: fade(#000, 85%);
    font-size: 28px;
    font-weight: bold;
    line-height: 80px;

    .logo {
      width: 36px;
      height: 36px;
      margin-right: 16px;
      margin-top: -4px;
    }
  }

  .main-container {
    // width: 100%;
    // height: calc(100vh - 160px);
    // background-image: url('../images/admin-bg.jpg');
    // background-position: center;
    // background-repeat: no-repeat;
    // background-size: cover;

    .main {
      position: absolute;
      right: 80px;
      top: 50%;
      display: flex;
      transform: translate(0, -50%);
      border-radius: 8px;
      overflow: hidden;
      -webkit-box-shadow: 2px 2px 6px #aaa;
      box-shadow: 2px 2px 6px #aaa;

      .main_right {
        background: #ffffff;
        padding: 24px;
        width: 420px;
        user-select: none;

        .sys_title {
          font-size: 24px;
          color: fade(#000, 85%);
          font-weight: bold;
          user-select: none;
          padding-bottom: 8px;
        }

        :deep(.ant-form-item label) {
          font-weight: bold;
        }

        .flex {
          align-items: center;
          display: flex;
          justify-content: space-between;
        }

        .forget_password {
          cursor: pointer;
        }

        .login-button {
          background: linear-gradient(128deg, #00aaeb, #00c1cd 59%, #0ac2b0 100%);
        }
      }

      .error-tip {
        text-align: center;
      }
    }
  }

  .footer {
    height: 80px;
  }
}
</style>
