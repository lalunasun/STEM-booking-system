<template>
    <div class="content-list">
      <div class="list-title">My Child</div>
      <a-spin :spinning="loading" style="min-height: 200px;">
        <div class="list-content">
          <div class="edit-view">
            <div v-for="child in childData" class="item flex-view">
                <span style="font-weight: bolder;">name:&nbsp;&nbsp;</span>
                 <div class="right-box">
                  <span>{{ child.name }}</span>
                 </div>
            </div>
          </div>
          <div class="edit-view">
            <div class="item flex-view">
              <div class="label">Add Child</div>

            </div>
            <div class="item flex-view">
              <div class="label">Child Name</div>
              <div class="right-box">
                <input type="text" v-model="tData.form.name" placeholder="Enter your child's name" maxlength="20" class="input-dom">
  
              </div>
            </div>
            <div class="item flex-view">
              <div class="label">Child Age</div>
              <div class="right-box">
                <input type="text" v-model="tData.form.age" placeholder="Enter your child's age" maxlength="100"
                  class="input-dom web-input">
              </div>
            </div>
            
          
            <button class="save mg" @click="submit()">Save</button>
          </div>
        </div>
      </a-spin>
    </div>
  </template>
  


<script setup>
import { message } from "ant-design-vue";

import { useUserStore } from "/@/store";
import { listApi, createApi } from '/@/api/index/child'



const userStore = useUserStore();
let childData = ref([])
let loading = ref(false)
let tData = reactive({
  form: {
    name: undefined,
    age: undefined
  }
})

onMounted(() => {
    getChildList()
})

const getChildList = () => {
    let userId = userStore.user_id
    listApi({parent: userId}).then(res => {
        childData.value = res.data

    })
}

const submit = () => {
  let formData = new FormData()
  let userId = userStore.user_id
  formData.append('parent', userId)
  if (tData.form.name) {
    formData.append('name', tData.form.name)
  }
  if (tData.form.age) {
    formData.append('age', tData.form.age)
  }
  createApi(
    formData).then(res => {
    message.success('保存成功')
    tData.form.name = undefined
    tData.form.age = undefined
    getChildList()
  }).catch(err => {
    console.log(err)
  })
}

</script>

<style scoped lang="less">
input,
textarea {
  border-style: none;
  outline: none;
  margin: 0;
  padding: 0;
}

.flex-view {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
}

.content-list {
  -webkit-box-flex: 1;
  -ms-flex: 1;
  flex: 1;

  .list-title {
    color: #152844;
    font-weight: 600;
    font-size: 18px;
    line-height: 48px;
    height: 48px;
    margin-bottom: 4px;
    border-bottom: 1px solid #cedce4;
  }

  .edit-view {
    .item {
      -webkit-box-align: center;
      -ms-flex-align: center;
      align-items: center;
      margin: 24px 0;

      .label {
        width: 100px;
        color: #152844;
        font-weight: 600;
        font-size: 14px;
      }

      .right-box {
        -webkit-box-flex: 1;
        -ms-flex: 1;
        flex: 1;
      }

      .avatar {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        margin-right: 16px;
      }

      .change-tips {
        -webkit-box-align: center;
        -ms-flex-align: center;
        align-items: center;
        -ms-flex-wrap: wrap;
        flex-wrap: wrap;
      }

      label {
        color: #4684e2;
        font-size: 14px;
        line-height: 22px;
        height: 22px;
        cursor: pointer;
        width: 100px;
        display: block;
      }

      .tip {
        color: #6f6f6f;
        font-size: 14px;
        height: 22px;
        line-height: 22px;
        margin: 0;
        width: 100%;
      }

      .right-box {
        -webkit-box-flex: 1;
        -ms-flex: 1;
        flex: 1;
      }

      .input-dom {
        width: 400px;
      }

      .input-dom {
        background: #f8fafb;
        border-radius: 4px;
        height: 40px;
        line-height: 40px;
        font-size: 14px;
        color: #152844;
        padding: 0 12px;
      }

      .tip {
        font-size: 12px;
        line-height: 16px;
        color: #6f6f6f;
        height: 16px;
        margin-top: 4px;
      }

      .intro {
        resize: none;
        background: #f8fafb;
        width: 100%;
        padding: 8px 12px;
        height: 82px;
        line-height: 22px;
        font-size: 14px;
        color: #152844;
      }
    }

    .save {
      background: #4684e2;
      border-radius: 32px;
      width: 96px;
      height: 32px;
      line-height: 32px;
      font-size: 14px;
      color: #fff;
      border: none;
      outline: none;
      cursor: pointer;
    }

    .mg {
      margin-left: 100px;
    }
  }
}
</style>
