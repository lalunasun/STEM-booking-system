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
      <a-tab-pane key="7" tab="Class Pass">
      </a-tab-pane>
    </a-tabs>
    <a-spin :spinning="loading" style="min-height: 200px;">
      <div class="list-content">
        <div v-if="showOrders" class="order-item-view" v-for="item in orderData" :key="item.id">
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
              <span v-if="item.status === 1" class="payment-note">Awaiting admin confirmation</span>
              

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
                    <div>
                      <h2 class="name">{{ item.title }}</h2>
                      <div class="student-line">
                        <span class="student-label">Student</span>
                        <strong>{{ item.child_name || 'Not assigned' }}</strong>
                        <span v-if="item.child" class="student-id">ID {{ item.child }}</span>
                      </div>
                      <p v-if="!isTrialOrder(item)" class="class-time">
                        {{ item.day || 'Day TBD' }} <span v-if="item.time_title">| {{ item.time_title }}</span>
                        <span v-if="item.room_title"> | {{ item.room_title }}</span>
                      </p>
                      <div v-else class="trial-slot-lines">
                        <p v-for="slot in item.trial_slots" :key="slot.label">
                          <span class="trial-label">{{ slot.label }}</span>
                          <span class="trial-course">{{ slot.title }}</span>
                          <span class="trial-meta">{{ formatTrialSlot(slot, item) }}</span>
                        </p>
                      </div>
                    </div>
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
            </div>
          </div>
          <div class="bottom flex-view">
            <div class="left">
              <span class="text">A total of {{ item.num }} lessons</span>
              <span v-if="isTrialOrder(item)" class="open" @click="openTrialDetail(item)">Trial Detail</span>
              <span v-else class="open" @click="handleDetail(item.thing)">Class Detail</span>
              <span v-if="[2, 6].includes(Number(item.status))" class="open danger-action" @click="openCancelClass(item)">Request Schedule Change</span>
            </div>
            <div class="right flex-view">


              <span class="text">Total</span>
              <span class="money">$ {{ item.amount }}</span>
            </div>
          </div>
        </div>
        <div
          v-if="showClassPasses"
          v-for="item in classPassData"
          :key="`class-pass-${item.id}`"
          class="order-item-view pass-card-view"
        >
          <div class="header flex-view">
            <div class="left">
              <span class="text">Pass Card</span>
              <span class="num mg-4">#CP{{ item.id }}</span>
              <span class="time">{{ item.created_time }}</span>
            </div>
            <div class="right">
              <span class="text">Status</span>
              <span class="state">{{ item.status }}</span>
            </div>
          </div>
          <div class="content flex-view">
            <div class="left-list">
              <div class="list-item flex-view">
                <div class="pass-card-icon">CP</div>
                <div class="detail flex-between flex-view">
                  <div>
                    <h2 class="name">{{ item.title || 'Class Pass' }}</h2>
                    <div class="student-line">
                      <span class="student-label">Student</span>
                      <strong>{{ item.child_name || 'Not assigned' }}</strong>
                      <span v-if="item.child" class="student-id">ID {{ item.child }}</span>
                    </div>
                    <p class="class-time">
                      Valid {{ item.valid_from || '-' }} to {{ item.valid_until || '-' }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div class="right-info">
              <div>
                <label style="font-weight: bolder;">Sessions</label>
                <span class="count">: {{ item.remaining_sessions }} / {{ item.total_sessions }}</span>
              </div>
              <p class="title">Notes</p>
              <p class="text">{{ item.note || 'None' }}</p>
            </div>
          </div>
          <div class="bottom flex-view">
            <div class="left">
              <span class="text">Used {{ item.used_sessions || 0 }} sessions</span>
              <span
                v-if="item.status === 'active' && Number(item.remaining_sessions || 0) > 0"
                class="open"
                @click="openClassPassRequest(item)"
              >
                Request a time
              </span>
            </div>
            <div class="right flex-view">
              <span class="text">Type</span>
              <span class="money pass-card-money">Pass</span>
            </div>
          </div>
        </div>
        <template v-if="isEmpty">
          <a-empty style="width: 100%;margin-top: 200px;" />
        </template>
      </div>
    </a-spin>
    <a-modal
      v-model:visible="cancelModal.visible"
      title="Schedule Change Request"
      ok-text="Submit"
      cancel-text="Close"
      :confirm-loading="cancelModal.submitting"
      @ok="submitCancelClass"
    >
      <div class="cancel-form">
        <p class="hint">Requests must be submitted at least 48 hours before class. For special cases, please call or email admin.</p>
        <template v-if="isTrialOrder(cancelModal.order)">
          <label>Trial class</label>
          <select v-model="cancelModal.trialClassId" class="date-input">
            <option value="">Please select a trial class</option>
            <option
              v-for="slot in cancelTrialSlots"
              :key="slot.label"
              :value="slot.class_id"
            >
              {{ slot.label }} - {{ slot.title }} - {{ formatTrialSlot(slot, cancelModal.order) }}
            </option>
          </select>
        </template>
        <template v-else>
          <label>Class date</label>
          <input
            v-model="cancelModal.lessonDate"
            class="date-input"
            type="date"
            :min="cancelDateLimits.min"
            :max="cancelDateLimits.max"
            @change="validateCancelDate"
          />
          <p class="date-guidance">
            This class meets on {{ cancelModal.order?.day || 'its scheduled weekday' }}.
            Select one of the highlighted dates:
          </p>
          <div v-if="availableCancelDates.length" class="available-date-list">
            <button
              v-for="date in availableCancelDates"
              :key="date.value"
              class="available-date"
              :class="{ selected: cancelModal.lessonDate === date.value }"
              type="button"
              @click="selectCancelDate(date.value)"
            >
              <span>{{ date.weekday }}</span>
              <strong>{{ date.label }}</strong>
            </button>
          </div>
          <p v-else class="no-date-hint">No eligible class dates are available for this term.</p>
        </template>
        <label>Message to admin</label>
        <textarea v-model="cancelModal.parentNote" class="note-input" rows="4" placeholder="Optional note"></textarea>
      </div>
    </a-modal>
    <a-modal
      v-model:visible="trialDetailModal.visible"
      title="Trial Package Detail"
      :footer="null"
      width="680px"
    >
      <div v-if="trialDetailModal.order" class="trial-detail-modal">
        <div class="trial-detail-summary">
          <span>Child: <b>{{ trialDetailModal.order.child_name || '-' }}</b></span>
          <span>Lessons: <b>{{ trialDetailModal.order.num }}</b></span>
          <span>Total: <b>$ {{ trialDetailModal.order.amount }}</b></span>
        </div>
        <div
          v-for="slot in trialDetailModal.order.trial_slots"
          :key="slot.label"
          class="trial-detail-row"
        >
          <div class="trial-detail-label">{{ slot.label }}</div>
          <div class="trial-detail-main">
            <div class="trial-detail-title">{{ slot.title }}</div>
            <div class="trial-detail-meta">{{ formatTrialSlot(slot, trialDetailModal.order) }}</div>
          </div>
        </div>
      </div>
    </a-modal>
    <a-modal
      v-model:visible="classPassModal.visible"
      title="Request a class pass time"
      ok-text="Submit"
      cancel-text="Close"
      :confirm-loading="classPassModal.submitting"
      @ok="submitClassPassRequest"
    >
      <div class="cancel-form">
        <p class="hint">
          Admin will review your request before it appears on the schedule.
        </p>
        <label>Pass card</label>
        <div class="pass-request-summary">
          <strong>{{ classPassModal.pass?.title || 'Class Pass' }}</strong>
          <span>
            {{ classPassModal.pass?.child_name || 'Student' }} ·
            {{ classPassModal.pass?.remaining_sessions || 0 }} sessions left
          </span>
        </div>

        <label>Class time</label>
        <select v-model="classPassModal.requestedClassId" class="date-input">
          <option value="">Please select a class</option>
          <option
            v-for="course in classPassCourseOptions"
            :key="course.id"
            :value="course.id"
          >
            {{ course.title }} - {{ course.day || 'Day TBD' }} - {{ course.time_title || 'Time TBD' }} - {{ course.room_title || 'Room TBD' }}
          </option>
        </select>

        <label>Requested date</label>
        <input
          v-model="classPassModal.requestedDate"
          class="date-input"
          type="date"
          :min="todayValue"
        />

        <label>Message to admin</label>
        <textarea v-model="classPassModal.parentNote" class="note-input" rows="4" placeholder="Optional note"></textarea>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { message } from "ant-design-vue";
import { userOrderListApi } from '/@/api/index/order'
import { cancelUserOrderApi } from '/@/api/index/order'
import { createCancelRequestApi } from '/@/api/index/course-adjustment'
import { bookingCreateApi, passListApi } from '/@/api/index/class-pass'
import { listApi as listThingList } from '/@/api/index/thing'
import { BASE_URL } from "/@/store/constants";
import { useUserStore } from "/@/store";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const loading = ref(false)
const orderData = ref([])
const classPassData = ref([])
const courseData = ref([])
const orderStatus = ref('')
const cancelModal = reactive({
  visible: false,
  order: null,
  lessonDate: '',
  trialClassId: '',
  parentNote: '',
  submitting: false,
})
const trialDetailModal = reactive({
  visible: false,
  order: null,
})
const classPassModal = reactive({
  visible: false,
  pass: null,
  requestedClassId: '',
  requestedDate: '',
  parentNote: '',
  submitting: false,
})

onMounted(() => {
  getOrderList()
  getCourseList()
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
  if (key === '7') {
    orderStatus.value = 'classPass'
  }
  getOrderList()
}

const showOrders = computed(() => orderStatus.value !== 'classPass')
const showClassPasses = computed(() => orderStatus.value === '' || orderStatus.value === 'classPass')
const isEmpty = computed(() => (
  (!showOrders.value || !orderData.value || orderData.value.length <= 0)
  && (!showClassPasses.value || !classPassData.value || classPassData.value.length <= 0)
))

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
const isTrialOrder = (item) => {
  return !!(item && item.trial_slots && item.trial_slots.length)
}

const dayIndex = {
  Sun: 0,
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
  Sat: 6,
}

const parseDateText = (value) => {
  if (!value) return null
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return null
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
}

const formatDateText = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const todayValue = computed(() => formatDateText(new Date()))

const dateAtStartOfDay = (value) => {
  const date = parseDateText(value)
  if (!date) return null
  date.setHours(0, 0, 0, 0)
  return date
}

const cancelDateLimits = computed(() => {
  const order = cancelModal.order
  return {
    min: order ? String(order.expect_time || '').slice(0, 10) : '',
    max: order ? String(order.return_time || '').slice(0, 10) : '',
  }
})

const isEligibleCancelDate = (value) => {
  const order = cancelModal.order
  const date = dateAtStartOfDay(value)
  if (!order || !date || dayIndex[order.day] === undefined) return false

  const start = dateAtStartOfDay(order.expect_time)
  const end = dateAtStartOfDay(order.return_time)
  if ((start && date < start) || (end && date > end)) return false
  if (date.getDay() !== dayIndex[order.day]) return false

  const timeMatch = String(order.time_title || '').match(/^(\d{1,2}):(\d{2})/)
  const lessonStart = new Date(date)
  lessonStart.setHours(
    timeMatch ? Number(timeMatch[1]) : 0,
    timeMatch ? Number(timeMatch[2]) : 0,
    0,
    0,
  )
  return lessonStart.getTime() - Date.now() >= 48 * 60 * 60 * 1000
}

const availableCancelDates = computed(() => {
  const order = cancelModal.order
  if (!order || isTrialOrder(order) || dayIndex[order.day] === undefined) return []

  const start = dateAtStartOfDay(order.expect_time)
  const end = dateAtStartOfDay(order.return_time)
  if (!start || !end) return []

  const first = new Date(Math.max(start.getTime(), Date.now()))
  first.setHours(0, 0, 0, 0)
  const daysAhead = (dayIndex[order.day] - first.getDay() + 7) % 7
  first.setDate(first.getDate() + daysAhead)

  const dates = []
  for (let date = new Date(first); date <= end && dates.length < 12; date.setDate(date.getDate() + 7)) {
    const value = formatDateText(date)
    if (!isEligibleCancelDate(value)) continue
    dates.push({
      value,
      weekday: date.toLocaleDateString('en-CA', { weekday: 'short' }),
      label: date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' }),
    })
  }
  return dates
})

const validateCancelDate = () => {
  if (!cancelModal.lessonDate || isEligibleCancelDate(cancelModal.lessonDate)) return true

  const selected = cancelModal.lessonDate
  cancelModal.lessonDate = ''
  message.warning(
    `${selected} has no ${cancelModal.order?.title || 'selected'} class. ` +
    `Please choose a highlighted ${cancelModal.order?.day || ''} date.`
  )
  return false
}

const selectCancelDate = (value) => {
  cancelModal.lessonDate = value
}

const getTrialSlotDate = (slot, order) => {
  if (slot.date) return slot.date
  if (!slot.day || dayIndex[slot.day] === undefined) return ''

  const baseDate = parseDateText(order && order.order_time)
  if (!baseDate) return ''

  const daysAhead = (dayIndex[slot.day] - baseDate.getDay() + 7) % 7
  const date = new Date(baseDate)
  date.setDate(baseDate.getDate() + daysAhead)
  return formatDateText(date)
}

const formatTrialSlot = (slot, order) => {
  if (slot.status === 'not_configured') {
    return 'Not added yet'
  }
  const parts = []
  const slotDate = getTrialSlotDate(slot, order)
  if (slotDate) parts.push(slotDate)
  if (slot.day) parts.push(slot.day)
  if (slot.time) parts.push(slot.time)
  if (slot.room) parts.push(slot.room)
  return parts.length ? parts.join(' | ') : 'Time TBD'
}

const cancelTrialSlots = computed(() => {
  if (!cancelModal.order || !cancelModal.order.trial_slots) {
    return []
  }
  return cancelModal.order.trial_slots.filter((slot) => slot.status !== 'not_configured' && slot.class_id)
})

const classPassCourseOptions = computed(() => (
  (courseData.value || [])
    .filter((item) => String(item.classification_title || '').trim().toLowerCase() !== 'trial')
    .sort((a, b) => {
      const titleCompare = String(a.title || '').localeCompare(String(b.title || ''))
      if (titleCompare !== 0) return titleCompare
      return String(a.time_title || '').localeCompare(String(b.time_title || ''))
    })
))

const getCourseList = () => {
  listThingList({}).then((res) => {
    courseData.value = res.data || []
  }).catch((err) => {
    console.log(err)
  })
}

const getOrderList = () => {
  loading.value = true
  let userId = userStore.user_id
  const orderRequest = showOrders.value
    ? userOrderListApi({ userId: userId, orderStatus: orderStatus.value })
    : Promise.resolve({ data: [] })
  const passRequest = showClassPasses.value
    ? passListApi({})
    : Promise.resolve({ data: [] })
  Promise.all([orderRequest, passRequest]).then(([orderRes, passRes]) => {
    const rows = orderRes.data || []
    rows.forEach((item, index) => {
      if (item.cover) {
        item.cover = BASE_URL + item.cover
      }
    })
    orderData.value = rows
    classPassData.value = passRes.data || []
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

const openTrialDetail = (item) => {
  trialDetailModal.order = item
  trialDetailModal.visible = true
}

const openClassPassRequest = (item) => {
  classPassModal.pass = item
  classPassModal.requestedClassId = classPassCourseOptions.value[0]?.id || ''
  classPassModal.requestedDate = ''
  classPassModal.parentNote = ''
  classPassModal.visible = true
}

const submitClassPassRequest = () => {
  if (classPassModal.submitting) {
    return
  }
  if (!classPassModal.pass || !classPassModal.requestedClassId || !classPassModal.requestedDate) {
    message.error('Please select a class and requested date')
    return
  }
  classPassModal.submitting = true
  bookingCreateApi({
    class_pass_id: classPassModal.pass.id,
    requested_class_id: classPassModal.requestedClassId,
    requested_date: classPassModal.requestedDate,
    parent_note: classPassModal.parentNote,
  }).then((res) => {
    if (res.code !== 0) {
      message.error(res.msg || 'Submit failed')
      return
    }
    message.success(res.msg || 'Class pass request submitted')
    classPassModal.visible = false
    getOrderList()
  }).catch((err) => {
    message.error(err.msg || 'Submit failed')
  }).finally(() => {
    classPassModal.submitting = false
  })
}

const openCancelClass = (item) => {
  cancelModal.order = item
  cancelModal.lessonDate = ''
  cancelModal.trialClassId = ''
  if (isTrialOrder(item)) {
    const firstSlot = (item.trial_slots || []).find((slot) => slot.status !== 'not_configured' && slot.class_id)
    cancelModal.trialClassId = firstSlot ? String(firstSlot.class_id) : ''
  }
  cancelModal.parentNote = ''
  cancelModal.visible = true
}

const submitCancelClass = () => {
  if (cancelModal.submitting) {
    return
  }
  if (!cancelModal.order) {
    message.error('Please select an order')
    return
  }
  if (isTrialOrder(cancelModal.order) && !cancelModal.trialClassId) {
    message.error('Please select the trial class')
    return
  }
  if (!isTrialOrder(cancelModal.order) && !cancelModal.lessonDate) {
    message.error('Please select the class date')
    return
  }
  if (!isTrialOrder(cancelModal.order) && !validateCancelDate()) {
    return
  }
  cancelModal.submitting = true
  createCancelRequestApi({
    order_id: cancelModal.order.id,
    user_id: userStore.user_id,
    lesson_date: isTrialOrder(cancelModal.order) ? '' : cancelModal.lessonDate,
    trial_class_id: isTrialOrder(cancelModal.order) ? cancelModal.trialClassId : '',
    parent_note: cancelModal.parentNote,
  }).then(res => {
    if (res.code !== 0) {
      message.error(res.msg || 'Submit failed')
      return
    }
    message.success(res.msg || 'Schedule change request submitted')
    cancelModal.visible = false
  }).catch(err => {
    message.error(err.msg || 'Submit failed')
  }).finally(() => {
    cancelModal.submitting = false
  })
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

    .payment-note {
      color: #667085;
      font-size: 13px;
      margin-right: 24px;
    }
  }

  .content {
    padding: 12px 0;
    overflow: visible;

    .left-list {
      min-height: 132px;
      -webkit-box-flex: 2;
      -ms-flex: 2;
      flex: 2;
      padding-right: 16px;

      .list-item {
        min-height: 60px;
        margin-bottom: 12px;
        cursor: pointer;
      }

      .thing-img {
        width: 48px;
        height: 60px;
        margin-right: 12px;
        object-fit: cover;
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
        margin: 0 0 6px;
      }

      .class-time {
        color: #5f77a6;
        font-size: 13px;
        line-height: 18px;
        margin: 0;
      }

      .student-line {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        margin: 0 0 7px;
        color: #152844;
        font-size: 12px;
        line-height: 18px;
      }

      .student-label {
        padding: 2px 7px;
        border-radius: 3px;
        background: #e7f0ff;
        color: #3568b8;
        font-weight: 600;
      }

      .student-id {
        color: #718096;
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

    .danger-action {
      color: #d9363e;
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

.trial-slot-lines {
  margin-top: 4px;
}

.trial-slot-lines p {
  display: grid;
  grid-template-columns: 70px minmax(90px, 1fr) minmax(180px, 1.5fr);
  gap: 8px;
  align-items: center;
  color: #475569;
  font-size: 13px;
  line-height: 18px;
  margin: 3px 0;
}

.trial-label {
  color: #315c9e;
  font-weight: 600;
}

.trial-course {
  color: #152844;
  font-weight: 600;
}

.trial-meta {
  color: #5f77a6;
}

.trial-detail-summary {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  color: #475569;
  margin-bottom: 16px;
}

.trial-detail-row {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid #e5edf3;
}

.trial-detail-label {
  width: 84px;
  color: #315c9e;
  font-weight: 600;
}

.trial-detail-title {
  color: #152844;
  font-weight: 600;
  margin-bottom: 4px;
}

.trial-detail-meta {
  color: #5f77a6;
}

.cancel-form {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .hint {
    color: #5f77a6;
    line-height: 20px;
    margin: 0 0 8px;
  }

  label {
    color: #152844;
    font-weight: 600;
  }

  .date-input,
  .note-input {
    border: 1px solid #d9d9d9;
    border-radius: 2px;
    padding: 8px;
  }

  .date-guidance {
    color: #5f77a6;
    line-height: 20px;
    margin: 4px 0 0;
  }

  .available-date-list {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 4px;
  }

  .available-date {
    border: 1px solid #91caff;
    border-radius: 4px;
    background: #e6f4ff;
    color: #0958d9;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 7px 5px;
    text-align: center;

    span {
      font-size: 11px;
    }

    strong {
      font-size: 13px;
    }

    &:hover,
    &.selected {
      border-color: #1677ff;
      background: #1677ff;
      color: #fff;
    }
  }

  .no-date-hint {
    color: #b42318;
    margin: 4px 0;
  }
}

.pass-card-view {
  border-left: 4px solid #1f7a8c;
}

.pass-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 6px;
  background: #e7f7f6;
  color: #1f7a8c;
  font-weight: 800;
}

.pass-card-money {
  color: #1f7a8c !important;
}

@media (max-width: 640px) {
  .cancel-form .available-date-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
