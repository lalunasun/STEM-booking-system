<template>
  <div>
    <!--页面区域-->
    <div class="page-view">
      <div class="table-operations">
        <a-space>
          <a-button type="primary" @click="handleAdd">New</a-button>
          <a-button  danger @click="handleBatchDelete">Mass Delete</a-button>
          <a-input-search addon-before="Title" enter-button @search="onSearch" @change="onSearchChange" />
        </a-space>
      </div>
      <a-table
          size="middle"
          rowKey="id"
          :loading="data.loading"
          :columns="columns"
          :data-source="data.dataList"
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
              <a-popconfirm title="Sure to delete?" ok-text="OK" cancel-text="Cancel" @confirm="confirmDelete(record)">
                <a href="#" style="color: red;">Delete</a>
              </a-popconfirm>
            </span>
          </template>
        </template>
      </a-table>
    </div>

    <!--弹窗区域-->
    <div>
      <a-modal
          :visible="modal.visile"
          :forceRender="true"
          :title="modal.title"
          width="880px"
          ok-text="OK"
          cancel-text="Cancel"
          @cancel="handleCancel"
          @ok="handleOk"
      >
        <div>
          <a-form ref="myform" :label-col="{ style: { width: '120px' } }" :model="modal.form" :rules="modal.rules">
            <a-row :gutter="24">
              <a-col span="24">
                <a-form-item label="Class Name" name="title">
                  <a-input placeholder="Please enter" v-model:value="modal.form.title"></a-input>
                </a-form-item>
              </a-col>
              <a-col span="12">
                <a-form-item label="Classification" name="classification">
                  <a-select placeholder="Please select"
                            allowClear
                            :options="modal.cData"
                            :field-names="{ label: 'title', value: 'id',}"
                            v-model:value="modal.form.classification"
                            >
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col span="12">
                <a-form-item label="Room" name="tag">
                  <a-select  placeholder="Please select" allowClear v-model:value="modal.form.tag">
                    <template v-for="item in modal.tagData">
                      <a-select-option :value="item.id">{{item.title}}</a-select-option>
                    </template>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col span="24">
                <a-form-item label="Cover Img">
                  <a-upload-dragger
                      name="file"
                      accept="image/*"
                      :multiple="false"
                      :before-upload="beforeUpload"
                      v-model:file-list="fileList"
                  >
                    <p class="ant-upload-drag-icon">
                      <template v-if="modal.form.coverUrl">
                        <img :src="modal.form.coverUrl"  style="width: 60px;height: 80px;"/>
                      </template>
                      <template v-else>
                        <file-image-outlined />
                      </template>
                    </p>
                    <p class="ant-upload-text">
                      Please select the cover image
                    </p>
                  </a-upload-dragger>
                </a-form-item>
              </a-col>

              <a-col span="24">
                <a-form-item label="Description">
                  <a-textarea placeholder="Please enter" v-model:value="modal.form.description"></a-textarea>
                </a-form-item>
              </a-col>
              
              <a-col span="13">
                <a-form-item label="Price" name="price">
                  <a-input-number  placeholder="Please enter" :min="0" v-model:value="modal.form.price" style="width: 100%;"></a-input-number>
                </a-form-item>
              </a-col>

              <a-col span="12">
                <a-form-item label="day" name="day">
                  <a-select placeholder="Please select" v-model:value="modal.form.day" style="width: 100%;">
                    <a-select-option value="Tue">Tuesday</a-select-option>
                    <a-select-option value="Wed">Wednesday</a-select-option>
                    <a-select-option value="Thu">Thursday</a-select-option>
                    <a-select-option value="Fri">Friday</a-select-option>
                    <a-select-option value="Sat">Saturday</a-select-option>
                    <a-select-option value="Sun">Sunday</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col span="12">
                <a-form-item label="Time period" name="time">
                  <a-select placeholder="Please select"
                            allowClear
                            :options="modal.timeData"
                            :field-names="{ label: 'time', value: 'id',}"
                            v-model:value="modal.form.time"
                            >
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col span="12">
                <a-form-item label="Status" name="status">
                  <a-select placeholder="Please select" allowClear v-model:value="modal.form.status">
                    <a-select-option key="0" value="0">Available</a-select-option>
                    <a-select-option key="1" value="1">Unavailable</a-select-option>
                  </a-select>
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
import { FormInstance, message, SelectProps } from 'ant-design-vue';
import { createApi, listApi, updateApi, deleteApi } from '/@/api/admin/thing';
import {listApi as listClassificationApi} from '/@/api/admin/classification'
import {listApi as listTagApi} from '/@/api/admin/tag'
import {listApi as listTimeApi} from '/@/api/admin/time'
import {BASE_URL} from "/@/store/constants";
import { FileImageOutlined } from '@ant-design/icons-vue';
const savedFormData = reactive({
  title: undefined,
  classification: undefined,
  tag: undefined,
  price: undefined,
  day: undefined,
  status: undefined,
  cover: undefined,
  coverUrl: undefined,
});
const columns = reactive([
//columns:ColumnType<any>[]=[
  {
    title: 'No.',
    dataIndex: 'index',
    key: 'index',
    width: 60
  },
  {
    title: 'Class name',
    dataIndex: 'title',
    key: 'title',
  },

  {
    title: 'Price',
    dataIndex: 'price',
    key: 'price'
  },
  {
    title: 'Day',
    dataIndex: 'day',
    key: 'day'
  },
  {
    title: 'Time',
    dataIndex: 'time_title',
    key: 'time'
  },

  {
    title: 'Room',
    dataIndex: 'room_name',
    key: 'tag',

  },
  {
    title: 'Status',
    dataIndex: 'display_status',
    key: 'status',
    customRender: ({ text }) => text || 'Available',
  },
  {
    title: 'Operation',
    dataIndex: 'action',
    key: 'operation',
    align: 'center',
    fixed: 'right',
    width: 140,
  },
]);

const beforeUpload = (file: File) => {
  // 改文件名
  const fileName = new Date().getTime().toString() + '.' + file.type.substring(6);
  const copyFile = new File([file], fileName);
  console.log(copyFile);
  modal.form.imageFile = copyFile;
  return false;
};

// 文件列表
const fileList = ref<any[]>([]);

// 页面数据
const data = reactive({
  dataList: [],
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
  cData: [],
  timeData: [],
  tagData: [{}],
  form: {
    id: undefined,
    title: undefined,
    classification: undefined,
    tag: undefined,

    price: undefined,
    day: undefined,
    time: undefined,
    status: undefined,
    cover: undefined,
    coverUrl: undefined,
    imageFile: undefined
  },
  rules: {
    title: [{ required: true, message: 'Please enter the Title', trigger: 'change' }],
    classification: [{ required: true, message: 'Please select the Classification', trigger: 'change' }],
    tag: [{ required: true, message: 'Please select a Room to teach', trigger: 'change'}],
    price: [{ required: true, message: 'Please enter the Price', trigger: 'change' }],
    status: [{ required: true, message: 'Please choose the status', trigger: 'change' }],
    day: [{ required: true, message: 'Please select', trigger: 'change' }],

    time: [{ required: true, message: 'Please enter the time pieriod', trigger: 'change' }],
  },
});

const myform = ref<FormInstance>();

onMounted(() => {
  getDataList();
  getCDataList();
  getTimeDataList();
  getTagDataList();
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
        data.dataList = res.data;
        
      })
      .catch((err) => {
        data.loading = false;
        console.log(err);
      });
}

const getCDataList = () => {
  listClassificationApi({}).then(res => {
    modal.cData = res.data
  })
}
const getTimeDataList = () => {
  listTimeApi({}).then(res => {
    modal.timeData = res.data
  })
}
const getTagDataList = ()=> {
  listTagApi({}).then(res => {
    res.data.forEach((item, index) => {
      item.index = index + 1
    })
    modal.tagData = res.data
  })
}

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
  modal.title = 'New';
  // 重置
  for (const key in modal.form) {
    modal.form[key] = savedFormData[key];
  }
  modal.form.cover = undefined
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
    if(record[key]) {
      modal.form[key] = record[key];
    }
  }
  if(modal.form.cover) {
    modal.form.coverUrl = BASE_URL + modal.form.cover
    modal.form.cover = undefined
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
        const formData = new FormData();
        if(modal.editFlag) {
          formData.append('id', modal.form.id)
        }
        formData.append('title', modal.form.title)
        if (modal.form.classification) {
          formData.append('classification', modal.form.classification)
        }
        if (modal.form.tag) {
         
              formData.append('tag', modal.form.tag)
            
          
        }
        if (modal.form.imageFile) {
          formData.append('cover', modal.form.imageFile)
        }
        formData.append('description', modal.form.description || '')
        formData.append('price', modal.form.price || '')
        console.log(1111111111111111111)
        console.log(modal.form.day)
        if (modal.form.day) {
          formData.append('day', modal.form.day)
        }
        if (modal.form.time) {
          formData.append('time', modal.form.time)
        }
        if (modal.form.status) {
          formData.append('status', modal.form.status)
        }

        if (modal.editFlag) {
          updateApi({
            id: modal.form.id
          },formData)
              .then((res) => {
                hideModal();
                getDataList();
                for (const key in savedFormData) { 
                  savedFormData[key] = modal.form[key]; 
                }
              })
              .catch((err) => {
                console.log(err);
                message.error(err.msg || 'Operation Failed');
              });
        } else {
          createApi(formData)
              .then((res) => {
                hideModal();
                getDataList();
                for (const key in savedFormData) { 
                  savedFormData[key] = modal.form[key]; 
                }
              })
              .catch((err) => {
                console.log(err);
                message.error(err.msg || 'Operation Failed');
              });
        }
      })
      .catch((err) => {
        console.log(err);
      });
};

const handleCancel = () => {
  hideModal();
};

// 恢复表单初始状态
const resetModal = () => {
  myform.value?.resetFields();
  fileList.value = []
};

// 关闭弹窗
const hideModal = () => {
  modal.visile = false;
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

.table-operations > button {
  margin-right: 8px;
}
</style>
