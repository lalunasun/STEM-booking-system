<template>
  <div>
    <!--页面区域-->
    <div class="page-view">
      <div class="table-operations">
        <a-space>
          <a-button type="primary" @click="handleAdd">Add</a-button>
          <a-button danger @click="handleBatchDelete">Mass Delete</a-button>
        </a-space>
      </div>
      <a-table
        size="middle"
        rowKey="id"
        :loading="data.loading"
        :columns="columns"
        :data-source="data.tagList"
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
        <template #bodyCell="{ text, record, index, column }">
          <template v-if="column.key === 'operation'">
            <span>
              <a @click="handleEdit(record)">Edit</a>
              <a-divider type="vertical" />
              <a @click="openPermissions(record)">Allowed courses</a>
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
      :visible="permissions.visible"
      :title="permissions.room?.title + ' - Allowed courses'"
      ok-text="Save"
      cancel-text="Cancel"
      :style="{ top: '24px' }"
      :body-style="{ maxHeight: 'calc(100vh - 180px)', overflowY: 'auto' }"
      :confirm-loading="permissions.saving"
      :ok-button-props="{ disabled: !permissions.term || permissions.loading || permissions.failed }"
      @cancel="permissions.visible = false"
      @ok="savePermissions"
    >
      <a-form layout="vertical">
        <a-form-item label="Term" required>
          <a-select v-model:value="permissions.term" :disabled="permissions.saving"
            :options="permissions.terms.map(item => ({value: item.id, label: item.title}))"
            @change="loadPermissions" />
        </a-form-item>
        <a-spin :spinning="permissions.loading">
          <template v-if="permissions.term && !permissions.failed">
            <a-form-item label="Allowed courses">
              <a-checkbox-group v-model:value="permissions.courseIds" class="course-options"
                :disabled="permissions.loading || permissions.saving"
                :options="permissions.courses.map(item => ({value: item.id, label: item.title}))" />
            </a-form-item>
            <a-button :disabled="permissions.loading || permissions.saving" @click="permissions.courseIds = [...permissions.suggested]">
              <template #icon><import-outlined /></template>
              Use existing courses
            </a-button>
            <a-form-item label="Note" style="margin-top: 16px">
              <a-textarea v-model:value="permissions.note" :maxlength="500" :rows="3" show-count />
            </a-form-item>
            <div class="permission-status">{{ permissions.configured ? 'Configured for this term' : 'Not configured for this term' }}</div>
          </template>
          <a-result v-else-if="permissions.failed" status="error" title="Could not load permissions">
            <template #extra><a-button @click="loadPermissions">Retry</a-button></template>
          </a-result>
        </a-spin>
      </a-form>
    </a-modal>
    <!--弹窗区域-->
    <div>
      <a-modal
        :visible="modal.visile"
        :forceRender="true"
        :title="modal.title"
        ok-text="OK"
        cancel-text="Cancel"
        @cancel="handleCancel"
        @ok="handleOk"
      >
        <div>
          <a-form ref="myform" :label-col="{ style: { width: '120px' } }" :model="modal.form" :rules="modal.rules">
            <a-row :gutter="24">
              <a-col span="24">
                <a-form-item label="Room name" name="title">
                  <a-input placeholder="Please enter" v-model:value="modal.form.title"></a-input>
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="Room seats" name="seat">
                  <a-input placeholder="Please enter" v-model:value="modal.form.seat"></a-input>
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </div>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { FormInstance, message } from 'ant-design-vue';
  import { createApi, listApi, updateApi, deleteApi, permissionsApi, savePermissionsApi } from '/@/api/admin/tag';
  import { listApi as listTerms } from '/@/api/admin/term';
  import { listApi as listCourses } from '/@/api/admin/course';
  import { ImportOutlined } from '@ant-design/icons-vue';
  import { notifyScheduleDataChanged } from '/@/utils/schedule-sync';

  const permissions = reactive({
    visible: false, loading: false, saving: false, failed: false, configured: false,
    room: null as any, term: undefined as number | undefined,
    terms: [] as any[], courses: [] as any[], courseIds: [] as number[],
    suggested: [] as number[], note: '',
  });
  let permissionRequest = 0;
  const loadPermissions = async () => {
    const request = ++permissionRequest;
    permissions.loading = true;
    permissions.failed = false;
    permissions.courseIds = [];
    permissions.suggested = [];
    permissions.note = '';
    try {
      const response = await permissionsApi({room: permissions.room.id, term: permissions.term});
      if (request !== permissionRequest) return;
      permissions.configured = response.data.configured;
      permissions.courseIds = response.data.course_ids;
      permissions.suggested = response.data.suggested_course_ids;
      permissions.note = response.data.note;
    } catch (err: any) {
      if (request === permissionRequest) {
        permissions.failed = true;
        message.error(err.msg || 'Could not load permissions');
      }
    } finally {
      if (request === permissionRequest) permissions.loading = false;
    }
  };
  const openPermissions = async (room: any) => {
    permissions.room = room;
    permissions.visible = true;
    permissions.loading = true;
    permissions.failed = true;
    permissions.term = undefined;
    try {
      const [terms, courses] = await Promise.all([listTerms({}), listCourses({})]);
      permissions.terms = terms.data || [];
      permissions.courses = (courses.data || []).filter(item => item.active);
      const now = Date.now();
      permissions.term = permissions.terms.find(item =>
        Date.parse(item.expect_time) <= now && Date.parse(item.return_time) >= now)?.id;
      permissions.failed = false;
      if (permissions.term) await loadPermissions();
    } catch (err: any) {
      message.error(err.msg || 'Could not load room options');
    } finally { permissions.loading = false; }
  };
  const savePermissions = async () => {
    if (!permissions.term || permissions.loading || permissions.failed) return;
    permissions.saving = true;
    try {
      await savePermissionsApi({
        room: permissions.room.id, term: permissions.term,
        course_ids: permissions.courseIds, note: permissions.note,
      });
      notifyScheduleDataChanged();
      message.success('Room courses saved');
      permissions.visible = false;
    } catch (err: any) { message.error(err.msg || 'Could not save permissions'); }
    finally { permissions.saving = false; }
  };


  const columns = reactive([
    {
      title: 'No.',
      dataIndex: 'index',
      key: 'index',
      align: 'center'
    },
    {
      title: 'Room name',
      dataIndex: 'title',
      key: 'title',
      align: 'center'
    },
    {
      title: 'Room seats',
      dataIndex: 'seat',
      key: 'seat',
      align: 'center'
    },
    {
      title: 'Operation',
      dataIndex: 'action',
      key: 'operation',
      align: 'center',
      fixed: 'right',
      width: 290,
    },
  ]);

  // 页面数据
  const data = reactive({
    tagList: [],
    loading: false,
    keyword: '',
    selectedRowKeys: [] as any[],
    pageSize: 10,
    page: 1,
  });

  // 弹窗数据源
  const modal = reactive({
    visile: false,
    editFlag: false,
    title: '',
    form: {
      id: undefined,
      title: undefined,
      seat: undefined
    },
    rules: {
      title: [{ required: true, message: 'Please enter', trigger: 'change' }],
      seat: [{ required: true, message: 'Please enter', trigger: 'change' }],
    },
  });

  const myform = ref<FormInstance>();

  onMounted(() => {
    getDataList();
  });

  const getDataList = () => {
    data.loading = true;
    listApi({
      keyword: data.keyword,
    })
      .then((res) => {
        data.loading = false;
        console.log(res);
        res.data.forEach((item: any, index: any) => {
          item.index = index + 1;
        });
        data.tagList = res.data;
      })
      .catch((err) => {
        data.loading = false;
        console.log(err);
      });
  };

  const onSearchChange = (e: Event) => {
    data.keyword = e?.target?.value;
    console.log(data.keyword);
  };

  const onSearch = () => {
    getDataList();
  };

  const rowSelection = ref({
    onChange: (selectedRowKeys: (string | number)[], selectedRows: DataItem[]) => {
      console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows);
      data.selectedRowKeys = selectedRowKeys;
    },
  });

  const handleAdd = () => {
    resetModal();
    modal.visile = true;
    modal.editFlag = false;
    modal.title = 'Add';
    // 重置
    for (const key in modal.form) {
      modal.form[key] = undefined;
    }
  };
  const handleEdit = (record: any) => {
    resetModal();
    modal.visile = true;
    modal.editFlag = true;
    modal.title = 'Edit';
    // 重置
    for (const key in modal.form) {
      modal.form[key] = undefined;
    }
    for (const key in record) {
      modal.form[key] = record[key];
    }
  };

  const confirmDelete = (record: any) => {
    console.log('delete', record);
    deleteApi({ ids: record.id })
      .then((res) => {
        getDataList();
      })
      .catch((err) => {
        message.error(err.msg || 'Operation Failed');
      });
  };

  const handleBatchDelete = () => {
    console.log(data.selectedRowKeys);
    if (data.selectedRowKeys.length <= 0) {
      console.log('hello');
      message.warn('Select items to delete');
      return;
    }
    deleteApi({ ids: data.selectedRowKeys.join(',') })
      .then((res) => {
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
        if (modal.editFlag) {
          updateApi({ id: modal.form.id }, modal.form)
            .then((res) => {
              hideModal();
              getDataList();
            })
            .catch((err) => {
              message.error(err.msg || 'Operation Failed');
            });
        } else {
          createApi(modal.form)
            .then((res) => {
              hideModal();
              getDataList();
            })
            .catch((err) => {
              message.error(err.msg || 'Operation Failed');
            });
        }
      })
      .catch((err) => {
        console.log('Cannot be blank');
      });
  };

  const handleCancel = () => {
    hideModal();
  };

  // 恢复表单初始状态
  const resetModal = () => {
    myform.value?.resetFields();
  };

  // 关闭弹窗
  const hideModal = () => {
    modal.visile = false;
  };
</script>

<style scoped lang="less">
  .course-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .course-options :deep(.ant-checkbox-wrapper) { margin-left: 0; overflow-wrap: anywhere; }
  .permission-status { color: #627d98; margin-top: 16px; }
  @media (max-width: 480px) { .course-options { grid-template-columns: 1fr; } }
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

  .table-operations > button {
    margin-right: 8px;
  }
</style>
