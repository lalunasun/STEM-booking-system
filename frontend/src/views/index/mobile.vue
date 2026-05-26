<template>
  <div class="mobile-app">
    <header class="mobile-header">
      <button class="brand" @click="scrollHome">
        <span class="brand-mark">M</span>
        <span>
          <b>My Classes</b>
          <small>Learning studio</small>
        </span>
      </button>
      <div v-if="userStore.user_token" class="profile-menu">
        <button class="profile-pill" @click="profileMenuOpen = !profileMenuOpen">
          {{ userStore.user_name || 'Parent' }}
        </button>
        <div v-if="profileMenuOpen" class="profile-dropdown">
          <button @click="goToOrders">Orders</button>
          <button @click="logoutMobile">Log out</button>
        </div>
      </div>
      <button v-else class="profile-pill" @click="router.push({ name: 'login', query: { redirect: '/index/mobile' } })">
        Log in
      </button>
    </header>

    <main class="mobile-main">
      <section class="home-hero">
        <div>
          <span class="hero-kicker">{{ userStore.user_token ? 'Parent home' : 'Mobile portal' }}</span>
          <h1>{{ userStore.user_token ? 'Your child’s classes, first.' : 'Manage classes from your phone.' }}</h1>
          <p>
            {{ userStore.user_token
              ? 'Check current classes, next lesson, payments, and makeup requests in one place.'
              : 'Log in to see your child’s schedule, orders, and reschedule options.' }}
          </p>
        </div>
      </section>

      <template v-if="userStore.user_token">
        <section ref="kidsRef" class="section-head kids-head">
          <div>
            <h2>Student status</h2>
            <p>Start here before booking anything new.</p>
          </div>
          <button class="text-link" @click="showMobileNotice('Kid editing will be added to the mobile app next.')">Edit</button>
        </section>

        <div v-if="childOptions.length > 0" class="child-strip">
          <button
            v-for="child in childOptions"
            :key="child.id"
            :class="{ active: String(selectedChildId) === String(child.id) }"
            @click="selectedChildId = child.id"
          >
            <span>{{ child.name }}</span>
            <small>{{ child.age ? `${child.age} yrs` : 'Age TBD' }}</small>
          </button>
        </div>

        <a-spin :spinning="homeData.loading" style="min-height: 160px;">
          <section class="status-grid">
            <article class="status-card next-card">
              <div class="card-label">Next class</div>
              <template v-if="nextClass">
                <h3>{{ nextClass.title }}</h3>
                <p>{{ nextClass.dateLine }}</p>
                <span>{{ nextClass.room || 'Room TBD' }}</span>
              </template>
              <template v-else>
                <h3>No scheduled class</h3>
                <p>Paid orders will show here after admin schedules them.</p>
              </template>
            </article>

            <article class="status-card">
              <div class="card-label">Current classes</div>
              <div v-if="currentClasses.length > 0" class="mini-list">
                <button v-for="item in currentClasses.slice(0, 3)" :key="item.key" @click="selectMobileClass(item)">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.dateLine }}</span>
                  <span class="term-line">{{ item.termLine }}</span>
                </button>
              </div>
              <p v-else class="muted">No active scheduled classes yet.</p>
            </article>

            <article class="status-card action-card">
              <div class="card-label">Action needed</div>
              <div v-if="actionItems.length > 0" class="action-list">
                <button v-for="item in actionItems.slice(0, 3)" :key="item.key" @click="scrollOrders">
                  <span>{{ item.label }}</span>
                  <b>{{ item.title }}</b>
                </button>
              </div>
              <p v-else class="muted">Nothing waiting right now.</p>
            </article>
          </section>
        </a-spin>
      </template>

      <template v-else>
        <section class="guest-actions">
          <button @click="router.push({ name: 'login', query: { redirect: '/index/mobile' } })">Log in</button>
          <button @click="showMobileNotice('Please log in to use the mobile app. Web portal stays separate.')">Browse classes</button>
        </section>
      </template>

      <section ref="catalogRef" class="section-head catalog-head">
        <div>
          <h2>Book a class</h2>
          <p>Choose a course first, then pick a day and time.</p>
        </div>
        <button class="text-link" @click="scrollTrial">Trial</button>
      </section>

      <div class="category-strip">
        <button
          v-for="item in categoryOptions"
          :key="item.key"
          :class="{ active: String(selectedCategoryKey) === String(item.key) }"
          @click="selectCategory(item.key)"
        >
          {{ item.title }}
        </button>
      </div>

      <a-spin :spinning="pageData.loading" style="min-height: 160px;">
        <section class="course-list">
          <button
            v-for="course in courseGroups"
            :key="course.title"
            class="course-card"
            :class="{ active: selectedCourseTitle === course.title }"
            @click="selectCourse(course)"
          >
            <div class="course-cover">
              <img v-if="course.cover" :src="course.cover" :alt="course.title" />
              <span v-else>{{ course.isTrialPackage ? 'Trial' : course.title }}</span>
            </div>
            <div class="course-copy">
              <h3>{{ course.title }}</h3>
              <p>{{ course.isTrialPackage ? 'Robotics + Coding trial package' : `${course.slots.length} time slots` }}</p>
              <em>{{ course.isTrialPackage ? '$98 / 3 lessons' : 'Tap to view times' }}</em>
            </div>
          </button>
        </section>

        <div v-if="courseGroups.length <= 0 && !pageData.loading" class="empty-state">
          No classes yet.
        </div>

        <section v-if="selectedCourse && !selectedCourse.isTrialPackage" class="time-section">
          <div class="section-head compact">
            <div>
              <h2>{{ selectedCourse.title }}</h2>
              <p>Available class times</p>
            </div>
          </div>

          <div class="day-stack">
            <div v-for="dayGroup in selectedCourseDayGroups" :key="dayGroup.day" class="day-block">
              <h3>{{ dayGroup.dayLabel }}</h3>
              <button
                v-for="slot in dayGroup.slots"
                :key="slot.id"
                class="slot-card"
                :class="{
                  full: slot.display_status === 'Full',
                  closed: slot.display_status === 'Closed',
                }"
                @click="selectSlot(slot)"
              >
                <div>
                  <strong>{{ slot.time_title || 'Time TBD' }}</strong>
                  <span>{{ slot.room_name || 'Room TBD' }}</span>
                </div>
                <div>
                  <b>{{ slot.display_status || 'Open' }}</b>
                  <span v-if="slot.available_seats !== null && slot.available_seats !== undefined">
                    {{ slot.available_seats }} seats left
                  </span>
                  <span v-else>Seat TBD</span>
                </div>
              </button>
            </div>
          </div>
        </section>
      </a-spin>

      <section v-if="selectedSlot" class="mobile-detail-card">
        <button class="close-mini" @click="selectedSlot = null">Close</button>
        <div class="card-label">Class detail</div>
        <h2>{{ selectedSlot.title }}</h2>
        <p>{{ selectedSlot.day || 'Day TBD' }} | {{ selectedSlot.time_title || 'Time TBD' }}</p>
        <p>{{ selectedSlot.room_name || 'Room TBD' }} · {{ selectedSlot.display_status || 'Open' }}</p>
        <button class="primary-action" @click="showMobileNotice('Mobile booking form is next. For now, booking stays in the web portal.')">
          Book this class
        </button>
      </section>

      <section ref="trialRef" class="mobile-detail-card soft-card">
        <div class="card-label">Trial package</div>
        <h2>Try Robotics + Coding</h2>
        <p>$98 / 3 lessons. Pick one Robotics time and one Coding time; Math is reserved for the next phase.</p>
        <button class="primary-action" @click="showMobileNotice('Mobile trial booking is next. The current full trial form is still on the web page.')">
          Start trial request
        </button>
      </section>

      <section ref="ordersRef" class="mobile-detail-card">
        <div class="card-label">Orders</div>
        <h2>My orders</h2>
        <div v-if="selectedOrders.length > 0" class="mobile-order-list">
          <button v-for="order in selectedOrders.slice(0, 5)" :key="order.id" @click="selectedOrder = order">
            <strong>{{ order.title || 'Order' }}</strong>
            <span>{{ getOrderStatusLabel(order.status) }} · $ {{ order.amount || '-' }}</span>
          </button>
        </div>
        <p v-else class="muted">No orders for this child yet.</p>
      </section>

      <section v-if="selectedOrder" class="mobile-detail-card soft-card">
        <button class="close-mini" @click="selectedOrder = null">Close</button>
        <div class="card-label">Order detail</div>
        <h2>{{ selectedOrder.title || 'Order' }}</h2>
        <p>{{ getOrderStatusLabel(selectedOrder.status) }} · Child: {{ selectedOrder.child_name || '-' }}</p>
        <p v-if="!isTrialOrder(selectedOrder)">
          {{ selectedOrder.day || 'Day TBD' }} | {{ selectedOrder.time_title || 'Time TBD' }} | {{ selectedOrder.room_title || 'Room TBD' }}
        </p>
        <div v-else class="mini-list">
          <button v-for="slot in selectedOrder.trial_slots" :key="slot.label">
            <strong>{{ slot.label }} · {{ slot.title }}</strong>
            <span>{{ formatTrialSlot(slot, selectedOrder) }}</span>
          </button>
        </div>
      </section>

      <section ref="rescheduleRef" class="mobile-detail-card">
        <div class="card-label">Reschedule</div>
        <h2>Request a change</h2>
        <p>Select one of the child’s scheduled classes. The mobile request form will keep the 48-hour rule.</p>
        <div v-if="currentClasses.length > 0" class="mobile-order-list">
          <button v-for="item in currentClasses.slice(0, 5)" :key="`res-${item.key}`" @click="selectMobileClass(item)">
            <strong>{{ item.title }}</strong>
            <span>{{ item.dateLine }} · {{ item.room || 'Room TBD' }}</span>
            <span class="term-line">{{ item.termLine }}</span>
          </button>
        </div>
        <p v-else class="muted">No scheduled classes available for reschedule.</p>
      </section>
    </main>

    <nav class="mobile-tabbar">
      <button class="active" @click="scrollHome">Home</button>
      <button @click="scrollCatalog">Book</button>
      <button @click="scrollReschedule">Reschedule</button>
      <button @click="scrollOrders">Orders</button>
      <button @click="scrollKids">Kids</button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { message } from 'ant-design-vue';
import { listApi as listClassificationList } from '/@/api/index/classification';
import { listApi as listThingList } from '/@/api/index/thing';
import { listApi as listChildApi } from '/@/api/index/child';
import { userOrderListApi } from '/@/api/index/order';
import { BASE_URL } from '/@/store/constants';
import { useUserStore } from '/@/store';

const router = useRouter();
const userStore = useUserStore();
const catalogRef = ref(null);
const kidsRef = ref(null);
const ordersRef = ref(null);
const rescheduleRef = ref(null);
const trialRef = ref(null);
const selectedSlot = ref(null);
const selectedOrder = ref(null);
const profileMenuOpen = ref(false);

const dayOrder = ['Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon'];
const dayLabels = {
  Mon: 'Monday',
  Tue: 'Tuesday',
  Wed: 'Wednesday',
  Thu: 'Thursday',
  Fri: 'Friday',
  Sat: 'Saturday',
  Sun: 'Sunday',
};
const shortDayLabels = {
  Mon: 'Mon',
  Tue: 'Tue',
  Wed: 'Wed',
  Thu: 'Thu',
  Fri: 'Fri',
  Sat: 'Sat',
  Sun: 'Sun',
};
const dayIndex = {
  Sun: 0,
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
  Sat: 6,
};

const pageData = reactive({
  loading: false,
  categories: [],
  things: [],
});

const homeData = reactive({
  loading: false,
  children: [],
  orders: [],
});

const selectedCategoryKey = ref('-1');
const selectedCourseTitle = ref('');
const selectedChildId = ref('');
const trialGroupTitle = 'Trial Package';

const categoryOptions = computed(() => [
  { key: '-1', title: 'All' },
  ...pageData.categories,
]);

const childOptions = computed(() => homeData.children || []);
const selectedChild = computed(() => (
  childOptions.value.find((item) => String(item.id) === String(selectedChildId.value))
));

onMounted(() => {
  loadCategories();
  loadClasses({});
  if (userStore.user_token) {
    loadHomeData();
  }
});

watch(
  () => userStore.user_token,
  (token) => {
    if (token) {
      loadHomeData();
    }
  },
);

watch(childOptions, (children) => {
  if (!selectedChildId.value && children.length > 0) {
    selectedChildId.value = children[0].id;
  }
});

const loadCategories = () => {
  listClassificationList().then((res) => {
    pageData.categories = (res.data || []).map((item) => ({
      ...item,
      key: item.id,
    }));
  });
};

const loadHomeData = () => {
  homeData.loading = true;
  Promise.all([
    listChildApi({ parent: userStore.user_id }),
    userOrderListApi({ userId: userStore.user_id, orderStatus: '' }),
  ])
    .then(([childrenRes, ordersRes]) => {
      homeData.children = childrenRes.data || [];
      homeData.orders = ordersRes.data || [];
      if (!selectedChildId.value && homeData.children.length > 0) {
        selectedChildId.value = homeData.children[0].id;
      }
    })
    .catch((err) => {
      console.log(err);
      message.error('Failed to load student status');
    })
    .finally(() => {
      homeData.loading = false;
    });
};

const loadClasses = (params) => {
  pageData.loading = true;
  listThingList(params)
    .then((res) => {
      pageData.things = (res.data || []).map((item) => ({
        ...item,
        cover: item.cover ? BASE_URL + item.cover : '',
      }));
      const groups = buildCourseGroups(pageData.things);
      selectedCourseTitle.value = groups.find((item) => !item.isTrialPackage)?.title || groups[0]?.title || '';
    })
    .catch((err) => {
      console.log(err);
      message.error('Failed to load classes');
    })
    .finally(() => {
      pageData.loading = false;
    });
};

const selectCategory = (key) => {
  selectedCategoryKey.value = key;
  loadClasses(String(key) === '-1' ? {} : { c: key });
};

const shouldShowTrialPackage = () => {
  const selected = categoryOptions.value.find((item) => String(item.key) === String(selectedCategoryKey.value));
  const title = String(selected?.title || 'All').trim().toLowerCase();
  return title === 'all' || title === 'trial';
};

const buildCourseGroups = (items) => {
  const grouped = new Map();
  items.forEach((item) => {
    if (String(item.classification_title || '').trim().toLowerCase() === 'trial') {
      return;
    }
    const title = item.title || 'Untitled';
    const groupKey = title.trim().toLowerCase();
    if (!grouped.has(groupKey)) {
      grouped.set(groupKey, {
        title,
        cover: item.cover,
        slots: [],
      });
    }
    const group = grouped.get(groupKey);
    if (!group.cover && item.cover) {
      group.cover = item.cover;
    }
    group.slots.push(item);
  });

  const groups = Array.from(grouped.values()).sort((a, b) => a.title.localeCompare(b.title));
  if (shouldShowTrialPackage()) {
    groups.push({
      title: trialGroupTitle,
      cover: '',
      slots: [],
      isTrialPackage: true,
    });
  }
  return groups;
};

const courseGroups = computed(() => buildCourseGroups(pageData.things));

const selectedCourse = computed(() => (
  courseGroups.value.find((item) => item.title === selectedCourseTitle.value)
));

const selectedCourseDayGroups = computed(() => {
  if (!selectedCourse.value) {
    return [];
  }
  const grouped = new Map();
  selectedCourse.value.slots.forEach((slot) => {
    const day = slot.day || 'TBD';
    if (!grouped.has(day)) {
      grouped.set(day, []);
    }
    grouped.get(day).push(slot);
  });
  return Array.from(grouped.entries())
    .sort(([dayA], [dayB]) => dayOrder.indexOf(dayA) - dayOrder.indexOf(dayB))
    .map(([day, slots]) => ({
      day,
      dayLabel: dayLabels[day] || day,
      slots: slots.sort((a, b) => String(a.time_title || '').localeCompare(String(b.time_title || ''))),
    }));
});

const selectedOrders = computed(() => {
  if (!selectedChildId.value) {
    return [];
  }
  return (homeData.orders || []).filter((order) => {
    const childId = order.child || order.child_id;
    if (childId) {
      return String(childId) === String(selectedChildId.value);
    }
    return selectedChild.value && order.child_name === selectedChild.value.name;
  });
});

const currentClasses = computed(() => {
  const items = [];
  selectedOrders.value
    .filter((order) => Number(order.status) === 6)
    .forEach((order) => {
      if (isTrialOrder(order)) {
        order.trial_slots
          .filter((slot) => slot.status !== 'not_configured' && slot.class_id)
          .forEach((slot) => {
            items.push(normalizeTrialSlot(order, slot));
          });
        return;
      }
      items.push(normalizeOrderClass(order));
    });
  return items.sort((a, b) => a.sortTime - b.sortTime);
});

const nextClass = computed(() => currentClasses.value[0] || null);

const actionItems = computed(() => {
  const items = [];
  selectedOrders.value.forEach((order) => {
    const status = Number(order.status);
    if (status === 1) {
      items.push({
        key: `pay-${order.id}`,
        label: 'Payment needed',
        title: order.title || 'Order',
      });
    }
    if (status === 2) {
      items.push({
        key: `schedule-${order.id}`,
        label: 'Waiting for schedule',
        title: order.title || 'Order',
      });
    }
  });
  return items;
});

const getOrderStatusLabel = (status) => {
  const value = Number(status);
  if (value === 1) return 'Pending payment';
  if (value === 2) return 'Paid';
  if (value === 6) return 'Scheduled';
  if (value === 7) return 'Canceled';
  if (value === 8) return 'Done';
  return 'Unknown';
};

const isTrialOrder = (item) => {
  return !!(item && item.trial_slots && item.trial_slots.length);
};

const parseDateText = (value) => {
  if (!value) return null;
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
};

const formatDateText = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatOrderDate = (value) => {
  const date = parseDateText(value);
  return date ? formatDateText(date) : '';
};

const formatTermLine = (order) => {
  const termName = order.term_title || 'Term TBD';
  const start = formatOrderDate(order.expect_time);
  const end = formatOrderDate(order.return_time);
  if (start && end) {
    return `${termName}: ${start} to ${end}`;
  }
  return termName;
};

const nextDateForDay = (day, baseValue) => {
  const baseDate = parseDateText(baseValue) || new Date();
  if (!day || dayIndex[day] === undefined) {
    return null;
  }
  const daysAhead = (dayIndex[day] - baseDate.getDay() + 7) % 7;
  const date = new Date(baseDate);
  date.setDate(baseDate.getDate() + daysAhead);
  return date;
};

const normalizeOrderClass = (order) => {
  const date = nextDateForDay(order.day, new Date());
  const time = order.time_title || 'Time TBD';
  return {
    key: `order-${order.id}`,
    order,
    title: order.title || 'Class',
    date,
    sortTime: date ? date.getTime() : Number.MAX_SAFE_INTEGER,
    dateLine: `${date ? formatDateText(date) : shortDayLabels[order.day] || 'Day TBD'} | ${shortDayLabels[order.day] || order.day || 'Day TBD'} | ${time}`,
    termLine: formatTermLine(order),
    room: order.room_title || '',
  };
};

const normalizeTrialSlot = (order, slot) => {
  const date = parseDateText(slot.date) || nextDateForDay(slot.day, order.order_time);
  const time = slot.time || 'Time TBD';
  return {
    key: `trial-${order.id}-${slot.class_id}-${slot.label}`,
    order,
    title: `${slot.title || 'Trial'} (${slot.label})`,
    date,
    sortTime: date ? date.getTime() : Number.MAX_SAFE_INTEGER,
    dateLine: `${date ? formatDateText(date) : shortDayLabels[slot.day] || 'Day TBD'} | ${shortDayLabels[slot.day] || slot.day || 'Day TBD'} | ${time}`,
    termLine: formatTermLine(order),
    room: slot.room || '',
  };
};

const selectCourse = (course) => {
  if (course.isTrialPackage) {
    scrollTrial();
    return;
  }
  selectedCourseTitle.value = course.title;
};

const selectSlot = (slot) => {
  selectedSlot.value = slot;
};

const selectMobileClass = (item) => {
  selectedOrder.value = item.order || null;
  scrollOrders();
};

const formatTrialSlot = (slot, order) => {
  if (slot.status === 'not_configured') {
    return 'Not added yet';
  }
  const parts = [];
  const date = slot.date || '';
  if (date) parts.push(date);
  if (slot.day) parts.push(slot.day);
  if (slot.time) parts.push(slot.time);
  if (slot.room) parts.push(slot.room);
  return parts.length ? parts.join(' | ') : 'Time TBD';
};

const showMobileNotice = (text) => {
  message.info(text);
};

const goToOrders = () => {
  profileMenuOpen.value = false;
  scrollOrders();
};

const logoutMobile = async () => {
  profileMenuOpen.value = false;
  await userStore.logout();
  selectedChildId.value = '';
  selectedSlot.value = null;
  selectedOrder.value = null;
  homeData.children = [];
  homeData.orders = [];
  message.success('Logged out');
  scrollHome();
};

const scrollHome = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const scrollCatalog = () => {
  catalogRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const scrollTrial = () => {
  trialRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const scrollOrders = () => {
  if (!userStore.user_token) {
    router.push({ name: 'login', query: { redirect: '/index/mobile' } });
    return;
  }
  ordersRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const scrollReschedule = () => {
  if (!userStore.user_token) {
    router.push({ name: 'login', query: { redirect: '/index/mobile' } });
    return;
  }
  rescheduleRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const scrollKids = () => {
  if (!userStore.user_token) {
    router.push({ name: 'login', query: { redirect: '/index/mobile' } });
    return;
  }
  kidsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};
</script>

<style scoped lang="less">
.mobile-app {
  min-height: 100vh;
  background: #f6fbff;
  color: #17324d;
  padding-bottom: 94px;
}

.mobile-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(255, 255, 255, .92);
  box-shadow: 0 8px 28px rgba(31, 122, 140, .1);
  backdrop-filter: blur(16px);
}

.brand,
.profile-pill,
.profile-dropdown button,
.text-link {
  border: 0;
  background: transparent;
  cursor: pointer;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #17324d;
  text-align: left;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff8a3d, #ffd166);
  color: #fff;
  font-size: 19px;
  font-weight: 900;
}

.brand b {
  display: block;
  font-size: 19px;
  line-height: 20px;
}

.brand small {
  display: block;
  margin-top: 3px;
  color: #6b7f94;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.profile-pill {
  height: 34px;
  max-width: 104px;
  padding: 0 13px;
  border-radius: 17px;
  background: #1f7a8c;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-menu {
  position: relative;
}

.profile-dropdown {
  position: absolute;
  top: 42px;
  right: 0;
  z-index: 30;
  min-width: 122px;
  padding: 8px;
  border: 1px solid rgba(31, 122, 140, .16);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 16px 34px rgba(23, 50, 77, .16);
}

.profile-dropdown button {
  width: 100%;
  padding: 10px 12px;
  border-radius: 11px;
  color: #17324d;
  font-size: 13px;
  font-weight: 800;
  text-align: left;
}

.profile-dropdown button:hover {
  background: #eef9fb;
}

.mobile-main {
  padding: 14px;
}

.home-hero {
  min-height: 178px;
  display: flex;
  align-items: flex-end;
  padding: 20px 18px;
  border-radius: 26px;
  background:
    radial-gradient(circle at 86% 18%, rgba(255, 138, 61, .34), transparent 28%),
    radial-gradient(circle at 18% 10%, rgba(42, 157, 143, .28), transparent 27%),
    linear-gradient(135deg, #fff3d6 0%, #e8fff6 47%, #e8f4ff 100%);
}

.hero-kicker {
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, .72);
  color: #49677f;
  font-size: 12px;
  font-weight: 800;
}

.home-hero h1 {
  max-width: 330px;
  margin: 13px 0 8px;
  font-size: 29px;
  line-height: 35px;
  font-weight: 900;
  color: #17324d;
}

.home-hero p {
  max-width: 335px;
  margin: 0;
  color: #49677f;
  font-size: 14px;
  line-height: 21px;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin: 22px 0 12px;
}

.section-head.compact {
  margin-top: 26px;
}

.catalog-head {
  scroll-margin-top: 74px;
}

.kids-head {
  scroll-margin-top: 74px;
}

.section-head h2 {
  margin: 0;
  font-size: 22px;
  line-height: 28px;
  font-weight: 900;
  color: #17324d;
}

.section-head p {
  margin: 4px 0 0;
  color: #6b7f94;
  font-size: 13px;
  line-height: 19px;
}

.text-link {
  color: #1f7a8c;
  font-size: 13px;
  font-weight: 900;
}

.child-strip {
  display: flex;
  gap: 18px;
  margin: -2px -14px 14px;
  padding: 0 14px 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.child-strip::-webkit-scrollbar,
.category-strip::-webkit-scrollbar {
  display: none;
}

.child-strip button {
  flex: 0 0 auto;
  min-width: 0;
  padding: 0 0 8px;
  border: 0;
  border-bottom: 3px solid transparent;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.child-strip button.active {
  border-bottom-color: #1f7a8c;
}

.child-strip span,
.child-strip small {
  display: block;
}

.child-strip span {
  color: #17324d;
  font-size: 16px;
  font-weight: 900;
}

.child-strip small {
  margin-top: 4px;
  color: #6b7f94;
  font-size: 12px;
  font-weight: 800;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.status-card {
  min-height: 122px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 12px 34px rgba(31, 122, 140, .07);
}

.next-card {
  border: 0;
  background: linear-gradient(135deg, #1f7a8c, #2a9d8f);
  color: #fff;
}

.card-label {
  color: #6b7f94;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .04em;
  text-transform: uppercase;
}

.next-card .card-label {
  color: rgba(255, 255, 255, .68);
}

.next-card h3 {
  color: #fff;
}

.status-card h3 {
  margin: 10px 0 5px;
  font-size: 22px;
  line-height: 28px;
  font-weight: 900;
}

.status-card p,
.status-card span {
  margin: 0;
  color: #6b7f94;
  font-size: 13px;
  line-height: 20px;
}

.next-card p,
.next-card span {
  color: #fff;
}

.mini-list,
.action-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.mini-list button,
.action-list button {
  display: grid;
  gap: 3px;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-radius: 15px;
  background: #f4fbff;
  text-align: left;
  cursor: pointer;
}

.mini-list strong,
.action-list b {
  color: #17324d;
  font-size: 14px;
  line-height: 18px;
}

.mini-list span,
.action-list span {
  color: #6b7f94;
  font-size: 12px;
  line-height: 17px;
}

.mini-list .term-line,
.mobile-order-list .term-line {
  color: #1f7a8c;
  font-weight: 800;
}

.action-list button {
  background: #fff3e8;
}

.muted {
  margin-top: 12px !important;
  color: #6b7f94;
}

.guest-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 14px;
}

.guest-actions button {
  height: 44px;
  border: 0;
  border-radius: 18px;
  background: #1f7a8c;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
}

.guest-actions button:last-child {
  background: #fff3d6;
  color: #9a5a00;
}

.category-strip {
  display: flex;
  gap: 8px;
  margin: 0 -14px 16px;
  padding: 0 14px 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.category-strip button {
  flex: 0 0 auto;
  height: 34px;
  padding: 0 13px;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: #fff;
  color: #334155;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.category-strip button.active {
  border-color: #1f7a8c;
  background: #1f7a8c;
  color: #fff;
}

.course-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.course-card {
  display: grid;
  grid-template-columns: 104px 1fr;
  gap: 13px;
  min-height: 122px;
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(31, 122, 140, .07);
  text-align: left;
  cursor: pointer;
}

.course-card.active {
  border-color: #1f7a8c;
}

.course-cover {
  height: 102px;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(135deg, #d9f8f2, #fff3d6);
}

.course-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.course-cover span {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1f7a8c;
  font-size: 20px;
  font-weight: 900;
}

.course-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.course-copy h3 {
  margin: 0;
  color: #17324d;
  font-size: 20px;
  line-height: 26px;
  font-weight: 900;
}

.course-copy p,
.course-copy em {
  margin: 4px 0 0;
  color: #6b7f94;
  font-size: 13px;
  line-height: 18px;
  font-style: normal;
}

.course-copy em {
  color: #1f7a8c;
  font-weight: 800;
}

.time-section {
  margin-top: 8px;
}

.day-block h3 {
  position: sticky;
  top: 62px;
  z-index: 4;
  margin: 0 -14px 8px;
  padding: 8px 14px;
  background: rgba(246, 251, 255, .94);
  color: #17324d;
  font-size: 15px;
  line-height: 24px;
  font-weight: 900;
  backdrop-filter: blur(10px);
}

.slot-card {
  width: 100%;
  min-height: 86px;
  margin-bottom: 9px;
  padding: 13px 14px;
  border: 1px solid #b7f0df;
  border-radius: 18px;
  background: #f0fff8;
  display: flex;
  justify-content: space-between;
  text-align: left;
  cursor: pointer;
}

.slot-card.full {
  background: #fff7ed;
  border-color: #fed7aa;
}

.slot-card.closed {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.slot-card div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.slot-card div:last-child {
  min-width: 108px;
  align-items: flex-end;
}

.slot-card strong,
.slot-card b {
  color: #17324d;
  font-size: 15px;
}

.slot-card span {
  color: #49677f;
  font-size: 13px;
}

.mobile-detail-card {
  position: relative;
  scroll-margin-top: 74px;
  margin-top: 18px;
  padding: 17px;
  border: 1px solid #e2e8f0;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 12px 34px rgba(31, 122, 140, .07);
}

.mobile-detail-card.soft-card {
  background: #effdf8;
  border-color: #b7f0df;
}

.mobile-detail-card h2 {
  margin: 9px 0 6px;
  color: #17324d;
  font-size: 21px;
  line-height: 27px;
  font-weight: 900;
}

.mobile-detail-card p {
  margin: 5px 0;
  color: #49677f;
  font-size: 13px;
  line-height: 20px;
}

.primary-action {
  height: 42px;
  margin-top: 13px;
  padding: 0 15px;
  border: 0;
  border-radius: 18px;
  background: #1f7a8c;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.close-mini {
  position: absolute;
  top: 14px;
  right: 14px;
  border: 0;
  background: transparent;
  color: #6b7f94;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.mobile-order-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.mobile-order-list button {
  display: grid;
  gap: 4px;
  width: 100%;
  padding: 11px 12px;
  border: 0;
  border-radius: 15px;
  background: #f4fbff;
  text-align: left;
  cursor: pointer;
}

.mobile-order-list strong {
  color: #17324d;
  font-size: 14px;
  line-height: 18px;
}

.mobile-order-list span {
  color: #6b7f94;
  font-size: 12px;
  line-height: 17px;
}

.empty-state {
  padding: 42px 0;
  color: #6b7f94;
  text-align: center;
  font-size: 15px;
}

.mobile-tabbar {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: 12px;
  z-index: 30;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 5px;
  padding: 8px;
  border-radius: 24px;
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 18px 50px rgba(31, 122, 140, .2);
  backdrop-filter: blur(16px);
}

.mobile-tabbar button {
  height: 42px;
  border: 0;
  border-radius: 18px;
  background: transparent;
  color: #6b7f94;
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
}

.mobile-tabbar button.active {
  background: #1f7a8c;
  color: #fff;
}
</style>
