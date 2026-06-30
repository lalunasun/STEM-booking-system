<template>
  <div class="classroom-page">
    <div class="classroom-toolbar">
      <div>
        <h1>Classroom</h1>
        <p>{{ selectedDate.format('dddd, MMM D, YYYY') }}</p>
      </div>
      <div class="toolbar-actions">
        <a-button size="large" @click="shiftDate(-1)">Previous</a-button>
        <a-button size="large" type="primary" ghost @click="goToday">Today</a-button>
        <a-button size="large" @click="shiftDate(1)">Next</a-button>
        <a-date-picker
          v-model:value="selectedDate"
          size="large"
          class="date-picker"
          :allow-clear="false"
          @change="loadClassroom"
        />
      </div>
    </div>

    <div class="classroom-filters">
      <a-input-search
        v-model:value="studentKeyword"
        size="large"
        placeholder="Search student"
        allow-clear
      />
      <div class="filter-actions">
        <a-switch v-model:checked="showEmptyClasses" />
        <span class="filter-label">Show empty classes</span>
        <a-button size="large" :loading="loading" @click="loadClassroom">Refresh</a-button>
      </div>
    </div>

    <a-spin :spinning="loading">
      <div class="classroom-grid">
        <aside class="room-browser">
          <div class="room-tabs">
            <button
              v-for="room in roomPages"
              :key="`tab-${room.key}`"
              type="button"
              :class="{ active: activeRoomKey === room.key }"
              :style="getRoomColorStyle(room.roomId)"
              @click="scrollToRoom(room.key)"
            >
              {{ room.roomName }}
            </button>
          </div>

          <div ref="roomPager" class="room-page-strip" @scroll.passive="syncRoomFromScroll">
            <section
              v-for="room in roomPages"
              :key="room.key"
              class="room-page"
              :data-room-key="room.key"
              :style="getRoomColorStyle(room.roomId)"
            >
              <header class="room-page-head">
                <div>
                  <h2>{{ room.roomName }}</h2>
                  <p>{{ room.lessonCount }} classes - {{ room.studentCount }} active students</p>
                </div>
              </header>

              <div class="time-slot-list">
                <section v-for="group in room.timeSlotGroups" :key="`${room.key}-${group.time}`" class="time-slot-group">
                  <header class="time-slot-head">
                    <span>{{ group.time }}</span>
                    <small>{{ group.lessonRows.length }} class{{ group.lessonRows.length === 1 ? '' : 'es' }}</small>
                  </header>
                  <div v-if="group.lessonRows.length" class="time-slot-lessons">
                    <button
                      v-for="row in group.lessonRows"
                      :key="row.key"
                      type="button"
                      class="lesson-button"
                      :class="{ active: selectedLessonKey === row.key }"
                      :style="getRoomColorStyle(row.lesson.room_id)"
                      @click="selectLesson(row.lesson)"
                    >
                      <span class="lesson-name">{{ row.lesson.class_name || 'Untitled class' }}</span>
                      <span class="lesson-meta">
                        {{ row.activeCount }}/{{ row.capacity }} students
                      </span>
                    </button>
                  </div>
                  <div v-else class="empty-time-slot">No class</div>
                </section>
              </div>
            </section>
          </div>
          <a-empty v-if="!roomPages.length" description="No classrooms on this date" />
        </aside>

        <main class="lesson-panel">
          <template v-if="selectedLesson">
            <section class="lesson-header" :style="getRoomColorStyle(selectedLesson.room_id)">
              <div>
                <h2>{{ selectedLesson.class_name || 'Untitled class' }}</h2>
                <p>{{ selectedLesson.room_name || 'No room' }} · {{ selectedLesson.time || '-' }}</p>
              </div>
              <div class="capacity-pill">
                {{ selectedLessonRow?.activeCount || 0 }}/{{ selectedLessonRow?.capacity || getLessonCapacity(selectedLesson) }}
              </div>
            </section>

            <div class="student-list">
              <article
                v-for="student in visibleStudents"
                :key="`${student.type}-${student.studentId}-${student.id || 0}`"
                class="student-card"
                :class="student.type"
              >
                <div class="student-main">
                  <div>
                    <div class="student-name-row">
                      <button type="button" class="student-name" @click="openStudent(student)">
                        {{ student.name }}
                      </button>
                      <a-tag v-if="student.badge" :color="studentTagColor(student.type)">{{ student.badge }}</a-tag>
                    </div>
                    <div class="student-subline">
                      <span v-if="student.title">{{ student.title }}</span>
                      <span v-if="getStudentNote(selectedLesson, student)" class="student-note">
                        Note: {{ getStudentNote(selectedLesson, student) }}
                      </span>
                    </div>
                  </div>
                  <div class="status-block">
                    <a-tag v-if="student.absentMarked" color="red">Absent</a-tag>
                    <a-tag v-else-if="student.commentDone" color="green">Done</a-tag>
                    <a-tag v-else color="orange">Need comment</a-tag>
                  </div>
                </div>

                <div class="student-actions">
                  <a-button
                    size="large"
                    :type="student.absentMarked ? 'default' : 'primary'"
                    @click="toggleAbsent(student)"
                  >
                    {{ student.absentMarked ? 'Mark present' : 'Absent' }}
                  </a-button>
                  <a-button size="large" @click="openComment(student)">Comment</a-button>
                  <a-button size="large" @click="openNote(student)">Note</a-button>
                  <a-button size="large" @click="openStudent(student)">Profile</a-button>
                </div>
              </article>
              <a-empty v-if="!visibleStudents.length" description="No students match this view" />
            </div>
          </template>
          <a-empty v-else description="Choose a class" />
        </main>
      </div>
    </a-spin>

    <a-modal
      v-model:visible="noteModal.visible"
      title="Student note"
      :confirm-loading="noteModal.saving"
      @ok="saveStudentNote"
    >
      <p class="modal-student">{{ noteModal.studentName }} · {{ noteModal.className }}</p>
      <a-textarea v-model:value="noteModal.note" :rows="5" placeholder="Visible on schedule/classroom only" />
    </a-modal>

    <a-modal
      v-model:visible="commentModal.visible"
      title="Class comment"
      :confirm-loading="commentModal.saving"
      @ok="saveStudentComment"
    >
      <p class="modal-student">{{ commentModal.studentName }} · {{ selectedLesson?.class_name || '' }}</p>
      <a-textarea v-model:value="commentModal.content" :rows="6" placeholder="Write this student's class performance comment" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import dayjs, { Dayjs } from 'dayjs';
import { message } from 'ant-design-vue';
import { listApi as listLessonsApi } from '/@/api/admin/lesson';
import { listApi as listTimeApi } from '/@/api/admin/time';
import { listApi as listNoteApi, saveApi as saveNoteApi } from '/@/api/admin/student-lesson-note';
import { markAbsentApi } from '/@/api/admin/student-attendance';
import { createCommentApi } from '/@/api/admin/student';
import { ADMIN_USER_ID } from '/@/store/constants';

interface ScheduleStudent {
  order_id?: number;
  student_id: number;
  name: string;
  term_title?: string;
  expect_time?: string;
  return_time?: string;
  comment_done?: boolean;
  absent_marked?: boolean;
}

interface AdjustmentStudent {
  adjustment_id?: number;
  student_id: number;
  name: string;
  date?: string;
  term_title?: string;
  comment_done?: boolean;
  absent_marked?: boolean;
}

interface TrialStudent {
  trial_request_id?: number;
  student_id: number;
  name: string;
  date?: string;
  comment_done?: boolean;
  absent_marked?: boolean;
}

interface ClassPassStudent {
  booking_id?: number;
  class_pass_id?: number;
  student_id: number;
  name: string;
  date?: string;
  pass_title?: string;
  comment_done?: boolean;
  absent_marked?: boolean;
}

interface TimeSlot {
  id: number;
  time: string;
}

interface LessonItem {
  id: number;
  lesson_id?: number;
  thing?: number;
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
  scheduled_class_pass_students?: ClassPassStudent[];
  moved_students?: AdjustmentStudent[];
  sick_leave_students?: AdjustmentStudent[];
}

interface DisplayStudent {
  id?: number;
  studentId: number;
  name: string;
  type: 'normal' | 'canceled' | 'rescheduled' | 'trial' | 'class_pass' | 'moved' | 'sick';
  badge?: string;
  title?: string;
  commentDone?: boolean;
  absentMarked?: boolean;
}

interface ClassroomLessonRow {
  key: string;
  lesson: LessonItem;
  students: DisplayStudent[];
  activeStudents: DisplayStudent[];
  activeCount: number;
  capacity: number;
}

interface TimeSlotGroup {
  time: string;
  lessonRows: ClassroomLessonRow[];
}

interface RoomPage {
  key: string;
  roomId?: number;
  roomName: string;
  lessonCount: number;
  studentCount: number;
  timeSlotGroups: TimeSlotGroup[];
}

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
const selectedDate = ref<Dayjs>(dayjs());
const studentKeyword = ref('');
const lessons = ref<LessonItem[]>([]);
const timeSlots = ref<TimeSlot[]>([]);
const loading = ref(false);
const selectedLessonKey = ref('');
const activeRoomKey = ref('');
const roomPager = ref<HTMLElement | null>(null);
const studentNotes = ref<Record<string, string>>({});
const showEmptyClasses = ref(true);

const noteModal = reactive({
  visible: false,
  saving: false,
  lessonId: 0,
  studentId: 0,
  studentName: '',
  className: '',
  note: '',
});

const commentModal = reactive({
  visible: false,
  saving: false,
  studentId: 0,
  studentName: '',
  content: '',
});

const lessonRows = computed<ClassroomLessonRow[]>(() =>
  [...lessons.value]
    .sort((a, b) =>
      `${a.time || ''}-${a.room_name || ''}-${a.class_name || ''}`.localeCompare(
        `${b.time || ''}-${b.room_name || ''}-${b.class_name || ''}`
      )
    )
    .map((lesson) => {
      const students = getDisplayStudents(lesson);
      const activeStudents = students.filter((student) => student.type !== 'canceled' && student.type !== 'sick');
      return {
        key: lessonKey(lesson),
        lesson,
        students,
        activeStudents,
        activeCount: activeStudents.length,
        capacity: getLessonCapacity(lesson),
      };
    })
);

const normalizeTime = (value?: string) => String(value || '').trim() || 'Time TBD';

const timeSortValue = (value?: string) => {
  const match = normalizeTime(value).match(/^(\d{1,2})(?::(\d{2}))?/);
  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }
  return Number(match[1]) * 60 + Number(match[2] || 0);
};

const visibleLessonRows = computed(() => {
  const keyword = studentKeyword.value.trim().toLowerCase();
  return lessonRows.value
    .filter((row) => showEmptyClasses.value || row.activeCount > 0)
    .filter((row) =>
      !keyword || row.students.some((student) => student.name.toLowerCase().includes(keyword))
    );
});

const timeSlotGroups = computed<TimeSlotGroup[]>(() => {
  const timeLabels = new Set<string>();
  timeSlots.value.forEach((slot) => timeLabels.add(normalizeTime(slot.time)));
  lessonRows.value.forEach((row) => timeLabels.add(normalizeTime(row.lesson.time)));

  return Array.from(timeLabels)
    .sort((a, b) => timeSortValue(a) - timeSortValue(b) || a.localeCompare(b))
    .map((time) => ({
      time,
      lessonRows: visibleLessonRows.value
        .filter((row) => normalizeTime(row.lesson.time) === time)
        .sort((a, b) =>
          `${a.lesson.room_name || ''}-${a.lesson.class_name || ''}`.localeCompare(
            `${b.lesson.room_name || ''}-${b.lesson.class_name || ''}`
          )
        ),
    }));
});

const roomPages = computed<RoomPage[]>(() => {
  const rooms = new Map<string, { key: string; roomId?: number; roomName: string; rows: ClassroomLessonRow[] }>();
  lessonRows.value.forEach((row) => {
    const roomId = Number(row.lesson.room_id || 0) || undefined;
    const key = roomId ? String(roomId) : `room-${row.lesson.room_name || 'none'}`;
    if (!rooms.has(key)) {
      rooms.set(key, {
        key,
        roomId,
        roomName: row.lesson.room_name || 'No room',
        rows: [],
      });
    }
    rooms.get(key)?.rows.push(row);
  });

  return Array.from(rooms.values())
    .sort((a, b) => a.roomName.localeCompare(b.roomName))
    .map((room) => {
      const timeLabels = new Set<string>();
      timeSlots.value.forEach((slot) => timeLabels.add(normalizeTime(slot.time)));
      room.rows.forEach((row) => timeLabels.add(normalizeTime(row.lesson.time)));
      const visibleRoomRows = visibleLessonRows.value.filter((row) => roomKey(row.lesson) === room.key);
      return {
        key: room.key,
        roomId: room.roomId,
        roomName: room.roomName,
        lessonCount: visibleRoomRows.length,
        studentCount: visibleRoomRows.reduce((sum, row) => sum + row.activeCount, 0),
        timeSlotGroups: Array.from(timeLabels)
          .sort((a, b) => timeSortValue(a) - timeSortValue(b) || a.localeCompare(b))
          .map((time) => ({
            time,
            lessonRows: visibleRoomRows
              .filter((row) => normalizeTime(row.lesson.time) === time)
              .sort((a, b) => String(a.lesson.class_name || '').localeCompare(String(b.lesson.class_name || ''))),
          })),
      };
    });
});

const selectedLessonRow = computed(() =>
  visibleLessonRows.value.find((row) => row.key === selectedLessonKey.value) || visibleLessonRows.value[0]
);

const selectedLesson = computed(() => selectedLessonRow.value?.lesson);

const visibleStudents = computed(() => {
  if (!selectedLessonRow.value) {
    return [];
  }
  const keyword = studentKeyword.value.trim().toLowerCase();
  const students = selectedLessonRow.value.activeStudents;
  if (!keyword) {
    return students;
  }
  return students.filter((student) => student.name.toLowerCase().includes(keyword));
});

watch(selectedLessonRow, (row) => {
  if (row) {
    selectedLessonKey.value = row.key;
    activeRoomKey.value = roomKey(row.lesson);
  }
});

watch(roomPages, (pages) => {
  if (!activeRoomKey.value && pages.length > 0) {
    activeRoomKey.value = pages[0].key;
  }
});

onMounted(() => {
  loadClassroom();
});

const loadClassroom = async () => {
  loading.value = true;
  try {
    const date = selectedDate.value.format('YYYY-MM-DD');
    const [lessonRes, noteRes, timeRes] = await Promise.all([
      listLessonsApi({ date }),
      listNoteApi({ date }),
      listTimeApi({}),
    ]);
    lessons.value = lessonRes.data || [];
    studentNotes.value = buildNoteMap(noteRes.data || []);
    timeSlots.value = timeRes.data || [];
    if (!lessons.value.some((lesson) => lessonKey(lesson) === selectedLessonKey.value)) {
      selectedLessonKey.value = lessons.value[0] ? lessonKey(lessons.value[0]) : '';
    }
  } catch (error: any) {
    message.error(error?.msg || 'Failed to load classroom');
  } finally {
    loading.value = false;
  }
};

const buildNoteMap = (items: any[]) => {
  const map: Record<string, string> = {};
  items.forEach((item) => {
    map[noteKey(Number(item.lesson_id || item.lesson), Number(item.student_id || item.student))] = item.note || '';
  });
  return map;
};

const lessonKey = (lesson: LessonItem) => String(lesson.lesson_id || lesson.id);
const roomKey = (lesson: LessonItem) => {
  const roomId = Number(lesson.room_id || 0) || undefined;
  return roomId ? String(roomId) : `room-${lesson.room_name || 'none'}`;
};

const selectLesson = (lesson: LessonItem) => {
  selectedLessonKey.value = lessonKey(lesson);
  activeRoomKey.value = roomKey(lesson);
};

const scrollToRoom = async (key: string) => {
  activeRoomKey.value = key;
  await nextTick();
  const target = roomPager.value?.querySelector(`[data-room-key="${key}"]`) as HTMLElement | null;
  target?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
};

const syncRoomFromScroll = () => {
  const pager = roomPager.value;
  if (!pager) return;
  const pages = Array.from(pager.querySelectorAll<HTMLElement>('.room-page'));
  let bestKey = activeRoomKey.value;
  let bestDistance = Number.MAX_SAFE_INTEGER;
  pages.forEach((page) => {
    const distance = Math.abs(page.offsetLeft - pager.scrollLeft);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestKey = page.dataset.roomKey || bestKey;
    }
  });
  activeRoomKey.value = bestKey;
};

const shiftDate = (days: number) => {
  selectedDate.value = selectedDate.value.add(days, 'day');
  loadClassroom();
};

const goToday = () => {
  selectedDate.value = dayjs();
  loadClassroom();
};

const isStudentActiveOnDate = (student: ScheduleStudent) => {
  if (!student.expect_time || !student.return_time) {
    return true;
  }
  const start = dayjs(student.expect_time).startOf('day');
  const end = dayjs(student.return_time).endOf('day');
  return selectedDate.value.isSame(start, 'day') ||
    selectedDate.value.isSame(end, 'day') ||
    (selectedDate.value.isAfter(start) && selectedDate.value.isBefore(end));
};

const isAdjustmentOnSelectedDate = (date?: string) => !!date && dayjs(date).isSame(selectedDate.value, 'day');

const getDisplayStudents = (lesson: LessonItem): DisplayStudent[] => {
  const canceled = (lesson.canceled_students || []).filter((student) => isAdjustmentOnSelectedDate(student.date));
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
      commentDone: !!student.comment_done,
      absentMarked: !!student.absent_marked,
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
      commentDone: !!student.comment_done,
      absentMarked: !!student.absent_marked,
    }));

  const trialStudents: DisplayStudent[] = (lesson.scheduled_trial_students || [])
    .filter((student) => isAdjustmentOnSelectedDate(student.date))
    .map((student) => ({
      id: student.trial_request_id,
      studentId: student.student_id,
      name: student.name,
      type: 'trial',
      badge: 'Trial',
      commentDone: !!student.comment_done,
      absentMarked: !!student.absent_marked,
    }));

  const classPassStudents: DisplayStudent[] = (lesson.scheduled_class_pass_students || [])
    .filter((student) => isAdjustmentOnSelectedDate(student.date))
    .map((student) => ({
      id: student.booking_id,
      studentId: student.student_id,
      name: student.name,
      type: 'class_pass',
      badge: 'Class Pass',
      title: student.pass_title,
      commentDone: !!student.comment_done,
      absentMarked: !!student.absent_marked,
    }));

  const movedStudents: DisplayStudent[] = (lesson.moved_students || []).map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'moved',
    badge: 'Moved',
    title: student.term_title,
    commentDone: !!student.comment_done,
    absentMarked: !!student.absent_marked,
  }));

  const canceledStudents: DisplayStudent[] = canceled.map((student) => ({
    id: student.adjustment_id,
    studentId: student.student_id,
    name: student.name,
    type: 'canceled',
    badge: 'Absent',
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

  return [
    ...normalStudents,
    ...rescheduledStudents,
    ...trialStudents,
    ...classPassStudents,
    ...movedStudents,
    ...canceledStudents,
    ...sickStudents,
  ].sort((a, b) => a.name.localeCompare(b.name));
};

const getLessonCapacity = (lesson: LessonItem) => {
  const capacity = Number(lesson.room_capacity);
  return Number.isFinite(capacity) && capacity > 0 ? capacity : 4;
};

const activeStudentCount = (lesson: LessonItem) =>
  getDisplayStudents(lesson).filter((student) => student.type !== 'canceled' && student.type !== 'sick').length;

const roomIds = computed(() => {
  const ids: number[] = [];
  lessons.value.forEach((lesson) => {
    const id = Number(lesson.room_id || 0);
    if (id && !ids.includes(id)) {
      ids.push(id);
    }
  });
  return ids;
});

const getRoomColor = (roomId?: number) => {
  const index = Math.max(0, roomIds.value.findIndex((id) => Number(id) === Number(roomId)));
  return roomColorPalette[index % roomColorPalette.length];
};

const getRoomColorStyle = (roomId?: number) => {
  const color = getRoomColor(roomId);
  return {
    '--room-bg': color.bg,
    '--room-border': color.border,
    '--room-text': color.text,
  };
};

const studentTagColor = (type: DisplayStudent['type']) => {
  if (type === 'trial') return 'purple';
  if (type === 'rescheduled' || type === 'moved') return 'blue';
  if (type === 'sick' || type === 'canceled') return 'red';
  return 'default';
};

const noteKey = (lessonId: number, studentId: number) => `${lessonId}-${studentId}`;

const getStudentNote = (lesson: LessonItem, student: DisplayStudent) =>
  studentNotes.value[noteKey(Number(lesson.lesson_id || lesson.id), student.studentId)] || '';

const openNote = (student: DisplayStudent) => {
  if (!selectedLesson.value) return;
  noteModal.lessonId = Number(selectedLesson.value.lesson_id || selectedLesson.value.id);
  noteModal.studentId = student.studentId;
  noteModal.studentName = student.name;
  noteModal.className = selectedLesson.value.class_name || 'Untitled class';
  noteModal.note = getStudentNote(selectedLesson.value, student);
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

const openComment = (student: DisplayStudent) => {
  commentModal.studentId = student.studentId;
  commentModal.studentName = student.name;
  commentModal.content = '';
  commentModal.visible = true;
};

const saveStudentComment = async () => {
  if (!selectedLesson.value) return;
  const content = commentModal.content.trim();
  if (!content) {
    message.warning('Please enter a comment');
    return;
  }
  commentModal.saving = true;
  try {
    await createCommentApi({
      student_id: commentModal.studentId,
      lesson_id: Number(selectedLesson.value.lesson_id || selectedLesson.value.id),
      lesson_date: selectedDate.value.format('YYYY-MM-DD'),
      content,
    });
    commentModal.visible = false;
    message.success('Student comment saved');
    await loadClassroom();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save student comment');
  } finally {
    commentModal.saving = false;
  }
};

const toggleAbsent = async (student: DisplayStudent) => {
  if (!selectedLesson.value) return;
  try {
    await markAbsentApi({
      lesson_id: Number(selectedLesson.value.lesson_id || selectedLesson.value.id),
      student_id: student.studentId,
      lesson_date: selectedDate.value.format('YYYY-MM-DD'),
      is_absent: !student.absentMarked,
    });
    message.success(student.absentMarked ? 'Marked present' : 'Marked absent');
    await loadClassroom();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to update attendance');
  }
};

const openStudent = (student: DisplayStudent) => {
  router.push({
    name: 'student',
    query: {
      id: student.studentId,
      returnTo: `/admin/classroom`,
    },
  });
};
</script>

<style scoped lang="less">
.classroom-page {
  min-height: calc(100vh - 96px);
  color: #0b203b;
}

.classroom-toolbar,
.classroom-filters {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.classroom-toolbar h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.15;
}

.classroom-toolbar p {
  margin: 6px 0 0;
  color: #637083;
  font-size: 16px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.date-picker {
  width: 190px;
}

.classroom-filters :deep(.ant-input-search) {
  max-width: 420px;
}

.classroom-grid {
  display: grid;
  grid-template-columns: minmax(360px, 42%) 1fr;
  gap: 16px;
}

.room-browser {
  min-width: 0;
}

.room-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
  scrollbar-width: thin;
}

.room-tabs button {
  flex: 0 0 auto;
  min-width: 96px;
  min-height: 38px;
  border: 1px solid var(--room-border);
  border-radius: 8px;
  background: var(--room-bg);
  color: var(--room-text);
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}

.room-tabs button.active {
  background: #fff;
  box-shadow: inset 0 -3px 0 var(--room-border);
}

.room-page-strip {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  padding-bottom: 8px;
}

.room-page {
  flex: 0 0 100%;
  min-width: 0;
  scroll-snap-align: start;
  border: 2px solid var(--room-border);
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.room-page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--room-border);
  background: var(--room-bg);
  color: var(--room-text);
}

.room-page-head h2 {
  margin: 0;
  font-size: 22px;
  line-height: 1.15;
}

.room-page-head p {
  margin: 4px 0 0;
  font-size: 13px;
  font-weight: 700;
}

.time-slot-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(100vh - 278px);
  overflow: auto;
  padding: 10px;
}

.time-slot-group {
  border: 1px solid #dbe2ec;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.time-slot-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 11px;
  border-bottom: 1px solid #dbe2ec;
  background: #f6f8fb;
  color: #0b203b;
  font-weight: 800;
}

.time-slot-head small {
  color: #637083;
  font-size: 12px;
  font-weight: 700;
}

.time-slot-lessons {
  display: grid;
  gap: 8px;
  padding: 8px;
}

.empty-time-slot {
  padding: 12px;
  color: #8a96a8;
  font-size: 13px;
}

.lesson-button {
  width: 100%;
  border: 2px solid var(--room-border);
  background: var(--room-bg);
  color: var(--room-text);
  border-radius: 8px;
  padding: 14px;
  text-align: left;
  cursor: pointer;
}

.lesson-button.active {
  box-shadow: 0 0 0 3px rgba(40, 111, 255, 0.18);
  background: #fff;
}

.lesson-time,
.lesson-name,
.lesson-meta {
  display: block;
}

.lesson-time {
  font-size: 14px;
  color: #536178;
}

.lesson-name {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 700;
}

.lesson-meta {
  margin-top: 4px;
  font-size: 14px;
}

.lesson-panel {
  min-height: 560px;
  background: #fff;
  border: 1px solid #dbe2ec;
  border-radius: 8px;
  padding: 16px;
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 2px solid var(--room-border);
  background: var(--room-bg);
  border-radius: 8px;
  padding: 16px;
  color: var(--room-text);
}

.lesson-header h2 {
  margin: 0;
  font-size: 26px;
}

.lesson-header p {
  margin: 6px 0 0;
  font-size: 16px;
}

.capacity-pill {
  min-width: 72px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #fff;
  text-align: center;
  font-size: 22px;
  font-weight: 700;
}

.student-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.student-card {
  border: 1px solid #dbe2ec;
  border-left: 6px solid #7399d5;
  border-radius: 8px;
  padding: 14px;
  background: #fbfdff;
}

.student-card.trial {
  border-left-color: #8f62cc;
}

.student-card.rescheduled,
.student-card.moved {
  border-left-color: #2f80ed;
}

.student-main {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.student-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.student-name {
  border: none;
  background: transparent;
  padding: 0;
  color: #0b46a0;
  font-size: 21px;
  font-weight: 700;
  cursor: pointer;
}

.student-subline {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  color: #5d6a7e;
  font-size: 14px;
}

.student-note {
  color: #1f5f8f;
}

.status-block {
  min-width: 104px;
  text-align: right;
}

.student-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}

.modal-student {
  margin: 0 0 12px;
  color: #536178;
}

@media (max-width: 900px) {
  .classroom-toolbar,
  .classroom-filters {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-actions {
    justify-content: flex-start;
  }

  .classroom-filters :deep(.ant-input-search),
  .date-picker {
    width: 100%;
    max-width: none;
  }

  .classroom-grid {
    grid-template-columns: 1fr;
  }

  .room-page-strip {
    max-width: calc(100vw - 32px);
  }

  .room-page {
    flex-basis: 100%;
  }

  .time-slot-list {
    max-height: 460px;
  }

  .lesson-button {
    min-width: 0;
  }
}
</style>
