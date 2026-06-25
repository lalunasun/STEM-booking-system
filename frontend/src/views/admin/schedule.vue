<template>
  <a-config-provider :locale="enUS">
    <div class="page-view">
      <header class="schedule-toolbar">
        <div class="schedule-title">
          <h2>Daily Schedule</h2>
          <span>{{ selectedDate.format('dddd, MMMM D, YYYY') }}</span>
        </div>

        <div class="schedule-actions">
          <a-input
            v-model:value="studentKeyword"
            allow-clear
            class="student-search"
            placeholder="Search student"
          />
          <a-button @click="selectPreviousDay">Previous</a-button>
          <a-button @click="selectToday">Today</a-button>
          <a-button @click="selectNextDay">Next</a-button>
        </div>
      </header>

      <section class="announcement" aria-label="Staff announcement">
        <div class="announcement-icon">A</div>
        <div>
          <strong>Staff announcement</strong>
          <p>{{ staffAnnouncement }}</p>
        </div>
      </section>

      <section class="date-picker-band" aria-label="Choose schedule date">
        <button
          v-for="date in visibleDates"
          :key="date.format('YYYY-MM-DD')"
          type="button"
          class="date-option"
          :class="{ selected: date.isSame(selectedDate, 'day'), today: date.isSame(dayjs(), 'day') }"
          @click="selectedDate = date"
        >
          <span class="date-weekday">{{ date.format('ddd') }}</span>
          <strong>{{ date.format('D') }}</strong>
          <span class="date-month">{{ date.format('MMM') }}</span>
        </button>
      </section>

      <div class="legend" aria-label="Student status legend">
        <span><i class="legend-dot normal"></i>Regular</span>
        <span><i class="legend-dot canceled"></i>Absent</span>
        <span><i class="legend-dot rescheduled"></i>Makeup</span>
        <span><i class="legend-dot trial"></i>Trial</span>
      </div>

      <div v-if="loading" class="board-message">Loading schedule...</div>
      <div v-else-if="!rooms.length" class="board-message">No classrooms configured.</div>
      <div v-else-if="!displayedTimeSlots.length" class="board-message">
        No classes scheduled on {{ selectedDate.format('dddd') }}.
      </div>

      <div v-else class="schedule-scroll">
        <div class="daily-board" :style="boardGridStyle">
          <div class="time-header">Time</div>
          <div v-for="room in rooms" :key="`room-${room.id}`" class="room-header">
            <strong>{{ room.title }}</strong>
            <span>{{ getTeacherPreset(room.id) }}</span>
            <small>{{ room.seat || 0 }} seats</small>
          </div>

          <template v-for="slot in displayedTimeSlots" :key="slot.id">
            <div class="time-cell">{{ slot.time }}</div>

            <div
              v-for="room in rooms"
              :key="`${slot.id}-${room.id}`"
              class="schedule-cell"
              :class="{ 'empty-cell': !getCellLessons(room.id, slot.id).length }"
            >
              <template v-if="getCellLessons(room.id, slot.id).length">
                <article
                  v-for="lesson in getCellLessons(room.id, slot.id)"
                  :key="lesson.id"
                  class="lesson-block"
                  :style="getLessonColorStyle(lesson)"
                >
                  <button
                    type="button"
                    class="lesson-heading"
                    @click="toDetailPage(lesson)"
                  >
                    <span class="lesson-title-line">
                      <strong>{{ lesson.class_name || 'Untitled class' }}</strong>
                      <small>{{ getTeacherPreset(room.id) }}</small>
                    </span>
                    <span
                      class="capacity"
                      :class="{ full: isLessonFull(lesson) }"
                    >
                      {{ getPresentStudentCount(lesson) }}/{{ getLessonCapacity(lesson) }}
                    </span>
                  </button>

                  <div class="student-list">
                    <div
                      v-for="student in getVisibleStudents(lesson)"
                      :key="`${lesson.id}-${student.type}-${student.id || student.name}`"
                      class="student-row"
                      :class="`student-${student.type}`"
                    >
                      <button
                        type="button"
                        class="student-main"
                        :title="getStudentHoverText(lesson, student)"
                        @click="toDetailPage(lesson)"
                      >
                        <span>{{ student.name }}</span>
                        <small v-if="student.badge">{{ student.badge }}</small>
                      </button>
                      <button
                        type="button"
                        class="note-button"
                        :class="{ 'has-note': !!getStudentNote(lesson, student) }"
                        :title="getStudentNote(lesson, student) || 'Add note'"
                        @click="openNote(lesson, student)"
                      >
                        <edit-outlined />
                      </button>
                    </div>
                    <span v-if="!getVisibleStudents(lesson).length" class="no-students">
                      No students
                    </span>
                  </div>
                </article>
              </template>
            </div>
          </template>
        </div>
      </div>

      <a-modal
        v-model:visible="noteModal.visible"
        title="Student note"
        ok-text="Save"
        cancel-text="Cancel"
        :confirm-loading="noteModal.saving"
        @ok="saveStudentNote"
      >
        <div class="note-context">
          <strong>{{ noteModal.studentName }}</strong>
          <span>{{ noteModal.className }} · {{ selectedDate.format('MMM D, YYYY') }}</span>
        </div>
        <a-textarea
          v-model:value="noteModal.note"
          :rows="5"
          :maxlength="1000"
          show-count
          placeholder="Add a note for this student and class date"
        />
      </a-modal>
    </div>
  </a-config-provider>
</template>

<script lang="ts" setup>
import { EditOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import enUS from 'ant-design-vue/es/locale/en_US';
import dayjs, { Dayjs } from 'dayjs';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { listApi as listLessonsApi } from '/@/api/admin/lesson';
import { listApi as listNotesApi, saveApi as saveNoteApi } from '/@/api/admin/student-lesson-note';
import { listApi as listRoomsApi } from '/@/api/admin/tag';
import { listApi as listTimesApi } from '/@/api/admin/time';
import { ADMIN_USER_ID } from '/@/store/constants';

interface RoomItem {
  id: number;
  title: string;
  seat?: number | string;
}

interface TimeItem {
  id: number;
  time: string;
}

interface ScheduleStudent {
  order_id: number;
  student_id: number;
  name: string;
  term_id: number;
  term_title: string;
  expect_time: string;
  return_time: string;
  status: number;
}

interface AdjustmentStudent {
  adjustment_id: number;
  student_id: number;
  name: string;
  date: string;
  term_id?: number;
  term_title?: string;
}

interface TrialStudent {
  trial_request_id: number;
  student_id: number;
  order_id?: number;
  name: string;
  date: string;
}

interface LessonItem {
  id: number;
  lesson_id?: number;
  thing: number;
  thing_id?: number;
  class_name?: string;
  day?: string;
  time?: string;
  room_id?: number;
  room_name?: string;
  room_capacity?: number | string;
  scheduled_students?: ScheduleStudent[];
  canceled_students?: AdjustmentStudent[];
  scheduled_reschedule_students?: AdjustmentStudent[];
  scheduled_trial_students?: TrialStudent[];
}

interface DisplayStudent {
  id?: number;
  studentId: number;
  name: string;
  type: 'normal' | 'canceled' | 'rescheduled' | 'trial';
  badge?: string;
  title?: string;
}

const dayCodes = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const weekendDayCodes = new Set(['Sat', 'Sun']);
const teacherNames = [
  'Teacher A',
  'Teacher B',
  'Teacher C',
  'Teacher D',
  'Teacher E',
  'Teacher F',
  'Teacher G',
  'Teacher H',
];
const lessonColorPalette = [
  { bg: '#f6ffed', border: '#95de64', text: '#135200' },
  { bg: '#e6f4ff', border: '#69b1ff', text: '#003a8c' },
  { bg: '#fff7e6', border: '#ffc069', text: '#873800' },
  { bg: '#f9f0ff', border: '#b37feb', text: '#391085' },
  { bg: '#e6fffb', border: '#5cdbd3', text: '#006d75' },
  { bg: '#fff1f0', border: '#ff7875', text: '#a8071a' },
];

const router = useRouter();
const selectedDate = ref<Dayjs>(dayjs());
const studentKeyword = ref('');
const lessons = ref<LessonItem[]>([]);
const rooms = ref<RoomItem[]>([]);
const timeSlots = ref<TimeItem[]>([]);
const loading = ref(false);
const initialized = ref(false);
const studentNotes = ref<Record<string, string>>({});
const noteModal = reactive({
  visible: false,
  saving: false,
  lessonId: 0,
  studentId: 0,
  studentName: '',
  className: '',
  note: '',
});
const staffAnnouncement = ref(
  'Please review your classroom assignment and student changes before the first lesson.'
);

const visibleDates = computed(() => {
  const daysSinceSaturday = (selectedDate.value.day() + 1) % 7;
  const saturday = selectedDate.value.subtract(daysSinceSaturday, 'day');
  return Array.from({ length: 7 }, (_, offset) => saturday.add(offset, 'day'));
});

const boardGridStyle = computed(() => ({
  gridTemplateColumns: `96px repeat(${rooms.value.length}, minmax(230px, 1fr))`,
}));

const displayedTimeSlots = computed(() => {
  const dayCode = selectedDayCode.value;
  return timeSlots.value.filter((slot) => {
    const minutes = getTimeMinutes(slot.time);
    if (dayCode === 'Mon') {
      return false;
    }
    if (weekendDayCodes.has(dayCode)) {
      return minutes >= 9 * 60 && minutes < 18 * 60 && minutes !== 12 * 60;
    }
    return minutes >= 16 * 60 && minutes < 20 * 60;
  });
});

onMounted(async () => {
  loading.value = true;
  try {
    const [roomResponse, timeResponse] = await Promise.all([
      listRoomsApi({}),
      listTimesApi({}),
    ]);
    rooms.value = [...(roomResponse.data || [])].sort((a, b) =>
      String(a.title || '').localeCompare(String(b.title || ''), undefined, { numeric: true })
    );
    timeSlots.value = [...(timeResponse.data || [])].sort((a, b) =>
      getTimeMinutes(a.time) - getTimeMinutes(b.time)
    );
    await loadSelectedDate();
    initialized.value = true;
  } finally {
    loading.value = false;
  }
});

watch(
  () => selectedDate.value.format('YYYY-MM-DD'),
  () => {
    if (initialized.value) {
      loadSelectedDate();
    }
  }
);

const loadSelectedDate = async () => {
  loading.value = true;
  try {
    if (selectedDayCode.value === 'Mon') {
      lessons.value = [];
      loadStudentNotes();
      return;
    }
    const lessonResponse = await listLessonsApi({
      date: selectedDate.value.format('YYYY-MM-DD'),
    });
    lessons.value = lessonResponse.data || [];
    loadStudentNotes();
  } catch (error) {
    lessons.value = [];
    console.log(error);
  } finally {
    loading.value = false;
  }
};

const getTimeMinutes = (value?: string) => {
  const match = String(value || '').match(/^(\d{1,2}):?(\d{2})?/);
  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }
  return Number(match[1]) * 60 + Number(match[2] || 0);
};

const selectedDayCode = computed(() => dayCodes[selectedDate.value.day()]);

const getCellLessons = (roomId: number, timeId: number) => {
  return lessons.value
    .filter((lesson) => lesson.day === selectedDayCode.value)
    .filter((lesson) => Number(lesson.room_id) === Number(roomId))
    .filter((lesson) => {
      const slot = timeSlots.value.find((item) => Number(item.id) === Number(timeId));
      return slot && lesson.time === slot.time;
    })
    .filter((lesson) => matchesStudentSearch(lesson))
    .sort((a, b) => String(a.class_name || '').localeCompare(String(b.class_name || '')));
};

const isStudentActiveOnDate = (student: ScheduleStudent) => {
  const start = dayjs(student.expect_time).startOf('day');
  const end = dayjs(student.return_time).endOf('day');
  return selectedDate.value.isSame(start, 'day') ||
    selectedDate.value.isSame(end, 'day') ||
    (selectedDate.value.isAfter(start) && selectedDate.value.isBefore(end));
};

const isAdjustmentOnSelectedDate = (date?: string) => {
  return !!date && dayjs(date).isSame(selectedDate.value, 'day');
};

const getDisplayStudents = (lesson: LessonItem): DisplayStudent[] => {
  const canceled = (lesson.canceled_students || [])
    .filter((student) => isAdjustmentOnSelectedDate(student.date));
  const canceledNames = new Set(canceled.map((student) => student.name));

  const normalStudents: DisplayStudent[] = (lesson.scheduled_students || [])
    .filter(isStudentActiveOnDate)
    .filter((student) => !canceledNames.has(student.name))
    .map((student) => ({
      id: student.order_id,
      studentId: student.student_id,
      name: student.name,
      type: 'normal',
      title: student.term_title,
    }));

  const canceledStudents: DisplayStudent[] = canceled.map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'canceled',
    badge: 'Absent',
    title: student.term_title,
  }));

  const rescheduledStudents: DisplayStudent[] = (lesson.scheduled_reschedule_students || [])
    .filter((student) => isAdjustmentOnSelectedDate(student.date))
    .map((student) => ({
      id: student.adjustment_id,
      studentId: student.student_id,
      name: student.name,
      type: 'rescheduled',
      badge: 'Makeup',
      title: student.term_title,
    }));

  const trialStudents: DisplayStudent[] = (lesson.scheduled_trial_students || [])
    .filter((student) => isAdjustmentOnSelectedDate(student.date))
    .map((student) => ({
      id: student.trial_request_id,
      studentId: student.student_id,
      name: student.name,
      type: 'trial',
      badge: 'Trial',
    }));

  return [
    ...normalStudents,
    ...canceledStudents,
    ...rescheduledStudents,
    ...trialStudents,
  ].sort((a, b) => a.name.localeCompare(b.name));
};

const getVisibleStudents = (lesson: LessonItem) => {
  const keyword = studentKeyword.value.trim().toLowerCase();
  const students = getDisplayStudents(lesson);
  if (!keyword) {
    return students;
  }
  return students.filter((student) => student.name.toLowerCase().includes(keyword));
};

const matchesStudentSearch = (lesson: LessonItem) => {
  const keyword = studentKeyword.value.trim().toLowerCase();
  return !keyword || getDisplayStudents(lesson).some((student) =>
    student.name.toLowerCase().includes(keyword)
  );
};

const getLessonCapacity = (lesson: LessonItem) => {
  const capacity = Number(lesson.room_capacity);
  return Number.isFinite(capacity) && capacity > 0 ? capacity : 0;
};

const getPresentStudentCount = (lesson: LessonItem) => {
  return getDisplayStudents(lesson).filter((student) => student.type !== 'canceled').length;
};

const isLessonFull = (lesson: LessonItem) => {
  const capacity = getLessonCapacity(lesson);
  return capacity > 0 && getPresentStudentCount(lesson) >= capacity;
};

const getTeacherPreset = (roomId: number) => {
  const roomIndex = Math.max(rooms.value.findIndex((room) => room.id === roomId), 0);
  return teacherNames[roomIndex % teacherNames.length];
};

const noteKey = (lessonId: number, studentId: number) => `${lessonId}:${studentId}`;

const getStudentNote = (lesson: LessonItem, student: DisplayStudent) => {
  return studentNotes.value[noteKey(lesson.lesson_id || lesson.id, student.studentId)] || '';
};

const getStudentHoverText = (lesson: LessonItem, student: DisplayStudent) => {
  const details = [];
  if (student.title) {
    details.push(`Term: ${student.title}`);
  }
  const note = getStudentNote(lesson, student);
  if (note) {
    details.push(`Note: ${note}`);
  }
  return details.join('\n') || student.name;
};

const loadStudentNotes = async () => {
  try {
    const response = await listNotesApi({
      date: selectedDate.value.format('YYYY-MM-DD'),
    });
    const nextNotes: Record<string, string> = {};
    (response.data || []).forEach((note: any) => {
      nextNotes[noteKey(Number(note.lesson), Number(note.student))] = note.note || '';
    });
    studentNotes.value = nextNotes;
  } catch (error) {
    studentNotes.value = {};
    console.log(error);
  }
};

const openNote = (lesson: LessonItem, student: DisplayStudent) => {
  noteModal.lessonId = Number(lesson.lesson_id || lesson.id);
  noteModal.studentId = student.studentId;
  noteModal.studentName = student.name;
  noteModal.className = lesson.class_name || 'Untitled class';
  noteModal.note = getStudentNote(lesson, student);
  noteModal.visible = true;
};

const saveStudentNote = async () => {
  noteModal.saving = true;
  try {
    await saveNoteApi({
      lesson_id: noteModal.lessonId,
      student_id: noteModal.studentId,
      lesson_date: selectedDate.value.format('YYYY-MM-DD'),
      note: noteModal.note,
      admin_user_id: localStorage.getItem(ADMIN_USER_ID),
    });
    studentNotes.value[noteKey(noteModal.lessonId, noteModal.studentId)] = noteModal.note.trim();
    noteModal.visible = false;
    message.success('Student note saved');
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save student note');
  } finally {
    noteModal.saving = false;
  }
};

const getLessonColorStyle = (lesson: LessonItem) => {
  const colorKey = Number(lesson.thing_id || lesson.thing || lesson.id || 0);
  const color = lessonColorPalette[colorKey % lessonColorPalette.length];
  return {
    '--lesson-bg': color.bg,
    '--lesson-border': color.border,
    '--lesson-text': color.text,
  };
};

const toDetailPage = (lesson: LessonItem) => {
  const thingId = lesson.thing_id || lesson.thing;
  const lessonId = lesson.lesson_id || lesson.id;
  if (!thingId) {
    return;
  }
  router.push({
    name: 'lesson',
    query: {
      id: thingId,
      lessonId,
      date: selectedDate.value.format('YYYY-MM-DD'),
    },
  });
};

const selectPreviousDay = () => {
  selectedDate.value = selectedDate.value.subtract(1, 'day');
};

const selectToday = () => {
  selectedDate.value = dayjs();
};

const selectNextDay = () => {
  selectedDate.value = selectedDate.value.add(1, 'day');
};
</script>

<style scoped>
.page-view {
  min-height: 100%;
  padding: 24px;
  background: #fff;
  color: #101828;
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
  font-weight: 700;
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

.student-search {
  width: 220px;
}

.announcement {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-top: 18px;
  border: 1px solid #b2ccff;
  border-left: 4px solid #2970ff;
  border-radius: 6px;
  background: #eff8ff;
  padding: 12px 14px;
}

.announcement-icon {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: #2970ff;
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 800;
}

.announcement strong {
  color: #1849a9;
  font-size: 13px;
}

.announcement p {
  margin: 2px 0 0;
  color: #344054;
  font-size: 13px;
}

.date-picker-band {
  display: flex;
  gap: 8px;
  margin-top: 18px;
  padding: 4px 2px 10px;
  overflow-x: auto;
  scrollbar-width: thin;
}

.date-option {
  flex: 0 0 72px;
  min-height: 72px;
  border: 1px solid #d0d5dd;
  border-radius: 6px;
  background: #fff;
  color: #344054;
  cursor: pointer;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 1px;
}

.date-option:hover {
  border-color: #1570ef;
}

.date-option.selected {
  border-color: #1570ef;
  background: #eff8ff;
  color: #175cd3;
  box-shadow: inset 0 -3px 0 #1570ef;
}

.date-option.today:not(.selected) {
  border-color: #84adff;
}

.date-option strong {
  font-size: 22px;
  line-height: 24px;
}

.date-weekday,
.date-month {
  font-size: 11px;
  line-height: 14px;
}

.legend {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  margin: 8px 0 14px;
  color: #475467;
  font-size: 12px;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.legend-dot.normal {
  background: #667085;
}

.legend-dot.canceled {
  background: #d92d20;
}

.legend-dot.rescheduled {
  background: #1570ef;
}

.legend-dot.trial {
  background: #7f56d9;
}

.schedule-scroll {
  overflow: auto;
  border: 1px solid #d0d5dd;
  border-radius: 7px;
  max-height: calc(100vh - 260px);
}

.daily-board {
  display: grid;
  min-width: max-content;
}

.time-header,
.room-header {
  position: sticky;
  top: 0;
  z-index: 5;
  min-height: 68px;
  padding: 13px 12px;
  border-right: 1px solid #d0d5dd;
  border-bottom: 1px solid #d0d5dd;
  background: #f2f4f7;
}

.time-header {
  left: 0;
  z-index: 7;
  color: #667085;
  font-weight: 700;
}

.room-header strong,
.room-header span,
.room-header small {
  display: block;
}

.room-header strong {
  font-size: 15px;
}

.room-header span {
  margin-top: 4px;
  color: #175cd3;
  font-size: 12px;
  font-weight: 600;
}

.room-header small {
  margin-top: 2px;
  color: #667085;
  font-size: 11px;
}

.time-cell {
  position: sticky;
  left: 0;
  z-index: 4;
  min-height: 146px;
  padding: 14px 10px;
  border-right: 1px solid #d0d5dd;
  border-bottom: 1px solid #d0d5dd;
  background: #f9fafb;
  color: #475467;
  font-size: 12px;
  font-weight: 700;
}

.schedule-cell {
  min-height: 146px;
  padding: 8px;
  border-right: 1px solid #e4e7ec;
  border-bottom: 1px solid #e4e7ec;
  background: #fff;
}

.schedule-cell.empty-cell {
  background: #fcfcfd;
}

.lesson-block {
  border: 1px solid var(--lesson-border);
  border-radius: 6px;
  background: var(--lesson-bg);
  color: var(--lesson-text);
  overflow: hidden;
}

.lesson-block + .lesson-block {
  margin-top: 8px;
}

.lesson-heading {
  width: 100%;
  min-height: 46px;
  padding: 7px 8px;
  border: 0;
  border-bottom: 1px solid color-mix(in srgb, var(--lesson-border) 58%, transparent);
  background: transparent;
  color: inherit;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  text-align: left;
}

.lesson-heading strong,
.lesson-heading small {
  display: inline;
}

.lesson-heading strong {
  font-size: 13px;
  line-height: 17px;
}

.lesson-heading small {
  margin-left: 6px;
  color: #475467;
  font-size: 11px;
}

.lesson-title-line {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.capacity {
  flex: 0 0 auto;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.76);
  padding: 2px 5px;
  color: #344054;
  font-size: 11px;
  font-weight: 700;
}

.capacity.full {
  color: #b42318;
}

.student-list {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 5px;
  padding: 7px;
}

.student-row {
  min-width: 0;
  min-height: 30px;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.78);
  color: #344054;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.student-main {
  min-width: 0;
  flex: 1 1 auto;
  min-height: 30px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 4px 7px;
  text-align: left;
}

.student-main span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.student-main small {
  flex: 0 0 auto;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
}

.note-button {
  flex: 0 0 30px;
  width: 30px;
  height: 30px;
  border: 0;
  border-left: 1px solid rgba(152, 162, 179, 0.45);
  background: rgba(255, 255, 255, 0.52);
  color: #667085;
  cursor: pointer;
}

.note-button:hover,
.note-button.has-note {
  background: #fff4e5;
  color: #b54708;
}

.student-canceled {
  border-color: #fda29b;
  background: #fef3f2;
  color: #b42318;
  text-decoration: line-through;
}

.student-rescheduled {
  border-color: #84adff;
  background: #eff8ff;
  color: #175cd3;
}

.student-trial {
  border-color: #d6bbfb;
  background: #f9f5ff;
  color: #6941c6;
}

.note-context {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 14px;
}

.note-context span {
  color: #667085;
  font-size: 12px;
}

.no-students,
.board-message {
  color: #98a2b3;
  font-size: 12px;
}

.board-message {
  padding: 48px;
  border: 1px dashed #d0d5dd;
  border-radius: 7px;
  text-align: center;
}

@media (max-width: 760px) {
  .page-view {
    padding: 16px;
  }

  .schedule-actions,
  .student-search {
    width: 100%;
  }

  .schedule-scroll {
    max-height: calc(100vh - 300px);
  }
}
</style>
