<template>
  <div>
    <div v-if="!route.query.id" class="page-view">
      <div class="table-operations">
        <a-space>
          <a-button v-if="canManageStudents" type="primary" @click="handleAdd">New</a-button>
          <a-button v-if="canManageStudents" type="primary" @click="openQuickAdd">Quick Add Student</a-button>
          <a-button v-if="canManageStudents" @click="openTrialBooking">New trial student</a-button>
          <a-button v-if="canManageStudents" @click="openCreationLog">Add history</a-button>
          <a-button v-if="canManageStudents" @click="openImportComments">Import Comments</a-button>
          <a-button v-if="canManageStudents" danger @click="handleBatchDelete">Mass Delete</a-button>
          <a-input-search addon-before="Student" enter-button @search="onSearch" @change="onSearchChange" />
        </a-space>
      </div>

      <a-table
        size="middle"
        rowKey="id"
        :loading="data.loading"
        :columns="columns"
        :data-source="data.studentList"
        :scroll="{ x: 1200 }"
        :row-selection="canManageStudents ? rowSelection : null"
        :pagination="{
          size: 'default',
          current: data.page,
          pageSize: data.pageSize,
          onChange: (current) => (data.page = current),
          showSizeChanger: false,
          showTotal: (total) => `Total of ${total} data`,
        }"
      >
        <template #bodyCell="{ text, record, column }">
          <template v-if="column.key === 'parent'">
            <div class="parent-identity">
              <strong>{{ record.parent_name || record.parent_username || '-' }}</strong>
              <span v-if="record.parent_username">@{{ record.parent_username }}</span>
              <span v-if="record.parent">User ID {{ record.parent }}</span>
            </div>
          </template>
          <template v-if="column.key === 'active_classes'">
            <div class="class-list">
              <div v-for="item in record.active_classes" :key="item">{{ item }}</div>
              <span v-if="!record.active_classes || record.active_classes.length === 0">-</span>
            </div>
          </template>
          <template v-if="column.key === 'active_terms'">
            <span>{{ formatList(record.active_terms) }}</span>
          </template>
          <template v-if="column.key === 'absences'">
            <a-badge
              :count="record.absence_records?.length || 0"
              :show-zero="true"
              :number-style="{
                backgroundColor: record.absence_records?.length ? '#fff1f0' : '#f5f5f5',
                color: record.absence_records?.length ? '#cf1322' : '#8c8c8c',
                boxShadow: 'none',
              }"
            />
          </template>
          <template v-if="column.key === 'operation'">
            <span>
              <a @click="handleView(record)">View Detail</a>
              <template v-if="canManageStudents">
                <a-divider type="vertical" />
                <a @click="handleEdit(record)">Edit</a>
                <a-divider type="vertical" />
                <a-popconfirm title="Sure to delete?" ok-text="Yes" cancel-text="No" @confirm="confirmDelete(record)">
                <a href="#" style="color: red;">Delete</a>
                </a-popconfirm>
              </template>
            </span>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      :visible="modal.visible"
      :forceRender="true"
      :title="modal.title"
      ok-text="OK"
      cancel-text="Cancel"
      @cancel="handleCancel"
      @ok="handleOk"
    >
      <a-form ref="myform" :label-col="{ style: { width: '110px' } }" :model="modal.form" :rules="modal.rules">
        <a-row :gutter="24">
          <a-col span="24">
            <a-form-item label="Student name" name="name">
              <a-input placeholder="Please enter" v-model:value="modal.form.name" allowClear />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="Age" name="age">
              <a-input-number placeholder="Please enter" v-model:value="modal.form.age" :min="1" :max="99" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="Gender" name="gender">
              <a-select
                placeholder="Optional"
                allowClear
                v-model:value="modal.form.gender"
                :options="[
                  { value: 'M', label: 'Male' },
                  { value: 'F', label: 'Female' },
                  { value: 'Other', label: 'Other' },
                ]"
              />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="Parent" name="parent" extra="Optional. You can link a parent account later.">
              <a-select
                placeholder="Optional"
                allowClear
                show-search
                optionFilterProp="label"
                v-model:value="modal.form.parent"
                :options="modal.parentData"
              />
            </a-form-item>
          </a-col>
          <a-col span="24">
            <a-form-item label="Remark" name="remark">
              <a-textarea
                v-model:value="modal.form.remark"
                placeholder="Optional internal note"
                :rows="3"
                :maxlength="500"
                show-count
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <a-drawer
      :visible="quick.visible"
      title="Quick Add Student"
      placement="right"
      width="min(560px, 100vw)"
      @close="closeQuickAdd"
    >
      <a-form :label-col="{ style: { width: '120px' } }">
        <a-divider orientation="left">Student information</a-divider>
        <a-form-item label="Student name" required>
          <a-input v-model:value="quick.form.name" placeholder="Required" allowClear />
        </a-form-item>
        <a-form-item label="Age">
          <a-input-number v-model:value="quick.form.age" :min="1" :max="99" style="width: 100%" />
        </a-form-item>
        <a-form-item label="Gender">
          <a-select
            v-model:value="quick.form.gender"
            placeholder="Optional"
            allow-clear
            :options="[
              { value: 'M', label: 'Male' },
              { value: 'F', label: 'Female' },
              { value: 'Other', label: 'Other' },
            ]"
          />
        </a-form-item>
        <a-form-item label="Parent" extra="Optional. You can link a parent account later.">
          <a-select
            v-model:value="quick.form.parent"
            placeholder="Optional"
            allow-clear
            show-search
            optionFilterProp="label"
            :options="quick.parentData"
          />
        </a-form-item>
        <a-form-item label="Note">
          <a-textarea v-model:value="quick.form.remark" :rows="2" :maxlength="500" show-count />
        </a-form-item>

        <a-divider orientation="left">First class</a-divider>
        <a-form-item label="Term" required>
          <a-select
            v-model:value="quick.form.term"
            placeholder="Select term"
            show-search
            optionFilterProp="label"
            allow-clear
            @change="handleQuickTermChange"
          >
            <a-select-option
              v-for="term in quick.terms"
              :key="term.id"
              :value="term.id"
              :label="term.title"
            >
              {{ term.title }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <div class="quick-filter-grid">
          <a-form-item label="Start date" required>
            <a-date-picker
              v-model:value="quick.form.startDate"
              value-format="YYYY-MM-DD"
              :disabled-date="disableQuickStartDate"
              style="width: 100%"
              @change="clearQuickResults"
            />
          </a-form-item>
          <a-form-item label="End date" required>
            <a-date-picker
              v-model:value="quick.form.endDate"
              value-format="YYYY-MM-DD"
              :disabled-date="disableQuickEndDate"
              style="width: 100%"
              @change="clearQuickResults"
            />
          </a-form-item>
        </div>
        <a-form-item label="Course" required>
          <a-select
            v-model:value="quick.form.course"
            placeholder="Select course"
            show-search
            optionFilterProp="label"
            allow-clear
            @change="handleQuickCourseChange"
          >
            <a-select-option
              v-for="course in quickCourseOptions"
              :key="course"
              :value="course"
              :label="course"
            >
              {{ course }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <div class="quick-filter-grid">
          <a-form-item label="Day">
            <a-select v-model:value="quick.form.day" placeholder="Any day" allow-clear @change="clearQuickResults">
              <a-select-option v-for="day in quickDayOptions" :key="day" :value="day">
                {{ dayLabel(day) }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="Time">
            <a-select v-model:value="quick.form.time" placeholder="Any time" allow-clear @change="clearQuickResults">
              <a-select-option v-for="time in quickTimeOptions" :key="time.id" :value="time.id">
                {{ time.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </div>
        <a-button block :loading="quick.searching" @click="findAvailableSlots">Find Available Slots</a-button>

        <div v-if="quick.results.length" class="quick-results">
          <div class="quick-results-title">Available rooms and times</div>
          <button
            v-for="slot in quick.results"
            :key="slot.slot_key"
            type="button"
            class="quick-slot"
            :class="{ selected: quick.selectedSlot?.slot_key === slot.slot_key, full: !isQuickSlotAvailable(slot) }"
            :disabled="!isQuickSlotAvailable(slot)"
            @click="selectQuickSlot(slot)"
          >
            <span class="quick-slot-main">
              <strong>{{ slot.title }}</strong>
              <small v-if="slot.new_class">New class</small>
              <span>{{ dayLabel(slot.day) }} {{ slot.time || '-' }} · {{ slot.room || 'Room TBD' }}</span>
            </span>
            <span class="quick-slot-capacity">
              {{ slot.enrolled_count }}/{{ slot.capacity ?? '-' }}
              <small v-if="slot.available_seats !== null && slot.available_seats !== undefined">
                {{ isQuickSlotAvailable(slot) ? `${slot.available_seats} left` : 'Full' }}
              </small>
            </span>
          </button>
        </div>
        <a-empty v-else-if="quick.searched" description="No matching class found" />
      </a-form>

      <template #footer>
        <div class="quick-drawer-footer">
          <a-button @click="closeQuickAdd">Cancel</a-button>
          <a-button type="primary" :loading="quick.saving" :disabled="!quick.selectedSlot" @click="saveQuickStudent">
            Save Student & Class
          </a-button>
        </div>
      </template>
    </a-drawer>

    <a-drawer
      :visible="creationLog.visible"
      title="Student additions"
      placement="right"
      width="min(560px, 100vw)"
      @close="creationLog.visible = false"
    >
      <a-alert
        v-if="creationLog.rows.some((row) => !row.confirmed)"
        type="info"
        show-icon
        message="Older entries are request records; their success cannot be verified from the old log."
        class="creation-log-notice"
      />
      <a-table
        size="small"
        rowKey="id"
        :loading="creationLog.loading"
        :columns="creationLogColumns"
        :data-source="creationLog.rows"
        :scroll="{ x: 520 }"
        :pagination="{ pageSize: 10, showSizeChanger: false }"
      >
        <template #bodyCell="{ record, column }">
          <template v-if="column.key === 'student'">
            <span v-if="record.student_name">{{ record.student_name }} <small>#{{ record.student_id }}</small></span>
            <span v-else-if="record.student_id">Student #{{ record.student_id }} (deleted)</span>
            <span v-else>Not recorded</span>
          </template>
          <template v-if="column.key === 'source'">{{ creationSourceLabel(record.source) }}</template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.confirmed ? 'green' : 'default'">
              {{ record.confirmed ? 'Created' : 'Unverified' }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-drawer>

    <a-modal
      :visible="importModal.visible"
      title="Import student comments"
      ok-text="Import"
      cancel-text="Cancel"
      :confirm-loading="importModal.loading"
      @cancel="closeImportComments"
      @ok="submitImportComments"
    >
      <div class="import-help">
        Upload a CSV file with headers. Supported formats:
        <code>student_id,comment,created_time</code>
        or
        <code>student_name,parent_username,comment,created_time</code>.
      </div>
      <a-upload
        accept=".csv,text/csv"
        :before-upload="beforeImportFileUpload"
        :file-list="importModal.fileList"
        :max-count="1"
        @remove="removeImportFile"
      >
        <a-button>Select CSV File</a-button>
      </a-upload>
      <div class="import-fallback-label">Optional: paste CSV here if you do not want to select a file.</div>
      <a-textarea
        v-model:value="importModal.text"
        :rows="6"
        placeholder="student_name,parent_username,comment,created_time&#10;Ivy Demo,parent_02,Great focus in robotics,2026-05-18 16:30"
      />
      <div v-if="importModal.result" class="import-result">
        Imported {{ importModal.result.created_count }} comments.
        <span v-if="importModal.result.error_count">
          {{ importModal.result.error_count }} rows need review.
        </span>
      </div>
      <div v-if="importModal.result?.errors?.length" class="import-errors">
        <div v-for="error in importModal.result.errors.slice(0, 5)" :key="`${error.row}-${error.error}`">
          Row {{ error.row }}: {{ error.error }}
        </div>
      </div>
    </a-modal>

    <a-modal
      :visible="detail.visible"
      title="Student Detail"
      width="820px"
      :footer="null"
      @cancel="closeDetail"
    >
      <a-spin :spinning="detail.loading">
      <div class="detail-view">
        <div class="detail-row">
          <span class="detail-label">Student name</span>
          <span>{{ detail.record.name || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Age</span>
          <span>{{ detail.record.age || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Gender</span>
          <span>{{ detail.record.gender || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Parent</span>
          <span>
            {{ detail.record.parent_name || detail.record.parent_username || '-' }}
            <template v-if="detail.record.parent_username"> · @{{ detail.record.parent_username }}</template>
            <template v-if="detail.record.parent"> · User ID {{ detail.record.parent }}</template>
          </span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Phone</span>
          <span>{{ detail.record.phone || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Active terms</span>
          <span>{{ formatList(detail.record.active_terms) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Remark</span>
          <span>{{ detail.record.remark || '-' }}</span>
        </div>
        <div v-if="detail.record.trial_packages?.length" class="detail-row detail-row-block">
          <span class="detail-label">Trial package</span>
          <div class="trial-package-list">
            <section
              v-for="trialPackage in detail.record.trial_packages"
              :key="trialPackage.trial_request_id"
              class="trial-package-item"
            >
              <div class="trial-package-head">
                <strong>Trial</strong>
                <a-tag :color="getTrialStatusColor(trialPackage.status)">
                  {{ formatTrialStatus(trialPackage.status) }}
                </a-tag>
                <a-popconfirm
                  v-if="canManageStudents && trialPackage.source === 'admin' && trialPackage.status === 'active'"
                  title="Cancel both trial sessions?"
                  ok-text="Cancel package"
                  cancel-text="Keep"
                  @confirm="cancelTrialBooking(trialPackage.trial_request_id)"
                >
                  <a-button size="small" danger>Cancel trial</a-button>
                </a-popconfirm>
              </div>
              <div class="trial-course-list">
                <div
                  v-for="course in trialPackage.courses"
                  :key="course.category"
                  class="trial-course-row"
                  :class="{ 'trial-course-missing': !course.configured }"
                >
                  <strong>{{ course.category }}</strong>
                  <span v-if="course.configured">
                    {{ course.class_name }} | {{ course.scheduled_date || 'Date TBD' }} | {{ course.day }} {{ course.time }} | {{ course.room }}
                  </span>
                  <span v-else>Not selected</span>
                </div>
              </div>
            </section>
          </div>
        </div>
        <div class="detail-row detail-row-block">
          <span class="detail-label">All courses</span>
          <div class="course-history">
            <div
              v-for="course in detail.record.course_history"
              :key="course.order_id"
              class="course-history-item"
            >
              <div class="course-history-main">
                <strong>{{ course.class_name || '-' }}</strong>
                <a-tag :color="course.course_status === 'Finished' ? 'default' : 'green'">
                  {{ course.course_status }}
                </a-tag>
              </div>
              <div class="course-history-meta">
                <span>Term: {{ course.term || '-' }}</span>
                <span>{{ course.day || '-' }} {{ course.time || '-' }}</span>
                <span>{{ course.room || '-' }}</span>
                <span>{{ course.start_date || '-' }} - {{ course.end_date || '-' }}</span>
              </div>
            </div>
            <span v-if="!detail.record.course_history || detail.record.course_history.length === 0">-</span>
          </div>
        </div>
        <div class="detail-row detail-row-block">
          <span class="detail-label">Absence / Leave History</span>
          <div class="absence-history">
            <div
              v-for="absence in detail.record.absence_records"
              :key="absence.adjustment_id"
              class="absence-history-item"
            >
              <div class="absence-history-main">
                <div>
                  <strong>{{ absence.class_name || '-' }}</strong>
                  <span class="absence-date">{{ absence.lesson_date || '-' }}</span>
                </div>
                <a-tag :color="getAbsenceStatusColor(absence.status)">
                  {{ formatAbsenceStatus(absence.status) }}
                </a-tag>
              </div>
              <div class="absence-history-meta">
                <span>Term: {{ absence.term || '-' }}</span>
                <span>{{ absence.day || '-' }} {{ absence.time || '-' }}</span>
                <span>Room: {{ absence.room || '-' }}</span>
                <span>Requested: {{ absence.created_time || '-' }}</span>
              </div>
              <p v-if="absence.reason" class="absence-reason">
                Reason: {{ absence.reason }}
              </p>
            </div>
            <span v-if="!detail.record.absence_records || detail.record.absence_records.length === 0">
              No absence records
            </span>
          </div>
        </div>
        <div class="detail-row detail-row-block">
          <span class="detail-label">Internal comments</span>
          <div class="comment-history">
            <div
              v-for="comment in visibleDetailComments"
              :key="comment.id"
              class="comment-history-item"
            >
              <div class="comment-meta">
                <strong>{{ comment.created_by || 'Administrator' }}</strong>
                <span>{{ comment.created_time }}</span>
              </div>
              <p>{{ comment.content }}</p>
            </div>
            <span v-if="!detail.record.comments || detail.record.comments.length === 0">
              No comments
            </span>
            <a-button
              v-if="detail.record.comments && detail.record.comments.length > 3"
              type="link"
              class="comment-toggle"
              @click="commentsExpanded = !commentsExpanded"
            >
              {{ commentsExpanded ? 'Hide old comments' : `Show ${detail.record.comments.length - 3} older comments` }}
            </a-button>
          </div>
        </div>
      </div>
      </a-spin>
    </a-modal>

    <a-modal
      v-model:visible="trialBooking.visible"
      title="New trial student"
      width="720px"
      ok-text="Book trial"
      :confirm-loading="trialBooking.saving"
      @ok="saveTrialBooking"
    >
      <div class="trial-booking-fields">
        <a-form-item label="Student name" required>
          <a-input v-model:value="trialBooking.studentName" :maxlength="30" placeholder="Student name" />
        </a-form-item>
        <a-form-item label="Age">
          <a-input-number v-model:value="trialBooking.age" :min="1" :max="99" style="width: 100%" />
        </a-form-item>
      </div>
      <a-form-item label="Parent account" extra="Optional. Link a parent account later if needed.">
        <a-select v-model:value="trialBooking.parentId" :options="quick.parentData" show-search option-filter-prop="label" allow-clear placeholder="Select parent" />
      </a-form-item>
      <div v-for="(session, index) in trialBooking.sessions" :key="index" class="trial-booking-session">
        <strong>Session {{ index + 1 }} · 90 minutes</strong>
        <div class="trial-booking-fields">
          <a-form-item label="Subject">
            <a-select v-model:value="session.subject" :options="trialSubjects" @change="onTrialSubjectChange(index)" />
          </a-form-item>
          <a-form-item label="Date">
            <a-date-picker v-model:value="session.date" style="width: 100%" @change="loadTrialOptions(index)" />
          </a-form-item>
        </div>
        <a-form-item v-if="supportsFlexibleTrial(session.subject)" label="Booking method">
          <a-radio-group v-model:value="session.mode" button-style="solid" @change="loadTrialOptions(index)">
            <a-radio-button value="existing">Existing class</a-radio-button>
            <a-radio-button value="flexible">Flexible trial slot</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item :label="session.mode === 'flexible' ? 'Time and room' : 'Class, time and room'">
          <a-select
            v-model:value="session.selectedKey"
            :loading="session.loading"
            :disabled="!session.date"
            :options="session.options.map((item) => ({
              value: item.option_key,
              label: getTrialOptionLabel(index, item),
              disabled: item.remaining < 1 || trialOptionConflicts(index, item),
            }))"
            :placeholder="session.mode === 'flexible' ? 'Select a 90-minute time and room' : 'Select an available class'"
            @change="onTrialClassChange(index)"
          />
          <div v-if="session.loaded && !session.loading && session.date && !session.options.length" class="trial-empty-help">
            <template v-if="session.mode === 'flexible'">
              No permitted room or school time is available for this date. Check Room Course Permissions or choose another date.
            </template>
            <template v-else>
              No {{ session.subject }} class is configured for {{ session.date.format('dddd') }}. Choose another date or use a flexible trial slot.
            </template>
          </div>
          <div v-if="selectedTrialOption(session)?.teacher_confirmation_required" class="trial-teacher-warning">
            No regular class is running in this room at that time. Teacher confirmation is needed.
          </div>
        </a-form-item>
      </div>
      <a-form-item label="Note">
        <a-textarea v-model:value="trialBooking.note" :rows="2" :maxlength="500" />
      </a-form-item>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message } from 'ant-design-vue';
import dayjs, { Dayjs } from 'dayjs';
import { availableSlotsApi, createApi, creationLogApi, deleteApi, detailApi, importCommentsApi, listApi, quickCreateApi, updateApi } from '/@/api/admin/student';
import { listApi as listCourseCatalogApi } from '/@/api/admin/course';
import { listApi as listUserApi } from '/@/api/admin/user';
import { listApi as listTermApi } from '/@/api/admin/term';
import { listApi as listThingApi } from '/@/api/admin/thing';
import { optionsApi as trialOptionsApi, createApi as createTrialApi, cancelApi as cancelTrialApi } from '/@/api/admin/trial-booking';
import { ADMIN_USER_ROLE } from '/@/store/constants';
import { useRoute, useRouter } from 'vue-router';
import { notifyScheduleDataChanged } from '/@/utils/schedule-sync';

const route = useRoute();
const router = useRouter();
const canManageStudents = computed(() => localStorage.getItem(ADMIN_USER_ROLE) !== '2');

const trialSubjects = ['Robotics', 'Coding', 'AI', '3D', 'VEX IQ', 'VEX V5', 'Spark Maths']
  .map((value) => ({ value, label: value }));
type TrialSessionForm = {
  subject: string;
  date: Dayjs | null;
  mode: 'existing' | 'flexible';
  selectedKey: string | undefined;
  options: any[];
  loading: boolean;
  loaded: boolean;
};
const newTrialSession = (subject: string): TrialSessionForm => ({
  subject, date: null, mode: 'existing', selectedKey: undefined, options: [], loading: false, loaded: false,
});
const trialBooking = reactive({
  visible: false,
  saving: false,
  studentName: '',
  age: undefined as number | undefined,
  parentId: undefined as number | undefined,
  note: '',
  sessions: [newTrialSession('Robotics'), newTrialSession('Coding')] as TrialSessionForm[],
});

const selectedTrialOption = (session: TrialSessionForm) =>
  session.options.find((item) => item.option_key === session.selectedKey);

const flexibleTrialSubjects = new Set(['AI', '3D', 'VEX IQ', 'VEX V5']);
const supportsFlexibleTrial = (subject: string) => flexibleTrialSubjects.has(subject);

const trialTimesOverlap = (first: any, second: any) =>
  Boolean(first && second && first.start < second.end && second.start < first.end);

const trialOptionConflicts = (index: number, option: any) => {
  const session = trialBooking.sessions[index];
  if (!session.date) return false;
  return trialBooking.sessions.some((other, otherIndex) => {
    if (otherIndex === index || !other.date || !other.selectedKey) return false;
    if (other.date.format('YYYY-MM-DD') !== session.date!.format('YYYY-MM-DD')) return false;
    return trialTimesOverlap(option, selectedTrialOption(other));
  });
};

const getTrialOptionLabel = (index: number, option: any) => {
  const status = option.remaining < 1
    ? 'Full'
    : trialOptionConflicts(index, option)
      ? 'Time conflict with the other session'
      : `${option.remaining} seats left`;
  const teacherStatus = option.teacher_confirmation_required ? ' · Teacher confirmation needed' : '';
  return `${option.course} · ${option.start}-${option.end} · ${option.room} · ${status}${teacherStatus}`;
};

const onTrialClassChange = (index: number) => {
  const session = trialBooking.sessions[index];
  const option = selectedTrialOption(session);
  if (option && trialOptionConflicts(index, option)) {
    session.selectedKey = undefined;
    message.warning('The two trial sessions cannot overlap on the same date');
  }
};

const onTrialSubjectChange = (index: number) => {
  const session = trialBooking.sessions[index];
  if (!supportsFlexibleTrial(session.subject)) session.mode = 'existing';
  loadTrialOptions(index);
};

const trialSessionsConflict = () => {
  const [first, second] = trialBooking.sessions;
  if (!first.date || !second.date || first.date.format('YYYY-MM-DD') !== second.date.format('YYYY-MM-DD')) {
    return false;
  }
  return trialTimesOverlap(selectedTrialOption(first), selectedTrialOption(second));
};

const openTrialBooking = async () => {
  trialBooking.studentName = '';
  trialBooking.age = undefined;
  trialBooking.parentId = undefined;
  trialBooking.note = '';
  trialBooking.sessions = [newTrialSession('Robotics'), newTrialSession('Coding')];
  trialBooking.visible = true;
  try {
    if (!quick.parentData.length) {
      const response = await listUserApi({});
      quick.parentData = (response.data || [])
        .filter((item: any) => item.role === '1')
        .map((item: any) => ({ value: item.id, label: `${item.nickname || item.username} · @${item.username} · ID ${item.id}` }));
    }
  } catch (error: any) {
    message.error(error?.msg || 'Could not load parents');
  }
};

const loadTrialOptions = async (index: number) => {
  const session = trialBooking.sessions[index];
  session.selectedKey = undefined;
  session.options = [];
  session.loaded = false;
  if (!session.date || !session.subject) return;
  const queryDate = session.date.format('YYYY-MM-DD');
  const querySubject = session.subject;
  session.loading = true;
  try {
    const queryMode = session.mode;
    const response = await trialOptionsApi({ subject: querySubject, date: queryDate, mode: queryMode });
    if (session.date?.format('YYYY-MM-DD') === queryDate && session.subject === querySubject && session.mode === queryMode) {
      if (response.code !== 0) throw new Error(response.msg || 'Could not load classes');
      session.options = response.data || [];
      session.loaded = true;
    }
  } catch (error: any) {
    message.error(error?.message || error?.msg || 'Could not load classes');
  } finally {
    session.loading = false;
  }
};

const saveTrialBooking = async () => {
  if (!trialBooking.studentName.trim()) {
    message.warning('Enter the new student name');
    return;
  }
  if (trialBooking.sessions.some((session) => !session.date || !session.selectedKey)) {
    message.warning('Select the date and class for both sessions');
    return;
  }
  if (trialSessionsConflict()) {
    message.warning('The two trial sessions cannot overlap on the same date');
    return;
  }
  trialBooking.saving = true;
  try {
    const response = await createTrialApi({
      student_name: trialBooking.studentName.trim(),
      age: trialBooking.age,
      parent_id: trialBooking.parentId,
      note: trialBooking.note,
      sessions: trialBooking.sessions.map((session) => {
        const option = selectedTrialOption(session);
        return session.mode === 'flexible'
          ? {
              mode: 'flexible',
              subject: session.subject,
              date: session.date!.format('YYYY-MM-DD'),
              room_id: option.room_id,
              start: option.start,
            }
          : {
              mode: 'existing',
              date: session.date!.format('YYYY-MM-DD'),
              lesson_id: option.lesson_id,
            };
      }),
    });
    if (response.code !== 0) throw new Error(response.msg || 'Could not book trial');
    notifyScheduleDataChanged();
    message.success('Trial student and package created');
    trialBooking.visible = false;
    getDataList();
    handleView({ id: response.data.student_id });
  } catch (error: any) {
    message.error(error?.message || error?.msg || 'Could not book trial');
  } finally {
    trialBooking.saving = false;
  }
};

const cancelTrialBooking = async (packageKey: string) => {
  try {
    const response = await cancelTrialApi(packageKey);
    if (response.code !== 0) throw new Error(response.msg || 'Could not cancel trial');
    notifyScheduleDataChanged();
    message.success('Trial package canceled');
    if (detail.record.id) await loadStudentDetail(detail.record.id);
  } catch (error: any) {
    message.error(error?.message || error?.msg || 'Could not cancel trial');
  }
};

const creationLogColumns = [
  { title: 'Server time', dataIndex: 'created_time', key: 'created_time', width: 145 },
  { title: 'Student', key: 'student', width: 160 },
  { title: 'Source', key: 'source', width: 105 },
  { title: 'Result', key: 'status', width: 110 },
];
const creationLog = reactive({
  visible: false,
  loading: false,
  rows: [] as any[],
});
const creationSourceLabel = (source: string) => ({
  admin_quick: 'Quick Add',
  admin: 'Admin New',
  admin_trial: 'Trial student',
  parent: 'Parent',
} as Record<string, string>)[source] || 'Other';

const openCreationLog = async () => {
  if (!canManageStudents.value) return;
  creationLog.visible = true;
  creationLog.loading = true;
  try {
    const response = await creationLogApi();
    creationLog.rows = response.data || [];
  } catch (error: any) {
    message.error(error?.msg || 'Failed to load student additions');
  } finally {
    creationLog.loading = false;
  }
};

const columns = reactive([
  {
    title: 'No.',
    dataIndex: 'index',
    key: 'index',
    align: 'center',
    width: 80,
  },
  {
    title: 'Student name',
    dataIndex: 'name',
    key: 'name',
    align: 'center',
    width: 260,
  },
  {
    title: 'Age',
    dataIndex: 'age',
    key: 'age',
    align: 'center',
    width: 90,
  },
  {
    title: 'Parent',
    dataIndex: 'parent',
    key: 'parent',
    align: 'left',
    width: 250,
  },
  {
    title: 'Active Classes',
    dataIndex: 'active_classes',
    key: 'active_classes',
    align: 'center',
    width: 520,
  },
  {
    title: 'Absences',
    dataIndex: 'absence_records',
    key: 'absences',
    align: 'center',
    width: 100,
  },
  {
    title: 'Operation',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 270,
  },
]);

const data = reactive({
  studentList: [],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 10,
  page: 1,
});

const modal = reactive({
  visible: false,
  editFlag: false,
  title: '',
  parentData: [] as any[],
  form: {
    id: undefined,
    name: undefined,
    age: undefined,
    gender: undefined,
    parent: undefined,
    remark: undefined,
  },
  rules: {
    name: [{ required: true, message: 'Please enter student name', trigger: 'change' }],
  },
});

const detail = reactive({
  visible: false,
  loading: false,
  record: {} as any,
});
const commentsExpanded = ref(false);

const importModal = reactive({
  visible: false,
  loading: false,
  file: null as any,
  fileList: [] as any[],
  text: '',
  result: null as any,
});

const quick = reactive({
  visible: false,
  searching: false,
  saving: false,
  searched: false,
  parentData: [] as any[],
  terms: [] as any[],
  things: [] as any[],
  courses: [] as any[],
  results: [] as any[],
  selectedSlot: null as any,
  form: {
    name: '',
    age: undefined as number | undefined,
    gender: undefined as string | undefined,
    parent: undefined as number | undefined,
    remark: '',
    term: undefined as number | undefined,
    startDate: undefined as string | undefined,
    endDate: undefined as string | undefined,
    course: undefined as string | undefined,
    day: undefined as string | undefined,
    time: undefined as number | undefined,
    thing: undefined as number | undefined,
  },
});

const myform = ref<FormInstance>();

const dayLabels: Record<string, string> = {
  Mon: 'Monday',
  Tue: 'Tuesday',
  Wed: 'Wednesday',
  Thu: 'Thursday',
  Fri: 'Friday',
  Sat: 'Saturday',
  Sun: 'Sunday',
};

const dayLabel = (day: string | undefined) => dayLabels[day || ''] || day || '-';

const quickCourseOptions = computed(() => {
  return quick.courses.filter(course => course.active).map(course => course.title);
});

const quickDayOptions = computed(() => {
  return [...new Set(
    quick.things
      .filter((thing: any) => String(thing.status) !== '1')
      .map((thing: any) => thing.day)
      .filter(Boolean),
  )];
});

const quickTimeOptions = computed(() => {
  const times = quick.things
    .filter((thing: any) => (
      (!quick.form.day || thing.day === quick.form.day)
      && thing.time
      && String(thing.status) !== '1'
    ))
    .map((thing: any) => ({ id: thing.time, label: thing.time_title || thing.time }));
  return Array.from(new Map(times.map((time: any) => [time.id, time])).values());
});

onMounted(() => {
  loadRouteState();
});

watch(
  () => route.query.id,
  () => loadRouteState(),
);

const loadRouteState = () => {
  const studentId = Number(route.query.id);
  if (studentId > 0) {
    loadStudentDetail(studentId);
    return;
  }
  detail.visible = false;
  getDataList();
};

const formatList = (value: string[] | undefined) => {
  if (!value || value.length === 0) {
    return '-';
  }
  return value.join(', ');
};

const formatAbsenceStatus = (status: string | undefined) => {
  const labels: Record<string, string> = {
    pending: 'Pending',
    approved: 'Approved',
    makeup_available: 'Makeup available',
    completed: 'Completed',
    rejected: 'Rejected',
    canceled: 'Canceled',
  };
  return labels[status || ''] || status || 'Unknown';
};

const getAbsenceStatusColor = (status: string | undefined) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    approved: 'blue',
    makeup_available: 'cyan',
    completed: 'green',
    rejected: 'red',
    canceled: 'default',
  };
  return colors[status || ''] || 'default';
};

const formatTrialStatus = (status: string | undefined) => {
  const labels: Record<string, string> = {
    pending: 'Pending payment',
    approved: 'Approved',
    scheduled: 'Scheduled',
    rejected: 'Rejected',
    canceled: 'Canceled',
  };
  return labels[status || ''] || status || 'Trial';
};

const getTrialStatusColor = (status: string | undefined) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    approved: 'blue',
    scheduled: 'purple',
    rejected: 'red',
    canceled: 'default',
  };
  return colors[status || ''] || 'purple';
};

const visibleDetailComments = computed(() => {
  const comments = detail.record.comments || [];
  return commentsExpanded.value ? comments : comments.slice(0, 3);
});

const getDataList = () => {
  data.loading = true;
  listApi({
    keyword: data.keyword,
  })
    .then((res) => {
      data.loading = false;
      res.data.forEach((item: any, index: any) => {
        item.index = index + 1;
      });
      data.studentList = res.data;
    })
    .catch((err) => {
      data.loading = false;
      message.error(err.msg || 'Operation Failed');
    });
};

const getParentDataList = () => {
  if (!canManageStudents.value) {
    return;
  }
  listUserApi({})
    .then((res) => {
      modal.parentData = res.data
        .filter((item: any) => item.role === '1')
        .map((item: any) => ({
          value: item.id,
          label: `${item.nickname || item.username} · @${item.username} · ID ${item.id}${item.mobile ? ` · ${item.mobile}` : ''}`,
        }));
    })
    .catch((err) => {
      message.error(err.msg || 'Failed to load parents');
    });
};

const onSearchChange = (e: any) => {
  data.keyword = e?.target?.value || '';
};

const onSearch = (value?: string) => {
  if (typeof value === 'string') {
    data.keyword = value.trim();
  }
  data.page = 1;
  getDataList();
};

const rowSelection = ref({
  onChange: (selectedRowKeys: (string | number)[]) => {
    data.selectedRowKeys = selectedRowKeys;
  },
});

const resetForm = () => {
  for (const key in modal.form) {
    modal.form[key] = undefined;
  }
  myform.value?.resetFields();
};

const handleAdd = () => {
  if (!canManageStudents.value) {
    return;
  }
  if (!modal.parentData.length) {
    getParentDataList();
  }
  resetForm();
  modal.visible = true;
  modal.editFlag = false;
  modal.title = 'New Student';
};

const resetQuickForm = () => {
  quick.form.name = '';
  quick.form.age = undefined;
  quick.form.gender = undefined;
  quick.form.parent = undefined;
  quick.form.remark = '';
  quick.form.term = undefined;
  quick.form.startDate = undefined;
  quick.form.endDate = undefined;
  quick.form.course = undefined;
  quick.form.day = undefined;
  quick.form.time = undefined;
  quick.form.thing = undefined;
  quick.results = [];
  quick.selectedSlot = null;
  quick.searched = false;
};

const loadQuickOptions = async () => {
  const requests: Promise<any>[] = [listTermApi({}), listThingApi({}), listCourseCatalogApi({})];
  if (!quick.parentData.length) {
    requests.push(listUserApi({}));
  }

  try {
    const [termResponse, thingResponse, courseResponse, parentResponse] = await Promise.all(requests);
    quick.terms = termResponse?.data || [];
    quick.things = thingResponse?.data || [];
    quick.courses = courseResponse?.data || [];
    if (parentResponse) {
      quick.parentData = (parentResponse.data || [])
        .filter((item: any) => item.role === '1')
        .map((item: any) => ({
          value: item.id,
          label: `${item.nickname || item.username} · @${item.username} · ID ${item.id}${item.mobile ? ` · ${item.mobile}` : ''}`,
        }));
    }
  } catch (err: any) {
    message.error(err.msg || 'Failed to load class options');
  }
};

const openQuickAdd = async () => {
  if (!canManageStudents.value) {
    return;
  }
  resetQuickForm();
  quick.visible = true;
  await loadQuickOptions();
};

const closeQuickAdd = () => {
  if (quick.saving) {
    return;
  }
  quick.visible = false;
};

const clearQuickResults = () => {
  quick.results = [];
  quick.selectedSlot = null;
  quick.form.thing = undefined;
  quick.searched = false;
};

const selectedQuickTerm = computed(() => (
  quick.terms.find((term: any) => Number(term.id) === Number(quick.form.term))
));

const handleQuickTermChange = () => {
  const term = selectedQuickTerm.value;
  quick.form.startDate = term?.expect_time ? dayjs(term.expect_time).format('YYYY-MM-DD') : undefined;
  quick.form.endDate = term?.return_time ? dayjs(term.return_time).format('YYYY-MM-DD') : undefined;
  clearQuickResults();
};

const outsideQuickTerm = (current: Dayjs) => {
  const term = selectedQuickTerm.value;
  if (!term?.expect_time || !term?.return_time) return false;
  return current.isBefore(dayjs(term.expect_time), 'day') || current.isAfter(dayjs(term.return_time), 'day');
};

const disableQuickStartDate = (current: Dayjs) => (
  outsideQuickTerm(current)
  || Boolean(quick.form.endDate && current.isAfter(dayjs(quick.form.endDate), 'day'))
);

const disableQuickEndDate = (current: Dayjs) => (
  outsideQuickTerm(current)
  || Boolean(quick.form.startDate && current.isBefore(dayjs(quick.form.startDate), 'day'))
);

const handleQuickCourseChange = () => {
  quick.form.day = undefined;
  quick.form.time = undefined;
  clearQuickResults();
};

const findAvailableSlots = async () => {
  if (!quick.form.term || !quick.form.startDate || !quick.form.endDate || !quick.form.course) {
    message.warning('Please select the term, class dates, and course first');
    return;
  }

  quick.searching = true;
  quick.searched = false;
  quick.selectedSlot = null;
  try {
    const response = await availableSlotsApi({
      term: quick.form.term,
      start_date: quick.form.startDate,
      end_date: quick.form.endDate,
      course: quick.form.course,
      day: quick.form.day,
      time: quick.form.time,
    });
    quick.results = response.data || [];
    quick.searched = true;
    if (!quick.results.length) {
      message.info('No matching class found');
    }
  } catch (err: any) {
    message.error(err.msg || 'Failed to find available slots');
  } finally {
    quick.searching = false;
  }
};

const isQuickSlotAvailable = (slot: any) => (
  slot.available_seats === null
  || slot.available_seats === undefined
  || Number(slot.available_seats) > 0
);

const selectQuickSlot = (slot: any) => {
  if (!isQuickSlotAvailable(slot)) {
    return;
  }
  quick.selectedSlot = slot;
  quick.form.thing = slot.id;
};

const saveQuickStudent = async () => {
  if (!quick.form.name.trim()) {
    message.warning('Please enter student name');
    return;
  }
  if (!quick.form.term || !quick.form.startDate || !quick.form.endDate || !quick.selectedSlot) {
    message.warning('Please select an available class');
    return;
  }

  const formData = new FormData();
  formData.append('name', quick.form.name.trim());
  formData.append('term', String(quick.form.term));
  formData.append('start_date', quick.form.startDate);
  formData.append('end_date', quick.form.endDate);
  if (quick.selectedSlot.id) {
    formData.append('thing', String(quick.selectedSlot.id));
  } else {
    formData.append('course', quick.selectedSlot.title);
    formData.append('room', String(quick.selectedSlot.room_id));
    formData.append('day', quick.selectedSlot.day);
    formData.append('time', String(quick.selectedSlot.time_id));
  }
  if (quick.form.age !== undefined && quick.form.age !== null) formData.append('age', String(quick.form.age));
  if (quick.form.gender) formData.append('gender', quick.form.gender);
  if (quick.form.parent) formData.append('parent', String(quick.form.parent));
  if (quick.form.remark.trim()) formData.append('remark', quick.form.remark.trim());

  quick.saving = true;
  try {
    const response = await quickCreateApi(formData);
    notifyScheduleDataChanged();
    message.success(response.msg || 'Student and class created');
    quick.visible = false;
    getDataList();
  } catch (err: any) {
    message.error(err.msg || 'Failed to create student and class');
  } finally {
    quick.saving = false;
  }
};

const handleEdit = (record: any) => {
  if (!canManageStudents.value) {
    return;
  }
  if (!modal.parentData.length) {
    getParentDataList();
  }
  resetForm();
  modal.visible = true;
  modal.editFlag = true;
  modal.title = 'Edit Student';
  for (const key in modal.form) {
    modal.form[key] = record[key];
  }
};

const loadStudentDetail = async (studentId: number) => {
  detail.visible = true;
  detail.loading = true;
  commentsExpanded.value = false;
  try {
    const res = await detailApi({ id: studentId });
    detail.record = res.data || {};
  } catch (err: any) {
    message.error(err.msg || 'Failed to load student detail');
    detail.visible = false;
  } finally {
    detail.loading = false;
  }
};

const openImportComments = () => {
  if (!canManageStudents.value) {
    return;
  }
  importModal.visible = true;
  importModal.result = null;
};

const closeImportComments = () => {
  importModal.visible = false;
};

const beforeImportFileUpload = (file: any) => {
  const fileName = String(file?.name || '').toLowerCase();
  if (!fileName.endsWith('.csv')) {
    message.warning('Please select a CSV file');
    return false;
  }
  importModal.file = file;
  importModal.fileList = [file];
  importModal.result = null;
  return false;
};

const removeImportFile = () => {
  importModal.file = null;
  importModal.fileList = [];
};

const submitImportComments = async () => {
  if (!canManageStudents.value) {
    return;
  }
  const text = importModal.text.trim();
  if (!importModal.file && !text) {
    message.warning('Please select a CSV file or paste CSV content');
    return;
  }
  const formData = new FormData();
  if (importModal.file) {
    formData.append('file', importModal.file);
  }
  if (text) {
    formData.append('text', text);
  }
  importModal.loading = true;
  try {
    const res = await importCommentsApi(formData);
    importModal.result = res.data;
    notifyScheduleDataChanged();
    message.success(res.msg || 'Comments imported');
    if (!importModal.result?.error_count) {
      importModal.visible = false;
      importModal.text = '';
      removeImportFile();
    }
    if (detail.visible && detail.record.id) {
      loadStudentDetail(detail.record.id);
    }
  } catch (err: any) {
    message.error(err.msg || 'Failed to import comments');
  } finally {
    importModal.loading = false;
  }
};

const handleView = (record: any) => {
  router.push({
    name: 'student',
    query: { id: record.id },
  });
};

const closeDetail = () => {
  detail.visible = false;
  const returnTo = String(route.query.returnTo || '');
  if (returnTo.startsWith('/admin/schedule') || returnTo.startsWith('/admin/classroom')) {
    router.push(returnTo);
    return;
  }
  router.push({ name: 'student' });
};

const confirmDelete = (record: any) => {
  if (!canManageStudents.value) {
    return;
  }
  deleteApi({ ids: record.id })
    .then(() => {
      notifyScheduleDataChanged();
      getDataList();
    })
    .catch((err) => {
      message.error(err.msg || 'Operation Failed');
    });
};

const handleBatchDelete = () => {
  if (!canManageStudents.value) {
    return;
  }
  if (data.selectedRowKeys.length <= 0) {
    message.warn('Select items to delete');
    return;
  }

  deleteApi({ ids: data.selectedRowKeys.join(',') })
    .then(() => {
      message.success('Delete Successful');
      notifyScheduleDataChanged();
      data.selectedRowKeys = [];
      getDataList();
    })
    .catch((err) => {
      message.error(err.msg || 'Operation Failed');
    });
};

const handleOk = () => {
  if (!canManageStudents.value) {
    return;
  }
  myform.value
    ?.validate()
    .then(() => {
      const formData = new FormData();
      formData.append('name', modal.form.name || '');
      if (modal.form.age !== undefined && modal.form.age !== null) {
        formData.append('age', String(modal.form.age));
      }
      if (modal.form.gender) {
        formData.append('gender', modal.form.gender);
      }
      if (modal.form.parent !== undefined && modal.form.parent !== null && modal.form.parent !== '') {
        formData.append('parent', String(modal.form.parent));
      }
      if (modal.form.remark) {
        formData.append('remark', modal.form.remark);
      }

      const action = modal.editFlag ? updateApi({ id: modal.form.id }, formData) : createApi(formData);
      action
        .then(() => {
          notifyScheduleDataChanged();
          hideModal();
          getDataList();
        })
        .catch((err) => {
          message.error(err.msg || 'Operation Failed');
        });
    })
    .catch(() => {});
};

const handleCancel = () => {
  hideModal();
};

const hideModal = () => {
  modal.visible = false;
};
</script>

<style scoped lang="less">
.parent-identity {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.parent-identity strong {
  color: #152844;
}

.parent-identity span {
  color: #64748b;
  font-size: 12px;
}

.page-view {
  min-height: 100%;
  background: #fff;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.table-operations {
  margin-bottom: 16px;
  text-align: right;
}

.quick-help {
  margin-bottom: 16px;
}

.quick-filter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.quick-results {
  margin-top: 18px;
}

.quick-results-title {
  color: #334155;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.quick-slot {
  align-items: center;
  background: #f8fbff;
  border: 1px solid #b8d4f5;
  border-radius: 4px;
  color: #17365d;
  cursor: pointer;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 10px 12px;
  text-align: left;
  width: 100%;
}

.quick-slot:hover,
.quick-slot.selected {
  background: #eaf3ff;
  border-color: #1677ff;
}

.quick-slot.full {
  background: #fafafa;
  border-color: #d9d9d9;
  color: #8c8c8c;
  cursor: not-allowed;
}

.quick-slot-main {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.quick-slot-main span {
  color: #64748b;
  font-size: 12px;
}

.quick-slot-capacity {
  flex: 0 0 auto;
  font-weight: 600;
  text-align: right;
}

.quick-slot-capacity small {
  color: #16a34a;
  display: block;
  font-size: 11px;
  font-weight: 400;
  margin-top: 2px;
}

.quick-slot.full .quick-slot-capacity small {
  color: #dc2626;
}

.quick-drawer-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.class-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  line-height: 20px;
  min-width: 360px;
}

.detail-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 12px;
  line-height: 22px;
}

.detail-row-block {
  align-items: start;
}

.detail-label {
  color: #64748b;
  font-weight: 600;
}

.course-history {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trial-package-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trial-package-item {
  border: 1px solid #d8c7ff;
  border-left: 4px solid #722ed1;
  border-radius: 4px;
  background: #fbf9ff;
  padding: 10px 12px;
}

.trial-package-head {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.trial-course-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.trial-course-row {
  color: #334155;
  display: grid;
  gap: 10px;
  grid-template-columns: 78px minmax(0, 1fr);
  line-height: 20px;
}

.trial-course-missing {
  color: #b45309;
}

.course-history-item {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 10px 12px;
}

.course-history-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.course-history-meta {
  color: #475569;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 14px;
  line-height: 20px;
}

.absence-history {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.absence-history-item {
  border: 1px solid #ffd8bf;
  border-radius: 4px;
  background: #fffaf5;
  padding: 10px 12px;
}

.absence-history-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.absence-date {
  color: #b45309;
  font-weight: 600;
  margin-left: 10px;
}

.absence-history-meta {
  color: #475569;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 14px;
  line-height: 20px;
}

.absence-reason {
  color: #7c2d12;
  margin: 8px 0 0;
  white-space: pre-wrap;
}

.comment-history {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comment-history-item {
  border-left: 3px solid #84adff;
  background: #f8fafc;
  padding: 9px 11px;
}

.comment-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
}

.comment-history-item p {
  margin: 5px 0 0;
  color: #1e293b;
  line-height: 20px;
  white-space: pre-wrap;
}

.comment-toggle {
  align-self: flex-start;
  padding-left: 0;
}

.import-help {
  color: #475569;
  line-height: 22px;
  margin-bottom: 10px;
}

.import-help code {
  background: #f1f5f9;
  border-radius: 4px;
  color: #0f172a;
  display: block;
  margin-top: 6px;
  padding: 3px 6px;
}

.import-result {
  color: #166534;
  margin-top: 10px;
}

.import-fallback-label {
  color: #64748b;
  font-size: 12px;
  margin: 12px 0 6px;
}

.import-errors {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #9a3412;
  margin-top: 10px;
  padding: 8px 10px;
}

.trial-booking-session {
  border: 1px solid #d7e2ef;
  border-radius: 6px;
  padding: 12px 14px 0;
  margin-bottom: 12px;
}

.trial-booking-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.trial-empty-help {
  color: #b45309;
  font-size: 12px;
  margin-top: 6px;
}

.trial-teacher-warning {
  margin-top: 8px;
  padding: 8px 10px;
  border-left: 3px solid #d99b2b;
  background: #fff8e8;
  color: #76510d;
  font-size: 13px;
}

@media (max-width: 640px) {
  .trial-booking-fields {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .quick-filter-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
