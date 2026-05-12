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
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { listApi } from '/@/api/admin/course-adjustment';

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
  { title: 'Created', dataIndex: 'created_time', key: 'created_time', align: 'center', width: 170 },
]);

const data = reactive({
  list: [],
  loading: false,
  keyword: '',
  pageSize: 20,
  page: 1,
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

const statusColor = (status: string) => {
  if (status === 'pending') {
    return 'orange';
  }
  if (status === 'approved' || status === 'completed') {
    return 'green';
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
</style>
