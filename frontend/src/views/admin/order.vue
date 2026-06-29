<template>
  <div class="page-view">
    <div class="table-operations">
      <a-space>
        <a-button danger @click="handleBatchDelete">Mass delete</a-button>
      </a-space>
    </div>

    <a-table
      size="middle"
      rowKey="id"
      :loading="data.loading"
      :columns="columns"
      :data-source="data.orderList"
      :scroll="{ x: 'max-content' }"
      :row-selection="rowSelection"
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
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(text)">{{ statusText(text) }}</a-tag>
        </template>

        <template v-else-if="column.key === 'course'">
          <div class="course-cell">
            <strong>{{ record.title || '--' }}</strong>
            <span>{{ record.day || '--' }} | {{ record.time_title || '--' }} | {{ record.room_title || '--' }}</span>
            <span v-if="record.term_title">Term: {{ record.term_title }}</span>
          </div>
        </template>

        <template v-else-if="column.key === 'operation'">
          <a-space>
            <a v-if="record.status === 1 && !isTrialOrder(record)" @click="openEdit(record)">Edit</a>
            <a-popconfirm
              v-if="record.status === 1"
              title="Confirm payment for this order?"
              ok-text="Yes"
              cancel-text="No"
              @confirm="confirmPayment(record)"
            >
              <a>Confirm payment</a>
            </a-popconfirm>
            <a-popconfirm
              v-if="record.status === 2"
              title="Add to lesson?"
              ok-text="Yes"
              cancel-text="No"
              @confirm="confirmCheckIn(record)"
            >
              <a>Schedule</a>
            </a-popconfirm>
            <a-popconfirm
              v-if="record.status === 6"
              title="Mark this order as done?"
              ok-text="Yes"
              cancel-text="No"
              @confirm="confirmCheckOut(record)"
            >
              <a>Mark done</a>
            </a-popconfirm>
            <a-popconfirm
              v-if="record.status !== 8 && record.status !== 7"
              title="Sure to cancel?"
              ok-text="Yes"
              cancel-text="No"
              @confirm="confirmCancel(record)"
            >
              <a>Cancel</a>
            </a-popconfirm>
            <a-popconfirm title="Sure to delete?" ok-text="Yes" cancel-text="No" @confirm="confirmDelete(record)">
              <a class="danger-link">Delete</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:visible="editModal.visible"
      title="Edit pending order"
      ok-text="Save"
      cancel-text="Cancel"
      :confirm-loading="editModal.saving"
      @ok="submitEdit"
    >
      <a-form layout="vertical">
        <a-form-item label="Student">
          <a-select
            v-model:value="editModal.form.child"
            show-search
            option-filter-prop="label"
            placeholder="Select student"
          >
            <a-select-option
              v-for="student in optionData.students"
              :key="student.id"
              :value="student.id"
              :label="studentLabel(student)"
            >
              {{ studentLabel(student) }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="Class">
          <a-select
            v-model:value="editModal.form.thing"
            show-search
            option-filter-prop="label"
            placeholder="Select class"
          >
            <a-select-option
              v-for="course in optionData.courses"
              :key="course.id"
              :value="course.id"
              :label="courseLabel(course)"
            >
              {{ courseLabel(course) }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="Term">
          <a-select
            v-model:value="editModal.form.term"
            allow-clear
            show-search
            option-filter-prop="label"
            placeholder="Select term"
          >
            <a-select-option
              v-for="term in optionData.terms"
              :key="term.id"
              :value="term.id"
              :label="term.title"
            >
              {{ term.title }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <div class="form-grid">
          <a-form-item label="Lessons">
            <a-input-number v-model:value="editModal.form.num" :min="1" :precision="0" style="width: 100%" />
          </a-form-item>
          <a-form-item label="Amount">
            <a-input v-model:value="editModal.form.amount" placeholder="Amount" />
          </a-form-item>
        </div>

        <a-form-item label="Admin note">
          <a-textarea v-model:value="editModal.form.remark" :rows="3" placeholder="Optional note" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue';
import { listApi, updateApi, markPaidApi, deleteApi, cancelApi, checkInApi, checkOutApi } from '/@/api/admin/order';
import { listApi as listStudentApi } from '/@/api/admin/student';
import { listApi as listThingApi } from '/@/api/admin/thing';
import { listApi as listTermApi } from '/@/api/admin/term';

const columns = reactive([
  { title: 'No.', dataIndex: 'index', key: 'index', align: 'center', width: 70 },
  { title: 'Parent', dataIndex: 'username', key: 'username', align: 'center', width: 150 },
  { title: 'Child', dataIndex: 'child_name', key: 'child_name', align: 'center', width: 170 },
  { title: 'Phone number', dataIndex: 'receiver_phone', key: 'receiver_phone', align: 'center', width: 150 },
  { title: 'Course', dataIndex: 'title', key: 'course', align: 'left', width: 280 },
  { title: 'Lessons', dataIndex: 'num', key: 'num', align: 'center', width: 90 },
  { title: 'Amount', dataIndex: 'amount', key: 'amount', align: 'center', width: 100 },
  { title: 'Order status', dataIndex: 'status', key: 'status', align: 'center', width: 150 },
  { title: 'Start', dataIndex: 'expect_time', key: 'expect_time', align: 'center', width: 120 },
  { title: 'Finish', dataIndex: 'return_time', key: 'return_time', align: 'center', width: 120 },
  { title: 'Remark', dataIndex: 'remark', key: 'remark', align: 'center', width: 180 },
  { title: 'Order time', dataIndex: 'order_time', key: 'order_time', align: 'center', width: 180 },
  { title: 'Operation', dataIndex: 'action', key: 'operation', align: 'center', fixed: 'right', width: 330 },
]);

const data = reactive({
  orderList: [] as any[],
  loading: false,
  keyword: '',
  selectedRowKeys: [] as any[],
  pageSize: 20,
  page: 1,
});

const optionData = reactive({
  students: [] as any[],
  courses: [] as any[],
  terms: [] as any[],
});

const editModal = reactive({
  visible: false,
  saving: false,
  record: null as any,
  form: {
    child: undefined as number | undefined,
    thing: undefined as number | undefined,
    term: undefined as number | undefined,
    num: 1,
    amount: '',
    remark: '',
  },
});

const ORDER_BADGE_REFRESH_EVENT = 'admin-order-badge-refresh';

const refreshOrderBadge = () => {
  window.dispatchEvent(new Event(ORDER_BADGE_REFRESH_EVENT));
};

onMounted(() => {
  getDataList();
  loadOptions();
});

const statusText = (status: number) => {
  const labels: Record<number, string> = {
    1: 'Pending payment',
    2: 'Paid',
    6: 'Scheduled',
    7: 'Canceled',
    8: 'Done',
  };
  return labels[Number(status)] || 'Unknown';
};

const statusColor = (status: number) => {
  const colors: Record<number, string> = {
    1: 'red',
    2: 'cyan',
    6: 'green',
    7: 'purple',
    8: 'default',
  };
  return colors[Number(status)] || 'default';
};

const isTrialOrder = (record: any) => Array.isArray(record.trial_slots) && record.trial_slots.length > 0;

const studentLabel = (student: any) => {
  const parent = student.parent_name || student.parent_username || 'No parent';
  return `${student.name} (${parent})`;
};

const courseLabel = (course: any) => {
  const pieces = [course.title, course.day, course.time_title || course.time, course.room_title || course.tag_title].filter(Boolean);
  return pieces.join(' | ');
};

const loadOptions = () => {
  listStudentApi({})
    .then((res) => {
      optionData.students = res.data || [];
    })
    .catch(() => {
      optionData.students = [];
    });
  listThingApi({})
    .then((res) => {
      optionData.courses = res.data || [];
    })
    .catch(() => {
      optionData.courses = [];
    });
  listTermApi({})
    .then((res) => {
      optionData.terms = res.data || [];
    })
    .catch(() => {
      optionData.terms = [];
    });
};

const getDataList = () => {
  data.loading = true;
  listApi({ keyword: data.keyword })
    .then((res) => {
      const rows = res.data || [];
      rows.forEach((item: any, index: number) => {
        item.index = index + 1;
        item.expect_time = item.expect_time || '--';
        item.return_time = item.return_time || '--';
        item.remark = item.remark || '--';
      });
      data.orderList = rows;
    })
    .catch((err) => {
      message.error(err.msg || 'Failed to load orders');
    })
    .finally(() => {
      data.loading = false;
    });
};

const rowSelection = ref({
  onChange: (selectedRowKeys: (string | number)[]) => {
    data.selectedRowKeys = selectedRowKeys;
  },
});

const openEdit = (record: any) => {
  if (record.status !== 1) {
    message.warning('Only pending payment orders can be edited');
    return;
  }
  editModal.record = record;
  editModal.form.child = record.child;
  editModal.form.thing = record.thing;
  editModal.form.term = record.term;
  editModal.form.num = Number(record.num || 1);
  editModal.form.amount = record.amount || '';
  editModal.form.remark = record.remark === '--' ? '' : record.remark || '';
  editModal.visible = true;
};

const submitEdit = () => {
  if (!editModal.record) return;
  const formData = new FormData();
  if (editModal.form.child) formData.append('child', String(editModal.form.child));
  if (editModal.form.thing) formData.append('thing', String(editModal.form.thing));
  if (editModal.form.term) formData.append('term', String(editModal.form.term));
  formData.append('num', String(editModal.form.num || 1));
  formData.append('amount', editModal.form.amount || '');
  formData.append('remark', editModal.form.remark || '');

  editModal.saving = true;
  updateApi({ id: editModal.record.id }, formData)
    .then(() => {
      message.success('Order updated');
      editModal.visible = false;
      getDataList();
    })
    .catch((err) => {
      message.error(err.msg || 'Failed to update order');
    })
    .finally(() => {
      editModal.saving = false;
    });
};

const confirmPayment = (record: any) => {
  markPaidApi({ id: record.id })
    .then(() => {
      message.success('Payment confirmed');
      getDataList();
      refreshOrderBadge();
    })
    .catch((err) => {
      message.error(err.msg || 'Failed to confirm payment');
    });
};

const confirmCheckIn = (record: any) => {
  if (record.status !== 2) {
    message.error('Order status wrong');
    return;
  }
  checkInApi({ id: record.id })
    .then(() => {
      getDataList();
      refreshOrderBadge();
      message.success('Successfully scheduled');
    })
    .catch((err) => {
      message.error(err.msg || 'Operation failed');
    });
};

const confirmCheckOut = (record: any) => {
  checkOutApi({ id: record.id })
    .then(() => {
      getDataList();
      refreshOrderBadge();
      message.success('Order done');
    })
    .catch((err) => {
      message.error(err.msg || 'Operation failed');
    });
};

const confirmCancel = (record: any) => {
  cancelApi({ id: record.id })
    .then(() => {
      getDataList();
      refreshOrderBadge();
      message.success('Canceled');
    })
    .catch((err) => {
      message.error(err.msg || 'Operation failed');
    });
};

const confirmDelete = (record: any) => {
  deleteApi({ ids: record.id })
    .then(() => {
      getDataList();
      refreshOrderBadge();
      message.success('Deleted');
    })
    .catch((err) => {
      message.error(err.msg || 'Operation failed');
    });
};

const handleBatchDelete = () => {
  if (data.selectedRowKeys.length <= 0) {
    message.warn('Please select orders to delete');
    return;
  }
  deleteApi({ ids: data.selectedRowKeys.join(',') })
    .then(() => {
      message.success('Deleted');
      data.selectedRowKeys = [];
      getDataList();
      refreshOrderBadge();
    })
    .catch((err) => {
      message.error(err.msg || 'Operation failed');
    });
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

.course-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  line-height: 1.35;
}

.course-cell span {
  color: #667085;
  font-size: 12px;
}

.danger-link {
  color: #cf1322;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
</style>
