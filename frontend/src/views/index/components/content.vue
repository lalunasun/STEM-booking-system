<template>
  <div class="content">
    <aside class="content-left">
      <div class="left-search-item">
        <h4>Category</h4>
        <a-tree
          :tree-data="contentData.cData"
          :selected-keys="contentData.selectedKeys"
          @select="onSelect"
          style="min-height: 220px;"
        />
      </div>
      <div class="left-search-item">
        <h4>Class Room</h4>
        <div class="tag-view tag-flex-view">
          <span
            class="tag"
            :class="{ 'tag-select': contentData.selectTagId === item.id }"
            v-for="item in contentData.tagData"
            :key="item.id"
            @click="clickTag(item.id)"
          >
            {{ item.title }}
          </span>
        </div>
      </div>
    </aside>

    <main class="content-right">
      <section class="booking-header">
        <div>
          <h2>Choose a Class</h2>
          <p>Select a course first, then pick a day and time that works for your child.</p>
        </div>
        <button class="trial-package-button" type="button" @click="openTrialPackage">
          Trial Package
        </button>
      </section>

      <a-spin :spinning="contentData.loading" style="min-height: 200px;">
        <div class="course-grid">
          <button
            v-for="course in courseGroups"
            :key="course.title"
            class="course-card"
            :class="{ 'course-card-active': selectedCourseTitle === course.title }"
            @click="selectCourse(course.title)"
          >
            <div class="course-cover">
              <img :src="course.cover" :alt="course.title" />
            </div>
            <div class="course-info">
              <h3>{{ course.title }}</h3>
              <span>{{ course.slots.length }} time slots</span>
            </div>
          </button>
        </div>

        <div v-if="courseGroups.length <= 0 && !contentData.loading" class="no-data">No Data</div>

        <section v-if="selectedCourse" class="schedule-section">
          <div class="section-title">
            <h3>{{ selectedCourse.title }}</h3>
            <span>Available class times</span>
          </div>

          <div class="day-list">
            <div v-for="dayGroup in selectedCourseDayGroups" :key="dayGroup.day" class="day-block">
              <div class="day-title">{{ dayGroup.dayLabel }}</div>
              <div class="slot-list">
                <button
                  v-for="slot in dayGroup.slots"
                  :key="slot.id"
                  class="slot-card"
                  :class="{
                    'slot-full': slot.display_status === 'Full',
                    'slot-closed': slot.display_status === 'Closed',
                  }"
                  @click="openDetail(slot)"
                >
                  <div class="slot-main">
                    <strong>{{ slot.time_title || 'Time TBD' }}</strong>
                    <span>{{ slot.room_name || 'Room TBD' }}</span>
                    <span class="slot-price">${{ slot.price || 0 }} / class</span>
                  </div>
                  <div class="slot-side">
                    <span class="slot-status">{{ slot.display_status }}</span>
                    <span v-if="slot.available_seats !== null && slot.available_seats !== undefined">
                      {{ slot.available_seats }} seats left
                    </span>
                    <span v-else>Seat TBD</span>
                    <span class="slot-action">{{ slot.display_status === 'Open' ? 'Choose for Child' : 'View Details' }}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </section>
      </a-spin>
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { listApi as listClassificationList } from '/@/api/index/classification';
import { listApi as listTagList } from '/@/api/index/tag';
import { listApi as listThingList } from '/@/api/index/thing';
import { BASE_URL } from '/@/store/constants';

const router = useRouter();

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

const contentData = reactive({
  selectTagId: -1,
  cData: [],
  selectedKeys: [],
  tagData: [],
  loading: false,
  thingData: [],
});

const selectedCourseTitle = ref('');

onMounted(() => {
  initSider();
  getThingList({});
});

const initSider = () => {
  contentData.cData.push({ key: '-1', title: 'All' });
  listClassificationList().then((res) => {
    res.data.forEach((item) => {
      item.key = item.id;
      contentData.cData.push(item);
    });
  });
  listTagList().then((res) => {
    contentData.tagData = res.data;
  });
};

const getSelectedKey = () => {
  return contentData.selectedKeys.length > 0 ? contentData.selectedKeys[0] : -1;
};

const onSelect = (selectedKeys) => {
  contentData.selectedKeys = selectedKeys;
  contentData.selectTagId = -1;
  getThingList({ c: getSelectedKey() });
};

const clickTag = (index) => {
  contentData.selectedKeys = [];
  contentData.selectTagId = index;
  getThingList({ tag: contentData.selectTagId });
};

const getThingList = (params) => {
  contentData.loading = true;
  listThingList(params)
    .then((res) => {
      contentData.loading = false;
      contentData.thingData = res.data.map((item) => ({
        ...item,
        cover: item.cover ? BASE_URL + item.cover : '',
      }));

      const groups = buildCourseGroups(contentData.thingData);
      selectedCourseTitle.value = groups[0]?.title || '';
    })
    .catch((err) => {
      console.log(err);
      contentData.loading = false;
    });
};

const buildCourseGroups = (items) => {
  const grouped = new Map();
  items.forEach((item) => {
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

  return Array.from(grouped.values()).sort((a, b) => a.title.localeCompare(b.title));
};

const courseGroups = computed(() => buildCourseGroups(contentData.thingData));

const selectedCourse = computed(() => {
  return courseGroups.value.find((item) => item.title === selectedCourseTitle.value);
});

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

const selectCourse = (title) => {
  selectedCourseTitle.value = title;
};

const openDetail = (slot) => {
  router.push({ name: 'detail', query: { id: slot.id } });
};

const openTrialPackage = () => {
  router.push({ name: 'confirm', query: { trial: '1' } });
};
</script>

<style scoped lang="less">
.content {
  display: flex;
  flex-direction: row;
  width: 1120px;
  margin: 64px auto;
}

.content-left {
  width: 220px;
  margin-right: 32px;
}

.left-search-item {
  overflow: hidden;
  border-bottom: 1px solid #cedce4;
  margin-top: 24px;
  padding-bottom: 24px;
}

h4 {
  color: #4d4d4d;
  font-weight: 600;
  font-size: 16px;
  line-height: 24px;
  height: 24px;
}

.tag-view {
  flex-wrap: wrap;
  margin-top: 4px;
}

.tag-flex-view {
  display: flex;
}

.tag {
  background: #fff;
  border: 1px solid #a1adc6;
  box-sizing: border-box;
  border-radius: 16px;
  height: 20px;
  line-height: 18px;
  padding: 0 8px;
  margin: 8px 8px 0 0;
  cursor: pointer;
  font-size: 12px;
  color: #152833;
}

.tag:hover,
.tag-select {
  background: #4684e3;
  color: #fff;
  border: 1px solid #4684e3;
}

.content-right {
  flex: 1;
  min-width: 0;
  padding-top: 12px;
}

.booking-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 22px;
  gap: 16px;
}

.booking-header h2 {
  color: #0f172a;
  font-size: 26px;
  line-height: 32px;
  margin: 0;
}

.booking-header p {
  color: #64748b;
  font-size: 14px;
  line-height: 22px;
  margin: 8px 0 0;
}

.trial-package-button {
  border: 1px solid #2563eb;
  background: #2563eb;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  height: 38px;
  padding: 0 16px;
  white-space: nowrap;
}

.trial-package-button:hover {
  background: #1d4ed8;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.course-card {
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  text-align: left;
  transition: border-color .2s, box-shadow .2s, transform .2s;
}

.course-card:hover,
.course-card-active {
  border-color: #3b82f6;
  box-shadow: 0 8px 24px rgba(15, 23, 42, .08);
  transform: translateY(-1px);
}

.course-cover {
  height: 150px;
  background: #f8fafc;
  border-radius: 6px;
  overflow: hidden;
}

.course-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.course-info {
  padding: 12px 2px 2px;
}

.course-info h3 {
  color: #0f172a;
  font-size: 19px;
  line-height: 26px;
  margin: 0;
}

.course-info span {
  color: #64748b;
  font-size: 13px;
  line-height: 20px;
}

.schedule-section {
  margin-top: 34px;
  border-top: 1px solid #e2e8f0;
  padding-top: 24px;
}

.section-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.section-title h3 {
  color: #0f172a;
  font-size: 22px;
  line-height: 28px;
  margin: 0;
}

.section-title span {
  color: #64748b;
  font-size: 13px;
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.day-block {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 18px;
  align-items: start;
}

.day-title {
  color: #334155;
  font-weight: 700;
  font-size: 15px;
  line-height: 42px;
}

.slot-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.slot-card {
  min-height: 74px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  border-radius: 8px;
  padding: 12px 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  width: 100%;
}

.slot-card:hover {
  border-color: #22c55e;
}

.slot-full {
  background: #fff7ed;
  border-color: #fed7aa;
}

.slot-closed {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #64748b;
}

.slot-main,
.slot-side {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.slot-main strong {
  color: #0f172a;
  font-size: 15px;
}

.slot-main span,
.slot-side span {
  color: #475569;
  font-size: 13px;
}

.slot-main .slot-price {
  color: #0f766e;
  font-weight: 600;
}

.slot-side {
  align-items: flex-end;
}

.slot-status {
  font-weight: 700;
  color: #166534 !important;
}

.slot-action {
  margin-top: 4px;
  color: #2563eb !important;
  font-weight: 700;
}

.slot-card:hover .slot-action {
  text-decoration: underline;
}

.slot-full .slot-status {
  color: #c2410c !important;
}

.slot-closed .slot-status {
  color: #64748b !important;
}

.no-data {
  height: 200px;
  line-height: 200px;
  text-align: center;
  width: 100%;
  font-size: 16px;
  color: #152844;
}
</style>
