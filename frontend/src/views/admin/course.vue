<template>
  <div class="page-view">
    <div class="table-operations">
      <a-space>
        <a-button type="primary" @click="openAdd">New course</a-button>
        <a-button danger :disabled="!selectedRowKeys.length" @click="removeSelected">Delete</a-button>
      </a-space>
    </div>
    <a-table row-key="id" :loading="loading" :columns="columns" :data-source="courses" :row-selection="rowSelection">
      <template #bodyCell="{ record, column }">
        <template v-if="column.key === 'active'">{{ record.active ? 'Active' : 'Inactive' }}</template>
        <template v-else-if="column.key === 'operation'"><a @click="openEdit(record)">Edit</a></template>
      </template>
    </a-table>
    <a-modal :visible="visible" :title="editing ? 'Edit course' : 'New course'" @cancel="visible = false" @ok="save">
      <a-form ref="formRef" :model="form" :rules="rules">
        <a-form-item label="Course name" name="title">
          <a-input v-model:value="form.title" placeholder="For example, VEX IQ" />
        </a-form-item>
        <a-form-item label="Status" name="active">
          <a-switch v-model:checked="form.active" checked-children="Active" un-checked-children="Inactive" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { FormInstance, message } from 'ant-design-vue';
import { createApi, deleteApi, listApi, updateApi } from '/@/api/admin/course';

const columns = [
  { title: 'Course name', dataIndex: 'title', key: 'title' },
  { title: 'Class instances', dataIndex: 'instance_count', key: 'instance_count' },
  { title: 'Status', dataIndex: 'active', key: 'active' },
  { title: 'Operation', key: 'operation', width: 120 },
];
const loading = ref(false);
const courses = ref<any[]>([]);
const selectedRowKeys = ref<any[]>([]);
const visible = ref(false);
const editing = ref(false);
const formRef = ref<FormInstance>();
const form = reactive({ id: undefined as number | undefined, title: '', active: true });
const rules = { title: [{ required: true, message: 'Please enter a course name' }] };
const rowSelection = { onChange: (keys: any[]) => (selectedRowKeys.value = keys) };

const load = async () => {
  loading.value = true;
  try { courses.value = (await listApi({})).data || []; }
  finally { loading.value = false; }
};
const reset = () => { form.id = undefined; form.title = ''; form.active = true; };
const openAdd = () => { reset(); editing.value = false; visible.value = true; };
const openEdit = (record: any) => { form.id = record.id; form.title = record.title; form.active = record.active; editing.value = true; visible.value = true; };
const save = async () => {
  try {
    await formRef.value?.validate();
    const request = editing.value ? updateApi({ id: form.id }, form) : createApi(form);
    await request;
    message.success('Saved'); visible.value = false; await load();
  } catch (error: any) {
    message.error(error?.msg || 'Cannot save course');
  }
};
const removeSelected = async () => {
  try { await deleteApi({ ids: selectedRowKeys.value.join(',') }); message.success('Deleted'); selectedRowKeys.value = []; await load(); }
  catch (error: any) { message.error(error?.msg || 'Cannot delete course'); }
};
onMounted(load);
</script>

<style scoped lang="less">
.page-view { min-height: 100%; background: #fff; padding: 24px; }
.table-operations { margin-bottom: 16px; text-align: right; }
</style>
