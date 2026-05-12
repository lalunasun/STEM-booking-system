<template>
  <div>
    <div class="page-view">
      <div class="table-operations">
        <a-space>
          <a-button type="primary" @click="handleAdd">New</a-button>
          <a-button danger @click="handleBatchDelete">Mass Delete</a-button>
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
          <template v-if="column.key === 'parent'">
            <span>{{ record.parent_name || record.parent_username || '-' }}</span>
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
          <template v-if="column.key === 'operation'">
            <span>
              <a @click="handleView(record)">View Detail</a>
              <a-divider type="vertical" />
              <a @click="handleEdit(record)">Edit</a>
              <a-divider type="vertical" />
              <a-popconfirm title="Sure to delete?" ok-text="Yes" cancel-text="No" @confirm="confirmDelete(record)">
                <a href="#" style="color: red;">Delete</a>
              </a-popconfirm>
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
            <a-form-item label="Parent" name="parent">
              <a-select
                placeholder="Please select"
                allowClear
                show-search
                optionFilterProp="label"
                v-model:value="modal.form.parent"
                :options="modal.parentData"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <a-modal
      :visible="detail.visible"
      title="Student Detail"
      :footer="null"
      @cancel="detail.visible = false"
    >
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
          <span class="detail-label">Parent</span>
          <span>{{ detail.record.parent_name || detail.record.parent_username || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Phone</span>
          <span>{{ detail.record.phone || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Active terms</span>
          <span>{{ formatList(detail.record.active_terms) }}</span>
        </div>
        <div class="detail-row detail-row-block">
          <span class="detail-label">Courses</span>
          <div class="class-list">
            <div v-for="item in detail.record.active_classes" :key="item">{{ item }}</div>
            <span v-if="!detail.record.active_classes || detail.record.active_classes.length === 0">-</span>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message } from 'ant-design-vue';
import { createApi, deleteApi, listApi, updateApi } from '/@/api/admin/student';
import { listApi as listUserApi } from '/@/api/admin/user';

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
    title: 'Active Classes',
    dataIndex: 'active_classes',
    key: 'active_classes',
    align: 'center',
    width: 520,
  },
  {
    title: 'Operation',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 190,
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
    parent: undefined,
  },
  rules: {
    name: [{ required: true, message: 'Please enter student name', trigger: 'change' }],
    parent: [{ required: true, message: 'Please select parent', trigger: 'change' }],
  },
});

const detail = reactive({
  visible: false,
  record: {} as any,
});

const myform = ref<FormInstance>();

onMounted(() => {
  getDataList();
  getParentDataList();
});

const formatList = (value: string[] | undefined) => {
  if (!value || value.length === 0) {
    return '-';
  }
  return value.join(', ');
};

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
  listUserApi({})
    .then((res) => {
      modal.parentData = res.data
        .filter((item: any) => item.role === '1')
        .map((item: any) => ({
          value: item.id,
          label: `${item.nickname || item.username}${item.mobile ? ` (${item.mobile})` : ''}`,
        }));
    })
    .catch((err) => {
      message.error(err.msg || 'Failed to load parents');
    });
};

const onSearchChange = (e: Event) => {
  data.keyword = e?.target?.value;
};

const onSearch = () => {
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
  resetForm();
  modal.visible = true;
  modal.editFlag = false;
  modal.title = 'New Student';
};

const handleEdit = (record: any) => {
  resetForm();
  modal.visible = true;
  modal.editFlag = true;
  modal.title = 'Edit Student';
  for (const key in modal.form) {
    modal.form[key] = record[key];
  }
};

const handleView = (record: any) => {
  detail.record = record;
  detail.visible = true;
};

const confirmDelete = (record: any) => {
  deleteApi({ ids: record.id })
    .then(() => {
      getDataList();
    })
    .catch((err) => {
      message.error(err.msg || 'Operation Failed');
    });
};

const handleBatchDelete = () => {
  if (data.selectedRowKeys.length <= 0) {
    message.warn('Select items to delete');
    return;
  }

  deleteApi({ ids: data.selectedRowKeys.join(',') })
    .then(() => {
      message.success('Delete Successful');
      data.selectedRowKeys = [];
      getDataList();
    })
    .catch((err) => {
      message.error(err.msg || 'Operation Failed');
    });
};

const handleOk = () => {
  myform.value
    ?.validate()
    .then(() => {
      const formData = new FormData();
      formData.append('name', modal.form.name || '');
      if (modal.form.age !== undefined && modal.form.age !== null) {
        formData.append('age', String(modal.form.age));
      }
      formData.append('parent', modal.form.parent || '');

      const action = modal.editFlag ? updateApi({ id: modal.form.id }, formData) : createApi(formData);
      action
        .then(() => {
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
</style>
