<template>
  <a-config-provider :locale="enUS">
    <div class="page-view">
      <header class="schedule-toolbar">
        <div class="schedule-title">
          <h2>Daily Schedule</h2>
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
          <a-date-picker
            :value="selectedDate"
            picker="week"
            :allow-clear="false"
            class="week-picker"
            format="[Week of] MMM D, YYYY"
            @change="selectWeek"
          />
          <a-button
            v-if="!adjustmentMode"
            type="primary"
            @click="enterAdjustmentMode"
          >
            <tool-outlined />
            Manual Adjustment
          </a-button>
        </div>
      </header>

      <section v-if="adjustmentMode" class="adjustment-toolbar">
        <div class="adjustment-mode">
          <strong>Manual adjustment</strong>
          <a-radio-group v-model:value="adjustmentScope" size="small">
            <a-radio-button value="date">This date only</a-radio-button>
            <a-radio-button value="future">All future classes</a-radio-button>
          </a-radio-group>
          <span v-if="adjustmentScope === 'date'">{{ draftActions.length }} unsaved change(s)</span>
          <span v-else>Permanent change from a selected effective date</span>
        </div>
        <div class="adjustment-actions">
          <a-button :disabled="!draftActions.length" @click="undoLastDraft">
            <undo-outlined /> Undo
          </a-button>
          <a-button :disabled="!draftActions.length" @click="discardDrafts">
            Discard
          </a-button>
          <a-button
            v-if="adjustmentScope === 'date' && savedAdjustments.length"
            danger
            @click="revertLastSaved"
          >
            Revert last saved
          </a-button>
          <a-button
            v-if="adjustmentScope === 'future' && permanentChanges.length"
            danger
            @click="revertLastPermanent"
          >
            Revert last permanent
          </a-button>
          <a-button
            v-if="adjustmentScope === 'date'"
            type="primary"
            :loading="savingAdjustments"
            :disabled="!draftActions.length"
            @click="saveAdjustments"
          >
            <save-outlined /> Save changes
          </a-button>
          <a-button @click="exitAdjustmentMode">Exit</a-button>
        </div>
      </section>

      <section class="announcement" aria-label="Staff announcement">
        <div class="announcement-icon">A</div>
        <strong>Staff announcement:</strong>
        <p>{{ staffAnnouncement }}</p>
      </section>

      <div class="schedule-workspace">
        <aside class="date-picker-rail" aria-label="Choose schedule date">
          <div class="selected-date-label">
            <strong>{{ selectedDate.format('MMM D') }}</strong>
            <span>{{ selectedDate.format('YYYY') }}</span>
          </div>
          <button
            v-for="date in visibleDates"
            :key="date.format('YYYY-MM-DD')"
            type="button"
            class="date-option"
            :class="{ selected: date.isSame(selectedDate, 'day'), today: date.isSame(dayjs(), 'day') }"
            @click="selectDate(date)"
          >
            <span class="date-weekday">{{ date.format('ddd') }}</span>
            <strong>{{ date.format('D') }}</strong>
          </button>
        </aside>

        <div class="schedule-main">
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
              <div
                v-for="room in rooms"
                :key="`room-${room.id}`"
                class="room-header"
                :style="getRoomColorStyle(room.id)"
              >
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
                      :class="{
                        'drop-target': adjustmentMode,
                        'drop-ready': canAcceptDrop(lesson),
                        'drop-blocked': adjustmentMode && draggedStudent && !canAcceptDrop(lesson),
                      }"
                      :style="getLessonColorStyle(lesson)"
                      :title="getDropTargetTitle(lesson)"
                      @dragenter.prevent
                      @dragover.prevent
                      @drop="dropStudent(lesson)"
                    >
                      <button
                        type="button"
                        class="lesson-heading"
                        @click="adjustmentMode && draggedStudent ? dropStudent(lesson) : toDetailPage(lesson)"
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
                          :class="[
                            `student-${student.type}`,
                            {
                              draggable: canDragStudent(student),
                              'selected-for-move': isSelectedStudent(lesson, student),
                            },
                          ]"
                        >
                          <span
                            v-if="canDragStudent(student)"
                            class="drag-handle"
                            draggable="true"
                            title="Drag, or click then choose a target class"
                            @click.stop="selectStudentForMove(lesson, student)"
                            @dragstart.stop="startStudentDrag($event, lesson, student)"
                            @dragend="draggedStudent = null"
                          >
                            <HolderOutlined />
                          </span>
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
                            v-if="adjustmentMode && student.type === 'normal'"
                            type="button"
                            class="sick-button"
                            title="Mark sick leave"
                            @click="openSickLeave(lesson, student)"
                          >
                            <medicine-box-outlined />
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

      <a-modal
        v-model:visible="permanentModal.visible"
        title="Permanent course change"
        ok-text="Confirm permanent change"
        cancel-text="Cancel"
        :confirm-loading="permanentModal.saving"
        @ok="savePermanentChange"
      >
        <div class="note-context">
          <strong>{{ permanentModal.studentName }}</strong>
          <span>Current class: {{ permanentModal.sourceClass }}</span>
        </div>
        <a-form layout="vertical">
          <a-form-item label="Effective date">
            <a-date-picker
              v-model:value="permanentModal.effectiveDate"
              :allow-clear="false"
              style="width: 100%"
              @change="loadPermanentOptions"
            />
          </a-form-item>
          <a-form-item label="New recurring class">
            <a-select
              v-model:value="permanentModal.targetLessonId"
              show-search
              option-filter-prop="label"
              placeholder="Select the new class"
              :loading="permanentModal.loadingOptions"
              :options="permanentModal.options"
            />
          </a-form-item>
          <a-form-item label="Reason">
            <a-textarea
              v-model:value="permanentModal.reason"
              :rows="3"
              :maxlength="500"
              placeholder="Reason for the permanent change"
            />
          </a-form-item>
        </a-form>
      </a-modal>

      <a-modal
        v-model:visible="sickModal.visible"
        title="Mark sick leave"
        ok-text="Add to changes"
        cancel-text="Cancel"
        @ok="addSickLeaveDraft"
      >
        <div class="note-context">
          <strong>{{ sickModal.studentName }}</strong>
          <span>{{ sickModal.className }} · {{ selectedDate.format('MMM D, YYYY') }}</span>
        </div>
        <a-textarea
          v-model:value="sickModal.reason"
          :rows="3"
          placeholder="Reason or internal note"
        />
        <a-checkbox v-model:checked="sickModal.deductLesson" class="deduct-option">
          Deduct 1 lesson from the student's remaining lesson count
        </a-checkbox>
      </a-modal>
    </div>
  </a-config-provider>
</template>

<script lang="ts" setup>
import {
  EditOutlined,
  HolderOutlined,
  MedicineBoxOutlined,
  SaveOutlined,
  ToolOutlined,
  UndoOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import enUS from 'ant-design-vue/es/locale/en_US';
import dayjs, { Dayjs } from 'dayjs';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { listApi as listLessonsApi } from '/@/api/admin/lesson';
import {
  listApi as listAdjustmentsApi,
  revertApi as revertAdjustmentApi,
  saveBatchApi,
} from '/@/api/admin/daily-adjustment';
import {
  createApi as createPermanentApi,
  listApi as listPermanentApi,
  optionsApi as permanentOptionsApi,
  revertApi as revertPermanentApi,
} from '/@/api/admin/permanent-course-change';
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
  reason?: string;
  lesson_count_delta?: number;
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
  moved_students?: AdjustmentStudent[];
  sick_leave_students?: AdjustmentStudent[];
}

interface DisplayStudent {
  id?: number;
  studentId: number;
  name: string;
  type: 'normal' | 'canceled' | 'rescheduled' | 'trial' | 'moved' | 'sick';
  badge?: string;
  title?: string;
}

interface DraftAction {
  type: 'move' | 'sick_leave';
  student_id: number;
  student_name: string;
  source_lesson_id: number;
  source_class: string;
  target_lesson_id?: number;
  target_class?: string;
  reason?: string;
  deduct_lesson?: boolean;
  term_title?: string;
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

const router = useRouter();
const route = useRoute();
const routeDate = String(route.query.date || '');
const selectedDate = ref<Dayjs>(
  routeDate && dayjs(routeDate).isValid() ? dayjs(routeDate) : dayjs(),
);
const studentKeyword = ref('');
const lessons = ref<LessonItem[]>([]);
const rooms = ref<RoomItem[]>([]);
const timeSlots = ref<TimeItem[]>([]);
const loading = ref(false);
const initialized = ref(false);
const studentNotes = ref<Record<string, string>>({});
const adjustmentMode = ref(false);
const adjustmentScope = ref('date');
const draftActions = ref<DraftAction[]>([]);
const savedAdjustments = ref<any[]>([]);
const permanentChanges = ref<any[]>([]);
const savingAdjustments = ref(false);
const draggedStudent = ref<{ lesson: LessonItem; student: DisplayStudent } | null>(null);
const noteModal = reactive({
  visible: false,
  saving: false,
  lessonId: 0,
  studentId: 0,
  studentName: '',
  className: '',
  note: '',
});
const sickModal = reactive({
  visible: false,
  lessonId: 0,
  studentId: 0,
  studentName: '',
  className: '',
  termTitle: '',
  reason: '',
  deductLesson: false,
});
const permanentModal = reactive({
  visible: false,
  saving: false,
  loadingOptions: false,
  studentId: 0,
  studentName: '',
  sourceLessonId: 0,
  sourceClass: '',
  effectiveDate: dayjs(),
  targetLessonId: undefined as number | undefined,
  reason: '',
  options: [] as Array<{ value: number; label: string }>,
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
    loadSavedAdjustments();
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

  const movedStudents: DisplayStudent[] = (lesson.moved_students || []).map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'moved',
    badge: 'Moved',
    title: student.term_title,
  }));

  const sickStudents: DisplayStudent[] = (lesson.sick_leave_students || []).map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'sick',
    badge: 'Sick leave',
    title: student.term_title,
  }));

  const lessonId = Number(lesson.lesson_id || lesson.id);
  const movedOutIds = new Set(
    draftActions.value
      .filter((action) => action.source_lesson_id === lessonId)
      .map((action) => action.student_id)
  );
  const draftMovedIn: DisplayStudent[] = draftActions.value
    .filter((action) => action.type === 'move' && action.target_lesson_id === lessonId)
    .map((action) => ({
      id: action.student_id,
      studentId: action.student_id,
      name: action.student_name,
      type: 'moved',
      badge: 'Moved draft',
      title: action.term_title,
    }));
  const draftSick: DisplayStudent[] = draftActions.value
    .filter((action) => action.type === 'sick_leave' && action.source_lesson_id === lessonId)
    .map((action) => ({
      id: action.student_id,
      studentId: action.student_id,
      name: action.student_name,
      type: 'sick',
      badge: 'Sick draft',
      title: action.term_title,
    }));

  return [
    ...normalStudents.filter((student) => !movedOutIds.has(student.studentId)),
    ...canceledStudents,
    ...rescheduledStudents,
    ...trialStudents,
    ...movedStudents,
    ...sickStudents,
    ...draftMovedIn,
    ...draftSick,
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
  return getDisplayStudents(lesson).filter(
    (student) => !['canceled', 'sick'].includes(student.type)
  ).length;
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

const loadSavedAdjustments = async () => {
  try {
    const response = await listAdjustmentsApi({
      date: selectedDate.value.format('YYYY-MM-DD'),
    });
    savedAdjustments.value = response.data || [];
  } catch (error) {
    savedAdjustments.value = [];
    console.log(error);
  }
};

const enterAdjustmentMode = () => {
  adjustmentMode.value = true;
  adjustmentScope.value = 'date';
  loadPermanentChanges();
};

const exitAdjustmentMode = () => {
  if (draftActions.value.length) {
    message.warning('Save or discard unsaved changes before exiting');
    return;
  }
  adjustmentMode.value = false;
};

const canDragStudent = (student: DisplayStudent) => {
  return adjustmentMode.value && student.type === 'normal';
};

const isSelectedStudent = (lesson: LessonItem, student: DisplayStudent) => {
  if (!draggedStudent.value) {
    return false;
  }
  const selectedLessonId = Number(
    draggedStudent.value.lesson.lesson_id || draggedStudent.value.lesson.id,
  );
  const lessonId = Number(lesson.lesson_id || lesson.id);
  return selectedLessonId === lessonId && draggedStudent.value.student.studentId === student.studentId;
};

const selectStudentForMove = (lesson: LessonItem, student: DisplayStudent) => {
  if (!canDragStudent(student)) {
    return;
  }
  if (adjustmentScope.value === 'future') {
    openPermanentChange(lesson, student);
    return;
  }
  if (isSelectedStudent(lesson, student)) {
    draggedStudent.value = null;
    return;
  }
  draggedStudent.value = { lesson, student };
  message.info(`${student.name} selected. Click a target class or drag the handle.`);
};

const canAcceptDrop = (targetLesson: LessonItem) => {
  const dragged = draggedStudent.value;
  if (!adjustmentMode.value || !dragged) {
    return false;
  }
  const sourceLessonId = Number(dragged.lesson.lesson_id || dragged.lesson.id);
  const targetLessonId = Number(targetLesson.lesson_id || targetLesson.id);
  if (sourceLessonId === targetLessonId) {
    return false;
  }
  if (draftActions.value.some((action) => action.student_id === dragged.student.studentId)) {
    return false;
  }
  const capacity = getLessonCapacity(targetLesson);
  return capacity <= 0 || getPresentStudentCount(targetLesson) < capacity;
};

const getDropTargetTitle = (targetLesson: LessonItem) => {
  const dragged = draggedStudent.value;
  if (!adjustmentMode.value || !dragged) {
    return '';
  }
  const sourceLessonId = Number(dragged.lesson.lesson_id || dragged.lesson.id);
  const targetLessonId = Number(targetLesson.lesson_id || targetLesson.id);
  if (sourceLessonId === targetLessonId) {
    return 'This is the current class';
  }
  if (draftActions.value.some((action) => action.student_id === dragged.student.studentId)) {
    return 'This student already has an unsaved adjustment';
  }
  const capacity = getLessonCapacity(targetLesson);
  if (capacity > 0 && getPresentStudentCount(targetLesson) >= capacity) {
    return 'This class is full';
  }
  return 'Release to move the student here';
};

const startStudentDrag = (event: DragEvent, lesson: LessonItem, student: DisplayStudent) => {
  if (!canDragStudent(student)) {
    return;
  }
  if (adjustmentScope.value === 'future') {
    event.preventDefault();
    openPermanentChange(lesson, student);
    return;
  }
  event.dataTransfer?.setData('text/plain', String(student.studentId));
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
  }
  draggedStudent.value = { lesson, student };
};

const dropStudent = (targetLesson: LessonItem) => {
  const dragged = draggedStudent.value;
  if (!adjustmentMode.value || !dragged) {
    return;
  }
  const sourceLessonId = Number(dragged.lesson.lesson_id || dragged.lesson.id);
  const targetLessonId = Number(targetLesson.lesson_id || targetLesson.id);
  if (sourceLessonId === targetLessonId) {
    message.warning('Choose a different class');
    return;
  }
  if (draftActions.value.some((action) => action.student_id === dragged.student.studentId)) {
    message.warning('This student already has an unsaved adjustment');
    return;
  }
  if (getPresentStudentCount(targetLesson) >= getLessonCapacity(targetLesson)) {
    message.error('Target class is full');
    return;
  }
  draftActions.value.push({
    type: 'move',
    student_id: dragged.student.studentId,
    student_name: dragged.student.name,
    source_lesson_id: sourceLessonId,
    source_class: dragged.lesson.class_name || 'Untitled class',
    target_lesson_id: targetLessonId,
    target_class: targetLesson.class_name || 'Untitled class',
    term_title: dragged.student.title,
  });
  draggedStudent.value = null;
};

const openSickLeave = (lesson: LessonItem, student: DisplayStudent) => {
  if (draftActions.value.some((action) => action.student_id === student.studentId)) {
    message.warning('This student already has an unsaved adjustment');
    return;
  }
  sickModal.lessonId = Number(lesson.lesson_id || lesson.id);
  sickModal.studentId = student.studentId;
  sickModal.studentName = student.name;
  sickModal.className = lesson.class_name || 'Untitled class';
  sickModal.termTitle = student.title || '';
  sickModal.reason = '';
  sickModal.deductLesson = false;
  sickModal.visible = true;
};

const addSickLeaveDraft = () => {
  draftActions.value.push({
    type: 'sick_leave',
    student_id: sickModal.studentId,
    student_name: sickModal.studentName,
    source_lesson_id: sickModal.lessonId,
    source_class: sickModal.className,
    reason: sickModal.reason,
    deduct_lesson: sickModal.deductLesson,
    term_title: sickModal.termTitle,
  });
  sickModal.visible = false;
};

const undoLastDraft = () => {
  draftActions.value.pop();
};

const discardDrafts = () => {
  draftActions.value = [];
};

const saveAdjustments = async () => {
  savingAdjustments.value = true;
  try {
    await saveBatchApi({
      lesson_date: selectedDate.value.format('YYYY-MM-DD'),
      actions: JSON.stringify(draftActions.value),
    });
    draftActions.value = [];
    message.success('Daily adjustments saved');
    await loadSelectedDate();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save adjustments');
  } finally {
    savingAdjustments.value = false;
  }
};

const revertLastSaved = async () => {
  const record = savedAdjustments.value[savedAdjustments.value.length - 1];
  if (!record) {
    return;
  }
  try {
    await revertAdjustmentApi({ id: record.id });
    message.success('Last saved adjustment reverted');
    await loadSelectedDate();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to revert adjustment');
  }
};

const loadPermanentChanges = async () => {
  try {
    const response = await listPermanentApi();
    permanentChanges.value = response.data || [];
  } catch (error) {
    permanentChanges.value = [];
  }
};

const openPermanentChange = (lesson: LessonItem, student: DisplayStudent) => {
  permanentModal.studentId = student.studentId;
  permanentModal.studentName = student.name;
  permanentModal.sourceLessonId = Number(lesson.lesson_id || lesson.id);
  permanentModal.sourceClass = lesson.class_name || 'Untitled class';
  permanentModal.effectiveDate = selectedDate.value;
  permanentModal.targetLessonId = undefined;
  permanentModal.reason = '';
  permanentModal.options = [];
  permanentModal.visible = true;
  loadPermanentOptions();
};

const loadPermanentOptions = async () => {
  if (!permanentModal.studentId || !permanentModal.sourceLessonId) {
    return;
  }
  permanentModal.loadingOptions = true;
  permanentModal.targetLessonId = undefined;
  try {
    const response = await permanentOptionsApi({
      student_id: permanentModal.studentId,
      source_lesson_id: permanentModal.sourceLessonId,
      effective_date: permanentModal.effectiveDate.format('YYYY-MM-DD'),
    });
    permanentModal.options = (response.data || []).map((option: any) => ({
      value: option.lesson_id,
      label: `${option.class_name} | ${option.day} ${option.time} | ${option.room} | first ${option.first_class_date}`,
    }));
  } catch (error: any) {
    permanentModal.options = [];
    message.error(error?.msg || 'Failed to load available classes');
  } finally {
    permanentModal.loadingOptions = false;
  }
};

const savePermanentChange = async () => {
  if (!permanentModal.targetLessonId) {
    message.warning('Select the new recurring class');
    return;
  }
  permanentModal.saving = true;
  try {
    await createPermanentApi({
      student_id: permanentModal.studentId,
      source_lesson_id: permanentModal.sourceLessonId,
      target_lesson_id: permanentModal.targetLessonId,
      effective_date: permanentModal.effectiveDate.format('YYYY-MM-DD'),
      reason: permanentModal.reason,
    });
    permanentModal.visible = false;
    message.success('Permanent course change saved');
    await Promise.all([loadSelectedDate(), loadPermanentChanges()]);
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save permanent course change');
  } finally {
    permanentModal.saving = false;
  }
};

const revertLastPermanent = async () => {
  const record = permanentChanges.value[0];
  if (!record) {
    return;
  }
  try {
    await revertPermanentApi({ id: record.id });
    message.success('Permanent course change reverted');
    await Promise.all([loadSelectedDate(), loadPermanentChanges()]);
  } catch (error: any) {
    message.error(error?.msg || 'Failed to revert permanent course change');
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

const getRoomColor = (roomId?: number) => {
  const roomIndex = rooms.value.findIndex((room) => Number(room.id) === Number(roomId));
  const colorIndex = roomIndex >= 0 ? roomIndex : 0;
  return roomColorPalette[colorIndex % roomColorPalette.length];
};

const getRoomColorStyle = (roomId?: number) => {
  const color = getRoomColor(roomId);
  return {
    '--room-bg': color.bg,
    '--room-border': color.border,
    '--room-text': color.text,
  };
};

const getLessonColorStyle = (lesson: LessonItem) => {
  const color = getRoomColor(lesson.room_id);
  return {
    '--lesson-bg': color.bg,
    '--lesson-border': color.border,
    '--lesson-text': color.text,
  };
};

const toDetailPage = (lesson: LessonItem) => {
  if (adjustmentMode.value) {
    return;
  }
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

const selectDate = (date: Dayjs) => {
  if (draftActions.value.length) {
    message.warning('Save or discard unsaved changes before changing date');
    return;
  }
  selectedDate.value = date;
};

const selectWeek = (date: Dayjs | null) => {
  if (date) {
    selectDate(date);
  }
};

const selectPreviousDay = () => {
  selectDate(selectedDate.value.subtract(1, 'day'));
};

const selectToday = () => {
  selectDate(dayjs());
};

const selectNextDay = () => {
  selectDate(selectedDate.value.add(1, 'day'));
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

.week-picker {
  width: 190px;
}

.adjustment-toolbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  border: 1px solid #84adff;
  border-radius: 6px;
  background: #eff8ff;
  padding: 10px 12px;
}

.adjustment-mode,
.adjustment-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.adjustment-mode > span {
  color: #175cd3;
  font-size: 12px;
}

.announcement {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  margin-top: 12px;
  border: 1px solid #b2ccff;
  border-left: 4px solid #2970ff;
  border-radius: 6px;
  background: #eff8ff;
  padding: 5px 10px;
}

.announcement-icon {
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
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
  min-width: 0;
  margin: 0;
  color: #344054;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-workspace {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 10px;
  margin-top: 10px;
}

.date-picker-rail {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.selected-date-label {
  min-height: 42px;
  display: grid;
  place-content: center;
  text-align: center;
  color: #344054;
}

.selected-date-label strong {
  font-size: 13px;
  line-height: 16px;
}

.selected-date-label span {
  color: #667085;
  font-size: 10px;
  line-height: 13px;
}

.schedule-main {
  min-width: 0;
}

.date-option {
  width: 100%;
  min-height: 50px;
  border: 1px solid #d0d5dd;
  border-radius: 5px;
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
  box-shadow: inset 3px 0 0 #1570ef;
}

.date-option.today:not(.selected) {
  border-color: #84adff;
}

.date-option strong {
  font-size: 17px;
  line-height: 19px;
}

.date-weekday {
  font-size: 11px;
  line-height: 12px;
}

.legend {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  min-height: 42px;
  margin: 0;
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
  max-height: calc(100vh - 205px);
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
  min-height: 42px;
  padding: 9px 10px;
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

.room-header {
  display: flex;
  align-items: center;
  gap: 7px;
  white-space: nowrap;
  background: var(--room-bg);
  color: var(--room-text);
  box-shadow: inset 0 -3px 0 var(--room-border);
}

.room-header strong {
  font-size: 13px;
}

.room-header span {
  color: var(--room-text);
  font-size: 11px;
  font-weight: 600;
}

.room-header small {
  margin-left: auto;
  color: var(--room-text);
  opacity: 0.72;
  font-size: 10px;
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

.lesson-block.drop-target {
  outline: 1px dashed #84adff;
  outline-offset: -3px;
}

.lesson-block.drop-ready:hover {
  outline: 2px solid #1570ef;
  background: #eff8ff;
}

.lesson-block.drop-blocked:hover {
  outline: 2px solid #d92d20;
  background: #fff1f0;
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

.student-row.draggable {
  border-color: #b8c8dc;
}

.student-row.selected-for-move {
  border-color: #1570ef;
  box-shadow: 0 0 0 2px rgba(21, 112, 239, 0.18);
}

.drag-handle {
  flex: 0 0 24px;
  align-self: stretch;
  border-right: 1px solid #d0d5dd;
  color: #667085;
  cursor: grab;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.58);
}

.drag-handle:active {
  cursor: grabbing;
  opacity: 0.68;
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

.sick-button {
  flex: 0 0 30px;
  width: 30px;
  height: 30px;
  border: 0;
  border-left: 1px solid rgba(152, 162, 179, 0.45);
  background: rgba(255, 255, 255, 0.52);
  color: #667085;
  cursor: pointer;
}

.sick-button:hover {
  background: #fef3f2;
  color: #b42318;
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

.student-moved {
  border-color: #84adff;
  background: #eff8ff;
  color: #175cd3;
}

.student-sick {
  border-color: #fda29b;
  background: #fef3f2;
  color: #b42318;
}

.deduct-option {
  margin-top: 16px;
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

  .week-picker {
    width: 100%;
  }

  .schedule-workspace {
    grid-template-columns: 1fr;
  }

  .date-picker-rail {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .selected-date-label,
  .date-option {
    flex: 0 0 56px;
  }

  .announcement strong {
    display: none;
  }

  .schedule-scroll {
    max-height: calc(100vh - 300px);
  }
}
</style>
