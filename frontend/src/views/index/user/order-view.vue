<template>
  <div class="content-list">
    <div class="list-title">My Orders</div>
    <a-tabs default-active-key="1" @change="onTabChange">
      <a-tab-pane key="1" tab="All">
      </a-tab-pane>
      <a-tab-pane key="2" tab="Pending payment">
      </a-tab-pane>
      <a-tab-pane key="3" tab="Paid">
      </a-tab-pane>
      <a-tab-pane key="4" tab="Scheduled">
      </a-tab-pane>
      <a-tab-pane key="5" tab="Canceled">
      </a-tab-pane>
      <a-tab-pane key="6" tab="Done">
      </a-tab-pane>
    </a-tabs>
    <a-spin :spinning="loading" style="min-height: 200px;">
      <div class="list-content">
        <div class="order-item-view" v-for="(item, index) in orderData" :key="index">
          <div class="header flex-view">
            <div class="left">
              <span class="text">Order number</span>
              <span class="num mg-4">#</span>
              <span class="num">{{ item.order_number }}</span>
              <span class="time">{{ item.order_time }}</span>
            </div>
            <div class="right">
              <a-popconfirm v-if="item.status === 1" title="Sure to cancel the order？" ok-text="yes" cancel-text="no"
                @confirm="handleCancel(item)">
                <a-button type="primary" size="small" style="margin-right: 24px;">Cancel</a-button>
              </a-popconfirm>
              <a-popconfirm v-if="item.status === 1" title="Already pay the order?" ok-text="yes" cancel-text="no"
                @confirm="handlePay(item)">
                <a-button type="primary" size="small" style="margin-right: 24px;">Pay</a-button>
              </a-popconfirm>
              

              <span class="text">Order Status</span>
              <span class="state">{{ getOrderStatusLabel(item.status) }}</span>
            </div>
          </div>
          <div class="content flex-view">
            <div class="left-list">
              <div class="list-item flex-view">
                <img :src="item.cover" class="thing-img">
                <div class="detail flex-between flex-view">
                  <div class="flex-between flex-top flex-view">
                    <h2 class="name">{{ item.title }}</h2>
                    <span class="count">x{{ item.num }}</span>
                  </div>
                  
                </div>
              </div>
            </div>
            <div class="right-info">
              <div>
                <label style="font-weight: bolder;">Term</label>
                <span class="count">: {{ item.term_title }}</span>
              </div>
              <p class="title">Notes</p>
              <p class="text">{{ item.remark || 'None' }}
              </p>
              <p><span style="font-weight: bolder;">Child name: {{ item.child_name }}</span></p>
            </div>
          </div>
          <div class="bottom flex-view">
            <div class="left">
              <span class="text">A total of {{ item.num }} lessons</span>
              <span class="open" @click="handleDetail(item.thing)">Class Detail</span>
            </div>
            <div class="right flex-view">


              <span class="text">Total</span>
              <span class="money">¥ {{ item.amount }}</span>
            </div>
          </div>
        </div>
        <template v-if="!orderData || orderData.length <= 0">
          <a-empty style="width: 100%;margin-top: 200px;" />
        </template>
      </div>
    </a-spin>
  </div>
</template>

<script setup>
import { message } from "ant-design-vue";
import { userOrderListApi } from '/@/api/index/order'
import { cancelUserOrderApi, payUserOrderApi } from '/@/api/index/order'
import { BASE_URL } from "/@/store/constants";
import { useUserStore } from "/@/store";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const loading = ref(false)
const orderData = ref([])
const orderStatus = ref('')

onMounted(() => {
  getOrderList()
})

const onTabChange = (key) => {
  console.log(key)
  if (key === '1') {
    orderStatus.value = ''
  }
  if (key === '2') {
    orderStatus.value = '1'
  }
  if (key === '3') {
    orderStatus.value = '2'
  }
  if (key === '4') {
    orderStatus.value = '6'
  }
  if (key === '5') {
    orderStatus.value = '7'
  }
  if (key === '6') {
    orderStatus.value = '8'
  }
  getOrderList()
}

const getOrderStatusLabel = (status) => {
  if (status === 1) {
    return 'Pending payment'
  }
  if (status === 2) {
    return 'Paid'
  }
  if (status === 6) {
    return 'Scheduled'
  }
  if (status === 7) {
    return 'Canceled'
  }
  if (status === 8) {
    return 'Done'
  }
  return 'Unknown'
}
const getOrderList = () => {
  loading.value = true
  let userId = userStore.user_id
  userOrderListApi({ userId: userId, orderStatus: orderStatus.value }).then(res => {
    res.data.forEach((item, index) => {
      if (item.cover) {
        item.cover = BASE_URL + item.cover
      }
    })
    orderData.value = res.data
    console.log(orderData.value)
    loading.value = false
  }).catch(err => {
    console.log(err)
    loading.value = false
  })
}
const handleDetail = (thingId) => {
  // 跳转新页面
  let text = router.resolve({ name: 'detail', query: { id: thingId } })
  window.open(text.href, '_blank')
}

// 取消订单
const handleCancel = (item) => {
  cancelUserOrderApi({
    id: item.id
  }).then(res => {
    message.success('取消成功')
    getOrderList()
  }).catch(err => {
    message.error(err.msg || '取消失败')
  })
}

// 支付订单
const handlePay = (item) => {
  payUserOrderApi({
    id: item.id
  }).then(res => {
    message.success('支付成功')
    getOrderList()
  }).catch(err => {
    message.error(err.msg || '支付失败')
  })
}

</script>
<style scoped lang="less">
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
    line-height: 24px;
    height: 24px;
    margin-bottom: 4px;
  }
}

.order-item-view {
  background: #f7f9fb;
  border-radius: 4px;
  padding: 16px;
  margin-top: 12px;

  .header {
    border-bottom: 1px solid #cedce4;
    padding-bottom: 12px;
    -webkit-box-pack: justify;
    -ms-flex-pack: justify;
    justify-content: space-between;
    font-size: 14px;

    .text {
      color: #6f6f6f;
    }

    .mg-4 {
      margin-left: 4px;
    }

    .num {
      font-weight: 500;
      color: #152844;
    }

    .num {
      font-weight: 500;
      color: #152844;
    }

    .time {
      margin-left: 16px;
      color: #a1adc5;
    }

    .state {
      color: #ff7b31;
      font-weight: 600;
      margin-left: 10px;
    }
  }

  .content {
    padding: 12px 0;
    overflow: hidden;

    .left-list {
      overflow: hidden;
      height: 132px;
      -webkit-box-flex: 2;
      -ms-flex: 2;
      flex: 2;
      padding-right: 16px;

      .list-item {
        height: 60px;
        margin-bottom: 12px;
        overflow: hidden;
        cursor: pointer;
      }

      .thing-img {
        width: 48px;
        height: 100%;
        margin-right: 12px;
      }

      .detail {
        -webkit-box-flex: 1;
        -ms-flex: 1;
        flex: 1;
        -webkit-box-orient: vertical;
        -webkit-box-direction: normal;
        -ms-flex-direction: column;
        flex-direction: column;
      }

      .flex-between {
        -webkit-box-pack: justify;
        -ms-flex-pack: justify;
        justify-content: space-between;
      }

      .flex-between {
        -webkit-box-pack: justify;
        -ms-flex-pack: justify;
        justify-content: space-between;
      }

      .flex-top {
        -webkit-box-align: start;
        -ms-flex-align: start;
        align-items: flex-start;
      }

      .name {
        color: #152844;
        font-weight: 600;
        font-size: 14px;
        line-height: 18px;
      }

      .count {
        color: #484848;
        font-size: 12px;
      }

      .flex-between {
        -webkit-box-pack: justify;
        -ms-flex-pack: justify;
        justify-content: space-between;
      }

      .flex-center {
        -webkit-box-align: center;
        -ms-flex-align: center;
        align-items: center;
      }

      .type {
        color: #6f6f6f;
        font-size: 12px;
      }

      .price {
        color: #ff7b31;
        font-weight: 600;
        font-size: 14px;
      }
    }

    .right-info {
      -webkit-box-flex: 1;
      -ms-flex: 1;
      flex: 1;
      border-left: 1px solid #cedce4;
      padding-left: 12px;
      line-height: 22px;
      font-size: 14px;

      .title {
        color: #6f6f6f;
      }

      .name {
        color: #152844;
      }

      .text {
        color: #484848;
      }

      .mg {
        margin-bottom: 4px;
      }
    }
  }

  .bottom {
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    border-top: 1px solid #cedce4;
    -webkit-box-pack: justify;
    -ms-flex-pack: justify;
    justify-content: space-between;
    font-size: 14px;
    padding-top: 14px;

    .text {
      color: #6f6f6f;
    }

    .open {
      color: #4684e2;
      margin-left: 8px;
      cursor: pointer;
    }

    .right {
      -webkit-box-align: center;
      -ms-flex-align: center;
      align-items: center;
    }

    .text {
      color: #6f6f6f;
    }

    .num {
      color: #152844;
      margin: 0 40px 0 8px;
    }

    .money {
      font-weight: 600;
      font-size: 18px;
      color: #ff7b31;
      margin-left: 8px;
    }
  }

}

.order-item-view:first-child {
  margin-top: 16px;
}
</style>
