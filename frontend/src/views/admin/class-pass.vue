<template>
  <div class="class-pass-page">
    <section class="page-head">
      <div>
        <h2>Class Pass</h2>
        <p>Issue passes, review parent requests, and deduct sessions after attendance.</p>
      </div>
      <div class="head-actions">
        <a-input-search
          v-model:value="keyword"
          placeholder="Parent, student, phone or ID"
          enter-button
          style="width: 300px"
          @search="loadData"
        />
        <a-button @click="loadData">Refresh</a-button>
        <a-button type="primary" @click="openCreatePass">New pass</a-button>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h3>Booking requests</h3>
          <p>Pending requests do not occupy the schedule until approved.</p>
        </div>
        <a-select v-model:value="bookingStatus" style="width: 160px" @change="loadBookings">
          <a-select-option value="">All status</a-select-option>
          <a-select-option value="pending">Pending</a-select-option>
          <a-select-option value="approved">Approved</a-select-option>
          <a-select-option value="completed">Completed</a-select-option>
          <a-select-option value="rejected">Rejected</a-select-option>
          <a-select-option value="canceled">Canceled</a-select-option>
        </a-select>
      </div>
      <a-table
        row-key="id"
        :columns="bookingColumns"
        :data-source="bookings"
        :pagination="{ pageSize: 8 }"
        :loading="loading.bookings"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'student'">
            <strong>{{ record.child_name }}</strong>
            <div class="muted">{{ record.parent_name || record.parent_username }}</div>
          </template>
          <template v-else-if="column.key === 'class'">
            <strong>{{ record.requested_class_name || 'Class' }}</strong>
            <div class="muted">
              {{ record.requested_date }} · {{ record.requested_class_day || 'Day' }}
              {{ record.requested_class_time || '' }}
            </div>
            <div class="muted">{{ record.requested_class_room || 'Room TBD' }}</div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="bookingStatusColor(record.status)">{{ record.status }}</a-tag>
            <div v-if="record.remaining_sessions !== undefined" class="muted">
              {{ record.remaining_sessions }} left
            </div>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-popconfirm
                v-if="record.status === 'pending'"
                title="Approve this booking?"
                @confirm="reviewBooking(record, 'approve')"
              >
                <a-button size="small" type="primary">Approve</a-button>
              </a-popconfirm>
              <a-popconfirm
                v-if="record.status === 'pending'"
                title="Reject this booking?"
                @confirm="reviewBooking(record, 'reject')"
              >
                <a-button size="small">Reject</a-button>
              </a-popconfirm>
              <a-popconfirm
                v-if="record.status === 'approved'"
                title="Mark completed and deduct one session?"
                @confirm="completeBooking(record)"
              >
                <a-button size="small">Complete</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h3>Issued passes</h3>
          <p>Only parents with the Class Pass flag can request a time from mobile.</p>
        </div>
      </div>
      <a-table
        row-key="id"
        :columns="passColumns"
        :data-source="passes"
        :pagination="{ pageSize: 8 }"
        :loading="loading.passes"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'student'">
            <strong>{{ record.child_name }}</strong>
            <div class="muted">{{ record.parent_name || record.parent_username }}</div>
          </template>
          <template v-else-if="column.key === 'sessions'">
            <strong>{{ record.remaining_sessions }}</strong>
            <span class="muted"> / {{ record.total_sessions }}</span>
            <div class="muted">used {{ record.used_sessions || 0 }}</div>
          </template>
          <template v-else-if="column.key === 'valid'">
            <span>{{ record.valid_from || '-' }} to {{ record.valid_until || '-' }}</span>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status === 'active' ? 'green' : 'default'">{{ record.status }}</a-tag>
          </template>
        </template>
      </a-table>
    </section>

    <a-modal
      v-model:visible="passModal.open"
      title="New class pass"
      :confirm-loading="passModal.saving"
      @ok="createPass"
    >
      <a-form layout="vertical">
        <a-form-item label="Student">
          <a-select
            v-model:value="passForm.child_id"
            show-search
            option-filter-prop="label"
            placeholder="Choose student"
          >
            <a-select-option
              v-for="child in students"
              :key="child.id"
              :value="child.id"
              :label="`${child.name} ${child.parent_name || child.parent_username || ''}`"
            >
              {{ child.name }} · {{ child.parent_name || child.parent_username || 'Parent' }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Title">
          <a-input v-model:value="passForm.title" />
        </a-form-item>
        <a-form-item label="Total sessions">
          <a-input-number v-model:value="passForm.total_sessions" :min="1" style="width: 100%" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="Valid from">
              <a-input v-model:value="passForm.valid_from" placeholder="YYYY-MM-DD" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="Valid until">
              <a-input v-model:value="passForm.valid_until" placeholder="YYYY-MM-DD" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="Note">
          <a-textarea v-model:value="passForm.note" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import {
  bookingCompleteApi,
  bookingListApi,
  bookingReviewApi,
  passCreateApi,
  passListApi,
} from '/@/api/admin/class-pass';
import { listApi as listStudentApi } from '/@/api/admin/student';

const loading = reactive({
  passes: false,
  bookings: false,
  students: false,
});

const passes = ref<any[]>([]);
const bookings = ref<any[]>([]);
const students = ref<any[]>([]);
const bookingStatus = ref('');
const keyword = ref('');

const passModal = reactive({
  open: false,
  saving: false,
});

const passForm = reactive({
  child_id: undefined as number | undefined,
  title: 'Class Pass',
  total_sessions: 10,
  valid_from: '',
  valid_until: '',
  note: '',
});

const bookingColumns = [
  { title: 'Student', key: 'student' },
  { title: 'Requested class', key: 'class' },
  { title: 'Pass', dataIndex: 'pass_title' },
  { title: 'Status', key: 'status' },
  { title: 'Parent note', dataIndex: 'parent_note' },
  { title: 'Action', key: 'action', width: 220 },
];

const passColumns = [
  { title: 'Student', key: 'student' },
  { title: 'Title', dataIndex: 'title' },
  { title: 'Sessions', key: 'sessions' },
  { title: 'Valid', key: 'valid' },
  { title: 'Status', key: 'status' },
  { title: 'Note', dataIndex: 'note' },
];

const bookingStatusColor = (status: string) => {
  if (status === 'pending') return 'orange';
  if (status === 'approved') return 'blue';
  if (status === 'completed') return 'green';
  if (status === 'rejected' || status === 'canceled') return 'red';
  return 'default';
};

const loadPasses = () => {
  loading.passes = true;
  passListApi({ keyword: keyword.value })
    .then((res) => {
      passes.value = res.data || [];
    })
    .finally(() => {
      loading.passes = false;
    });
};

const loadBookings = () => {
  loading.bookings = true;
  bookingListApi({ status: bookingStatus.value, keyword: keyword.value })
    .then((res) => {
      bookings.value = res.data || [];
    })
    .finally(() => {
      loading.bookings = false;
    });
};

const loadStudents = () => {
  loading.students = true;
  listStudentApi({})
    .then((res) => {
      students.value = res.data || [];
    })
    .finally(() => {
      loading.students = false;
    });
};

const loadData = () => {
  loadBookings();
  loadPasses();
  loadStudents();
};

const openCreatePass = () => {
  passForm.child_id = undefined;
  passForm.title = 'Class Pass';
  passForm.total_sessions = 10;
  passForm.valid_from = '';
  passForm.valid_until = '';
  passForm.note = '';
  passModal.open = true;
};

const createPass = () => {
  if (!passForm.child_id) {
    message.warning('Please choose a student');
    return;
  }
  passModal.saving = true;
  passCreateApi({ ...passForm })
    .then((res) => {
      if (res.code === 0) {
        message.success(res.msg || 'Class pass created');
        passModal.open = false;
        loadPasses();
      } else {
        message.error(res.msg || 'Create failed');
      }
    })
    .finally(() => {
      passModal.saving = false;
    });
};

const reviewBooking = (record: any, action: 'approve' | 'reject') => {
  bookingReviewApi({ id: record.id, action })
    .then((res) => {
      if (res.code === 0) {
        message.success(res.msg || 'Booking updated');
        loadBookings();
        loadPasses();
      } else {
        message.error(res.msg || 'Update failed');
      }
    });
};

const completeBooking = (record: any) => {
  bookingCompleteApi({ id: record.id, deduct: true })
    .then((res) => {
      if (res.code === 0) {
        message.success(res.msg || 'Booking completed');
        loadBookings();
        loadPasses();
      } else {
        message.error(res.msg || 'Complete failed');
      }
    });
};

onMounted(loadData);
</script>

<style scoped lang="less">
.class-pass-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-head,
.panel {
  background: #fff;
  border: 1px solid #e5e8ef;
  border-radius: 8px;
  padding: 18px 20px;
}

.page-head,
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-head h2,
.panel h3 {
  margin: 0;
  color: #082042;
}

.page-head p,
.panel-head p {
  margin: 4px 0 0;
  color: #6b778c;
}

.head-actions {
  display: flex;
  gap: 8px;
}

.muted {
  color: #6b778c;
  font-size: 12px;
}
</style>
