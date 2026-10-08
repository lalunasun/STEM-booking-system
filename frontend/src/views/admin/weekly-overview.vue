<template>
  <a-config-provider :locale="enUS">
    <div class="overview-page" :class="{ 'is-fullscreen': isFullscreen }">
      <header class="overview-toolbar">
        <div>
          <h2>Weekly Overview</h2>
          <p v-if="weekDays.length" class="overview-range">
            {{ overviewRangeStart.format('MMM D') }} - {{ overviewRangeEnd.format('MMM D, YYYY') }}
          </p>
        </div>
        <div class="overview-actions">
          <a-button title="Previous week" @click="changeWeek(-1)">
            <left-outlined />
            Previous
          </a-button>
          <a-button @click="goToCurrentWeek">Today</a-button>
          <a-button title="Next week" @click="changeWeek(1)">
            Next
            <right-outlined />
          </a-button>
          <a-button class="assistant-button" title="Open quick query" @click="assistantOpen = true">
            <message-outlined />
            Quick Query
          </a-button>
          <a-date-picker
            :value="selectedWeek"
            picker="week"
            :allow-clear="false"
            format="[Week of] MMM D, YYYY"
            @change="selectWeek"
          />
          <div class="overview-zoom" role="group" aria-label="Overview zoom">
            <a-button
              title="Zoom out"
              aria-label="Zoom out"
              :disabled="overviewZoom <= overviewZoomSteps[0]"
              @click="changeOverviewZoom(-1)"
            >
              <zoom-out-outlined />
            </a-button>
            <span>{{ Math.round(overviewZoom * 100) }}%</span>
            <a-button
              title="Zoom in"
              aria-label="Zoom in"
              :disabled="overviewZoom >= overviewZoomSteps[overviewZoomSteps.length - 1]"
              @click="changeOverviewZoom(1)"
            >
              <zoom-in-outlined />
            </a-button>
          </div>
          <a-button
            class="overview-fullscreen-button"
            :title="isFullscreen ? 'Exit full screen' : 'Full screen'"
            :aria-label="isFullscreen ? 'Exit full screen' : 'Full screen'"
            :aria-pressed="isFullscreen"
            @click="toggleFullscreen"
          >
            <fullscreen-exit-outlined v-if="isFullscreen" />
            <fullscreen-outlined v-else />
          </a-button>
        </div>
      </header>

      <div v-if="loading" class="overview-state">Loading overview...</div>
      <div v-else-if="!dayBlocks.length" class="overview-state">
        No classes scheduled for this week.
      </div>
      <div v-else class="overview-board">
        <div
          class="overview-grid"
          :style="{
            gridTemplateColumns: `112px repeat(${dayBlocks.length * rooms.length}, minmax(${Math.round(155 * overviewZoom)}px, 1fr))`,
          }"
        >
          <div class="grid-corner">Time</div>
          <div
            v-for="(day, dayIndex) in dayBlocks"
            :key="`day-${day.key}`"
            class="day-header"
            :class="{ 'day-start': dayIndex > 0 }"
            :style="{ gridColumn: `span ${rooms.length}` }"
          >
            <div class="day-header-content">
              <strong>{{ day.date.format('dddd') }}</strong>
              <span>{{ day.date.format('MMM D') }}</span>
            </div>
          </div>

          <div class="grid-corner room-label">Room</div>
          <template v-for="(day, dayIndex) in dayBlocks" :key="`rooms-${day.key}`">
            <div
              v-for="room in rooms"
              :key="`${day.key}-room-${room.id}`"
              class="room-header"
              :class="{ 'day-start': dayIndex > 0 && room.id === rooms[0]?.id }"
              :style="roomColorStyle(room.title)"
            >
              {{ room.title }}
            </div>
          </template>

          <template v-for="row in weekTimeRows" :key="`week-${row.start}`">
            <div class="time-label">{{ row.label }}</div>
            <template v-for="(day, dayIndex) in dayBlocks" :key="`${row.start}-${day.key}`">
              <div
                v-for="room in rooms"
                :key="`${day.key}-${row.start}-${room.id}`"
                class="day-cell"
                :class="{
                  'day-start': dayIndex > 0 && room.id === rooms[0]?.id,
                  empty: !getCellLessons(day, room.id, row.start).length,
                }"
              >
                <article
                  v-for="lesson in getCellLessons(day, room.id, row.start)"
                  :key="lesson.id"
                  class="lesson-card"
                  :title="lesson.class_name || 'Class'"
                  :style="roomColorStyle(room.title)"
                >
                  <strong>{{ courseCode(lesson.class_name) }}</strong>
                  <small v-if="isNonStandardTime(lesson.time)">{{ lesson.time }}</small>
                  <span v-for="student in getStudents(lesson, day.date)" :key="`${lesson.id}-${student.key}`">
                    {{ student.name }}
                  </span>
                  <em v-if="!getStudents(lesson, day.date).length">No students</em>
                </article>
              </div>
            </template>
          </template>
        </div>
      </div>

      <div v-if="dayBlocks.length" class="overview-mobile">
        <section v-for="day in dayBlocks" :key="`mobile-day-${day.key}`" class="mobile-day">
          <header class="mobile-day-header">
            <strong>{{ day.date.format('dddd') }}</strong>
            <span>{{ day.date.format('MMM D, YYYY') }}</span>
          </header>

          <div v-for="row in day.timeRows" :key="`${day.key}-${row.start}`" class="mobile-time-block">
            <div class="mobile-time-label">{{ row.label }}</div>
            <div class="mobile-room-list">
              <template v-for="room in rooms" :key="`${day.key}-${row.start}-room-${room.id}`">
                <div v-if="getCellLessons(day, room.id, row.start).length" class="mobile-room-row">
                  <div class="mobile-room-name" :style="roomColorStyle(room.title)">
                    {{ room.title }}
                  </div>
                  <div class="mobile-room-lessons">
                    <article
                      v-for="lesson in getCellLessons(day, room.id, row.start)"
                      :key="lesson.id"
                      class="lesson-card"
                      :title="lesson.class_name || 'Class'"
                      :style="roomColorStyle(room.title)"
                    >
                      <strong>{{ courseCode(lesson.class_name) }}</strong>
                      <small v-if="isNonStandardTime(lesson.time)">{{ lesson.time }}</small>
                      <span v-for="student in getStudents(lesson, day.date)" :key="`${lesson.id}-${student.key}`">
                        {{ student.name }}
                      </span>
                      <em v-if="!getStudents(lesson, day.date).length">No students</em>
                    </article>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </section>
      </div>

      <a-drawer
        title="Quick Query"
        placement="right"
        :visible="assistantOpen"
        :width="520"
        :body-style="{ padding: '16px' }"
        @close="assistantOpen = false"
      >
        <div class="assistant-panel">
          <p class="assistant-intro">
            Ask about recurring class availability or a student's remaining lessons.
            Results are read-only and calculated from current system data.
          </p>

          <div class="assistant-examples">
            <button v-for="example in assistantExamples" :key="example" type="button" @click="askAssistant(example)">
              {{ example }}
            </button>
          </div>

          <div v-if="!assistantMessages.length" class="assistant-empty">
            Try a sample question or enter your own below.
          </div>
          <div v-else class="assistant-history">
            <section v-for="(message, index) in assistantMessages" :key="index" class="assistant-exchange">
              <div class="assistant-question">{{ message.question }}</div>
              <div class="assistant-answer" :class="{ error: message.error }">
                <template v-if="message.loading">
                  <a-spin size="small" />
                  <span>Checking current data...</span>
                </template>
                <template v-else-if="message.error">
                  {{ message.error }}
                </template>
                <template v-else-if="message.result">
                  <div class="assistant-answer-heading">
                    <strong>{{ message.result.answer }}</strong>
                    <a-tag v-if="message.result.interpreter === 'ai'" color="blue">AI interpreted</a-tag>
                    <a-tag v-else>Local query</a-tag>
                  </div>

                  <div v-if="message.result.intent === 'availability'" class="assistant-results">
                    <article v-for="item in message.result.items" :key="`${item.term}-${item.class_id}`" class="assistant-result-row">
                      <div>
                        <strong>{{ item.course }}</strong>
                        <span>{{ item.day }} {{ item.time }} · {{ item.room }}</span>
                        <small>{{ item.term }}</small>
                      </div>
                      <b>{{ item.available_seats }} / {{ item.capacity }} left</b>
                    </article>
                  </div>

                  <div v-else class="assistant-results">
                    <article
                      v-for="item in message.result.items"
                      :key="`${item.type || 'student'}-${item.order_id || item.class_pass_id || item.student_id}`"
                      class="assistant-result-row"
                    >
                      <div v-if="item.type">
                        <strong>{{ item.course }}</strong>
                        <span v-if="item.type === 'enrollment'">
                          {{ item.day }} {{ item.time }}<template v-if="item.room"> · {{ item.room }}</template>
                        </span>
                        <small>{{ item.term || item.type.replace('_', ' ') }}</small>
                      </div>
                      <div v-else>
                        <strong>{{ item.student_name }} #{{ item.student_id }}</strong>
                        <span v-if="item.parent">Parent: {{ item.parent }}</span>
                      </div>
                      <b v-if="item.balance_source === 'calendar_estimate' && item.calendar_estimate">
                        ~{{ item.calendar_estimate }} dates
                      </b>
                      <b v-else-if="item.remaining_lessons !== undefined">{{ item.remaining_lessons }} left</b>
                    </article>
                  </div>

                  <p v-if="message.result.interpreter === 'local_fallback'" class="assistant-note">
                    The AI service did not respond, so this answer used the local query parser.
                  </p>
                </template>
              </div>
            </section>
          </div>

          <div class="assistant-composer">
            <a-textarea
              v-model:value="assistantQuestion"
              :rows="3"
              :maxlength="500"
              placeholder="Example: Which Scratch classes have seats on Saturday?"
              @keydown.ctrl.enter.prevent="askAssistant()"
            />
            <a-button
              type="primary"
              :loading="assistantLoading"
              :disabled="!assistantQuestion.trim()"
              @click="askAssistant()"
            >
              <send-outlined />
              Ask
            </a-button>
          </div>
        </div>
      </a-drawer>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import {
  FullscreenExitOutlined,
  FullscreenOutlined,
  LeftOutlined,
  MessageOutlined,
  RightOutlined,
  SendOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
} from '@ant-design/icons-vue';
import enUS from 'ant-design-vue/es/locale/en_US';
import dayjs, { Dayjs } from 'dayjs';
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { queryApi as queryAssistantApi } from '/@/api/admin/assistant';
import { listApi as listLessonsApi } from '/@/api/admin/lesson';
import { listApi as listRoomsApi } from '/@/api/admin/tag';
import { listApi as listTimesApi } from '/@/api/admin/time';
import { compareRoomNames } from '/@/utils/room-order';
import { subscribeToScheduleDataChanges } from '/@/utils/schedule-sync';

interface RoomItem {
  id: number;
  title: string;
}

interface LessonRecord {
  id: number;
  room_id?: number;
  class_name?: string;
  time?: string;
  scheduled_students?: any[];
  canceled_students?: any[];
  scheduled_reschedule_students?: any[];
  scheduled_trial_students?: any[];
  continuing_trial_students?: any[];
  scheduled_class_pass_students?: any[];
  moved_students?: any[];
}

interface TimeRow {
  start: number;
  label: string;
}

interface DayBlock {
  key: string;
  date: Dayjs;
  lessons: LessonRecord[];
  timeRows: TimeRow[];
}

interface AssistantResult {
  intent: 'availability' | 'student_remaining';
  answer: string;
  items: any[];
  interpreter: 'ai' | 'local' | 'local_fallback';
}

interface AssistantMessage {
  question: string;
  loading?: boolean;
  error?: string;
  result?: AssistantResult;
}

const selectedWeek = ref<Dayjs>(dayjs());
const rooms = ref<RoomItem[]>([]);
const timeSlots = ref<string[]>([]);
const dayBlocks = ref<DayBlock[]>([]);
const loading = ref(false);
const isFullscreen = ref(false);
const assistantOpen = ref(false);
const assistantQuestion = ref('');
const assistantLoading = ref(false);
const assistantMessages = ref<AssistantMessage[]>([]);
const assistantExamples = [
  'Which Scratch classes have seats on Saturday?',
  'What classes still have seats on Tuesday?',
  'How many lessons does Leon-Z2019 have left?',
];
const overviewZoomSteps = [0.55, 0.7, 0.85, 1];
const overviewZoom = ref(1);
let unsubscribeScheduleSync: (() => void) | undefined;

const legacyRoomKeys = new Set(['room2', 'room6', 'room7', 'room8']);
const roomColorPalette = [
  { bg: '#edf5ff', border: '#78a9e6', text: '#184f90' },
  { bg: '#eef9f1', border: '#72b989', text: '#25633a' },
  { bg: '#fff7e8', border: '#e4ad55', text: '#805018' },
  { bg: '#f7f0fb', border: '#ad85c7', text: '#654077' },
  { bg: '#eaf9f8', border: '#63b8b0', text: '#246761' },
  { bg: '#fff0f1', border: '#df858b', text: '#8b363d' },
  { bg: '#f2f3fb', border: '#8993cc', text: '#434d88' },
  { bg: '#f7f5ed', border: '#b5a56c', text: '#675d31' },
];
const roomColorIndexes: Record<string, number> = {
  room1: 0,
  room3: 1,
  room4: 2,
  room5: 3,
  library: 4,
  vexiqlab: 5,
  vexv5lab: 6,
  v5lab: 6,
  meetingroom: 7,
};

const getMonday = (date: Dayjs) => date.startOf('day').subtract((date.day() + 6) % 7, 'day');

const weekDays = computed(() => {
  const monday = getMonday(selectedWeek.value);
  return [5, 6, 1, 2, 3, 4].map((offset) => monday.add(offset, 'day'));
});

const overviewRangeStart = computed(() => weekDays.value.reduce((start, date) => date.isBefore(start) ? date : start));
const overviewRangeEnd = computed(() => weekDays.value.reduce((end, date) => date.isAfter(end) ? date : end));

const getTimeMinutes = (value?: string) => {
  const match = String(value || '').match(/^(\d{1,2}):?(\d{2})?/);
  return match ? Number(match[1]) * 60 + Number(match[2] || 0) : Number.MAX_SAFE_INTEGER;
};

const getTimeRange = (value?: string) => {
  const parts = String(value || '').split('-');
  return {
    start: getTimeMinutes(parts[0]),
    end: getTimeMinutes(parts[1] || parts[0]),
  };
};

const formatMinutes = (minutes: number) => {
  const hour = Math.floor(minutes / 60).toString().padStart(2, '0');
  const minute = (minutes % 60).toString().padStart(2, '0');
  return `${hour}:${minute}`;
};

const normalizeRowStart = (minutes: number) => Math.floor(minutes / 60) * 60;

const isNonStandardTime = (value?: string) => {
  const range = getTimeRange(value);
  return range.start === Number.MAX_SAFE_INTEGER
    || range.start % 60 !== 0
    || range.end - range.start !== 60;
};

const compactRoomName = (value: unknown) => String(value || '').trim().toLowerCase().replace(/\s+/g, '');

const roomColorStyle = (roomName: string) => {
  const color = roomColorPalette[roomColorIndexes[compactRoomName(roomName)] ?? 0];
  return {
    '--room-bg': color.bg,
    '--room-border': color.border,
    '--room-text': color.text,
  };
};

const courseCode = (name?: string) => {
  const value = String(name || '').toLowerCase().replace(/\s+/g, ' ').trim();
  if (value.includes('scratch jr')) return 'SJr';
  if (value.includes('scratch')) return 'Sc';
  if (value.includes('creator')) return 'Cr';
  if (value.includes('wedo')) return 'Wd';
  if (value.includes('spike')) return 'Sp';
  if (value.includes('roblox')) return 'Rb';
  if (value.includes('vex iq')) return 'VxIQ';
  if (value.includes('vex v5') || value === 'v5') return 'VxV5';
  if (value.includes('python')) return 'Py';
  if (value.includes('java')) return 'Jv';
  if (value.includes('math')) return 'Math';
  return String(name || 'Class').slice(0, 4);
};

const sameDate = (value: unknown, date: Dayjs) => Boolean(value) && dayjs(String(value)).isSame(date, 'day');

const getStudents = (lesson: LessonRecord, date: Dayjs) => {
  const canceled = new Set(
    (lesson.canceled_students || [])
      .filter((student) => sameDate(student.date, date))
      .map((student) => `${student.student_id}-${student.name}`),
  );
  const students: Array<{ key: string; name: string }> = [];
  const add = (student: any) => {
    const name = String(student?.name || '').trim();
    if (!name) return;
    const key = `${student.student_id || student.id || name}-${name}`;
    if (canceled.has(key) || students.some((item) => item.key === key)) return;
    students.push({ key, name });
  };

  (lesson.scheduled_students || []).forEach((student) => {
    const start = dayjs(student.expect_time).startOf('day');
    const end = dayjs(student.return_time).endOf('day');
    if (date.isSame(start, 'day') || date.isSame(end, 'day') || date.isAfter(start, 'day') && date.isBefore(end, 'day')) {
      add(student);
    }
  });
  (lesson.scheduled_reschedule_students || []).filter((student) => sameDate(student.date, date)).forEach(add);
  (lesson.scheduled_trial_students || []).filter((student) => sameDate(student.date, date)).forEach(add);
  (lesson.continuing_trial_students || []).filter((student) => sameDate(student.date, date)).forEach((student) =>
    add({ ...student, name: `${student.name} (trial ${courseCode(student.trial_course)})` }));
  (lesson.scheduled_class_pass_students || []).filter((student) => sameDate(student.date, date)).forEach(add);
  (lesson.moved_students || []).forEach(add);
  return students;
};

const buildTimeRows = (lessons: LessonRecord[]) => {
  const starts = new Set<number>();
  lessons.forEach((lesson) => {
    const range = getTimeRange(lesson.time);
    if (range.start === Number.MAX_SAFE_INTEGER) return;
    starts.add(normalizeRowStart(range.start));
  });
  return [...starts]
    .sort((left, right) => left - right)
    .map((start) => ({
      start,
      label: `${formatMinutes(start)}-${formatMinutes(start + 60)}`,
    }));
};

const weekTimeRows = computed(() => {
  const rows = new Set<number>();
  dayBlocks.value.forEach((day) => {
    day.timeRows.forEach((row) => {
      rows.add(row.start);
    });
  });
  return [...rows]
    .sort((left, right) => left - right)
    .map((start) => ({
      start,
      label: `${formatMinutes(start)}-${formatMinutes(start + 60)}`,
    }));
});

const loadOverview = async () => {
  loading.value = true;
  try {
    const [roomResponse, timeResponse, ...dailyResponses] = await Promise.all([
      listRoomsApi({}),
      listTimesApi({}),
      ...weekDays.value.map((date) => listLessonsApi({ date: date.format('YYYY-MM-DD') })),
    ]);
    const allRooms = [...(roomResponse.data || [])].sort((left, right) => compareRoomNames(left.title, right.title));
    timeSlots.value = [...(timeResponse.data || [])]
      .map((slot: any) => String(slot.time || ''))
      .filter(Boolean);
      dayBlocks.value = weekDays.value
      .map((date, index) => {
        const lessons = ((dailyResponses[index]?.data || []) as LessonRecord[])
          .filter((lesson) => getStudents(lesson, date).length > 0);
        return {
          key: date.format('YYYY-MM-DD'),
          date,
          lessons,
          timeRows: buildTimeRows(lessons),
        };
      })
      .filter((day) => day.lessons.length > 0);

    const hasCurrentStudents = (roomId: number) => dayBlocks.value.some((day) =>
      day.lessons
        .filter((lesson) => Number(lesson.room_id) === Number(roomId))
        .some((lesson) => getStudents(lesson, day.date).length > 0),
    );
    rooms.value = allRooms.filter((room) =>
      !legacyRoomKeys.has(compactRoomName(room.title)) || hasCurrentStudents(room.id),
    );
  } catch (error) {
    dayBlocks.value = [];
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const getCellLessons = (day: DayBlock, roomId: number, start: number) => day.lessons
  .filter((lesson) => Number(lesson.room_id) === Number(roomId))
  .filter((lesson) => normalizeRowStart(getTimeRange(lesson.time).start) === start);

const changeWeek = (amount: number) => {
  selectedWeek.value = selectedWeek.value.add(amount, 'week');
  loadOverview();
};

const goToCurrentWeek = () => {
  selectedWeek.value = dayjs();
  loadOverview();
};

const selectWeek = (date: Dayjs | null) => {
  if (date) {
    selectedWeek.value = date;
    loadOverview();
  }
};

const askAssistant = async (preset?: string) => {
  const question = String(preset || assistantQuestion.value || '').trim();
  if (!question || assistantLoading.value) return;
  assistantOpen.value = true;
  assistantQuestion.value = '';
  assistantLoading.value = true;
  const message: AssistantMessage = { question, loading: true };
  assistantMessages.value.push(message);
  try {
    const response = await queryAssistantApi(question);
    message.result = response.data as AssistantResult;
  } catch (error: any) {
    message.error = String(error?.msg || error?.message || 'The query could not be completed.');
  } finally {
    message.loading = false;
    assistantLoading.value = false;
  }
};

const changeOverviewZoom = (direction: number) => {
  const currentIndex = overviewZoomSteps.indexOf(overviewZoom.value);
  const nextIndex = Math.min(
    overviewZoomSteps.length - 1,
    Math.max(0, currentIndex + direction),
  );
  overviewZoom.value = overviewZoomSteps[nextIndex];
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const handleFullscreenKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isFullscreen.value) {
    isFullscreen.value = false;
  }
};

onMounted(() => {
  if (window.matchMedia('(max-width: 720px)').matches) {
    overviewZoom.value = 0.7;
  }
  loadOverview();
  window.addEventListener('keydown', handleFullscreenKeydown);
  unsubscribeScheduleSync = subscribeToScheduleDataChanges(loadOverview);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleFullscreenKeydown);
  unsubscribeScheduleSync?.();
});
</script>

<style scoped>
.overview-page {
  min-height: 100%;
  padding: 24px;
  background: #f5f7fa;
  color: #172b4d;
}

.overview-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.overview-toolbar h2 {
  margin: 0;
  color: #102a43;
  font-size: 28px;
  line-height: 1.2;
}

.overview-range {
  margin: 6px 0 0;
  color: #627d98;
}

.overview-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.assistant-panel {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 104px);
}

.assistant-intro {
  margin: 0 0 12px;
  color: #52667a;
  line-height: 1.5;
}

.assistant-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 16px;
}

.assistant-examples button {
  padding: 5px 9px;
  border: 1px solid #b8c7d9;
  border-radius: 4px;
  background: #fff;
  color: #245b9e;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  text-align: left;
}

.assistant-examples button:hover {
  border-color: #2f80ed;
  background: #f2f7ff;
}

.assistant-empty {
  flex: 1;
  padding: 56px 18px;
  border: 1px dashed #c8d4e2;
  color: #718096;
  text-align: center;
}

.assistant-history {
  flex: 1;
  min-height: 160px;
  max-height: calc(100vh - 390px);
  overflow-y: auto;
  padding-right: 4px;
}

.assistant-exchange + .assistant-exchange {
  margin-top: 18px;
}

.assistant-question {
  max-width: 88%;
  margin-left: auto;
  padding: 8px 10px;
  border-radius: 6px 6px 2px 6px;
  background: #1f6feb;
  color: #fff;
  line-height: 1.4;
}

.assistant-answer {
  margin-top: 8px;
  padding: 11px;
  border: 1px solid #d5dee9;
  border-radius: 2px 6px 6px 6px;
  background: #f8fafc;
  color: #243b53;
}

.assistant-answer.error {
  border-color: #efb4b4;
  background: #fff5f5;
  color: #a61b1b;
}

.assistant-answer > span {
  margin-left: 8px;
}

.assistant-answer-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  line-height: 1.45;
}

.assistant-results {
  margin-top: 10px;
  border-top: 1px solid #d9e2ec;
}

.assistant-result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid #e7edf4;
}

.assistant-result-row > div {
  min-width: 0;
}

.assistant-result-row strong,
.assistant-result-row span,
.assistant-result-row small {
  display: block;
}

.assistant-result-row span,
.assistant-result-row small {
  color: #627d98;
  font-size: 12px;
}

.assistant-result-row b {
  flex: none;
  color: #17633a;
  font-size: 12px;
}

.assistant-note {
  margin: 10px 0 0;
  color: #7b8794;
  font-size: 12px;
}

.assistant-composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #d9e2ec;
}

.assistant-composer .ant-btn {
  height: 64px;
}

.overview-zoom {
  display: none;
  align-items: center;
  gap: 6px;
}

.overview-zoom span {
  min-width: 44px;
  color: #486581;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.overview-state {
  padding: 72px 24px;
  border: 1px solid #d9e2ec;
  border-radius: 6px;
  background: #fff;
  color: #627d98;
  text-align: center;
}

.overview-board {
  position: relative;
  max-height: calc(100vh - 150px);
  min-height: 420px;
  overflow-x: auto;
  overflow-y: auto;
  border: 1px solid #bcccdc;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 1px 2px rgb(16 42 67 / 6%);
}

.overview-mobile {
  display: none;
}

.overview-grid {
  display: grid;
  width: max-content;
  min-width: 100%;
}

.grid-corner,
.day-header,
.room-header,
.time-label,
.day-cell {
  box-sizing: border-box;
  border-right: 1px solid #d9e2ec;
  border-bottom: 1px solid #d9e2ec;
}

.grid-corner,
.day-header {
  position: sticky;
  top: 0;
  z-index: 4;
  height: 50px;
  min-height: 50px;
  padding: 10px 8px;
  background: #fff200;
  color: #111827;
  font-weight: 700;
  text-align: center;
}

.room-header {
  position: sticky;
  top: 50px;
  z-index: 3;
  height: 40px;
  min-height: 40px;
  padding: 9px 6px;
  background: var(--room-bg, #f0f4f8);
  color: var(--room-text, #243b53);
  font-size: 12px;
  font-weight: 700;
  text-align: center;
  border-bottom: 3px solid var(--room-border, #bcccdc);
}

.grid-corner {
  left: 0;
  z-index: 7;
  background: #f0f4f8;
  color: #243b53;
  box-shadow: 3px 0 5px rgb(16 42 67 / 10%);
}

.room-label {
  top: 50px;
  left: 0;
  z-index: 6;
  height: 40px;
  min-height: 40px;
  padding: 9px 8px;
  background: #f0f4f8;
  color: #627d98;
  font-size: 12px;
}

.day-header-content strong,
.day-header-content span {
  display: block;
}

.day-header-content strong {
  font-size: 15px;
}

.day-header-content span {
  margin-top: 3px;
  font-size: 12px;
  font-weight: 500;
}

.time-label {
  position: sticky;
  left: 0;
  z-index: 2;
  min-height: 84px;
  padding: 11px 8px;
  background: #f8fafc;
  color: #334e68;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 3px 0 5px rgb(16 42 67 / 10%);
}

.day-cell {
  min-height: 84px;
  padding: 5px;
  background: #fff;
}

.day-cell.empty {
  background: #fbfcfe;
}

.lesson-card {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 2px 5px;
  margin-bottom: 4px;
  padding: 5px 6px;
  border: 1px solid var(--room-border, #9fb3c8);
  border-radius: 4px;
  background: var(--room-bg, #edf5ff);
  color: #102a43;
  font-size: 11px;
  line-height: 1.25;
}

.lesson-card:last-child {
  margin-bottom: 0;
}

.lesson-card strong {
  color: var(--room-text, #184f90);
  font-size: 12px;
}

.lesson-card small {
  flex-basis: 100%;
  color: #627d98;
  font-size: 10px;
}

.lesson-card span {
  white-space: normal;
  overflow-wrap: anywhere;
}

.lesson-card em {
  color: #829ab1;
  font-size: 11px;
  font-style: normal;
}

/* Keep each day's room group visually separate while scrolling horizontally. */
.day-header.day-start,
.room-header.day-start,
.day-cell.day-start {
  border-left: 10px solid #fff200;
}

@media (max-width: 900px) {
  .overview-page {
    padding: 16px;
  }

  .overview-toolbar {
    display: block;
  }

  .overview-actions {
    margin-top: 14px;
  }
}

@media (max-width: 720px) {
  .overview-page {
    padding: 12px;
  }

  .overview-toolbar {
    gap: 12px;
    margin-bottom: 14px;
  }

  .overview-toolbar h2 {
    font-size: 22px;
  }

  .overview-actions {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
    margin-top: 12px;
  }

  .overview-actions .ant-btn {
    min-width: 0;
    padding: 0 6px;
  }

  .overview-actions .ant-picker {
    grid-column: 1 / -1;
    width: 100%;
  }

  .overview-zoom {
    display: flex;
    grid-column: 1 / 3;
    justify-self: start;
  }

  .overview-fullscreen-button {
    grid-column: 3;
    justify-self: end;
  }

  .overview-board {
    display: block;
    max-height: calc(100vh - 205px);
    min-height: 430px;
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
  }

  .overview-grid {
    min-width: 920px;
  }

  .day-header-content {
    position: sticky;
    left: 112px;
    width: max-content;
    margin: 0;
    padding-left: 8px;
    text-align: left;
  }

  .overview-mobile {
    display: none;
  }

  .mobile-day-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 14px;
    background: #fff200;
    color: #111827;
  }

  .mobile-day-header strong {
    font-size: 17px;
  }

  .mobile-day-header span {
    font-size: 12px;
    font-weight: 600;
  }

  .mobile-time-block + .mobile-time-block {
    border-top: 1px solid #d9e2ec;
  }

  .mobile-time-label {
    padding: 9px 14px;
    background: #f8fafc;
    color: #334e68;
    font-size: 13px;
    font-weight: 700;
  }

  .mobile-room-row {
    display: grid;
    grid-template-columns: 86px minmax(0, 1fr);
    gap: 8px;
    padding: 8px 10px;
    border-top: 1px solid #edf2f7;
  }

  .mobile-room-name {
    align-self: start;
    padding: 7px 5px;
    border-left: 4px solid var(--room-border, #bcccdc);
    background: var(--room-bg, #f0f4f8);
    color: var(--room-text, #243b53);
    font-size: 11px;
    font-weight: 700;
    line-height: 1.25;
    overflow-wrap: anywhere;
  }

  .mobile-room-lessons {
    min-width: 0;
  }

  .mobile-room-lessons .lesson-card {
    margin-bottom: 6px;
  }

  .mobile-room-lessons .lesson-card:last-child {
    margin-bottom: 0;
  }

  .mobile-room-lessons .lesson-card span {
    white-space: normal;
    overflow-wrap: anywhere;
  }
}

.overview-page.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 12px;
}

.overview-page.is-fullscreen .overview-toolbar {
  flex: none;
  margin-bottom: 10px;
}

.overview-page.is-fullscreen .overview-toolbar > div:first-child {
  display: none;
}

.overview-page.is-fullscreen .overview-actions {
  width: 100%;
  margin-top: 0;
}

.overview-page.is-fullscreen .overview-board {
  flex: 1;
  min-height: 0;
  max-height: none;
  height: auto;
}

.overview-page.is-fullscreen .overview-state {
  flex: 1;
}

@media print {
  .overview-page {
    padding: 0;
    background: #fff;
  }

  .overview-actions {
    display: none;
  }

  .overview-board {
    break-inside: avoid;
    box-shadow: none;
  }
}
</style>
