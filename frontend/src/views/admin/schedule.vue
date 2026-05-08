<template>
  <a-config-provider :locale="enUS">
    <div class="page-view">
      <div class="schedule-toolbar">
        <div class="schedule-title">
          <h2>Schedule</h2>
          <span>{{ currentRangeLabel }}</span>
        </div>

        <div class="schedule-actions">
          <a-button @click="goPrevious">Previous</a-button>
          <a-button @click="goToday">Today</a-button>
          <a-button @click="goNext">Next</a-button>
          <a-radio-group v-model:value="viewMode" button-style="solid">
            <a-radio-button value="week">Week</a-radio-button>
            <a-radio-button value="month">Month</a-radio-button>
          </a-radio-group>
        </div>
      </div>

      <div v-if="viewMode === 'week'" class="week-board">
        <div v-for="day in weekDays" :key="day.key" class="week-day">
          <div class="week-day-header">
            <strong>{{ day.name }}</strong>
            <span>{{ day.dateLabel }}</span>
          </div>

          <ul v-if="getLessonsByDay(day.dayCode).length" class="events week-events">
            <li v-for="item in getLessonsByDay(day.dayCode)" :key="`${day.key}-${item.id}`">
              <button class="event-button" type="button" @click="toDetailPage(item.thing)">
                <span class="event-name">{{ item.class_name || 'Untitled class' }}</span>
                <span class="event-time">{{ item.time || 'Time TBD' }}</span>
              </button>
            </li>
          </ul>

          <div v-else class="empty-day">No classes</div>
        </div>
      </div>

      <a-calendar
        v-else
        v-model:value="value"
        :mode="calendarMode"
        @panelChange="handlePanelChange"
      >
        <template #headerRender></template>

        <template #dateCellRender="{ current }">
          <ul class="events">
            <li v-for="item in getListData(current)" :key="`${current.format('YYYY-MM-DD')}-${item.id}`">
              <a-badge status="success" :text="getLessonLabel(item)" @click="toDetailPage(item.thing)" />
            </li>
          </ul>
        </template>

      </a-calendar>
    </div>
  </a-config-provider>
</template>

<script lang="ts" setup>
import enUS from 'ant-design-vue/es/locale/en_US';
import dayjs, { Dayjs } from 'dayjs';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { listApi } from '/@/api/admin/lesson';

type ViewMode = 'week' | 'month';

interface LessonItem {
  id: number;
  thing: number;
  class_name?: string;
  day?: string;
  time?: string;
}

const dayCodes = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

const router = useRouter();
const value = ref<Dayjs>(dayjs());
const viewMode = ref<ViewMode>('week');
const lessonData = ref<LessonItem[]>([]);

const calendarMode = computed(() => 'month');

const weekStart = computed(() => value.value.startOf('week'));

const weekDays = computed(() =>
  dayCodes.map((dayCode, index) => {
    const date = weekStart.value.add(index, 'day');
    return {
      key: date.format('YYYY-MM-DD'),
      dayCode,
      name: dayNames[index],
      dateLabel: date.format('MMM D'),
    };
  })
);

const currentRangeLabel = computed(() => {
  if (viewMode.value === 'week') {
    const start = weekStart.value;
    const end = start.add(6, 'day');
    return `${start.format('MMM D, YYYY')} - ${end.format('MMM D, YYYY')}`;
  }

  return value.value.format('MMMM YYYY');
});

onMounted(() => {
  getLessonList();
});

const toDetailPage = (id?: number) => {
  if (!id) {
    return;
  }

  const target = router.resolve({ name: 'lesson', query: { id } });
  window.open(target.href, '_blank');
};

const getLessonList = () => {
  listApi({})
    .then((res) => {
      lessonData.value = res.data || [];
    })
    .catch((err) => {
      console.log(err);
    });
};

const getLessonsByDay = (dayCode?: string) => {
  if (!dayCode) {
    return [];
  }

  return lessonData.value
    .filter((item) => item.day === dayCode)
    .sort((a, b) => (a.time || '').localeCompare(b.time || ''));
};

const getListData = (current: Dayjs) => {
  return getLessonsByDay(dayCodes[current.day()]);
};

const getLessonLabel = (item: LessonItem) => {
  const name = item.class_name || 'Untitled class';
  return item.time ? `${item.time} ${name}` : name;
};

const handlePanelChange = (date: Dayjs) => {
  value.value = date;
  viewMode.value = 'month';
};

const goPrevious = () => {
  const unit = viewMode.value === 'week' ? 'week' : 'month';
  value.value = value.value.subtract(1, unit);
};

const goToday = () => {
  value.value = dayjs();
};

const goNext = () => {
  const unit = viewMode.value === 'week' ? 'week' : 'month';
  value.value = value.value.add(1, unit);
};
</script>

<style scoped>
.page-view {
  min-height: 100%;
  background: #fff;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.schedule-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.schedule-title h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}

.schedule-title span {
  display: block;
  margin-top: 4px;
  color: #667085;
}

.schedule-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.week-board {
  display: grid;
  grid-template-columns: repeat(7, minmax(140px, 1fr));
  border: 1px solid #eaecf0;
  border-radius: 8px;
  overflow: hidden;
}

.week-day {
  min-height: 520px;
  border-right: 1px solid #eaecf0;
  background: #fff;
}

.week-day:last-child {
  border-right: 0;
}

.week-day-header {
  min-height: 72px;
  padding: 14px;
  border-bottom: 1px solid #eaecf0;
  background: #f8fafc;
}

.week-day-header strong {
  display: block;
  color: #101828;
  font-size: 14px;
}

.week-day-header span {
  display: block;
  margin-top: 4px;
  color: #667085;
  font-size: 13px;
}

.events {
  list-style: none;
  margin: 0;
  padding: 0;
}

.week-events {
  padding: 10px;
}

.week-events li + li {
  margin-top: 8px;
}

.event-button {
  width: 100%;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
  background: #f6ffed;
  color: #135200;
  padding: 9px 10px;
  text-align: left;
  cursor: pointer;
}

.event-button:hover {
  border-color: #73d13d;
  background: #efffdf;
}

.event-name,
.event-time {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-name {
  font-weight: 600;
}

.event-time {
  margin-top: 4px;
  font-size: 12px;
  color: #3f6212;
}

.empty-day {
  padding: 16px 14px;
  color: #98a2b3;
  font-size: 13px;
}

.events .ant-badge-status {
  overflow: hidden;
  white-space: nowrap;
  width: 100%;
  text-overflow: ellipsis;
  font-size: 12px;
}

@media (max-width: 1200px) {
  .week-board {
    grid-template-columns: repeat(2, minmax(220px, 1fr));
  }

  .week-day {
    min-height: 260px;
    border-bottom: 1px solid #eaecf0;
  }
}

@media (max-width: 640px) {
  .page-view {
    padding: 16px;
  }

  .week-board {
    grid-template-columns: 1fr;
  }

  .schedule-actions {
    width: 100%;
  }
}
</style>
