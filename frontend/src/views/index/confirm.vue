<template>
  <div>
    <Header/>
    <section class="cart-page flex-view">
      <div class="left-flex">
        <div class="title flex-view">
          <h3>Order Details</h3>
        </div>
        <div class="cart-list-view">
          <div v-if="!trialMode" class="list-th flex-view">
            <span class="line-1">Class name</span>
            <span class="line-2">Price</span>

            <!--<span class="line-6">操作</span>-->
          </div>
          <div v-if="!trialMode" class="list">
            <div class="items flex-view">
              <div class="book flex-view">
                <img :src="pageData.cover">
                <h2>{{ pageData.title }}</h2>
                <h2>On {{ pageData.day }}</h2>
              </div>
              <div class="pay">¥{{ pageData.price }}</div>

            </div>
          </div>
          <div v-else class="trial-package-view">
            <h3>Trial Package</h3>
            <p>Includes one Robotics class, one Coding class, and one Math class. Math scheduling is not available yet.</p>
            <div class="trial-select-row">
              <label>Robotics:</label>
              <a-select
                placeholder="Select Robotics time"
                :options="roboticsTrialOptions"
                v-model:value="trialData.robotics"
                style="width: 420px;"
                @change="calculateAmount"
              />
            </div>
            <div class="trial-select-row">
              <label>Coding:</label>
              <a-select
                placeholder="Select Coding time"
                :options="codingTrialOptions"
                v-model:value="trialData.coding"
                style="width: 420px;"
                @change="calculateAmount"
              />
            </div>
            <div class="trial-select-row muted">
              <label>Math:</label>
              <span>No math classes available yet</span>
            </div>
          </div>
        </div>
        <div class="title flex-view">
          <div>
            <label><b>Term:</b><b>&nbsp;&nbsp;&nbsp;</b></label>
              <a-select placeholder="Please select"
                        allowClear
                        :options="termData.term"
                        :field-names="{ label: 'title', value: 'id',}"
                        v-model:value="time_period.time"
                        style="width: 15vw;"
                        @change="calculateAmount"
                        >
              </a-select>
          </div>
          <div>
            <label><b>Child:</b><b>&nbsp;&nbsp;&nbsp;</b></label>
              <a-select placeholder="Please select"
                        allowClear
                        :options="childData.child"
                        :field-names="{ label: 'name', value: 'id',}"
                        v-model:value="pageData.child"
                        style="width: 15vw;"
                        @change="calculateAmount"
                        >
              </a-select>
          </div>

        </div>

      </div>
      <div class="right-flex">
        <div class="title flex-view">
          <h3>Settlement</h3>

        </div>
        <div class="price-view">
          <div class="price-item flex-view">
            <span>Num of classes:</span>
            <div class="price">
              <span class="font-big">{{ pageData.num }}</span>
            </div>

          </div>


          <div class="total-price-view flex-view">
            <span>Total</span>
            <div class="price">
              <span class="font-big">¥{{ pageData.amount }}</span>
            </div>

          </div>
          <div class="btns-view">
            <button class="btn buy" @click="handleBack()">Back</button>
            <button class="btn pay jiesuan" @click="handleJiesuan()">Settle</button>
          </div>
        </div>
      </div>
    </section>

   
  </div>
</template>

<script setup lang="ts">
//import { ref } from 'vue';
import {message} from "ant-design-vue";
import Header from '/@/views/index/components/header.vue'
import Footer from '/@/views/index/components/footer.vue'
import {createApi, createTrialApi} from '/@/api/index/order'
import {listApi as listThingApi} from '/@/api/index/thing'
import {listApi as listTermApi} from '/@/api/index/term'
import {listApi as listChildApi} from '/@/api/index/child'
import {useUserStore} from "/@/store";
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const trialMode = computed(() => route.query.trial === '1')


const pageData = reactive({
  id: undefined,
  title: undefined,
  cover: undefined,
  price: undefined,
  day: undefined,
  num: undefined,
  remark: '',
  count: 1,
  amount: 0,
  receiverName: undefined,
  receiverPhone: undefined,
  receiverAddress: undefined,
  expect_time: undefined,
  return_time: undefined,
  child: undefined
})

const termData = reactive({
  term: [],
  loading: false,
  keyword: ''
})  

const childData = reactive({
  child: [],
  loading: false,
})  

const time_period = reactive({
  time: undefined
})

const trialData = reactive<{ robotics?: number; coding?: number; slots: any[] }>({
  robotics: undefined,
  coding: undefined,
  slots: []
})





const myform = ref()

onMounted(() => {

  pageData.id = route.query.id
  pageData.title = route.query.title
  pageData.cover = route.query.cover
  pageData.price = route.query.price
  pageData.day = route.query.day
  //pageData.amount = pageData.price
  pageData.amount = pageData.price ? Number(pageData.price) : 0
  if (trialMode.value) {
    pageData.title = 'Trial Package'
    pageData.price = 0
    pageData.amount = 0
    pageData.num = 0
    listTrialThingData()
  }
  listTermData()
  listChildData()
})



const listTermData = () => {
termData.loading = true;
      listTermApi({
        keyword: termData.keyword,
      })
        .then((res) => {
          termData.loading = false;
          console.log(res);
          res.data.forEach((item: any, index: any) => {
            item.index = index + 1;
          });
          termData.term = res.data;
        })
        .catch((err) => {
          termData.loading = false;
          console.log(err);
        });

}

const listChildData = () => {
childData.loading = true;
let userId = userStore.user_id
      listChildApi({
        parent: userId
      })
        .then((res) => {
          childData.loading = false;
          console.log(res);
          res.data.forEach((item: any, index: any) => {
            item.index = index + 1;
          });
          childData.child = res.data;
        })
        .catch((err) => {
          childData.loading = false;
          console.log(err);
        });

}


const dayOfWeekMap = {
  "Sun": 0,
  "Mon": 1,
  "Tue": 2,
  "Wed": 3,
  "Thu": 4,
  "Fri": 5,
  "Sat": 6
}

const slotLabel = (item) => {
  const seats = item.available_seats ?? '-'
  return `${item.title} - ${item.day} ${item.time_title || ''} (${item.room_name || 'Room TBD'}, ${seats} seats left)`
}

const isRoboticsSlot = (item) => {
  const text = `${item.classification_title || ''} ${item.title || ''}`.toLowerCase()
  return text.includes('robotic') || text.includes('creator')
}

const isCodingSlot = (item) => {
  const text = `${item.classification_title || ''} ${item.title || ''}`.toLowerCase()
  return text.includes('coding') || text.includes('scratch')
}

const trialSlotOptions = (predicate) => {
  return trialData.slots
    .filter((item) => predicate(item))
    .filter((item) => item.display_status === 'Open')
    .filter((item) => Number(item.available_seats) > 0)
    .map((item) => ({
      label: slotLabel(item),
      value: item.id,
    }))
}

const roboticsTrialOptions = computed(() => trialSlotOptions(isRoboticsSlot))
const codingTrialOptions = computed(() => trialSlotOptions(isCodingSlot))

const getTrialSelectedSlots = () => {
  return [trialData.robotics, trialData.coding]
    .filter(Boolean)
    .map((id) => trialData.slots.find((item) => item.id === id))
    .filter(Boolean)
}

const listTrialThingData = () => {
  listThingApi({}).then((res) => {
    trialData.slots = res.data || []
  }).catch((err) => {
    console.log(err)
    message.error('Failed to load trial class times')
  })
}


const calculateAmount = () => {
  if (trialMode.value) {
    const selectedSlots = getTrialSelectedSlots()
    pageData.num = selectedSlots.length
    pageData.amount = selectedSlots.reduce((sum, item) => sum + Number(item.price || 0), 0)
    return
  }

  let termPrice = 0
  termData.term.forEach((item) => {
      if (time_period.time === item.id) {
        pageData.expect_time = item.expect_time
        pageData.return_time = item.return_time
        termPrice = item.price ? Number(item.price) : undefined
      }
    }
  )
  
  if (pageData.expect_time && pageData.return_time && pageData.price) {
    let startDate = new Date(pageData.expect_time);
    const currentTime = Date.now()
    if (startDate.getTime() < currentTime) {  //报名时超过学期起始，以单价计
      startDate = new Date()
      const endDate = new Date(pageData.return_time);
    
      const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      // 计算订单中包含的星期day数量
      let weekDays = 0;

      
      for (let date = new Date(startDate); date <= endDate; date.setDate(date.getDate() + 1)) {
        if (date.getDay() === dayOfWeekMap[pageData.day]) { // 1 表示星期一
          weekDays++;
        }
      }
      pageData.num = weekDays
      // 更新订单金额，假设价格是每天的价格
      pageData.amount = pageData.price * weekDays;
    } 
    else { //按学期计
      const endDate = new Date(pageData.return_time);
      const targetDay = dayOfWeekMap[pageData.day]
      let weekDays = 0;

      if (targetDay === undefined) {
        pageData.num = 0
        pageData.amount = 0
        return
      }

      for (let date = new Date(startDate); date <= endDate; date.setDate(date.getDate() + 1)) {
        if (date.getDay() === targetDay) {
          weekDays++;
        }
      }

      pageData.num = weekDays
      pageData.amount = termPrice !== undefined ? termPrice : Number(pageData.price) * weekDays
    }
   
  }
};





const handleBack = () => {
  router.back()
  console.log('back...')
}
/*
const handleJiesuan = () => {
  const formData = new FormData()
  let userId = userStore.user_id
  if (!userId) {
    message.warn('请先登录！')
    return
  }
  formData.append('user', userId)
  //formData.append('thing', pageData.id)
  //formData.append('count', pageData.count)
  // 在向formData添加数据之前，先做类型判断和转换
  formData.append('thing', pageData.id ? String(pageData.id) : '') // 将id转换为字符串类型
  formData.append('count', String(pageData.count)) // 将count转换为字符串类型

  formData.append('amount', String(pageData.amount)) // 将amount转换为字符串类型

  if (pageData.remark) {
    formData.append('remark', pageData.remark)
  }
  /*console.log(formData)
  createApi(formData).then(res => {
    message.success('请支付订单')
    router.push({'name': 'pay', query: {'amount': pageData.amount}})
  }).catch(err => {
    message.error(err.msg || '失败')
  })*/

  const handleJiesuan = () => {
    const formData = new FormData()
    let userId = userStore.user_id
    if (!userId) {
      message.warn('请先登录！')
      return
    }

    if (!time_period.time) {
      message.warn('Please select a term')
      return
    }

    if (!pageData.child) {
      message.warn('Please select a child')
      return
    }

    if (trialMode.value) {
      const selectedSlots = getTrialSelectedSlots()
      if (!trialData.robotics || !trialData.coding || selectedSlots.length < 2) {
        message.warn('Please select Robotics and Coding trial times')
        return
      }
      calculateAmount()
      formData.append('term', String(time_period.time))
      formData.append('child', String(pageData.child))
      formData.append('user', userId)
      formData.append('thing_ids', JSON.stringify(selectedSlots.map((item) => item.id)))

      createTrialApi(formData).then(res => {
        if (res.code === 0) {
          message.success('Please pay for the trial orders')
          router.push({'name': 'pay', query: {'amount': pageData.amount}})
        } else {
          message.error(res.msg || 'Failed')
        }
      }).catch(err => {
        console.error(err);
        message.error(err.msg || 'Failed')
      })
      return
    }

    calculateAmount()

    if (!pageData.num || !pageData.amount) {
      message.warn('Unable to calculate this order. Please check the term dates and class day.')
      return
    }

    if (pageData.expect_time) {
      formData.append('expect_time', pageData.expect_time); 
    }
    if (pageData.return_time) {
      formData.append('return_time', pageData.return_time); 
    }
    formData.append('term', String(time_period.time))
    formData.append('child', String(pageData.child))
    formData.append('user', userId)
    formData.append('thing', pageData.id ? String(pageData.id) : '') 
    formData.append('count', '1') 
    formData.append('num', String(pageData.num))
    formData.append('amount', String(pageData.amount)) 
    if (pageData.remark) {
      formData.append('remark', pageData.remark)
    }


    createApi(formData).then(res => {
      if (res.code === 0) {
          message.success('Please pay for the order')
          router.push({'name': 'pay', query: {'amount': pageData.amount}})
      } else {
          const errorMsg = res.msg || 'Failed';
          console.error(errorMsg);
          message.error(errorMsg)
      }
    }).catch(err => {
      console.error(err);
      message.error(err.msg || 'Failed')
    })
  }
/*
  createApi(formData).then(res => {
    if (res.data&&res.data.code === 200) {
        message.success('请支付订单')
        router.push({'name': 'pay', query: {'amount': pageData.amount}})
      } else {
        const errorMsg = res.data && res.data.msg ? res.data.msg : '提交订单失败';
        console.error(errorMsg);
        message.error(res.msg || '提交订单失败')
      }
    }).catch(err => {
      console.error(err); // 打印错误信息
      message.error(err.msg || '提交订单失败')
    })
}
*/



</script>

<style scoped lang="less">

.flex-view {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
}

.cart-page {
  width: 1024px;
  min-height: 50vh;
  margin: 100px auto;
}

.left-flex {
  -webkit-box-flex: 17;
  -ms-flex: 17;
  flex: 17;
  padding-right: 20px;
}

.title {
  -webkit-box-pack: justify;
  -ms-flex-pack: justify;
  justify-content: space-between;
  -webkit-box-align: center;
  -ms-flex-align: center;
  align-items: center;

  h3 {
    color: #152844;
    font-weight: 600;
    font-size: 18px;
    height: 26px;
    line-height: 26px;
    margin: 0;
  }
}

.cart-list-view {
  margin: 4px 0 40px;

  .list-th {
    height: 42px;
    line-height: 42px;
    border-bottom: 1px solid #cedce4;
    color: #152844;
    font-size: 14px;

    .line-1 {
      -webkit-box-flex: 1;
      -ms-flex: 1;
      flex: 1;
      margin-right: 20px;
    }

    .line-2, .pc-style .cart-list-view .list-th .line-3, .pc-style .cart-list-view .list-th .line-4 {
      width: 65px;
      margin-right: 20px;
    }

    .line-5 {
      width: 80px;
      margin-right: 40px;
    }

    .line-6 {
      width: 28px;
    }
  }
}

.trial-package-view {
  border-bottom: 1px solid #cedce4;
  padding: 14px 0 22px;

  h3 {
    color: #152844;
    font-size: 18px;
    line-height: 24px;
    margin: 0 0 8px;
  }

  p {
    color: #5f77a6;
    font-size: 14px;
    line-height: 22px;
    margin: 0 0 16px;
  }
}

.trial-select-row {
  align-items: center;
  display: flex;
  gap: 12px;
  margin-top: 12px;

  label {
    color: #152844;
    font-weight: 700;
    width: 86px;
  }
}

.trial-select-row.muted {
  color: #6f6f6f;
}

.items {
  -webkit-box-align: center;
  -ms-flex-align: center;
  align-items: center;
  margin-top: 20px;

  .book {
    -webkit-box-flex: 1;
    -ms-flex: 1;
    flex: 1;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    margin-right: 20px;
    cursor: pointer;

    img {
      width: 48px;
      margin-right: 16px;
      border-radius: 4px;
    }

    h2 {
      -webkit-box-flex: 1;
      -ms-flex: 1;
      flex: 1;
      font-size: 14px;
      line-height: 22px;
      color: #152844;
    }
  }

  .type {
    width: 65px;
    margin-right: 20px;
    color: #152844;
    font-size: 14px;
  }

  .pay {
    color: #ff8a00;
    font-weight: 600;
    font-size: 16px;
    width: 65px;
    margin-right: 20px;
  }

  .num-box {
    width: 80px;
    margin-right: 43px;
    border-radius: 4px;
    border: 1px solid #cedce4;
    -webkit-box-pack: justify;
    -ms-flex-pack: justify;
    justify-content: space-between;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    height: 32px;
    padding: 0 4px;
  }

  .delete {
    margin-left: 36px;
    width: 24px;
    cursor: pointer;
  }
}

.mb-24 {
  margin-bottom: 24px;
}

.show-txt {
  color: #ff8a00;
  font-size: 14px;
}

.remark {
  width: 100%;
  background: #f6f9fb;
  border: 0;
  border-radius: 4px;
  padding: 6px 12px;
  //color: #152844;
  margin-top: 16px;
  resize: none;
  height: 56px;
  line-height: 22px;
}

.right-flex {
  -webkit-box-flex: 8;
  -ms-flex: 8;
  flex: 8;
  padding-left: 24px;
  border-left: 1px solid #cedce4;
}

.click-txt {
  color: #4684e2;
  font-size: 14px;
  cursor: pointer;
}

.address-view {
  margin: 12px 0 24px;

  .info {
    color: #909090;
    font-size: 14px;

    .info-blue {
      cursor: pointer;
      color: #4684e2;
    }
  }

  .name {
    color: #152844;
    font-weight: 500;
  }

  .tel {
    color: #152844;
    float: right;
  }

  .address {
    color: #152844;
    margin-top: 4px;
  }
}

.price-view {
  overflow: hidden;
  margin-top: 16px;

  .price-item {
    -webkit-box-pack: justify;
    -ms-flex-pack: justify;
    justify-content: space-between;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    margin-bottom: 8px;
    font-size: 14px;

    .item-name {
      color: #152844;
    }

    .price-txt {
      font-weight: 500;
      color: #ff8a00;
    }
  }

  .total-price-view {
    margin-top: 12px;
    border-top: 1px solid #cedce4;
    -webkit-box-pack: justify;
    -ms-flex-pack: justify;
    justify-content: space-between;
    -webkit-box-align: start;
    -ms-flex-align: start;
    align-items: flex-start;
    padding-top: 10px;
    color: #152844;
    font-weight: 500;

    .price {
      color: #ff8a00;
      font-size: 16px;
      height: 36px;
      line-height: 36px;
    }
  }

  .btns-view {
    margin-top: 24px;
    text-align: right;

    .buy {
      background: #fff;
      color: #4684e2;
    }

    .jiesuan {
      cursor: pointer;
      background: #4684e2;
      color: #fff;
    }

    .btn {
      cursor: pointer;
      width: 96px;
      height: 36px;
      line-height: 33px;
      margin-left: 16px;
      text-align: center;
      border-radius: 32px;
      border: 1px solid #4684e2;
      font-size: 16px;
      outline: none;
    }
  }

}

</style>
