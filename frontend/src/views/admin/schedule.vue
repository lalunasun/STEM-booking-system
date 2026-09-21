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
            v-if="canManageSchedule && savedAdjustments.length && !adjustmentMode"
            :title="'Show saved adjustments for this date'"
            @click="showSavedAdjustments = !showSavedAdjustments"
          >
            <undo-outlined /> Adjustments ({{ savedAdjustments.length }})
          </a-button>
          <a-button
            v-if="!adjustmentMode && canManageSchedule"
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
          <span v-if="adjustmentScope === 'date' && draggedStudent" class="selected-move-student">
            Selected: {{ draggedStudent.student.name }} · {{ draggedStudent.sourceDate }}
          </span>
          <a-button
            v-if="adjustmentScope === 'date' && draggedStudent"
            size="small"
            type="primary"
            @click="selectDateForMove"
          >
            Choose target date, then class
          </a-button>
          <a-button
            v-if="adjustmentScope === 'date' && draggedStudent"
            size="small"
            @click="clearSelectedStudent"
          >
            Clear selection
          </a-button>
        </div>
        <div class="adjustment-actions">
          <a-button :disabled="!draftActions.length" @click="undoLastDraft">
            <undo-outlined /> Undo
          </a-button>
          <a-button :disabled="!draftActions.length" @click="discardDrafts">
            Discard
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

      <section v-if="adjustmentMode && adjustmentScope === 'date' && draftActions.length" class="saved-adjustments">
        <strong>Unsaved changes</strong>
        <div v-for="(action, index) in draftActions" :key="`${action.student_id}-${index}`" class="saved-adjustment-row">
          <span class="saved-adjustment-description">
            <strong>{{ action.student_name }}</strong>
            {{ action.type === 'sick_leave' ? 'Sick leave' : 'Move' }} · {{ action.source_class }}
            <template v-if="action.target_class"> → {{ action.target_class }}</template>
          </span>
          <a-button size="small" :title="`Remove ${action.student_name}'s unsaved change`" @click="removeDraftAction(index)">
            <close-outlined />
          </a-button>
        </div>
      </section>

      <section
        v-if="canManageSchedule && savedAdjustments.length && (adjustmentMode && adjustmentScope === 'date' || showSavedAdjustments)"
        class="saved-adjustments"
        aria-label="Saved daily adjustments"
      >
        <strong>Saved adjustments for {{ selectedDate.format('MMM D') }}</strong>
        <div v-for="record in savedAdjustments" :key="record.id" class="saved-adjustment-row">
          <span class="saved-adjustment-description">
            <strong>{{ record.student_name }}</strong>
            <span v-if="record.adjustment_type === 'sick_leave'">
              Sick leave · {{ record.source_class }} · {{ record.source_room }} ·
              {{ record.source_time }} · {{ record.source_lesson_date }}
              <template v-if="record.lesson_count_delta">· 1 lesson deducted</template>
            </span>
            <span v-else>
              Move · {{ record.source_class }} · {{ record.source_room }}
              ({{ record.source_lesson_date }}) → {{ record.target_class }} ·
              {{ record.target_room }} ({{ record.target_lesson_date }})
            </span>
          </span>
          <a-popconfirm
            :title="getRevertConfirmation(record)"
            ok-text="Revert"
            cancel-text="Keep"
            @confirm="revertSavedAdjustment(record)"
          >
            <a-button
              size="small"
              danger
              :loading="revertingAdjustmentId === record.id"
              :disabled="revertingAdjustmentId !== null && revertingAdjustmentId !== record.id"
            >
              <undo-outlined /> Revert
            </a-button>
          </a-popconfirm>
        </div>
      </section>

      <section v-if="adjustmentMode && adjustmentScope === 'future' && permanentChanges.length" class="saved-adjustments">
        <strong>Active permanent changes</strong>
        <div v-for="record in permanentChanges" :key="record.id" class="saved-adjustment-row">
          <span class="saved-adjustment-description">
            <strong>{{ record.student_name }}</strong>
            {{ record.source_class }} → {{ record.target_class }} · from {{ record.effective_date }}
          </span>
          <a-popconfirm
            :title="`Revert ${record.student_name}'s permanent change to ${record.source_class}?`"
            ok-text="Revert"
            cancel-text="Keep"
            @confirm="revertPermanentChange(record)"
          >
            <a-button size="small" danger :loading="revertingPermanentId === record.id">
              <undo-outlined /> Revert
            </a-button>
          </a-popconfirm>
        </div>
      </section>

      <section class="announcement" aria-label="Staff announcement">
        <div class="announcement-icon">A</div>
        <strong>Staff announcement:</strong>
        <template v-if="editingAnnouncement">
          <a-textarea
            v-model:value="announcementDraft"
            class="announcement-input"
            :maxlength="500"
            :auto-size="{ minRows: 1, maxRows: 3 }"
            placeholder="Staff announcement"
          />
          <a-button
            type="primary"
            size="small"
            :loading="savingAnnouncement"
            @click="saveAnnouncement"
          >
            <save-outlined /> Save
          </a-button>
          <a-button size="small" @click="cancelAnnouncementEdit">Cancel</a-button>
        </template>
        <template v-else>
          <p>{{ staffAnnouncement }}</p>
          <a-button v-if="canManageSchedule" size="small" type="link" @click="startAnnouncementEdit">
            <edit-outlined /> Edit
          </a-button>
        </template>
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

          <div
            v-else
            ref="scheduleScrollRef"
            class="schedule-scroll"
            @dragover.prevent="handleScheduleDragOver"
            @dragleave="stopAutoScroll"
            @wheel="handleScheduleWheel"
          >
            <div class="daily-board" :style="boardGridStyle">
              <div class="time-header">Time</div>
              <div
                v-for="room in rooms"
                :key="`room-${room.id}`"
                class="room-header"
                :style="getRoomColorStyle(room.id)"
              >
                <strong>{{ room.title }}</strong>
                <span v-if="editingTeacherRoomId !== room.id" class="teacher-name">
                  {{ getTeacherPreset(room.id) }}
                  <button
                    v-if="canManageSchedule"
                    type="button"
                    class="teacher-edit-btn"
                    :title="`Edit ${room.title} teacher`"
                    @click.stop="startTeacherEdit(room.id)"
                  >
                    <edit-outlined />
                  </button>
                </span>
                <a-input
                  v-else
                  v-model:value="inlineTeacherDraft"
                  class="teacher-inline-input"
                  size="small"
                  :maxlength="80"
                  :disabled="savingInlineTeacherRoomId === room.id"
                  @pressEnter="saveInlineTeacher(room.id)"
                  @blur="saveInlineTeacher(room.id)"
                  @keydown.esc="cancelTeacherEdit"
                />
                <small>{{ room.seat || 0 }} seats</small>
              </div>

              <template v-for="slot in displayedTimeSlots" :key="slot.id">
                <div class="time-cell">{{ slot.time }}</div>

                <div
                  v-for="room in rooms"
                  :key="`${slot.id}-${room.id}`"
                  class="schedule-cell"
                  :class="{ 'empty-cell': !getCellLessons(room.id, slot.id).length && !getContinuingLessons(room.id, slot.id).length && !getContinuingTrials(room.id, slot.id).length }"
                  @dragover.prevent
                  @drop.self="dropStudentToCell(room, slot)"
                >
                  <template v-if="getCellLessons(room.id, slot.id).length || getContinuingLessons(room.id, slot.id).length || getContinuingTrials(room.id, slot.id).length">
                    <div
                      class="slot-summary"
                      :class="{ full: isCellFull(room.id, slot.id) }"
                    >
                      <span>Room slot</span>
                      <strong>{{ getCellPresentStudentCount(room.id, slot.id) }}/{{ getCellCapacity(room.id, slot.id) }}</strong>
                    </div>
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
                          <small v-if="!isStandardHourTime(lesson.time)">{{ lesson.time }}</small>
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
                            @dragend="endStudentDrag"
                          >
                            <HolderOutlined />
                          </span>
                          <button
                            type="button"
                            class="student-main"
                            :title="getStudentHoverText(lesson, student)"
                            @click="adjustmentMode
                              ? selectStudentForMove(lesson, student)
                              : lesson.virtual_trial
                                ? openStudentDetail(student)
                                : toDetailPage(lesson)"
                          >
                            <span>{{ student.name }}</span>
                            <small v-if="student.badge">{{ student.badge }}</small>
                            <small
                              v-if="getCommentStatusLabel(lesson, student)"
                              class="comment-status"
                              :class="getCommentStatusClass(student)"
                            >
                              {{ getCommentStatusLabel(lesson, student) }}
                            </small>
                          </button>
                          <button
                            v-if="canManageSchedule && adjustmentMode && student.type === 'normal'"
                            type="button"
                            class="sick-button"
                            title="Mark sick leave"
                            @click="openSickLeave(lesson, student)"
                          >
                            <medicine-box-outlined />
                          </button>
                          <button
                            v-if="canMarkAttendance(lesson, student)"
                            type="button"
                            class="attendance-button"
                            :class="{ absent: student.absentMarked }"
                            :disabled="savingAttendanceKey === getAttendanceKey(lesson, student)"
                            :title="student.absentMarked ? 'Clear absent' : 'Mark absent'"
                            @click="toggleAbsent(lesson, student)"
                          >
                            {{ student.absentMarked ? 'Present' : 'Mark absent' }}
                          </button>
                          <a-popconfirm
                            v-if="getSavedAdjustment(lesson, student)"
                            :title="getRevertConfirmation(getSavedAdjustment(lesson, student)!)"
                            ok-text="Revert"
                            cancel-text="Keep"
                            @confirm="revertSavedAdjustment(getSavedAdjustment(lesson, student)!)"
                          >
                            <button
                              type="button"
                              class="note-button"
                              :title="`Revert ${student.name}'s adjustment`"
                              :disabled="revertingAdjustmentId !== null"
                            >
                              <undo-outlined />
                            </button>
                          </a-popconfirm>
                          <button
                            v-if="!lesson.virtual_trial"
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
                    <div
                      v-for="lesson in getContinuingLessons(room.id, slot.id)"
                      :key="`continuing-${lesson.id}`"
                      class="slot-continuation"
                      :class="{ 'trial-continuation': lesson.virtual_trial }"
                    >
                      <template v-if="lesson.virtual_trial">
                        <span>Trial continues:</span>
                        <button
                          v-for="student in getVisibleStudents(lesson)"
                          :key="`continuing-student-${lesson.id}-${student.studentId}`"
                          type="button"
                          @click="openStudentDetail(student)"
                        >
                          {{ student.name }}
                        </button>
                        <span>· {{ lesson.class_name || 'Trial' }} · {{ lesson.time }}</span>
                      </template>
                      <template v-else>
                        Continues: {{ lesson.class_name || 'Class' }} · {{ lesson.time }}
                      </template>
                    </div>
                    <div
                      v-for="trial in getContinuingTrials(room.id, slot.id)"
                      :key="`trial-continuing-${trial.trial_session_id}`"
                      class="slot-continuation"
                    >
                      Trial continues: {{ trial.name }} · {{ trial.trial_course }} · {{ trial.trial_time }}
                    </div>
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
          <a-form-item label="Course">
            <a-select
              v-model:value="permanentModal.courseName"
              show-search
              option-filter-prop="label"
              placeholder="Select course"
              :loading="permanentModal.loadingOptions"
              :options="permanentCourseOptions"
              @change="onPermanentCourseChange"
            />
          </a-form-item>
          <a-form-item label="First class date">
            <a-date-picker
              v-model:value="permanentModal.firstClassDate"
              :disabled="!permanentModal.courseName"
              :disabled-date="isPermanentDateDisabled"
              style="width: 100%"
              @change="onPermanentDateChange"
            />
          </a-form-item>
          <a-form-item label="Time and room">
            <a-select
              v-model:value="permanentModal.targetLessonId"
              placeholder="Select time and room"
              :disabled="!permanentModal.firstClassDate"
              :loading="permanentModal.loadingTargets"
              :options="permanentTargetOptions"
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
  CloseOutlined,
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
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
import { markAbsentApi } from '/@/api/admin/student-attendance';
import { listApi as listNotesApi, saveApi as saveNoteApi } from '/@/api/admin/student-lesson-note';
import {
  saveStaffAnnouncementApi,
  saveTeacherAssignmentsApi,
  staffAnnouncementApi,
  teacherAssignmentsApi,
} from '/@/api/admin/system-setting';
import { listApi as listRoomsApi } from '/@/api/admin/tag';
import { listApi as listTimesApi } from '/@/api/admin/time';
import { ADMIN_USER_ID, ADMIN_USER_ROLE } from '/@/store/constants';
import { compareRoomNames } from '/@/utils/room-order';
import { notifyScheduleDataChanged } from '/@/utils/schedule-sync';

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
  comment_done?: boolean;
  absent_marked?: boolean;
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
  comment_done?: boolean;
  absent_marked?: boolean;
}

interface TrialStudent {
  trial_request_id?: number;
  trial_session_id?: number;
  student_id: number;
  order_id?: number;
  name: string;
  date: string;
  comment_done?: boolean;
  absent_marked?: boolean;
  trial_course?: string;
  trial_time?: string;
  continuing?: boolean;
}

interface ClassPassStudent {
  booking_id: number;
  class_pass_id?: number;
  student_id: number;
  name: string;
  date?: string;
  pass_title?: string;
  comment_done?: boolean;
  absent_marked?: boolean;
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
  continuing_trial_students?: TrialStudent[];
  scheduled_class_pass_students?: ClassPassStudent[];
  moved_students?: AdjustmentStudent[];
  sick_leave_students?: AdjustmentStudent[];
  virtual_trial?: boolean;
  teacher_confirmation_required?: boolean;
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

interface DraftAction {
  type: 'move' | 'sick_leave';
  student_id: number;
  student_name: string;
  source_lesson_id: number;
  source_lesson_date?: string;
  source_class: string;
  target_lesson_id?: number;
  target_lesson_date?: string;
  target_class?: string;
  reason?: string;
  deduct_lesson?: boolean;
  term_title?: string;
}

interface SavedAdjustment {
  id: number;
  student_id: number;
  student_name: string;
  adjustment_type: 'move' | 'sick_leave';
  source_lesson_id: number;
  target_lesson_id?: number;
  source_class: string;
  source_room?: string;
  source_time?: string;
  source_lesson_date: string;
  target_class?: string;
  target_room?: string;
  target_time?: string;
  target_lesson_date: string;
  lesson_count_delta: number;
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
const savedAdjustments = ref<SavedAdjustment[]>([]);
const showSavedAdjustments = ref(false);
const revertingAdjustmentId = ref<number | null>(null);
const permanentChanges = ref<any[]>([]);
const revertingPermanentId = ref<number | null>(null);
const savingAdjustments = ref(false);
const draggedStudent = ref<{ lesson: LessonItem; student: DisplayStudent; sourceDate: string } | null>(null);
const scheduleScrollRef = ref<HTMLElement | null>(null);
const autoScrollFrame = ref<number | null>(null);
const autoScrollVector = reactive({ x: 0, y: 0 });
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
  loadingTargets: false,
  studentId: 0,
  studentName: '',
  sourceLessonId: 0,
  sourceClass: '',
  earliestDate: dayjs(),
  courseName: undefined as string | undefined,
  firstClassDate: null as Dayjs | null,
  targetLessonId: undefined as number | undefined,
  reason: '',
  options: [] as Array<{ lesson_id: number; class_name: string; day: string; time: string; room: string; first_class_date: string; enrollment_end_date: string; remaining: number | null }>,
  targetOptions: [] as Array<{ lesson_id: number; class_name: string; day: string; time: string; room: string; first_class_date: string; enrollment_end_date: string; remaining: number | null }>,
});
const permanentCourseOptions = computed(() => [...new Set(permanentModal.options.map((item) => item.class_name))]
  .sort((left, right) => left.localeCompare(right))
  .map((name) => ({ value: name, label: name })));
const permanentTargetOptions = computed(() => permanentModal.targetOptions
  .filter((item) => item.class_name === permanentModal.courseName &&
    item.first_class_date === permanentModal.firstClassDate?.format('YYYY-MM-DD'))
  .map((item) => ({
    value: item.lesson_id,
    label: `${item.time} · ${item.room}${item.remaining === null ? '' : ` · ${item.remaining} left`}`,
    disabled: item.remaining === 0,
  })));
const staffAnnouncement = ref(
  'Please review your classroom assignment and student changes before the first lesson.'
);
const announcementDraft = ref('');
const editingAnnouncement = ref(false);
const savingAnnouncement = ref(false);
const teacherAssignments = ref<Record<string, string>>({});
const editingTeacherRoomId = ref<number | null>(null);
const inlineTeacherDraft = ref('');
const savingInlineTeacherRoomId = ref<number | null>(null);
const savingAttendanceKey = ref('');
const canManageSchedule = computed(() => localStorage.getItem(ADMIN_USER_ROLE) !== '2');

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
      if (minutes < 9 * 60 || minutes >= 18 * 60 || minutes === 12 * 60) {
        return false;
      }
    } else if (minutes < 16 * 60 || minutes >= 20 * 60) {
      return false;
    }

    return isStandardHourTime(slot.time);
  });
});

onMounted(async () => {
  window.addEventListener('keydown', handleScheduleKeydown);
  loading.value = true;
  try {
    const [roomResponse, timeResponse, announcementResponse, teacherResponse] = await Promise.all([
      listRoomsApi({}),
      listTimesApi({}),
      staffAnnouncementApi(),
      teacherAssignmentsApi(),
    ]);
    if (announcementResponse?.data?.value) {
      staffAnnouncement.value = announcementResponse.data.value;
    }
    if (teacherResponse?.data?.value) {
      teacherAssignments.value = teacherResponse.data.value;
    }
    rooms.value = [...(roomResponse.data || [])].sort((a, b) => compareRoomNames(a.title, b.title));
    timeSlots.value = [...(timeResponse.data || [])].sort((a, b) =>
      getTimeMinutes(a.time) - getTimeMinutes(b.time)
    );
    await loadSelectedDate();
    initialized.value = true;
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleScheduleKeydown);
  stopAutoScroll();
});

watch(
  () => selectedDate.value.format('YYYY-MM-DD'),
  () => {
    if (initialized.value) {
      loadSelectedDate();
    }
  }
);

const startAnnouncementEdit = () => {
  if (!canManageSchedule.value) {
    return;
  }
  announcementDraft.value = staffAnnouncement.value;
  editingAnnouncement.value = true;
};

const cancelAnnouncementEdit = () => {
  announcementDraft.value = '';
  editingAnnouncement.value = false;
};

const saveAnnouncement = async () => {
  if (!canManageSchedule.value) {
    return;
  }
  savingAnnouncement.value = true;
  try {
    const response = await saveStaffAnnouncementApi({ value: announcementDraft.value });
    if (response.code !== 0) {
      message.error(response.msg || 'Failed to save announcement');
      return;
    }
    staffAnnouncement.value = response.data?.value || announcementDraft.value;
    editingAnnouncement.value = false;
    message.success('Announcement saved');
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save announcement');
  } finally {
    savingAnnouncement.value = false;
  }
};

const startTeacherEdit = (roomId: number) => {
  if (!canManageSchedule.value) {
    return;
  }
  editingTeacherRoomId.value = roomId;
  inlineTeacherDraft.value = getTeacherPreset(roomId);
};

const cancelTeacherEdit = () => {
  editingTeacherRoomId.value = null;
  inlineTeacherDraft.value = '';
};

const saveInlineTeacher = async (roomId: number) => {
  if (!canManageSchedule.value) {
    return;
  }
  if (editingTeacherRoomId.value !== roomId || savingInlineTeacherRoomId.value === roomId) {
    return;
  }

  const nextAssignments = {
    ...teacherAssignments.value,
    [String(roomId)]: inlineTeacherDraft.value.trim() || getTeacherFallback(roomId),
  };

  savingInlineTeacherRoomId.value = roomId;
  try {
    const response = await saveTeacherAssignmentsApi({
      value: JSON.stringify(nextAssignments),
    });
    if (response.code !== 0) {
      message.error(response.msg || 'Failed to save teacher');
      return;
    }
    teacherAssignments.value = response.data?.value || {};
    editingTeacherRoomId.value = null;
    inlineTeacherDraft.value = '';
    message.success('Teacher saved');
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save teacher');
  } finally {
    savingInlineTeacherRoomId.value = null;
  }
};

const loadSelectedDate = async () => {
  loading.value = true;
  savedAdjustments.value = [];
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
    await loadSavedAdjustments();
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

const getTimeRange = (value?: string) => {
  const parts = String(value || '').split('-');
  return {
    start: getTimeMinutes(parts[0]),
    end: getTimeMinutes(parts[1] || parts[0]),
  };
};

const isStandardHourTime = (value?: string) => {
  const { start, end } = getTimeRange(value);
  return start % 60 === 0 && end - start === 60;
};

const selectedDayCode = computed(() => dayCodes[selectedDate.value.day()]);

const getCellLessons = (roomId: number, timeId: number) => {
  return getRawCellLessons(roomId, timeId)
    .filter((lesson) => matchesStudentSearch(lesson))
    .sort((a, b) => String(a.class_name || '').localeCompare(String(b.class_name || '')));
};

const getRawCellLessons = (roomId: number, timeId: number) => {
  const slot = timeSlots.value.find((item) => Number(item.id) === Number(timeId));
  if (!slot) return [];
  const rowStart = getTimeMinutes(slot.time);
  return lessons.value
    .filter((lesson) => lesson.day === selectedDayCode.value)
    .filter((lesson) => Number(lesson.room_id) === Number(roomId))
    .filter((lesson) => Math.floor(getTimeRange(lesson.time).start / 60) * 60 === rowStart);
};

const getOverlappingCellLessons = (roomId: number, timeId: number) => {
  const slot = timeSlots.value.find((item) => Number(item.id) === Number(timeId));
  if (!slot) return [];
  const rowStart = getTimeMinutes(slot.time);
  return lessons.value
    .filter((lesson) => lesson.day === selectedDayCode.value)
    .filter((lesson) => Number(lesson.room_id) === Number(roomId))
    .filter((lesson) => {
      const { start, end } = getTimeRange(lesson.time);
      return start < rowStart + 60 && end > rowStart;
    });
};

const getContinuingLessons = (roomId: number, timeId: number) => {
  const slot = timeSlots.value.find((item) => Number(item.id) === Number(timeId));
  if (!slot) return [];
  const rowStart = getTimeMinutes(slot.time);
  return getOverlappingCellLessons(roomId, timeId)
    .filter((lesson) => getTimeRange(lesson.time).start < rowStart)
    .filter((lesson) => getPresentStudentCount(lesson) > 0)
    .filter(matchesStudentSearch);
};

const getContinuingTrials = (roomId: number, timeId: number) => {
  const slot = timeSlots.value.find((item) => Number(item.id) === Number(timeId));
  if (!slot) return [];
  const rowStart = getTimeMinutes(slot.time);
  const visibleIds = new Set(getOverlappingCellLessons(roomId, timeId).flatMap((lesson) => [
    ...(lesson.scheduled_trial_students || []),
    ...(lesson.continuing_trial_students || []),
  ]).map((student) => student.trial_session_id).filter(Boolean));
  return lessons.value
    .filter((lesson) => Number(lesson.room_id) === Number(roomId))
    .flatMap((lesson) => (lesson.scheduled_trial_students || []).filter((student) =>
      student.trial_session_id && student.trial_time &&
      !visibleIds.has(student.trial_session_id) &&
      getTimeRange(student.trial_time).start < rowStart &&
      getTimeRange(student.trial_time).end > rowStart &&
      (!studentKeyword.value.trim() || student.name.toLowerCase().includes(studentKeyword.value.trim().toLowerCase()))
    ));
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
      id: student.trial_session_id || student.trial_request_id,
      studentId: student.student_id,
      name: student.name,
      type: 'trial',
      badge: student.trial_time ? `Trial · ${student.trial_time}` : 'Trial',
      commentDone: !!student.comment_done,
      absentMarked: !!student.absent_marked,
    }));
  const continuingTrialStudents: DisplayStudent[] = (lesson.continuing_trial_students || []).map((student) => ({
    id: student.trial_session_id,
    studentId: student.student_id,
    name: student.name,
    type: 'trial',
    badge: `Trial continues · ${student.trial_course}`,
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
    ...continuingTrialStudents,
    ...classPassStudents,
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

const countsTowardRoomCapacity = (student: DisplayStudent) => {
  return ['normal', 'rescheduled', 'trial', 'class_pass', 'moved'].includes(student.type);
};

const getPresentStudentCount = (lesson: LessonItem) => {
  return getDisplayStudents(lesson).filter(
    countsTowardRoomCapacity
  ).length;
};

const isLessonFull = (lesson: LessonItem) => {
  const capacity = getLessonCapacity(lesson);
  return capacity > 0 && getRoomSlotPresentStudentCount(lesson) >= capacity;
};

const getRoomSlotPresentStudentCount = (lesson: LessonItem) => {
  const { start, end } = getTimeRange(lesson.time);
  const counts = timeSlots.value
    .filter((slot) => isStandardHourTime(slot.time))
    .filter((slot) => getTimeMinutes(slot.time) < end && getTimeMinutes(slot.time) + 60 > start)
    .map((slot) => getCellPresentStudentCount(Number(lesson.room_id), slot.id));
  return Math.max(0, ...counts);
};

const isSameRoomSlot = (left: LessonItem, right: LessonItem) => {
  return Number(left.room_id) === Number(right.room_id) &&
    left.day === right.day &&
    left.time === right.time;
};

const getCellCapacity = (roomId: number, timeId: number) => {
  const lessonsInCell = getRawCellLessons(roomId, timeId);
  if (lessonsInCell.length) {
    return getLessonCapacity(lessonsInCell[0]);
  }
  const room = rooms.value.find((item) => Number(item.id) === Number(roomId));
  const capacity = Number(room?.seat);
  return Number.isFinite(capacity) && capacity > 0 ? capacity : 0;
};

const getCellPresentStudentCount = (roomId: number, timeId: number) => {
  return getContinuingTrials(roomId, timeId).length + getOverlappingCellLessons(roomId, timeId).reduce(
    (total, lesson) => total + getPresentStudentCount(lesson),
    0
  );
};

const isCellFull = (roomId: number, timeId: number) => {
  const capacity = getCellCapacity(roomId, timeId);
  return capacity > 0 && getCellPresentStudentCount(roomId, timeId) >= capacity;
};

const getLessonEndMinutes = (lesson: LessonItem) => {
  return getTimeRange(lesson.time).end;
};

const isLessonEnded = (lesson: LessonItem) => {
  const today = dayjs();
  if (selectedDate.value.isBefore(today, 'day')) {
    return true;
  }
  if (selectedDate.value.isAfter(today, 'day')) {
    return false;
  }
  return today.hour() * 60 + today.minute() >= getLessonEndMinutes(lesson);
};

const needsLessonComment = (student: DisplayStudent) => {
  return ['normal', 'rescheduled', 'trial', 'moved'].includes(student.type);
};

const getCommentStatusLabel = (lesson: LessonItem, student: DisplayStudent) => {
  if (!isLessonEnded(lesson) || !needsLessonComment(student)) {
    return '';
  }
  if (student.commentDone) {
    return 'Done';
  }
  if (student.absentMarked) {
    return 'Absent';
  }
  return 'Comment needed';
};

const getCommentStatusClass = (student: DisplayStudent) => {
  if (student.commentDone) {
    return 'comment-done';
  }
  if (student.absentMarked) {
    return 'comment-absent';
  }
  return 'comment-needed';
};

const getAttendanceKey = (lesson: LessonItem, student: DisplayStudent) => {
  return `${lesson.lesson_id || lesson.id}:${student.studentId}`;
};

const canMarkAttendance = (lesson: LessonItem, student: DisplayStudent) => {
  return !lesson.virtual_trial && isLessonEnded(lesson) && needsLessonComment(student) && (!student.commentDone || student.absentMarked);
};

const toggleAbsent = async (lesson: LessonItem, student: DisplayStudent) => {
  const key = getAttendanceKey(lesson, student);
  savingAttendanceKey.value = key;
  try {
    const response = await markAbsentApi({
      lesson_id: Number(lesson.lesson_id || lesson.id),
      student_id: student.studentId,
      lesson_date: selectedDate.value.format('YYYY-MM-DD'),
      is_absent: !student.absentMarked,
    });
    if (response.code !== 0) {
      message.error(response.msg || 'Failed to update attendance');
      return;
    }
    message.success(response.data?.is_absent ? 'Marked absent' : 'Absent cleared');
    await loadSelectedDate();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to update attendance');
  } finally {
    savingAttendanceKey.value = '';
  }
};

const getTeacherFallback = (roomId: number) => {
  const roomIndex = Math.max(rooms.value.findIndex((room) => room.id === roomId), 0);
  return teacherNames[roomIndex % teacherNames.length];
};

const getTeacherPreset = (roomId: number) => {
  return teacherAssignments.value[String(roomId)] || getTeacherFallback(roomId);
};

const runAutoScroll = () => {
  const scrollEl = scheduleScrollRef.value;
  if (!scrollEl || !draggedStudent.value || (!autoScrollVector.x && !autoScrollVector.y)) {
    autoScrollFrame.value = null;
    return;
  }
  scrollEl.scrollLeft += autoScrollVector.x;
  scrollEl.scrollTop += autoScrollVector.y;
  autoScrollFrame.value = window.requestAnimationFrame(runAutoScroll);
};

const stopAutoScroll = () => {
  autoScrollVector.x = 0;
  autoScrollVector.y = 0;
  if (autoScrollFrame.value !== null) {
    window.cancelAnimationFrame(autoScrollFrame.value);
    autoScrollFrame.value = null;
  }
};

const startAutoScroll = () => {
  if (autoScrollFrame.value === null && (autoScrollVector.x || autoScrollVector.y)) {
    autoScrollFrame.value = window.requestAnimationFrame(runAutoScroll);
  }
};

const edgeSpeed = (distance: number, edgeSize: number) => {
  const intensity = Math.max(0, Math.min(1, (edgeSize - distance) / edgeSize));
  return Math.ceil(4 + intensity * 18);
};

const handleScheduleDragOver = (event: DragEvent) => {
  if (!draggedStudent.value || !scheduleScrollRef.value) {
    stopAutoScroll();
    return;
  }

  const edgeSize = 56;
  const rect = scheduleScrollRef.value.getBoundingClientRect();
  const leftDistance = event.clientX - rect.left;
  const rightDistance = rect.right - event.clientX;
  const topDistance = event.clientY - rect.top;
  const bottomDistance = rect.bottom - event.clientY;

  autoScrollVector.x = 0;
  autoScrollVector.y = 0;
  if (leftDistance >= 0 && leftDistance < edgeSize) {
    autoScrollVector.x = -edgeSpeed(leftDistance, edgeSize);
  } else if (rightDistance >= 0 && rightDistance < edgeSize) {
    autoScrollVector.x = edgeSpeed(rightDistance, edgeSize);
  }
  if (topDistance >= 0 && topDistance < edgeSize) {
    autoScrollVector.y = -edgeSpeed(topDistance, edgeSize);
  } else if (bottomDistance >= 0 && bottomDistance < edgeSize) {
    autoScrollVector.y = edgeSpeed(bottomDistance, edgeSize);
  }

  if (autoScrollVector.x || autoScrollVector.y) {
    startAutoScroll();
  } else {
    stopAutoScroll();
  }
};

const handleScheduleWheel = (event: WheelEvent) => {
  const scrollEl = scheduleScrollRef.value;
  if (!scrollEl || (!event.shiftKey && !event.deltaX)) {
    return;
  }
  if (event.cancelable) {
    event.preventDefault();
  }
  scrollEl.scrollLeft += event.shiftKey ? event.deltaY : event.deltaX;
};

const handleScheduleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && draggedStudent.value) {
    stopAutoScroll();
    draggedStudent.value = null;
  }
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
  const date = selectedDate.value.format('YYYY-MM-DD');
  try {
    const response = await listAdjustmentsApi({
      date,
    });
    if (selectedDate.value.format('YYYY-MM-DD') === date) {
      savedAdjustments.value = response.data || [];
    }
  } catch (error) {
    if (selectedDate.value.format('YYYY-MM-DD') === date) {
      savedAdjustments.value = [];
    }
    console.log(error);
  }
};

const enterAdjustmentMode = () => {
  if (!canManageSchedule.value) {
    message.warning('Teacher accounts can view schedules and write comments only');
    return;
  }
  adjustmentMode.value = true;
  adjustmentScope.value = 'date';
  loadPermanentChanges();
};

const exitAdjustmentMode = () => {
  if (draftActions.value.length) {
    message.warning('Save or discard unsaved changes before exiting');
    return;
  }
  clearSelectedStudent();
  adjustmentMode.value = false;
};

const canDragStudent = (student: DisplayStudent) => {
  return canManageSchedule.value && adjustmentMode.value && ['normal', 'moved'].includes(student.type);
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
  if (!canManageSchedule.value) {
    return;
  }
  if (!canDragStudent(student)) {
    return;
  }
  if (adjustmentScope.value === 'future') {
    openPermanentChange(lesson, student);
    return;
  }
  if (isSelectedStudent(lesson, student)) {
    clearSelectedStudent();
    return;
  }
  draggedStudent.value = {
    lesson,
    student,
    sourceDate: selectedDate.value.format('YYYY-MM-DD'),
  };
  message.info(`${student.name} selected. Choose a date, then click a target class.`);
};

const clearSelectedStudent = () => {
  draggedStudent.value = null;
};

const selectDateForMove = () => {
  if (draggedStudent.value) {
    message.info('Choose a date from the left, then click the target class.');
  }
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
  if (capacity <= 0 || isSameRoomSlot(dragged.lesson, targetLesson)) {
    return true;
  }
  return getRoomSlotPresentStudentCount(targetLesson) < capacity;
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
  if (capacity > 0 && !isSameRoomSlot(dragged.lesson, targetLesson) && getRoomSlotPresentStudentCount(targetLesson) >= capacity) {
    return 'This room slot is full';
  }
  return 'Release to move the student here';
};

const startStudentDrag = (event: DragEvent, lesson: LessonItem, student: DisplayStudent) => {
  if (!canManageSchedule.value) {
    event.preventDefault();
    return;
  }
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
  draggedStudent.value = {
    lesson,
    student,
    sourceDate: selectedDate.value.format('YYYY-MM-DD'),
  };
};

const endStudentDrag = () => {
  stopAutoScroll();
  draggedStudent.value = null;
};

const dropStudent = (targetLesson: LessonItem) => {
  stopAutoScroll();
  if (!canManageSchedule.value) {
    return;
  }
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
  const capacity = getLessonCapacity(targetLesson);
  if (capacity > 0 && !isSameRoomSlot(dragged.lesson, targetLesson) && getRoomSlotPresentStudentCount(targetLesson) >= capacity) {
    message.error('Target room slot is full');
    return;
  }
  draftActions.value.push({
    type: 'move',
    student_id: dragged.student.studentId,
    student_name: dragged.student.name,
    source_lesson_id: sourceLessonId,
    source_lesson_date: dragged.sourceDate,
    source_class: dragged.lesson.class_name || 'Untitled class',
    target_lesson_id: targetLessonId,
    target_lesson_date: selectedDate.value.format('YYYY-MM-DD'),
    target_class: targetLesson.class_name || 'Untitled class',
    term_title: dragged.student.title,
  });
  draggedStudent.value = null;
};

const dropStudentToCell = (room: RoomItem, slot: TimeItem) => {
  if (!adjustmentMode.value || !draggedStudent.value) {
    return;
  }
  const targetLessons = getRawCellLessons(room.id, slot.id);
  if (targetLessons.length === 1) {
    dropStudent(targetLessons[0]);
    return;
  }
  if (targetLessons.length > 1) {
    message.info('Choose the specific course block in this room and time');
    return;
  }
  message.warning('No course is configured in this room and time. Add a course first.');
};

const openSickLeave = (lesson: LessonItem, student: DisplayStudent) => {
  if (!canManageSchedule.value) {
    return;
  }
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

const removeDraftAction = (index: number) => {
  draftActions.value.splice(index, 1);
};

const saveAdjustments = async () => {
  if (!canManageSchedule.value) {
    return;
  }
  savingAdjustments.value = true;
  try {
    await saveBatchApi({
      lesson_date: selectedDate.value.format('YYYY-MM-DD'),
      actions: JSON.stringify(draftActions.value),
    });
    draftActions.value = [];
    notifyScheduleDataChanged();
    message.success('Daily adjustments saved');
    await loadSelectedDate();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save adjustments');
  } finally {
    savingAdjustments.value = false;
  }
};

const getRevertConfirmation = (record: SavedAdjustment) =>
  record.adjustment_type === 'sick_leave'
    ? `Revert ${record.student_name}'s sick leave? Any deducted lesson will be restored.`
    : `Revert ${record.student_name}'s move? Their original class will be restored.`;

const getSavedAdjustment = (lesson: LessonItem, student: DisplayStudent) => {
  if (!canManageSchedule.value || !['moved', 'sick'].includes(student.type)) return null;
  const lessonId = Number(lesson.lesson_id || lesson.id);
  return savedAdjustments.value.find((record) =>
    record.id === student.id && record.student_id === student.studentId &&
    (student.type === 'sick' ? record.source_lesson_id === lessonId : record.target_lesson_id === lessonId)
  ) || null;
};

const revertSavedAdjustment = async (record: SavedAdjustment) => {
  if (!canManageSchedule.value) {
    return;
  }
  const date = selectedDate.value.format('YYYY-MM-DD');
  if (
    revertingAdjustmentId.value !== null ||
    !savedAdjustments.value.some((item) => item.id === record.id) ||
    (record.source_lesson_date !== date && record.target_lesson_date !== date)
  ) {
    return;
  }
  revertingAdjustmentId.value = record.id;
  try {
    const response = await revertAdjustmentApi({ id: record.id });
    if (response.code !== 0) {
      message.error(response.msg || 'Failed to revert adjustment');
      return;
    }
    notifyScheduleDataChanged();
    message.success(`${record.student_name}'s adjustment reverted`);
    await loadSelectedDate();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to revert adjustment');
  } finally {
    revertingAdjustmentId.value = null;
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
  if (!canManageSchedule.value) {
    return;
  }
  permanentModal.studentId = student.studentId;
  permanentModal.studentName = student.name;
  permanentModal.sourceLessonId = Number(lesson.lesson_id || lesson.id);
  permanentModal.sourceClass = lesson.class_name || 'Untitled class';
  permanentModal.earliestDate = selectedDate.value;
  permanentModal.courseName = undefined;
  permanentModal.firstClassDate = null;
  permanentModal.targetLessonId = undefined;
  permanentModal.reason = '';
  permanentModal.options = [];
  permanentModal.targetOptions = [];
  permanentModal.visible = true;
  loadPermanentOptions();
};

const loadPermanentOptions = async () => {
  if (!permanentModal.studentId || !permanentModal.sourceLessonId) {
    return;
  }
  permanentModal.loadingOptions = true;
  try {
    const response = await permanentOptionsApi({
      student_id: permanentModal.studentId,
      source_lesson_id: permanentModal.sourceLessonId,
      effective_date: permanentModal.earliestDate.format('YYYY-MM-DD'),
    });
    if (response.code !== 0) throw new Error(response.msg || 'No classes available on this date');
    permanentModal.options = response.data || [];
  } catch (error: any) {
    permanentModal.options = [];
    message.error(error?.msg || 'Failed to load available classes');
  } finally {
    permanentModal.loadingOptions = false;
  }
};

const onPermanentCourseChange = () => {
  permanentModal.firstClassDate = null;
  permanentModal.targetLessonId = undefined;
  permanentModal.targetOptions = [];
};

const isPermanentDateDisabled = (date: Dayjs) => {
  const options = permanentModal.options.filter((item) => item.class_name === permanentModal.courseName);
  if (!options.length || date.isBefore(permanentModal.earliestDate, 'day')) return true;
  const day = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.day()];
  return !options.some((item) => item.day === day &&
    !date.isAfter(dayjs(item.enrollment_end_date), 'day'));
};

const onPermanentDateChange = async () => {
  permanentModal.targetLessonId = undefined;
  permanentModal.targetOptions = [];
  if (!permanentModal.firstClassDate || !permanentModal.courseName) return;
  const course = permanentModal.courseName;
  const date = permanentModal.firstClassDate.format('YYYY-MM-DD');
  permanentModal.loadingTargets = true;
  try {
    const response = await permanentOptionsApi({
      student_id: permanentModal.studentId,
      source_lesson_id: permanentModal.sourceLessonId,
      effective_date: date,
      course,
    });
    if (response.code !== 0) throw new Error(response.msg || 'No classes available on this date');
    if (permanentModal.courseName === course && permanentModal.firstClassDate?.format('YYYY-MM-DD') === date) {
      permanentModal.targetOptions = response.data || [];
    }
  } catch (error: any) {
    message.error(error?.message || error?.msg || 'Failed to load available classes');
  } finally {
    permanentModal.loadingTargets = false;
  }
};

const savePermanentChange = async () => {
  if (!canManageSchedule.value) {
    return;
  }
  if (!permanentModal.firstClassDate || !permanentModal.targetLessonId) {
    message.warning('Select the first class date, time and room');
    return;
  }
  permanentModal.saving = true;
  try {
    const response = await createPermanentApi({
      student_id: permanentModal.studentId,
      source_lesson_id: permanentModal.sourceLessonId,
      target_lesson_id: permanentModal.targetLessonId,
      effective_date: permanentModal.firstClassDate.format('YYYY-MM-DD'),
      reason: permanentModal.reason,
    });
    if (response.code !== 0) {
      message.error(response.msg || 'Failed to save permanent course change');
      return;
    }
    permanentModal.visible = false;
    notifyScheduleDataChanged();
    message.success('Permanent course change saved');
    await Promise.all([loadSelectedDate(), loadPermanentChanges()]);
  } catch (error: any) {
    message.error(error?.msg || 'Failed to save permanent course change');
  } finally {
    permanentModal.saving = false;
  }
};

const revertPermanentChange = async (record: any) => {
  if (!canManageSchedule.value || revertingPermanentId.value !== null ||
      !permanentChanges.value.some((item) => item.id === record.id)) return;
  revertingPermanentId.value = record.id;
  try {
    const response = await revertPermanentApi({ id: record.id });
    if (response.code !== 0) {
      message.error(response.msg || 'Failed to revert permanent course change');
      return;
    }
    notifyScheduleDataChanged();
    message.success(`${record.student_name}'s permanent change reverted`);
    await Promise.all([loadSelectedDate(), loadPermanentChanges()]);
  } catch (error: any) {
    message.error(error?.msg || 'Failed to revert permanent course change');
  } finally {
    revertingPermanentId.value = null;
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

const openStudentDetail = (student: DisplayStudent) => {
  router.push({
    name: 'student',
    query: {
      id: student.studentId,
      returnTo: route.fullPath,
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

.selected-move-student {
  border-radius: 4px;
  background: #dbeafe;
  color: #174ea6 !important;
  font-weight: 700;
  padding: 3px 6px;
}

.saved-adjustments {
  margin-top: 8px;
  border-bottom: 1px solid #d0d5dd;
  padding: 4px 2px 8px;
}

.saved-adjustments > strong {
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
}

.saved-adjustment-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 5px 0;
}

.saved-adjustment-row + .saved-adjustment-row {
  border-top: 1px solid #eef0f3;
}

.saved-adjustment-description {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  min-width: 0;
  font-size: 13px;
}

.saved-adjustment-row .ant-btn {
  flex: none;
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
  flex: 1;
  min-width: 0;
  margin: 0;
  color: #344054;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.announcement-input {
  flex: 1;
  min-width: 180px;
  font-size: 13px;
}

.announcement :deep(.ant-btn-link) {
  padding-inline: 4px;
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
  overscroll-behavior: contain;
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

.room-header .teacher-name {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--room-text);
  font-size: 11px;
  font-weight: 600;
  min-width: 0;
}

.teacher-edit-btn {
  width: 18px;
  height: 18px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--room-text);
  cursor: pointer;
  opacity: 0.72;
  padding: 0;
}

.teacher-edit-btn:hover {
  background: rgba(255, 255, 255, 0.7);
  opacity: 1;
}

.teacher-inline-input {
  width: 112px;
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

.slot-summary {
  margin-bottom: 7px;
  padding: 4px 6px;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  background: #f8fafc;
  color: #475467;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  line-height: 16px;
}

.slot-summary strong {
  color: #344054;
  font-size: 12px;
}

.slot-summary.full strong {
  color: #b42318;
}

.slot-continuation {
  padding: 3px 2px;
  color: #667085;
  font-size: 11px;
  line-height: 15px;
}

.slot-continuation.trial-continuation {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 4px;
  margin: 4px 8px;
  padding: 7px 9px;
  border: 1px solid #d6bbfb;
  border-radius: 4px;
  background: #f9f5ff;
  color: #6941c6;
}

.trial-continuation button {
  border: 0;
  background: transparent;
  color: #6941c6;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.lesson-block {
  border: 1px solid var(--lesson-border);
  border-radius: 4px;
  background: color-mix(in srgb, var(--lesson-bg) 72%, white);
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
  margin-top: 6px;
}

.lesson-heading {
  width: 100%;
  min-height: 28px;
  padding: 5px 7px;
  border: 0;
  border-bottom: 1px solid color-mix(in srgb, var(--lesson-border) 58%, transparent);
  background: color-mix(in srgb, var(--lesson-bg) 86%, white);
  color: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  text-align: left;
}

.lesson-heading strong,
.lesson-heading small {
  display: inline;
}

.lesson-heading strong {
  font-size: 12px;
  line-height: 16px;
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

.student-main .comment-status {
  border-radius: 999px;
  padding: 2px 5px;
  text-transform: none;
}

.comment-needed {
  background: #fff4e5;
  color: #b54708;
}

.comment-done {
  background: #ecfdf3;
  color: #027a48;
}

.comment-absent {
  background: #fef3f2;
  color: #b42318;
}

.attendance-button {
  flex: 0 0 auto;
  min-width: 58px;
  height: 30px;
  border: 0;
  border-left: 1px solid rgba(152, 162, 179, 0.45);
  background: rgba(255, 255, 255, 0.52);
  color: #667085;
  cursor: pointer;
  font-size: 10px;
  font-weight: 700;
  padding: 0 6px;
  white-space: nowrap;
}

.attendance-button:hover,
.attendance-button.absent {
  background: #fef3f2;
  color: #b42318;
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

  .adjustment-toolbar {
    position: static;
    flex-direction: column;
    align-items: stretch;
  }

  .adjustment-mode,
  .adjustment-actions {
    width: 100%;
  }

  .adjustment-mode :deep(.ant-radio-group) {
    display: flex;
    width: 100%;
  }

  .adjustment-mode :deep(.ant-radio-button-wrapper) {
    flex: 1;
    height: auto;
    padding: 5px 7px;
    text-align: center;
    white-space: normal;
    line-height: 20px;
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
