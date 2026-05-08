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
        <div class="time-header">Time</div>
        <div v-for="day in weekDays" :key="day.key" class="week-day-header">
          <div>
            <strong>{{ day.name }}</strong>
            <span>{{ day.dateLabel }}</span>
          </div>
        </div>

        <template v-for="slot in timeSlots" :key="slot.hour">
          <div class="time-cell">{{ slot.label }}</div>

          <div v-for="day in weekDays" :key="`${slot.hour}-${day.key}`" class="week-time-cell">
            <button
              v-for="item in getLessonsByDayAndHour(day.dayCode, day.date, slot.hour)"
              :key="`${slot.hour}-${day.key}-${item.id}`"
              class="event-button"
              type="button"
              @click="toDetailPage(item)"
            >
              <span class="event-name">{{ item.class_name || 'Untitled class' }}</span>
              <span v-if="hasStudentNames(item, day.date)" class="student-list">
                <span
                  v-for="student in getNormalStudents(item, day.date)"
                  :key="`normal-${item.id}-${student.name}`"
                  class="student-name"
                  :title="student.term_title"
                >
                  {{ student.name }}
                </span>
                <span
                  v-for="student in getRescheduledStudents(item, day.date)"
                  :key="`rescheduled-${item.id}-${student.name}`"
                  class="student-name rescheduled-student"
                  :title="student.term_title"
                >
                  <span class="rescheduled-star">*</span>{{ student.name }}
                </span>
              </span>
            </button>
          </div>
        </template>
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
              <button class="month-event-button" type="button" @click="toDetailPage(item)">
                <span class="month-event-title">{{ getLessonLabel(item) }}</span>
                <span v-if="hasStudentNames(item, current)" class="month-student-list">
                  <span
                    v-for="student in getNormalStudents(item, current)"
                    :key="`month-normal-${item.id}-${student.name}`"
                    :title="student.term_title"
                  >
                    {{ student.name }}
                  </span>
                  <span
                    v-for="student in getRescheduledStudents(item, current)"
                    :key="`month-rescheduled-${item.id}-${student.name}`"
                    class="rescheduled-student"
                    :title="student.term_title"
                  >
                    <span class="rescheduled-star">*</span>{{ student.name }}
                  </span>
                </span>
              </button>
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
  lesson_id?: number;
  thing: number;
  thing_id?: number;
  class_name?: string;
  day?: string;
  time?: string;
  students?: string[];
  reschedule_students?: string[];
  scheduled_students?: ScheduleStudent[];
}

interface ScheduleStudent {
  order_id: number;
  name: string;
  term_id: number;
  term_title: string;
  expect_time: string;
  return_time: string;
  status: number;
}

const dayCodes = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const timeSlots = Array.from({ length: 11 }, (_, index) => {
  const hour = index + 9;
  return {
    hour,
    label: `${hour}:00-${hour + 1}:00`,
  };
});

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
      date,
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

const toDetailPage = (item: LessonItem) => {
  const thingId = item.thing_id || item.thing;
  const lessonId = item.lesson_id || item.id;

  if (!thingId) {
    return;
  }

  router.push({
    name: 'lesson',
    query: {
      id: thingId,
      lessonId,
    },
  });
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

const isStudentActiveOnDate = (student: ScheduleStudent, date: Dayjs) => {
  const start = dayjs(student.expect_time).startOf('day');
  const end = dayjs(student.return_time).endOf('day');
  return date.isSame(start, 'day') || date.isSame(end, 'day') || (date.isAfter(start) && date.isBefore(end));
};

const getNormalStudents = (item: LessonItem, date: Dayjs) => {
  return (item.scheduled_students || []).filter((student) => isStudentActiveOnDate(student, date));
};

const getRescheduledStudents = (_item: LessonItem, _date: Dayjs) => {
  return [];
};

const hasStudentNames = (item: LessonItem, date?: Dayjs) => {
  if (!date) {
    return (item.scheduled_students || []).length > 0;
  }

  return getNormalStudents(item, date).length > 0 || getRescheduledStudents(item, date).length > 0;
};

const getLessonsByDay = (dayCode?: string, date?: Dayjs) => {
  if (!dayCode) {
    return [];
  }

  return lessonData.value
    .filter((item) => item.day === dayCode)
    .sort((a, b) => (a.time || '').localeCompare(b.time || ''));
};

const getLessonStartHour = (item: LessonItem) => {
  const match = String(item.time || '').match(/^(\d{1,2})/);
  return match ? Number(match[1]) : undefined;
};

const getLessonsByDayAndHour = (dayCode: string, date: Dayjs, hour: number) => {
  return getLessonsByDay(dayCode, date).filter((item) => getLessonStartHour(item) === hour);
};

const getListData = (current: Dayjs) => {
  return getLessonsByDay(dayCodes[current.day()], current);
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
  grid-template-columns: 88px repeat(7, minmax(130px, 1fr));
  border: 1px solid #eaecf0;
  border-radius: 8px;
  overflow: hidden;
}

.time-header,
.week-day-header {
  min-height: 74px;
  padding: 14px;
  border-right: 1px solid #eaecf0;
  border-bottom: 1px solid #eaecf0;
  background: #f8fafc;
}

.time-header {
  color: #667085;
  font-weight: 600;
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

.time-cell {
  min-height: 86px;
  padding: 12px 10px;
  border-right: 1px solid #eaecf0;
  border-bottom: 1px solid #eaecf0;
  background: #fcfcfd;
  color: #667085;
  font-size: 12px;
  font-weight: 600;
}

.week-time-cell {
  min-height: 86px;
  padding: 8px;
  border-right: 1px solid #eaecf0;
  border-bottom: 1px solid #eaecf0;
  background: #fff;
}

.week-day-header:nth-child(8n),
.week-time-cell:nth-child(8n) {
  border-right: 0;
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
  display: block;
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
}

.event-button + .event-button {
  margin-top: 6px;
}

.event-button:hover {
  border-color: #73d13d;
  background: #efffdf;
}

.event-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-name {
  font-weight: 600;
}

.student-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.student-name {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-radius: 4px;
  background: #ffffff;
  color: #344054;
  font-size: 12px;
  line-height: 18px;
  padding: 1px 6px;
}

.rescheduled-student {
  color: #166534;
}

.rescheduled-star {
  color: #16a34a;
  font-weight: 700;
  margin-right: 2px;
}

.empty-day {
  padding: 16px 14px;
  color: #98a2b3;
  font-size: 13px;
}

.month-event-button {
  width: 100%;
  border: 0;
  background: transparent;
  color: #135200;
  cursor: pointer;
  display: block;
  overflow: hidden;
  padding: 0;
  text-align: left;
}

.month-event-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.month-event-title::before {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 4px;
  border-radius: 50%;
  background: #52c41a;
  vertical-align: 1px;
}

.month-student-list {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #667085;
  font-size: 11px;
  padding-left: 10px;
}

.month-student-list span + span {
  margin-left: 4px;
}

@media (max-width: 1200px) {
  .week-board {
    overflow-x: auto;
    grid-template-columns: 88px repeat(7, minmax(150px, 1fr));
  }

  .time-header,
  .time-cell,
  .week-day-header,
  .week-time-cell {
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .page-view {
    padding: 16px;
  }

  .week-board {
    grid-template-columns: 78px repeat(7, minmax(140px, 1fr));
  }

  .schedule-actions {
    width: 100%;
  }
}
</style>
