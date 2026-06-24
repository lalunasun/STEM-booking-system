<template>
  <div class="page-view">
    <div class="table-operations">
      <a-input-search
        v-model:value="data.keyword"
        addon-before="Student"
        enter-button
        style="width: 320px"
        @search="getDataList"
      />
    </div>
    <a-table
      size="middle"
      rowKey="id"
      :loading="data.loading"
      :columns="columns"
      :data-source="data.list"
      :scroll="{ x: 1300 }"
      :pagination="{
        size: 'default',
        current: data.page,
        pageSize: data.pageSize,
        onChange: (current) => (data.page = current),
        showSizeChanger: false,
        showTotal: (total) => `Total of ${total} data`,
      }"
    >
      <template #bodyCell="{ record, column }">
        <template v-if="column.key === 'request_type'">
          <a-tag color="blue">{{ formatRequestType(record.request_type) }}</a-tag>
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
        </template>
        <template v-if="column.key === 'note'">
          <div class="note-cell">
            <div v-if="record.parent_note">Parent: {{ record.parent_note }}</div>
            <div v-if="record.admin_note">Admin: {{ record.admin_note }}</div>
            <span v-if="!record.parent_note && !record.admin_note">-</span>
          </div>
        </template>
        <template v-if="column.key === 'recommendations'">
          <div class="recommendation-cell">
            <template v-if="record.status === 'completed' && record.selected_target_date">
              <div class="selected-schedule">
                <strong>Scheduled:</strong> {{ formatSelectedSchedule(record) }}
              </div>
            </template>
            <template v-else>
              <div v-for="(option, index) in record.recommended_option_list" :key="`${record.id}-${index}`">
                {{ index + 1 }}. {{ formatOption(option) }}
              </div>
              <div v-if="record.admin_extra_recommendation_detail" class="extra-option">
                3. {{ formatOption(record.admin_extra_recommendation_detail) }}
              </div>
              <span v-if="!hasRecommendations(record)">-</span>
            </template>
          </div>
        </template>
        <template v-if="column.key === 'operation'">
          <div v-if="record.status === 'pending'" class="operation-cell">
            <a @click="openReview(record, 'approve')">Approve</a>
            <a-divider type="vertical" />
            <a class="reject-link" @click="openReview(record, 'reject')">Reject</a>
          </div>
          <div v-else-if="record.status === 'makeup_available'" class="operation-cell">
            <a @click="openExtraRecommendation(record)">Add 3rd Option</a>
            <a-divider type="vertical" />
            <a @click="openConfirmSchedule(record)">Confirm Schedule</a>
          </div>
          <span v-else>-</span>
        </template>
      </template>
    </a-table>
    <a-modal
      v-model:visible="reviewModal.visible"
      :title="reviewModal.action === 'approve' ? 'Approve Request' : 'Reject Request'"
      ok-text="Confirm"
      cancel-text="Close"
      @ok="submitReview"
    >
      <div class="review-form">
        <p class="hint" v-if="reviewModal.action === 'approve'">
          Approving a cancel request will create makeup eligibility only. It will not schedule a makeup class yet.
        </p>
        <label>Admin note</label>
        <textarea v-model="reviewModal.adminNote" rows="4" placeholder="Optional note"></textarea>
      </div>
    </a-modal>
    <a-modal
      v-model:visible="extraModal.visible"
      title="Add 3rd Makeup Option"
      ok-text="Save"
      cancel-text="Close"
      @ok="submitExtraRecommendation"
    >
      <div class="review-form">
        <p class="hint">
          Options exclude the student's existing classes and stay in the current term.
          A later term is included only when the student is already enrolled in that term.
        </p>
        <label>Makeup option</label>
        <a-select v-model:value="extraModal.selectedValue" placeholder="Select an option">
          <a-select-option
            v-for="option in extraModal.options"
            :key="optionKey(option)"
            :value="optionKey(option)"
          >
            {{ formatOption(option) }}
          </a-select-option>
        </a-select>
      </div>
    </a-modal>
    <a-modal
      v-model:visible="scheduleModal.visible"
      title="Confirm Makeup Schedule"
      ok-text="Schedule"
      cancel-text="Close"
      @ok="submitConfirmSchedule"
    >
      <div class="review-form">
        <p class="hint">This will place the student into the selected class as a rescheduled student.</p>
        <label>Makeup option</label>
        <a-select v-model:value="scheduleModal.selectedValue" placeholder="Select an option">
          <a-select-option
            v-for="option in scheduleModal.options"
            :key="optionKey(option)"
            :value="optionKey(option)"
          >
            {{ formatOption(option) }}
          </a-select-option>
        </a-select>
        <label>Admin note</label>
        <textarea v-model="scheduleModal.adminNote" rows="3" placeholder="Optional note"></textarea>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue';
import {
  addExtraRecommendationApi,
  confirmMakeupScheduleApi,
  listApi,
  recommendationOptionsApi,
  reviewApi,
} from '/@/api/admin/course-adjustment';
import { useUserStore } from '/@/store';

const userStore = useUserStore();

const columns = reactive([
  { title: 'No.', dataIndex: 'index', key: 'index', align: 'center', width: 70 },
  { title: 'Student', dataIndex: 'student_name', key: 'student_name', align: 'center', width: 160 },
  { title: 'Parent', dataIndex: 'parent_name', key: 'parent_name', align: 'center', width: 160 },
  { title: 'Phone', dataIndex: 'parent_phone', key: 'parent_phone', align: 'center', width: 140 },
  { title: 'Class', dataIndex: 'original_class_title', key: 'original_class_title', align: 'center', width: 160 },
  { title: 'Class date', dataIndex: 'original_lesson_date', key: 'original_lesson_date', align: 'center', width: 120 },
  { title: 'Time', dataIndex: 'original_time', key: 'original_time', align: 'center', width: 120 },
  { title: 'Term', dataIndex: 'original_term_title', key: 'original_term_title', align: 'center', width: 140 },
  { title: 'Type', dataIndex: 'request_type', key: 'request_type', align: 'center', width: 150 },
  { title: 'Status', dataIndex: 'status', key: 'status', align: 'center', width: 120 },
  { title: 'Note', dataIndex: 'note', key: 'note', width: 260 },
  { title: 'Recommendations', dataIndex: 'recommendations', key: 'recommendations', width: 360 },
  { title: 'Created', dataIndex: 'created_time', key: 'created_time', align: 'center', width: 170 },
  { title: 'Operation', dataIndex: 'operation', key: 'operation', align: 'center', width: 150, fixed: 'right' },
]);

const data = reactive({
  list: [],
  loading: false,
  keyword: '',
  pageSize: 20,
  page: 1,
});
const reviewModal = reactive({
  visible: false,
  action: 'approve',
  record: null as any,
  adminNote: '',
});
const extraModal = reactive({
  visible: false,
  record: null as any,
  options: [] as any[],
  selectedValue: '',
});
const scheduleModal = reactive({
  visible: false,
  record: null as any,
  options: [] as any[],
  selectedValue: '',
  adminNote: '',
});

onMounted(() => {
  getDataList();
});

const getDataList = () => {
  data.loading = true;
  listApi({ keyword: data.keyword })
    .then((res) => {
      data.loading = false;
      res.data.forEach((item: any, index: number) => {
        item.index = index + 1;
      });
      data.list = res.data;
    })
    .catch(() => {
      data.loading = false;
    });
};

const formatRequestType = (type: string) => {
  if (type === 'cancel_class') {
    return 'Cancel Class';
  }
  if (type === 'makeup_class') {
    return 'Makeup Class';
  }
  if (type === 'admin_manual_reschedule') {
    return 'Manual';
  }
  return type || '-';
};

const optionKey = (option: any) => `${option.class_id}|${option.date}`;

const formatOption = (option: any) => {
  if (!option) {
    return '-';
  }
  const seats = option.available_seats === null || option.available_seats === undefined ? '-' : option.available_seats;
  const term = option.term_title ? ` | ${option.term_title}` : '';
  return `${option.class_title} | ${option.date} ${option.day} | ${option.time} | ${option.room}${term} | seats ${seats}`;
};

const formatSelectedSchedule = (record: any) => {
  const parts = [
    record.selected_target_class_title,
    record.selected_target_date,
    record.selected_target_day,
    record.selected_target_time,
    record.selected_target_room,
  ].filter(Boolean);
  return parts.length ? parts.join(' | ') : '-';
};

const hasRecommendations = (record: any) => {
  return (record.recommended_option_list && record.recommended_option_list.length > 0) || record.admin_extra_recommendation_detail;
};

const openReview = (record: any, action: string) => {
  reviewModal.record = record;
  reviewModal.action = action;
  reviewModal.adminNote = '';
  reviewModal.visible = true;
};

const submitReview = () => {
  if (!reviewModal.record) {
    message.error('Please select a request');
    return;
  }
  reviewApi({
    id: reviewModal.record.id,
    action: reviewModal.action,
    admin_note: reviewModal.adminNote,
    admin_user_id: userStore.admin_user_id,
  }).then((res) => {
    if (res.code !== 0) {
      message.error(res.msg || 'Review failed');
      return;
    }
    message.success(reviewModal.action === 'approve' ? 'Request approved' : 'Request rejected');
    reviewModal.visible = false;
    getDataList();
  }).catch((err) => {
    message.error(err.msg || 'Review failed');
  });
};

const openExtraRecommendation = (record: any) => {
  extraModal.record = record;
  extraModal.options = [];
  extraModal.selectedValue = '';
  extraModal.visible = true;
  recommendationOptionsApi({ id: record.id }).then((res) => {
    if (res.code !== 0) {
      message.error(res.msg || 'Load options failed');
      return;
    }
    const existingKeys = new Set((record.recommended_option_list || []).map((item: any) => optionKey(item)));
    extraModal.options = (res.data || []).filter((item: any) => !existingKeys.has(optionKey(item)));
  }).catch((err) => {
    message.error(err.msg || 'Load options failed');
  });
};

const submitExtraRecommendation = () => {
  if (!extraModal.record) {
    message.error('Please select a makeup eligibility');
    return;
  }
  if (!extraModal.selectedValue) {
    message.error('Please select an option');
    return;
  }
  const [classId, date] = extraModal.selectedValue.split('|');
  addExtraRecommendationApi({
    id: extraModal.record.id,
    class_id: classId,
    date,
  }).then((res) => {
    if (res.code !== 0) {
      message.error(res.msg || 'Save failed');
      return;
    }
    message.success('Extra recommendation saved');
    extraModal.visible = false;
    getDataList();
  }).catch((err) => {
    message.error(err.msg || 'Save failed');
  });
};

const openConfirmSchedule = (record: any) => {
  scheduleModal.record = record;
  scheduleModal.options = [
    ...(record.recommended_option_list || []),
    ...(record.admin_extra_recommendation_detail ? [record.admin_extra_recommendation_detail] : []),
  ];
  scheduleModal.selectedValue = scheduleModal.options.length > 0 ? optionKey(scheduleModal.options[0]) : '';
  scheduleModal.adminNote = '';
  scheduleModal.visible = true;
};

const submitConfirmSchedule = () => {
  if (!scheduleModal.record) {
    message.error('Please select a makeup eligibility');
    return;
  }
  if (!scheduleModal.selectedValue) {
    message.error('Please select a makeup option');
    return;
  }
  const [classId, date] = scheduleModal.selectedValue.split('|');
  confirmMakeupScheduleApi({
    id: scheduleModal.record.id,
    class_id: classId,
    date,
    admin_note: scheduleModal.adminNote,
  }).then((res) => {
    if (res.code !== 0) {
      message.error(res.msg || 'Schedule failed');
      return;
    }
    message.success('Makeup class scheduled');
    scheduleModal.visible = false;
    getDataList();
  }).catch((err) => {
    message.error(err.msg || 'Schedule failed');
  });
};

const statusColor = (status: string) => {
  if (status === 'pending') {
    return 'orange';
  }
  if (status === 'approved' || status === 'completed') {
    return 'green';
  }
  if (status === 'makeup_available') {
    return 'cyan';
  }
  if (status === 'rejected' || status === 'canceled') {
    return 'red';
  }
  return 'default';
};
</script>

<style scoped lang="less">
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

.note-cell {
  max-width: 260px;
  white-space: normal;
  line-height: 20px;
}

.selected-schedule {
  border-left: 3px solid #52c41a;
  background: #f6ffed;
  color: #135200;
  padding: 6px 8px;
}

.recommendation-cell {
  max-width: 360px;
  white-space: normal;
  line-height: 20px;

  .extra-option {
    color: #1677ff;
    margin-top: 4px;
  }
}

.operation-cell {
  white-space: nowrap;
}

.reject-link {
  color: #d9363e;
}

.review-form {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .hint {
    color: #5f77a6;
    line-height: 20px;
    margin: 0 0 8px;
  }

  label {
    color: #152844;
    font-weight: 600;
  }

  textarea {
    border: 1px solid #d9d9d9;
    border-radius: 2px;
    padding: 8px;
  }
}
</style>
