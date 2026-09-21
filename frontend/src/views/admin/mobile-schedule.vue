<template>
  <div class="mobile-schedule-page">
    <header class="mobile-schedule-header">
      <div>
        <p>Mobile Schedule</p>
        <h1>{{ selectedDate.format('dddd, MMM D, YYYY') }}</h1>
      </div>
      <a-button size="small" :loading="loading" @click="loadSchedule">Refresh</a-button>
    </header>

    <div class="date-bar">
      <a-button size="large" @click="shiftDate(-1)">Previous</a-button>
      <a-button size="large" type="primary" ghost @click="goToday">Today</a-button>
      <a-button size="large" @click="shiftDate(1)">Next</a-button>
      <a-date-picker
        v-model:value="selectedDate"
        size="large"
        :allow-clear="false"
        @change="loadSchedule"
      />
    </div>

    <div class="legend">
      <span><i class="dot regular"></i>Regular</span>
      <span><i class="dot makeup"></i>Makeup</span>
      <span><i class="dot canceled"></i>Canceled</span>
      <span><i class="dot trial"></i>Trial</span>
      <span><i class="dot class-pass"></i>Pass</span>
    </div>

    <a-spin :spinning="loading">
      <div v-if="roomPages.length" class="room-tabs">
        <button
          v-for="room in roomPages"
          :key="`tab-${room.key}`"
          type="button"
          :class="{ active: activeRoomKey === room.key }"
          :style="roomStyle(room.roomId)"
          @click="scrollToRoom(room.key)"
        >
          {{ room.roomName }}
        </button>
      </div>

      <div
        v-if="roomPages.length"
        ref="roomPager"
        class="room-pager"
        @scroll.passive="syncActiveRoom"
      >
        <section
          v-for="room in roomPages"
          :key="room.key"
          class="room-page"
          :data-room-key="room.key"
          :style="roomStyle(room.roomId)"
        >
          <header class="room-head">
            <div>
              <h2>{{ room.roomName }}</h2>
              <p>{{ room.lessonCount }} classes · {{ room.studentCount }} students</p>
            </div>
          </header>

          <div class="time-list">
            <section
              v-for="group in room.timeGroups"
              :key="`${room.key}-${group.time}`"
              class="time-group"
            >
              <h3>{{ group.time }}</h3>
              <div class="lesson-list">
                <article
                  v-for="lessonRow in group.lessons"
                  :key="lessonRow.key"
                  class="lesson-card"
                >
                  <div class="lesson-head">
                    <strong>{{ lessonRow.lesson.class_name || 'Untitled class' }}</strong>
                    <span>{{ lessonRow.students.length }}/{{ lessonRow.capacity }}</span>
                  </div>

                  <div v-if="lessonRow.students.length" class="student-list">
                    <div
                      v-for="student in lessonRow.students"
                      :key="`${lessonRow.key}-${student.type}-${student.studentId}-${student.id || student.name}`"
                      class="student-line"
                      :class="student.type"
                    >
                      <div class="student-name-row">
                        <span class="student-name">{{ student.name }}</span>
                        <span v-if="student.badge" class="student-badge">{{ student.badge }}</span>
                      </div>
                      <p v-if="student.title" class="student-title">{{ student.title }}</p>
                      <p v-if="getStudentNote(lessonRow.lesson, student)" class="student-note">
                        Note: {{ getStudentNote(lessonRow.lesson, student) }}
                      </p>
                    </div>
                  </div>
                  <p v-else class="empty-students">No students</p>
                </article>
              </div>
            </section>
          </div>
        </section>
      </div>

      <a-empty v-else :description="`No classes scheduled on ${selectedDate.format('YYYY-MM-DD')}`">
        <a-button type="primary" ghost @click="loadDemoDate">Load demo date</a-button>
      </a-empty>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import dayjs, { Dayjs } from 'dayjs';
import { message } from 'ant-design-vue';
import { listApi as listLessonsApi } from '/@/api/admin/lesson';
import { listApi as listNotesApi } from '/@/api/admin/student-lesson-note';
import { listApi as listRoomsApi } from '/@/api/admin/tag';
import { compareRoomNames } from '/@/utils/room-order';

interface ScheduleStudent {
  order_id?: number;
  student_id: number;
  name: string;
  term_title?: string;
  expect_time?: string;
  return_time?: string;
}

interface AdjustmentStudent {
  adjustment_id?: number;
  student_id: number;
  name: string;
  date?: string;
  term_title?: string;
}

interface TrialStudent {
  trial_request_id?: number;
  student_id: number;
  name: string;
  date?: string;
}

interface ClassPassStudent {
  booking_id?: number;
  student_id: number;
  name: string;
  date?: string;
  pass_title?: string;
}

interface RoomItem {
  id: number;
  title: string;
  seat?: number | string;
}

interface LessonItem {
  id: number;
  lesson_id?: number;
  class_name?: string;
  time?: string;
  room_id?: number;
  room_name?: string;
  room_capacity?: number | string;
  scheduled_students?: ScheduleStudent[];
  canceled_students?: AdjustmentStudent[];
  scheduled_reschedule_students?: AdjustmentStudent[];
  scheduled_trial_students?: TrialStudent[];
  scheduled_class_pass_students?: ClassPassStudent[];
  moved_students?: AdjustmentStudent[];
  sick_leave_students?: AdjustmentStudent[];
}

interface DisplayStudent {
  id?: number;
  studentId: number;
  name: string;
  type: 'regular' | 'makeup' | 'canceled' | 'trial' | 'class-pass' | 'moved' | 'sick';
  badge?: string;
  title?: string;
}

interface LessonRow {
  key: string;
  lesson: LessonItem;
  students: DisplayStudent[];
  capacity: number;
}

interface TimeGroup {
  time: string;
  lessons: LessonRow[];
}

interface RoomPage {
  key: string;
  roomId?: number;
  roomName: string;
  lessonCount: number;
  studentCount: number;
  timeGroups: TimeGroup[];
}

const roomPalette = [
  { bg: '#edf5ff', border: '#78a9e6', text: '#184f90' },
  { bg: '#eef9f1', border: '#72b989', text: '#25633a' },
  { bg: '#fff7e8', border: '#e4ad55', text: '#805018' },
  { bg: '#f7f0fb', border: '#ad85c7', text: '#654077' },
  { bg: '#eaf9f8', border: '#63b8b0', text: '#246761' },
  { bg: '#fff0f1', border: '#df858b', text: '#8b363d' },
  { bg: '#f2f3fb', border: '#8993cc', text: '#434d88' },
  { bg: '#f7f5ed', border: '#b5a56c', text: '#675d31' },
];

const selectedDate = ref<Dayjs>(dayjs());
const lessons = ref<LessonItem[]>([]);
const rooms = ref<RoomItem[]>([]);
const noteMap = ref<Record<string, string>>({});
const loading = ref(false);
const activeRoomKey = ref('');
const roomPager = ref<HTMLElement | null>(null);

const lessonRows = computed<LessonRow[]>(() =>
  lessons.value
    .map((lesson) => ({
      key: lessonKey(lesson),
      lesson,
      students: getDisplayStudents(lesson),
      capacity: getCapacity(lesson),
    }))
    .sort((a, b) =>
      timeSortValue(a.lesson.time) - timeSortValue(b.lesson.time) ||
      String(a.lesson.room_name || '').localeCompare(String(b.lesson.room_name || '')) ||
      String(a.lesson.class_name || '').localeCompare(String(b.lesson.class_name || ''))
    )
);

const roomIds = computed(() => {
  return rooms.value.map((room) => room.id);
});

const roomPages = computed<RoomPage[]>(() => {
  const roomMap = new Map<string, { key: string; roomId?: number; roomName: string; rows: LessonRow[] }>();

  // Keep room tabs aligned with Schedule, including the configured room name
  // instead of the potentially stale label returned with a lesson.
  rooms.value.forEach((room) => {
    roomMap.set(String(room.id), {
      key: String(room.id),
      roomId: room.id,
      roomName: room.title,
      rows: [],
    });
  });

  lessonRows.value.forEach((row) => {
    const id = Number(row.lesson.room_id || 0) || undefined;
    const key = id ? String(id) : `room-${row.lesson.room_name || 'none'}`;
    if (!roomMap.has(key)) {
      roomMap.set(key, {
        key,
        roomId: id,
        roomName: row.lesson.room_name || 'No room',
        rows: [],
      });
    }
    roomMap.get(key)?.rows.push(row);
  });

  return Array.from(roomMap.values())
    .sort((a, b) => compareRoomNames(a.roomName, b.roomName))
    .map((room) => {
      const groups = new Map<string, LessonRow[]>();
      room.rows.forEach((row) => {
        const time = normalizeTime(row.lesson.time);
        if (!groups.has(time)) {
          groups.set(time, []);
        }
        groups.get(time)?.push(row);
      });
      const timeGroups = Array.from(groups.entries())
        .sort(([a], [b]) => timeSortValue(a) - timeSortValue(b))
        .map(([time, rows]) => ({
          time,
          lessons: rows.sort((a, b) => String(a.lesson.class_name || '').localeCompare(String(b.lesson.class_name || ''))),
        }));
      return {
        key: room.key,
        roomId: room.roomId,
        roomName: room.roomName,
        lessonCount: room.rows.length,
        studentCount: room.rows.reduce((sum, row) => sum + row.students.filter(isPresentStudent).length, 0),
        timeGroups,
      };
    });
});

const loadSchedule = async () => {
  loading.value = true;
  try {
    const date = selectedDate.value.format('YYYY-MM-DD');
    const [lessonRes, roomRes] = await Promise.all([
      listLessonsApi({ date }),
      listRoomsApi({}),
    ]);
    lessons.value = unwrapList(lessonRes);
    rooms.value = unwrapList(roomRes)
      .sort((a: RoomItem, b: RoomItem) => compareRoomNames(a.title, b.title));
    try {
      const noteRes = await listNotesApi({ date });
      noteMap.value = buildNoteMap(unwrapList(noteRes));
    } catch (noteError) {
      noteMap.value = {};
    }
  } catch (error: any) {
    message.error(error?.msg || 'Failed to load mobile schedule');
  } finally {
    loading.value = false;
  }
};

const buildNoteMap = (items: any[]) => {
  const nextMap: Record<string, string> = {};
  items.forEach((item) => {
    const lessonId = Number(item.lesson_id || item.lesson);
    const studentId = Number(item.student_id || item.student);
    const note = item.note || '';
    nextMap[`${lessonId}-${studentId}`] = note;
    nextMap[`${lessonId}:${studentId}`] = note;
  });
  return nextMap;
};

const unwrapList = (response: any) => {
  if (Array.isArray(response?.data)) {
    return response.data;
  }
  if (Array.isArray(response?.data?.data)) {
    return response.data.data;
  }
  if (Array.isArray(response)) {
    return response;
  }
  return [];
};

const shiftDate = (days: number) => {
  selectedDate.value = selectedDate.value.add(days, 'day');
  loadSchedule();
};

const goToday = () => {
  selectedDate.value = dayjs();
  loadSchedule();
};

const loadDemoDate = () => {
  selectedDate.value = dayjs('2026-07-07');
  loadSchedule();
};

const scrollToRoom = async (key: string) => {
  activeRoomKey.value = key;
  await nextTick();
  const target = roomPager.value?.querySelector(`[data-room-key="${key}"]`) as HTMLElement | null;
  target?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
};

const syncActiveRoom = () => {
  const pager = roomPager.value;
  if (!pager) return;
  let nextKey = activeRoomKey.value;
  let bestDistance = Number.MAX_SAFE_INTEGER;
  pager.querySelectorAll<HTMLElement>('.room-page').forEach((page) => {
    const distance = Math.abs(page.offsetLeft - pager.scrollLeft);
    if (distance < bestDistance) {
      bestDistance = distance;
      nextKey = page.dataset.roomKey || nextKey;
    }
  });
  activeRoomKey.value = nextKey;
};

const lessonKey = (lesson: LessonItem) => String(lesson.lesson_id || lesson.id);
const normalizeTime = (value?: string) => String(value || '').trim() || 'Time TBD';
const timeSortValue = (value?: string) => {
  const match = normalizeTime(value).match(/^(\d{1,2})(?::(\d{2}))?/);
  if (!match) return Number.MAX_SAFE_INTEGER;
  return Number(match[1]) * 60 + Number(match[2] || 0);
};

const isOnSelectedDate = (date?: string) => !!date && dayjs(date).isSame(selectedDate.value, 'day');

const isStudentActiveOnDate = (student: ScheduleStudent) => {
  if (!student.expect_time || !student.return_time) return true;
  const start = dayjs(student.expect_time).startOf('day');
  const end = dayjs(student.return_time).endOf('day');
  return selectedDate.value.isSame(start, 'day') ||
    selectedDate.value.isSame(end, 'day') ||
    (selectedDate.value.isAfter(start) && selectedDate.value.isBefore(end));
};

const getDisplayStudents = (lesson: LessonItem): DisplayStudent[] => {
  const canceled = (lesson.canceled_students || []).filter((student) => isOnSelectedDate(student.date));
  const canceledNames = new Set(canceled.map((student) => student.name));

  const regular = (lesson.scheduled_students || [])
    .filter(isStudentActiveOnDate)
    .filter((student) => !canceledNames.has(student.name))
    .map((student) => ({
      id: student.order_id,
      studentId: student.student_id,
      name: student.name,
      type: 'regular' as const,
      title: student.term_title,
    }));

  const makeup = (lesson.scheduled_reschedule_students || [])
    .filter((student) => isOnSelectedDate(student.date))
    .map((student) => ({
      id: student.adjustment_id,
      studentId: student.student_id,
      name: student.name,
      type: 'makeup' as const,
      badge: 'Makeup',
      title: student.term_title,
    }));

  const moved = (lesson.moved_students || []).map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'moved' as const,
    badge: 'Moved',
    title: student.term_title,
  }));

  const trial = (lesson.scheduled_trial_students || [])
    .filter((student) => isOnSelectedDate(student.date))
    .map((student) => ({
      id: student.trial_request_id,
      studentId: student.student_id,
      name: student.name,
      type: 'trial' as const,
      badge: 'Trial',
    }));

  const classPass = (lesson.scheduled_class_pass_students || [])
    .filter((student) => isOnSelectedDate(student.date))
    .map((student) => ({
      id: student.booking_id,
      studentId: student.student_id,
      name: student.name,
      type: 'class-pass' as const,
      badge: 'Pass',
      title: student.pass_title,
    }));

  const canceledRows = canceled.map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'canceled' as const,
    badge: 'Canceled',
    title: student.term_title,
  }));

  const sick = (lesson.sick_leave_students || []).map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'sick' as const,
    badge: 'Sick',
    title: student.term_title,
  }));

  return [...regular, ...makeup, ...moved, ...trial, ...classPass, ...canceledRows, ...sick]
    .sort((a, b) => a.name.localeCompare(b.name));
};

const isPresentStudent = (student: DisplayStudent) => !['canceled', 'sick'].includes(student.type);

const getCapacity = (lesson: LessonItem) => {
  const capacity = Number(lesson.room_capacity);
  return Number.isFinite(capacity) && capacity > 0 ? capacity : 4;
};

const getStudentNote = (lesson: LessonItem, student: DisplayStudent) => {
  const lessonId = Number(lesson.lesson_id || lesson.id);
  return noteMap.value[`${lessonId}-${student.studentId}`] || noteMap.value[`${lessonId}:${student.studentId}`] || '';
};

const getRoomColor = (roomId?: number) => {
  const index = Math.max(0, roomIds.value.findIndex((id) => Number(id) === Number(roomId)));
  return roomPalette[index % roomPalette.length];
};

const roomStyle = (roomId?: number) => {
  const color = getRoomColor(roomId);
  return {
    '--room-bg': color.bg,
    '--room-border': color.border,
    '--room-text': color.text,
  };
};

watch(roomPages, (pages) => {
  if (!pages.length) {
    activeRoomKey.value = '';
    return;
  }
  if (!pages.some((room) => room.key === activeRoomKey.value)) {
    activeRoomKey.value = pages[0].key;
  }
});

onMounted(loadSchedule);
</script>

<style scoped lang="less">
.mobile-schedule-page {
  min-height: calc(100vh - 96px);
  color: #10233f;
}

.mobile-schedule-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.mobile-schedule-header p {
  margin: 0 0 2px;
  color: #2d6cdf;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}

.mobile-schedule-header h1 {
  margin: 0;
  font-size: 24px;
  line-height: 1.15;
}

.date-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.date-bar :deep(.ant-picker) {
  grid-column: 1 / -1;
  width: 100%;
}

.legend {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 4px 0 10px;
  color: #52637a;
  font-size: 12px;
  white-space: nowrap;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.dot.regular {
  background: #64748b;
}

.dot.makeup {
  background: #1677ff;
}

.dot.canceled {
  background: #d92d20;
}

.dot.trial {
  background: #7f56d9;
}

.dot.class-pass {
  background: #0f9f6e;
}

.room-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.room-tabs button {
  flex: 0 0 auto;
  min-width: 92px;
  min-height: 38px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  background: var(--room-bg);
  color: var(--room-text);
  font-weight: 900;
}

.room-tabs button.active {
  background: #fff;
  box-shadow: inset 0 -3px 0 var(--room-border);
}

.room-pager {
  display: flex;
  align-items: flex-start;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  padding-bottom: 10px;
}

.room-page {
  flex: 0 0 100%;
  min-width: 0;
  scroll-snap-align: start;
  border: 2px solid var(--room-border);
  border-radius: 8px;
  background: #fff;
}

.room-head {
  padding: 12px 14px;
  border-bottom: 1px solid var(--room-border);
  background: var(--room-bg);
  color: var(--room-text);
}

.room-head h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
}

.room-head p {
  margin: 5px 0 0;
  font-size: 13px;
  font-weight: 800;
}

.time-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
}

.time-group {
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  overflow: hidden;
}

.time-group h3 {
  margin: 0;
  padding: 9px 12px;
  background: #f5f7fb;
  border-bottom: 1px solid #d8e1ec;
  font-size: 17px;
  line-height: 1.2;
}

.lesson-list {
  display: grid;
  gap: 8px;
  padding: 10px;
}

.lesson-card {
  border: 1px solid color-mix(in srgb, var(--room-border) 66%, white);
  border-radius: 8px;
  background: color-mix(in srgb, var(--room-bg) 58%, white);
  overflow: hidden;
}

.lesson-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--room-border) 52%, white);
  color: var(--room-text);
}

.lesson-head strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 16px;
}

.lesson-head span {
  flex: 0 0 auto;
  color: #53637a;
  font-size: 12px;
  font-weight: 900;
}

.student-list {
  display: grid;
  gap: 7px;
  padding: 9px;
}

.student-line {
  border: 1px solid #d8e1ec;
  border-left: 5px solid #64748b;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.86);
  padding: 8px;
}

.student-line.makeup,
.student-line.moved {
  border-left-color: #1677ff;
  background: #eef6ff;
}

.student-line.canceled,
.student-line.sick {
  border-left-color: #d92d20;
  background: #fff1f0;
}

.student-line.trial {
  border-left-color: #7f56d9;
  background: #f7f0ff;
}

.student-line.class-pass {
  border-left-color: #0f9f6e;
  background: #ecfdf5;
}

.student-name-row {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}

.student-name {
  color: #10233f;
  font-size: 16px;
  font-weight: 900;
}

.student-line.canceled .student-name,
.student-line.sick .student-name {
  color: #b42318;
  text-decoration: line-through;
}

.student-badge {
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(16, 35, 63, 0.08);
  color: currentColor;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
}

.student-title,
.student-note,
.empty-students {
  margin: 5px 0 0;
  color: #53637a;
  font-size: 12px;
  line-height: 1.35;
}

.student-note {
  color: #1f5f8f;
  font-weight: 700;
}

.empty-students {
  padding: 10px;
  color: #8b98aa;
}

@media (min-width: 760px) {
  .mobile-schedule-page {
    max-width: 720px;
    margin: 0 auto;
  }
}
</style>
